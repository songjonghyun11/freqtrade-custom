#!/usr/bin/env bash
# 목적: 터미널(WSL) 안 꺼지게, 결과/로그만 남기고 안전 종료
set -u
set -o pipefail

TR="${TR:-20250101-20260210}"
TS="$(date +%Y%m%d_%H%M%S)"
LOG="user_data/backtest_results/sweep_logs/bt_${TR}_TDFG_GuardV4_CLOSEPOS090_PLUSVOL_PLUSRSI_${TS}.log"
OV="user_data/overrides/guard_v4_closepos090_plus_vol_plus_rsi.json"

# (1) override 생성
cat > "$OV" <<'JSON'
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_confirm": 0,
      "guard_close_pos_min": 0.90,
      "guard_use_vol": 1,
      "guard_vol_ratio_min": 3.5,
      "guard_vol_z_min": 2.0,
      "guard_use_rsi": 1,
      "guard_rsi14_min": 70
    }
  }
}
JSON

# (2) 백테 전 zip 목록 스냅샷
before="$(mktemp)"
after="$(mktemp)"
ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$before" || true

CMD=(docker run --rm -v "$(pwd)/user_data":/freqtrade/user_data
  freqtradeorg/freqtrade:stable backtesting --no-color
  --config /freqtrade/user_data/config/config_spot.json
  --config /freqtrade/user_data/overrides/exit_baseline.json
  --config /freqtrade/user_data/overrides/$(basename "$OV")
  --strategy TDFG_GuardV4
  --strategy-path /freqtrade/user_data/strategies
  --timerange "$TR"
)

# (3) 실행 (에러여도 터미널 안 죽게)
"${CMD[@]}" >"$LOG" 2>&1
RC=$?

ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$after" || true
ZIP="$(comm -13 "$before" "$after" | tail -n 1)"
rm -f "$before" "$after"

# (4) zip 못 잡았으면 최신 zip로 fallback (그래도 안 죽게)
if [ -z "${ZIP:-}" ]; then
  ZIP="$(ls -1t user_data/backtest_results/backtest-result-*.zip 2>/dev/null | head -n 1 || true)"
fi

echo "RC=$RC"
echo "LOG=$LOG"
echo "OV=$OV"
echo "ZIP=$ZIP"

# (5) 요약표 한 줄 (없어도 안 죽게)
grep -n "│ TDFG_GuardV4" "$LOG" | tail -n 3 || true

# (6) zip 검증 + 포렌식 (zip 없으면 종료)
if [ -z "${ZIP:-}" ] || [ ! -f "$ZIP" ]; then
  echo "ERROR: ZIP not found. Check LOG=$LOG"
  exit 0
fi

python tools/entry_forensics.py \
  --zip "$ZIP" \
  --strategy TDFG_GuardV4 \
  --pre 48 --post 12 \
  --bad_exit "stop_loss,ema_cross_exit" \
  --bad_profit_abs 0 || true

OUTDIR="user_data/backtest_results/forensics/$(basename "$ZIP" .zip)"
if [ -f "$OUTDIR/report.txt" ]; then
  sed -n '1,80p' "$OUTDIR/report.txt"
else
  echo "WARN: report.txt not found in $OUTDIR"
fi

exit 0
