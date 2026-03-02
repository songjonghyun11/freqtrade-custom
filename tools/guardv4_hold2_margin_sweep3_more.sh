#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/freqtrade"

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

PY="$HOME/freqtrade/venv311/bin/python"
[ -x "$PY" ] || PY=python3

need_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing cmd: $1"; exit 2; }; }
need_cmd docker; need_cmd mktemp; need_cmd comm; need_cmd ls; need_cmd head; need_cmd sed; need_cmd stat; need_cmd sort; need_cmd grep

IMG="freqtradeorg/freqtrade:stable"
STRATEGY="TDFG_GuardV4"
TIMERANGE="${TIMERANGE:-20250101-20260210}"

CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"
OV_GUARD="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"
OV_EXITBEST="/freqtrade/user_data/overrides/exit_ema_best_pack.json"

HOLDC=2
MARGINS=(0.0006 0.0008 0.0010)

TMPDIR_HOST="user_data/overrides/sweep_tmp"
mkdir -p "$TMPDIR_HOST"

CSV="$OUTDIR/_hold2_margin_more_${TIMERANGE}_${TS}.csv"
echo "margin,zip,trades,profit_abs,dd_usdt,dd_pct,sl_count" > "$CSV"

list_zip_names(){ ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | xargs -n1 basename 2>/dev/null | sort || true; }
pick_new_zip(){ comm -13 "$1" "$2" | tail -n 1; }

extract_summary_line(){
  grep -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│|[|][[:space:]]*'"$STRATEGY"'[[:space:]]*[|]' "$1" | tail -n 1 || true
}

extract_summary_metrics(){
  local line="$1"
  LINE="$line" "$PY" - <<'PY'
import os, re
line=os.environ["LINE"].replace("│","|")
parts=[p.strip() for p in line.split("|") if p.strip()]
trades = parts[1] if len(parts)>1 else "?"
profit_abs = parts[3] if len(parts)>3 else "?"
m=re.search(r'([0-9.]+)\s*USDT\s*([0-9.]+)%', line)
dd_usdt, dd_pct = (m.group(1), m.group(2)) if m else ("?","?")
print(f"TRADES={trades} PROFIT_ABS={profit_abs} DD_USDT={dd_usdt} DD_PCT={dd_pct}")
PY
}

pick_zip_robust(){
  local beforef="$1" afterf="$2"
  local fn; fn="$(pick_new_zip "$beforef" "$afterf" || true)"
  [ -n "${fn:-}" ] && { echo "user_data/backtest_results/${fn}"; return 0; }
  echo "$(ls -1t user_data/backtest_results/backtest-result-*.zip 2>/dev/null | head -n 1 || true)"
}

make_override(){
  local m="$1"
  local tag; tag="$(echo "$m" | sed 's/\./p/g')"
  local f_host="${TMPDIR_HOST}/ov_hold${HOLDC}_m${tag}.json"
  cat > "$f_host" <<JSON
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_breakout_hold_candles": ${HOLDC},
      "guard_breakout_margin_min": ${m}
    }
  }
}
JSON
  echo "/freqtrade/${f_host}"
}

run_one(){
  local m="$1"
  local tag; tag="$(echo "$m" | sed 's/\./p/g')"
  echo ""
  echo "==== HOLD${HOLDC}_MARGIN_${m} (TIMERANGE=$TIMERANGE) ===="

  local ov; ov="$(make_override "$m")"

  local before after
  before="$(mktemp)"; after="$(mktemp)"
  list_zip_names > "$before" || true

  local log="${OUTDIR}/bt_hold${HOLDC}_m${tag}_${TIMERANGE}_${STRATEGY}_${TS}.log"

  docker run --rm -v "$(pwd)/user_data":/freqtrade/user_data \
    "$IMG" backtesting --no-color \
    --config "$CONFIG_BASE" --config "$OV_EXIT" --config "$OV_V2OFF" --config "$OV_GUARD" --config "$ov" --config "$OV_EXITBEST" \
    --strategy "$STRATEGY" --strategy-path /freqtrade/user_data/strategies --timerange "$TIMERANGE" \
    > "$log" 2>&1

  list_zip_names > "$after" || true
  local zip; zip="$(pick_zip_robust "$before" "$after")"
  rm -f "$before" "$after"

  local line; line="$(extract_summary_line "$log")"
  local sm; sm="$(extract_summary_metrics "$line")"
  echo "SUMMARY_METRICS: $sm"

  OUT="user_data/backtest_results/sweep_logs/_slcnt_hold${HOLDC}_m${tag}_${TS}.out"
  $PY tools/stoploss_forensics.py "$zip" > "$OUT" 2>&1
  slc="$(grep -oE 'STOP_LOSS_COUNT=[0-9]+' "$OUT" | tail -n 1 | sed 's/STOP_LOSS_COUNT=//')"
  echo "STOP_LOSS_COUNT=$slc"

  local trades profit_abs dd_usdt dd_pct
  trades="$(echo "$sm" | sed -n 's/.*TRADES=\([^ ]*\).*/\1/p')"
  profit_abs="$(echo "$sm" | sed -n 's/.*PROFIT_ABS=\([^ ]*\).*/\1/p')"
  dd_usdt="$(echo "$sm" | sed -n 's/.*DD_USDT=\([^ ]*\).*/\1/p')"
  dd_pct="$(echo "$sm" | sed -n 's/.*DD_PCT=\([^ ]*\).*/\1/p')"

  echo "${m},${zip},${trades},${profit_abs},${dd_usdt},${dd_pct},${slc}" >> "$CSV"
}

echo "START: hold=${HOLDC} margin more sweep3 | margins=${MARGINS[*]}"
echo "CSV=$CSV"
for m in "${MARGINS[@]}"; do
  run_one "$m"
done
echo "DONE. CSV=$CSV"
