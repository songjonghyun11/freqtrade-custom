#!/usr/bin/env bash
set -Eeuo pipefail

cd ~/freqtrade || exit 1
TR="${TR:-20250101-20260210}"
TS="$(date +%Y%m%d_%H%M%S)"
LOGDIR="user_data/backtest_results/sweep_logs"
ZDIR="user_data/backtest_results"
mkdir -p "$LOGDIR"

# (1) override 파일 "정답 구조"로 재생성
mkdir -p user_data/overrides

cat > user_data/overrides/guard_v4_only_closeconfirm_fix.json <<'JSON'
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_confirm": 1,
      "guard_use_vol": 0,
      "guard_use_rsi": 0
    }
  }
}
JSON

cat > user_data/overrides/guard_v4_only_closepos_fix.json <<'JSON'
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_pos_min": 0.35,
      "guard_close_confirm": 0,
      "guard_use_vol": 0,
      "guard_use_rsi": 0
    }
  }
}
JSON

# (2) ZIP에서 _config.json의 guard 파라미터 박힘을 확정 출력
zip_show_guard () {
  python - "$1" <<'PY'
import sys, json, zipfile
zp = sys.argv[1]
with zipfile.ZipFile(zp) as zf:
    cfg_name = [n for n in zf.namelist() if n.endswith("_config.json")][0]
    cfg = json.loads(zf.read(cfg_name))
sp = cfg.get("strategy_parameters") or {}
print("ZIP=", zp)
print("CONFIG.strategy =", cfg.get("strategy"))
print("SP_KEYS_HAS_TDFG_GuardV4 =", ("TDFG_GuardV4" in sp))
print("TDFG_GuardV4_PARAMS =", sp.get("TDFG_GuardV4"))
PY
}

# (3) ZIP에서 trades/손익/승률/손실비율 뽑기
zip_metrics () {
  python - "$1" "TDFG_GuardV4" <<'PY'
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
pabs = sum(f(t,"profit_abs",0.0) for t in trades)
wins = sum(1 for t in trades if f(t,"profit_abs",0.0) > 0)
bads = sum(1 for t in trades if f(t,"profit_abs",0.0) <= 0)
winr = (wins/n*100) if n else 0.0
badr = (bads/n*100) if n else 0.0
ex = Counter((t.get("exit_reason") or "NA") for t in trades)

print(f"MAIN_JSON={main}")
print(f"STRATEGY_KEYS={list((root.get('strategy') or {}).keys())}")
print(f"trades={n} profit_abs={pabs:.3f} winrate={winr:.2f}% badrate(profit<=0)={badr:.2f}%")
print("EXIT_REASON_TOP:", ", ".join([f"{k}:{v}" for k,v in ex.most_common(8)]))
PY
}

run_case () {
  local NAME="$1"
  local OV="$2"
  local LOG="${LOGDIR}/bt_${TR}_TDFG_GuardV4_${NAME}_${TS}.log"

  local before after
  before="$(mktemp)"; after="$(mktemp)"
  ls -1 "${ZDIR}"/backtest-result-*.zip 2>/dev/null | sort >"$before" || true

  docker run --rm -v "$(pwd)/user_data":/freqtrade/user_data \
    freqtradeorg/freqtrade:stable backtesting --no-color \
    --config /freqtrade/user_data/config/config_spot.json \
    --config /freqtrade/user_data/overrides/exit_baseline.json \
    --config "/freqtrade/user_data/overrides/${OV}" \
    --strategy TDFG_GuardV4 \
    --timerange "${TR}" >"${LOG}" 2>&1

  ls -1 "${ZDIR}"/backtest-result-*.zip 2>/dev/null | sort >"$after" || true
  local ZIP
  ZIP="$(comm -13 "$before" "$after" | tail -n 1 || true)"
  rm -f "$before" "$after"

  echo "==== ${NAME} ===="
  echo "RC=$?"
  echo "LOG=${LOG}"
  echo "ZIP=${ZIP}"

  if [ -z "${ZIP}" ] || [ ! -f "${ZIP}" ]; then
    echo "❌ NEW ZIP 못 잡음. (backtest-result-*.zip 생성 자체가 안 됐거나, 경로가 다름)"
    tail -n 120 "${LOG}" || true
    return 1
  fi

  zip_show_guard "${ZIP}"
  zip_metrics "${ZIP}"
  echo
}

run_case "ONLY_CLOSECONFIRM_FIX" "guard_v4_only_closeconfirm_fix.json"
run_case "ONLY_CLOSEPOS_FIX"     "guard_v4_only_closepos_fix.json"

echo "✅ DONE"
