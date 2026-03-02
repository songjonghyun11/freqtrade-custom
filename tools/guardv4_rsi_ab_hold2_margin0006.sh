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

# 고정 베이스
CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"
OV_GUARD_BASE="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"
OV_EXITBEST="/freqtrade/user_data/overrides/exit_ema_best_pack.json"
OV_FINAL="/freqtrade/user_data/overrides/guard_v4_final_lock.json"   # hold=2 + margin=0.0006

# RSI만 덮어쓰기용 override 2개(호스트에 생성)
cat > user_data/overrides/ov_rsi70_only.json <<'JSON'
{ "strategy_parameters": { "TDFG_GuardV4": { "guard_rsi14_min": 70 } } }
JSON
cat > user_data/overrides/ov_rsi65_only.json <<'JSON'
{ "strategy_parameters": { "TDFG_GuardV4": { "guard_rsi14_min": 65 } } }
JSON

list_zip_names(){ ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | xargs -n1 basename 2>/dev/null | sort || true; }
pick_new_zip(){ comm -13 "$1" "$2" | tail -n 1; }

extract_summary_line(){
  local log="$1"
  grep -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│|[|][[:space:]]*'"$STRATEGY"'[[:space:]]*[|]' "$log" | tail -n 1 || true
}

extract_summary_metrics(){
  local line="$1"
  if [ -z "${line:-}" ]; then
    echo "TRADES=? PROFIT_ABS=? DD_USDT=? DD_PCT=?"
    return 0
  fi
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

run_case(){
  local name="$1"
  local ov_rsi="$2"
  echo ""
  echo "==== CASE_${name} (RSI=${name}, TIMERANGE=$TIMERANGE) ===="

  local before after
  before="$(mktemp)"; after="$(mktemp)"
  list_zip_names > "$before" || true

  local log="${OUTDIR}/bt_rsiAB_hold2_m0006_${name}_${TIMERANGE}_${TS}.log"

  docker run --rm -v "$(pwd)/user_data":/freqtrade/user_data \
    "$IMG" backtesting --no-color \
    --config "$CONFIG_BASE" \
    --config "$OV_EXIT" \
    --config "$OV_V2OFF" \
    --config "$OV_GUARD_BASE" \
    --config "$OV_FINAL" \
    --config "$OV_EXITBEST" \
    --config "$ov_rsi" \
    --strategy "$STRATEGY" \
    --strategy-path /freqtrade/user_data/strategies \
    --timerange "$TIMERANGE" \
    > "$log" 2>&1

  list_zip_names > "$after" || true
  local zip; zip="$(pick_zip_robust "$before" "$after")"
  rm -f "$before" "$after"

  echo "ZIP=$zip"
  local line; line="$(extract_summary_line "$log")"
  local sm; sm="$(extract_summary_metrics "$line")"
  echo "SUMMARY_METRICS: $sm"

  local out2="${OUTDIR}/_slcnt_rsiAB_${name}_${TS}.out"
  $PY tools/stoploss_forensics.py "$zip" > "$out2" 2>&1
  local slc; slc="$(grep -oE 'STOP_LOSS_COUNT=[0-9]+' "$out2" | tail -n 1 | sed 's/STOP_LOSS_COUNT=//')"
  echo "STOP_LOSS_COUNT=$slc"
}

echo "START: RSI A/B on FINAL_LOCK(hold=2, margin=0.0006) | TIMERANGE=$TIMERANGE"
run_case "70" "/freqtrade/user_data/overrides/ov_rsi70_only.json"
run_case "65" "/freqtrade/user_data/overrides/ov_rsi65_only.json"
echo ""
echo "DONE."
