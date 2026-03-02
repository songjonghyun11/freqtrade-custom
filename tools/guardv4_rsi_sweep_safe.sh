#!/usr/bin/env bash
set -e

TR="${TR:-20250101-20260210}"
TS="$(date +%Y%m%d_%H%M%S)"

mkdir -p user_data/overrides user_data/backtest_results/sweep_logs

# python3 강제(WSL/venv 여부랑 무관하게 동작)
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. (fix) sudo apt-get update && sudo apt-get install -y python3"
  exit 1
fi

PICKED_ZIP=""

pick_new_zip () {
  local cmd="$1"
  local before after rc
  before="$(mktemp)"; after="$(mktemp)"

  ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$before" || true

  set +e
  bash -lc "$cmd"
  rc=$?
  set -e

  ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$after" || true
  PICKED_ZIP="$(comm -13 "$before" "$after" | tail -n 1 || true)"

  rm -f "$before" "$after"
  return $rc
}

zip_metrics () {
  local zip_path="$1"
  local strat="$2"

  python3 - "$zip_path" "$strat" <<'PY'
import sys, json, zipfile
from collections import Counter

zip_path, strat = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(zip_path) as zf:
    roots = [n for n in zf.namelist() if n.endswith(".json") and "/" not in n and "meta" not in n]
    main = max(roots, key=lambda n: zf.getinfo(n).file_size)
    data = json.loads(zf.read(main))

root = data.get("root", data)
snode = (root.get("strategy") or {}).get(strat) or {}
trades = snode.get("trades") or []

def f(t, k, d=0.0):
    v = t.get(k, d)
    return float(v) if v is not None else d

n = len(trades)
pabs = sum(f(t, "profit_abs", 0.0) for t in trades)
wins = sum(1 for t in trades if f(t, "profit_abs", 0.0) > 0)
bads = sum(1 for t in trades if f(t, "profit_abs", 0.0) <= 0)
winr = (wins / n * 100) if n else 0.0
badr = (bads / n * 100) if n else 0.0
ex = Counter((t.get("exit_reason") or "NA") for t in trades)

print(f"ZIP={zip_path}")
print(f"MAIN_JSON={main}")
print(f"STRATEGY_KEYS={list((root.get('strategy') or {}).keys())}")
print(f"STRATEGY={strat} trades={n} profit_abs={pabs:.3f} winrate={winr:.2f}% badrate(profit<=0)={badr:.2f}%")
print("EXIT_REASON_TOP:", ", ".join([f"{k}:{v}" for k,v in ex.most_common(6)]))
PY
}

run_rsi () {
  local RSI="$1"
  local NAME="CLOSEPOS090_PLUSVOL_RSI${RSI}"
  local OV="user_data/overrides/guard_v4_closepos090_plus_vol_rsi${RSI}.json"
  local LOG="user_data/backtest_results/sweep_logs/bt_${TR}_TDFG_GuardV4_${NAME}_${TS}.log"

  # close_pos=0.90 고정 + VOL ON + RSI만 스윕
  cat > "$OV" <<JSON
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_confirm": 0,
      "guard_close_pos_min": 0.90,

      "guard_use_vol": 1,
      "guard_vol_ratio_min": 3.5,
      "guard_vol_z_min": 2.0,

      "guard_use_rsi": 1,
      "guard_rsi14_min": ${RSI}
    }
  }
}
JSON

  local CMD="docker run --rm -v \"$(pwd)/user_data\":/freqtrade/user_data \
    freqtradeorg/freqtrade:stable backtesting --no-color \
    --config /freqtrade/user_data/config/config_spot.json \
    --config /freqtrade/user_data/overrides/exit_baseline.json \
    --config /freqtrade/user_data/overrides/$(basename "$OV") \
    --strategy TDFG_GuardV4 \
    --strategy-path /freqtrade/user_data/strategies \
    --timerange \"${TR}\" >\"${LOG}\" 2>&1"

  echo "==== ${NAME} ===="
  pick_new_zip "$CMD"
  local RC=$?
  local ZIP="$PICKED_ZIP"

  echo "RC=${RC}"
  echo "LOG=${LOG}"
  echo "OV=${OV}"
  echo "ZIP=${ZIP}"

  # 요약 1줄 (로그에서 표 1줄만)
  local SUMMARY
  SUMMARY="$(grep -n "│ TDFG_GuardV4" "$LOG" | tail -n 1 || true)"
  echo "SUMMARY=${SUMMARY}"

  # zip 메트릭(짧게)
  if [ -n "$ZIP" ] && [ -f "$ZIP" ]; then
    zip_metrics "$ZIP" "TDFG_GuardV4"

    # 포렌식(BAD_RATE) - 출력은 report.txt에서 TOTAL 줄만 뽑기
    set +e
    python3 tools/entry_forensics.py \
      --zip "$ZIP" \
      --strategy TDFG_GuardV4 \
      --pre 48 --post 12 \
      --bad_exit "stop_loss,ema_cross_exit" \
      --bad_profit_abs 0 >/dev/null 2>&1
    set -e

    local OUTDIR="user_data/backtest_results/forensics/$(basename "$ZIP" .zip)"
    if [ -f "$OUTDIR/report.txt" ]; then
      grep -m1 "TOTAL=" "$OUTDIR/report.txt" || true
      # BAD exit reason 블록(짧게 6줄)
      awk '
        BEGIN{p=0}
        /== BAD EXIT REASONS ==/{p=1; print; next}
        p==1{print; c++; if(c>=6) exit}
      ' "$OUTDIR/report.txt" || true
    else
      echo "WARN: report.txt not found at ${OUTDIR}/report.txt"
    fi
  else
    echo "ERROR: ZIP not found (command may have failed)."
  fi

  echo
}

# ====== RSI 4개만 ======
run_rsi 60
run_rsi 65
run_rsi 70
run_rsi 75

echo "DONE. logs in: user_data/backtest_results/sweep_logs"
