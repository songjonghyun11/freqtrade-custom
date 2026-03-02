import argparse, json, zipfile, math
from pathlib import Path
import pandas as pd
import numpy as np

def find_trades_in_obj(obj, path="root"):
    """Recursively find candidate trade lists (list[dict]) with keys like pair/open_date/profit_abs."""
    candidates = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            candidates += find_trades_in_obj(v, f"{path}.{k}")
    elif isinstance(obj, list):
        if len(obj) > 0 and isinstance(obj[0], dict):
            keys = set(obj[0].keys())
            must = {"pair", "open_date", "close_date"}
            maybe = {"profit_abs", "profit_ratio", "exit_reason", "enter_tag"}
            if must.issubset(keys) and (len(keys & maybe) >= 2):
                candidates.append((path, obj))
        for i, v in enumerate(obj[:50]):  # cap deep scan cost
            candidates += find_trades_in_obj(v, f"{path}[{i}]")
    return candidates

def read_zip_json(zip_path: Path):
    with zipfile.ZipFile(zip_path) as zf:
        json_files = [n for n in zf.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
        # prefer the main result json: backtest-result-*.json
        main = None
        for n in json_files:
            if n.startswith("backtest-result-") and n.count("_") == 0:
                main = n
                break
        if not main:
            # fallback: largest json
            main = sorted(json_files, key=lambda x: zf.getinfo(x).file_size, reverse=True)[0]
        data = json.loads(zf.read(main))
        return main, data

def locate_ohlcv(pair: str):
    sym = pair.replace("/", "_")
    # Candidates (root first, then spot/5m)
    cands = [
        Path(f"user_data/data/binance/{sym}-5m.feather"),
        Path(f"user_data/data/binance/spot/5m/{sym}-5m.feather"),
    ]
    exists = [p for p in cands if p.exists()]
    if not exists:
        raise FileNotFoundError(f"OHLCV feather not found for {pair}: tried {cands}")
    # choose the one with larger mtime OR bigger size (usually newer)
    exists.sort(key=lambda p: (p.stat().st_mtime, p.stat().st_size), reverse=True)
    return exists[0]

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-12)
    return 100 - (100 / (1 + rs))

