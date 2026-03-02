#!/usr/bin/env bash
# ✅ 절대 set -e 금지: 에러 나도 셸 안 꺼지게
set +e

TR="${TR:-20250101-20260210}"
TS="$(date +%Y%m%d_%H%M%S)"
LOGDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$LOGDIR"

# (1) 이번 실행에서 새로 생긴 zip만 정확히 잡기 (로그 의존 X)
pick_new_zip () {
  local cmd="$1"
  local before after newzip rc
  before="$(mktemp)"; after="$(mktemp)"

  ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$before"
  bash -lc "$cmd"
  rc=$?
  ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | sort >"$after"

  newzip="$(comm -13 "$before" "$after" | tail -n 1)"
  rm -f "$before" "$after"
  echo "$newzip"
  return $rc
}

# (2) zip에서 결과 요약 뽑기
zip_metrics () {
  python - "$1" "$2" <<'PY'
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

print(f"ZIP={zip_path}")
print(f"MAIN_JSON={main}")
print(f"STRATEGY_KEYS={list((root.get('strategy') or {}).keys())}")
print(f"STRATEGY={strat} trades={n} profit_abs={pabs:.3f} winrate={winr:.2f}% badrate(profit<=0)={badr:.2f}%")
print("EXIT_REASON_TOP:", ", ".join([f"{k}:{v}" for k,v in ex.most_common(8)]))
PY
}

# (3) zip에 guard 파라미터가 진짜 박혔는지 확인
zip_guard_params () {
  python - "$1" <<'PY'
import sys, json, zipfile
zp=sys.argv[1]
with zipfile.ZipFile(zp) as zf:
    roots=[n for n in zf.namelist() if n.endswith(".json") and "/" not in n and "meta" not in n]
    main=max(roots, key=lambda n: zf.getinfo(n).file_size)
    data=json.loads(zf.read(main))
root=data.get("root", data)
sp = root.get("strategy_parameters", {})
print("TDFG_GuardV4_PARAMS=", sp.get("TDFG_GuardV4"))
PY
}

# (0) override 2개를 "정답 형태"로 강제 생성/덮어쓰기
cat > user_data/overrides/guard_v4_only_closeconfirm.json <<'JSON'
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_confirm": 1,
      "guard_close_pos_min": null,
      "guard_use_vol": 0,
      "guard_use_rsi": 0
    }
  }
}
JSON

cat > user_data/overrides/guard_v4_only_closepos.json <<'JSON'
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_close_confirm": 0,
      "guard_close_pos_min": 0.35,
      "guard_use_vol": 0,
      "guard_use_rsi": 0
    }
  }
}
JSON

run_one () {
  local NAME="$1"
  local OV="$2"
  local LOG="${LOGDIR}/bt_${TR}_TDFG_GuardV4_${NAME}_${TS}.log"

  local CMD="docker run --rm -v \"$(pwd)/user_data\":/freqtrade/user_data \
    freqtradeorg/freqtrade:stable backtesting --no-color \
    --config /freqtrade/user_data/config/config_spot.json \
    --config /freqtrade/user_data/overrides/exit_baseline.json \
    --config /freqtrade/user_data/overrides/${OV} \
    --strategy TDFG_GuardV4 \
    --strategy-path /freqtrade/user_data/strategies \
    --timerange \"${TR}\" >\"${LOG}\" 2>&1"

  local ZIP
  ZIP="$(pick_new_zip "$CMD")"
  local rc=$?

  echo "==== ${NAME} ===="
  echo "RC=${rc}"
  echo "LOG=${LOG}"
  echo "ZIP=${ZIP}"

  if [ -z "${ZIP}" ] || [ ! -f "${ZIP}" ]; then
    echo "❌ ZIP 못잡음. (아마 backtest 실패 or zip 생성 안됨)"
    echo "----- LOG TAIL -----"
    tail -n 80 "${LOG}" || true
    echo "--------------------"
    return 0
  fi

  zip_guard_params "${ZIP}"
  zip_metrics "${ZIP}" "TDFG_GuardV4"
  echo
}

run_one "ONLY_CLOSECONFIRM_FIX" "guard_v4_only_closeconfirm.json"
run_one "ONLY_CLOSEPOS_FIX"     "guard_v4_only_closepos.json"

echo "✅ DONE. logs in: ${LOGDIR}"
