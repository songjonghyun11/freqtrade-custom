# -*- coding: utf-8 -*-
from typing import Dict, Any, List
from pathlib import Path
import json
import pandas as pd

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import IntParameter, DecimalParameter


class TestDonchianFearGreedStrategy(IStrategy):
    """
    Donchian 돌파 + 거래량 배수 + (옵션) Fear&Greed 게이트
    - 룩어헤드 방지: Donchian 상단은 shift(1), merge_asof(backward)
    - 파라미터 우선순위(중요):
        1) config.strategy_parameters[TestDonchianFearGreedStrategy]
        2) Hyperopt Parameter .value (IntParameter/DecimalParameter)
        3) buy_params (디폴트)
    """
    timeframe = "5m"
    startup_candle_count = 120

    # ---- 디폴트 파라미터 (백테 기본값) ----
    buy_params = {
        "use_fg": 1,
        "buy_fg_threshold": 50,
        "buy_vol_mult": 1.20,
        "buy_dc_period": 20,
    }

    # ---- 하이퍼옵트/실행 파라미터(.value 필수) ----
    use_fg = IntParameter(0, 1, default=buy_params["use_fg"], space="buy", optimize=True)
    buy_fg_threshold = IntParameter(45, 80, default=buy_params["buy_fg_threshold"], space="buy", optimize=True)
    buy_vol_mult = DecimalParameter(1.00, 2.50, default=buy_params["buy_vol_mult"], decimals=2, space="buy", optimize=True)
    buy_dc_period = IntParameter(12, 40, default=buy_params["buy_dc_period"], space="buy", optimize=True)

    # ROI/SL(필요 시 하이퍼옵트에서 조정)
    minimal_roi = {"0": 0.05, "60": 0.02, "240": 0.0}
    stoploss = -0.08

    # ---------------- 내부 유틸 ----------------
    @staticmethod
    def _pair_safe(pair: str) -> str:
        # 'BTC/USDT' -> 'BTC_USDT'
        return pair.replace("/", "_")

    def _strategy_overrides(self) -> Dict[str, Any]:
        """
        config.strategy_parameters.TestDonchianFearGreedStrategy 블록을 가져옴.
        없으면 빈 dict.
        """
        cfg = self.config or {}
        sp = cfg.get("strategy_parameters", {})
        return sp.get(self.__class__.__name__, {}) if isinstance(sp, dict) else {}

    def _param(self, key: str, cast=None):
        """
        파라미터 우선순위:
        1) config override (strategy_parameters)
        2) Hyperopt Parameter .value (동일 이름의 속성이 Parameter일 때)
        3) buy_params 디폴트
        """
        # 1) config override
        ov = self._strategy_overrides()
        if key in ov:
            v = ov[key]
            return cast(v) if cast else v

        # 2) Hyperopt Parameter .value
        if hasattr(self, key):
            attr = getattr(self, key)
            if hasattr(attr, "value"):
                v = attr.value
                return cast(v) if cast else v

        # 3) defaults
        v = self.buy_params.get(key, None)
        return cast(v) if cast else v

    def _candidate_fg_paths(self, pair: str) -> List[Path]:
        userdir = Path(self.config.get("user_data_dir", "/freqtrade/user_data"))
        safe = self._pair_safe(pair)
        return [
            userdir / "collectors" / "data" / safe / "fear_greed.json",
            userdir / "collectors" / "data" / "fear_greed.json",
            userdir / "data" / "custom" / "fear_greed.csv",
            userdir / "data" / "custom" / "fear_greed.json",
        ]

    def _load_fg_series(self, pair: str) -> pd.Series:
        """
        다양한 포맷(csv/json/jsonl)을 수용해서 FG 시계열 반환(UTC, float)
        파일 없거나 파싱 실패 → 상수 50 폴백
        """
        for p in self._candidate_fg_paths(pair):
            if not p.exists():
                continue
            try:
                if p.suffix.lower() == ".csv":
                    df = pd.read_csv(p)
                else:
                    # json or jsonl
                    txt = p.read_text(encoding="utf-8").strip()
                    try:
                        data = json.loads(txt)  # list or dict
                        if isinstance(data, dict):
                            data = data.get("data", [])
                    except Exception:
                        # jsonl
                        data = [json.loads(line) for line in txt.splitlines() if line.strip()]
                    df = pd.DataFrame(data)
                # 컬럼 정규화: timestamp(UTC sec) or date(ISO), value
                if "timestamp" in df.columns:
                    t = pd.to_datetime(df["timestamp"], unit="s", utc=True, errors="coerce")
                elif "date" in df.columns:
                    t = pd.to_datetime(df["date"], utc=True, errors="coerce")
                else:
                    continue
                s = pd.Series(df["value"].astype(float).values, index=t, name="fg").sort_index()
                s = s.dropna().ffill()
                if len(s):
                    return s
            except Exception:
                continue

        # 폴백(상수 50, 더미 인덱스)
        idx = pd.date_range("2000-01-01", periods=1, tz="UTC")
        return pd.Series([50.0], index=idx, name="fg")

    # ---------------- 지표 ----------------
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
        df = dataframe.copy()
        # UTC 통일
        df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")

        p = int(self._param("buy_dc_period", int))
        vol_mult = float(self._param("buy_vol_mult", float))

        # Donchian 상단/하단 (상단은 직전값으로 shift(1) → 룩어헤드 제거)
        df["dc_high"] = df["high"].rolling(p, min_periods=p).max().shift(1)
        df["dc_low"] = df["low"].rolling(p, min_periods=p).min()

        # 거래량 배수 필터
        vol_ma = df["volume"].rolling(p, min_periods=p).mean()
        df["vol_ok"] = df["volume"] > (vol_ma * vol_mult)

        # Fear & Greed 병합 (옵션 데이터) - backward asof + tolerance
        try:
            s = self._load_fg_series(metadata.get("pair", "BTC/USDT"))
            fgdf = s.rename("fg").to_frame().reset_index().rename(columns={"index": "date"})
            df = pd.merge_asof(
                df.sort_values("date"),
                fgdf.sort_values("date"),
                on="date",
                direction="backward",
                tolerance=pd.Timedelta("30D"),
            )
            df["fg"] = df["fg"].fillna(50.0).astype(float)
        except Exception:
            df["fg"] = 50.0

        return df

    # ---------------- 매수 ----------------
    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
        df = dataframe.copy()

        cond_dc = (df["close"] > df["dc_high"])   # 직전 Donchian 상단 돌파
        cond_vol = df["vol_ok"]                   # 거래량 배수 충족

        use_fg = int(self._param("use_fg", int)) == 1
        th = int(self._param("buy_fg_threshold", int))
        cond_fg = (df["fg"] >= th) if use_fg else True

        df.loc[:, "buy"] = 0
        df.loc[cond_dc & cond_vol & cond_fg, "buy"] = 1
        return df

    # ---------------- 매도 ----------------
    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
        df = dataframe.copy()
        # 단순: Donchian 하단 이탈 시 청산
        cond_exit = (df["close"] < df["dc_low"])
        df.loc[:, "sell"] = 0
        df.loc[cond_exit, "sell"] = 1
        return df