def compute_features(df: pd.DataFrame):
    # Expect columns: date, open, high, low, close, volume
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df = df.set_index("date")

    o = df["open"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    v = df["volume"].astype(float)

    rng = (h - l) / (o.replace(0, np.nan))
    body = (c - o).abs() / (o.replace(0, np.nan))
    upper = (h - np.maximum(o, c)) / (o.replace(0, np.nan))
    lower = (np.minimum(o, c) - l) / (o.replace(0, np.nan))
    close_pos = (c - l) / ((h - l) + 1e-12)

    # ATR-ish (simple TR mean)
    tr = (h - l)
    atr14 = tr.rolling(14, min_periods=14).mean()

    ema12 = ema(c, 12)
    ema26 = ema(c, 26)
    macd = ema12 - ema26
    macd_slope3 = macd.diff().rolling(3, min_periods=3).mean()

    rsi14 = rsi(c, 14)

    # Donchian 20 high (prev)
    dc20_high_prev = h.rolling(20, min_periods=20).max().shift(1)

    # Volume stats (prev 48)
    v_mean48 = v.rolling(48, min_periods=48).mean().shift(1)
    v_std48 = v.rolling(48, min_periods=48).std(ddof=0).shift(1)
    v_z = (v - v_mean48) / (v_std48 + 1e-12)
    v_ratio = v / (v_mean48 + 1e-12)

    out = pd.DataFrame({
        "open": o, "high": h, "low": l, "close": c, "volume": v,
        "rng": rng, "body": body,
        "upper_wick": upper, "lower_wick": lower,
        "upper_wick_ratio": upper / (rng + 1e-12),
        "close_pos": close_pos,
        "atr14": atr14,
        "rng_over_atr": (h - l) / (atr14 + 1e-12),
        "ema12": ema12, "ema26": ema26, "macd": macd, "macd_slope3": macd_slope3,
        "rsi14": rsi14,
        "dc20_high_prev": dc20_high_prev,
        "breakout_pct": (c - dc20_high_prev) / (dc20_high_prev + 1e-12),
        "vol_z": v_z,
        "vol_ratio": v_ratio,
    })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True)
    ap.add_argument("--strategy", default="TestDonchianFearGreedStrategy")
    ap.add_argument("--pre", type=int, default=48)
    ap.add_argument("--post", type=int, default=12)
    ap.add_argument("--outdir", default="")
    ap.add_argument("--bad_exit", default="stop_loss,ema_cross_exit")
    ap.add_argument("--bad_profit_abs", type=float, default=0.0)
    args = ap.parse_args()

    zip_path = Path(args.zip)
    json_name, data = read_zip_json(zip_path)

    cands = find_trades_in_obj(data)
    if not cands:
        raise SystemExit(f"NO_TRADES_FOUND_IN_ZIP: {zip_path}")

    # pick candidate with most rows
    cands.sort(key=lambda x: len(x[1]), reverse=True)
    trades_path, trades = cands[0]

    tdf = pd.DataFrame(trades).copy()
    if tdf.empty:
        raise SystemExit(f"EMPTY_TRADES: {zip_path}")

    # normalize
    for col in ["open_date", "close_date"]:
        tdf[col] = pd.to_datetime(tdf[col], utc=True, errors="coerce")
    tdf = tdf.dropna(subset=["pair", "open_date"]).reset_index(drop=True)

    # label bad trades
    bad_exits = set([s.strip() for s in args.bad_exit.split(",") if s.strip()])
    tdf["profit_abs"] = pd.to_numeric(tdf.get("profit_abs", np.nan), errors="coerce")
    tdf["profit_ratio"] = pd.to_numeric(tdf.get("profit_ratio", np.nan), errors="coerce")
    tdf["exit_reason"] = tdf.get("exit_reason", "").astype(str)

    # if profit_abs missing, fallback to profit_ratio
    if tdf["profit_abs"].isna().all() and not tdf["profit_ratio"].isna().all():
        # approximate profit_abs not possible -> use ratio sign
        tdf["is_bad"] = (tdf["profit_ratio"] < 0) & (tdf["exit_reason"].isin(bad_exits))
    else:
        tdf["is_bad"] = (tdf["profit_abs"] < args.bad_profit_abs) & (tdf["exit_reason"].isin(bad_exits))

    # output dir
    outdir = Path(args.outdir) if args.outdir else Path("user_data/backtest_results/forensics") / zip_path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    # load OHLCV per pair once
    feats_rows = []
    meta = []
    for pair, grp in tdf.groupby("pair"):
        fp = locate_ohlcv(pair)
        raw = pd.read_feather(fp)
        feat = compute_features(raw)

        # quick access index
        idx = feat.index

        for _, tr in grp.iterrows():
            t = tr["open_date"]
            if pd.isna(t):
                continue
            # find nearest candle at/just before open_date
            pos = idx.searchsorted(t, side="right") - 1
            if pos < 0 or pos >= len(idx):
                continue
            t0 = idx[pos]
            pre_start = max(0, pos - args.pre)
            post_end = min(len(idx)-1, pos + args.post)

            # entry candle features
            row = feat.iloc[pos].to_dict()

            # context window features
            win = feat.iloc[pre_start:pos+1]
            fut = feat.iloc[pos+1:post_end+1]

            row.update({
                "pair": pair,
                "open_date": t0,
                "exit_reason": tr["exit_reason"],
                "enter_tag": tr.get("enter_tag", ""),
                "profit_abs": tr.get("profit_abs", np.nan),
                "profit_ratio": tr.get("profit_ratio", np.nan),
                "is_bad": bool(tr["is_bad"]),
                "pre_n": len(win),
                "post_n": len(fut),
            })

            # additional “chart-like” signals
            # 1) failed breakout in next 3 candles: price returns below dc20_high_prev
            dc = row.get("dc20_high_prev", np.nan)
            if not np.isnan(dc) and len(fut) >= 3:
                min_next3 = float(fut["close"].iloc[:3].min())
                row["failed_breakout_3"] = int(min_next3 < dc)
            else:
                row["failed_breakout_3"] = np.nan

            # 2) MFE/MAE within next post candles
            if len(fut) > 0:
                entry = float(row["close"])
                row["mfe_post"] = float((fut["close"].max() - entry) / (entry + 1e-12))
                row["mae_post"] = float((fut["close"].min() - entry) / (entry + 1e-12))
            else:
                row["mfe_post"] = np.nan
                row["mae_post"] = np.nan

            feats_rows.append(row)
        meta.append({"pair": pair, "file": str(fp), "rows": int(len(raw))})

    fdf = pd.DataFrame(feats_rows)
    if fdf.empty:
        raise SystemExit("NO_FEATURE_ROWS (check dates/timeframe mismatch)")

    # save raw features
    f_csv = outdir / "entry_features.csv"
    fdf.to_csv(f_csv, index=False)

    # summary
    total = len(fdf)
    bad = int(fdf["is_bad"].sum())
    bad_rate = bad / total * 100.0

    # simple “rule mining” 1-feature thresholds
    report = []
    numeric_cols = [c for c in fdf.columns if c not in {"pair","open_date","exit_reason","enter_tag","is_bad"}]
    numeric_cols = [c for c in numeric_cols if pd.api.types.is_numeric_dtype(fdf[c])]

    def eval_rule(mask, name):
        n = int(mask.sum())
        if n < 30:
            return
        br = float(fdf.loc[mask, "is_bad"].mean() * 100.0)
        lift = br / (bad_rate + 1e-12)
        report.append((br, lift, n, name))

    for col in numeric_cols:
        s = fdf[col].replace([np.inf, -np.inf], np.nan).dropna()
        if len(s) < 200:
            continue
        qs = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
        ths = sorted(set([float(s.quantile(q)) for q in qs]))
        for th in ths:
            eval_rule(fdf[col] >= th, f"{col} >= {th:.6g}")
            eval_rule(fdf[col] <= th, f"{col} <= {th:.6g}")

    report.sort(key=lambda x: (x[0], x[2]), reverse=True)

    # feature contrast bad vs good
    contrast = []
    good_df = fdf[~fdf["is_bad"]]
    bad_df = fdf[fdf["is_bad"]]
    for col in numeric_cols:
        if col in {"profit_abs","profit_ratio"}:
            continue
        g = pd.to_numeric(good_df[col], errors="coerce")
        b = pd.to_numeric(bad_df[col], errors="coerce")
        if g.notna().sum() < 50 or b.notna().sum() < 50:
            continue
        gm = float(g.mean())
        bm = float(b.mean())
        sd = float(fdf[col].std(ddof=0) + 1e-12)
        z = (bm - gm) / sd
        contrast.append((abs(z), z, col, gm, bm))
    contrast.sort(reverse=True)

    out_txt = outdir / "report.txt"
    with out_txt.open("w", encoding="utf-8") as f:
        f.write(f"ZIP={zip_path}\nJSON={json_name}\nTRADES_PATH={trades_path}\n")
        f.write(f"TOTAL={total}  BAD={bad}  BAD_RATE={bad_rate:.2f}%  (bad_exit={args.bad_exit})\n\n")
        f.write("== TOP 25 CONTRAST (bad vs good) ==\n")
        for a, z, col, gm, bm in contrast[:25]:
            f.write(f"{col:20s}  z={z:+.3f}  good_mean={gm:.6g}  bad_mean={bm:.6g}\n")
        f.write("\n== TOP 40 1-FEATURE RULES (bad_rate high, support>=30) ==\n")
        for br, lift, n, name in report[:40]:
            f.write(f"bad_rate={br:6.2f}%  lift={lift:5.2f}  n={n:4d}  rule: {name}\n")

        # extra: exit_reason distribution for bad trades
        f.write("\n== BAD EXIT REASONS ==\n")
        f.write(str(bad_df["exit_reason"].value_counts(dropna=False)) + "\n")

        f.write("\n== OHLCV FILES USED ==\n")
        for m in meta:
            f.write(f"{m['pair']:8s} rows={m['rows']:7d} file={m['file']}\n")

    print("OK")
    print("OUTDIR =", outdir)
    print("FEATURES =", f_csv)
    print("REPORT   =", out_txt)
    print(f"TOTAL={total} BAD={bad} BAD_RATE={bad_rate:.2f}%")

if __name__ == "__main__":
    main()
