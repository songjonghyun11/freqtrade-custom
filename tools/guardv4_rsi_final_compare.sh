#!/usr/bin/env bash
set -euo pipefail

# =========================
# GuardV4 RSI70 vs RSI75 "결승 비교" (V2 OFF 포함)
# - WSL 다운 방지: 화면 출력 최소, 로그는 파일로만
# - zip 확정: pick_new_zip(before/after) (로그 의존 금지)
# - python: venv311 우선, 없으면 python3
# - V2 OFF: strategy_parameters.TestDonchianFearGreedStrategyFG.guard_enable=0
# =========================

ROOT="${HOME}/freqtrade"
cd "$ROOT"

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing cmd: $1"; exit 2; }; }
need_cmd docker
need_cmd find
need_cmd comm
need_cmd mktemp
need_cmd grep

# ✅ python 고정 (python 금지)
PY="python3"
if [ -x "${ROOT}/venv311/bin/python" ]; then
  PY="${ROOT}/venv311/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "ERROR: python3 not found. install: sudo apt-get update && sudo apt-get install -y python3 python3-pip"
  exit 2
fi

# ====== 고정값(필요하면 여기만 수정) ======
IMG="freqtradeorg/freqtrade:stable"
STRATEGY="TDFG_GuardV4"
TIMERANGE="${TIMERANGE:-20250101-20260210}"

CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"

# ✅ V2 OFF override (호스트 파일이 없으면 자동 생성)
HOST_V2OFF="user_data/overrides/guard_v2_off.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"

OV_RSI70="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"
OV_RSI75="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi75.json"

# (선택) 추가 override 있으면 "컨테이너 경로"로 넣어라.
# 예: EXTRA_OVS=( "/freqtrade/user_data/overrides/pairs_8.json" )
EXTRA_OVS=()

make_v2off_file() {
  if [ -f "$HOST_V2OFF" ]; then
    return 0
  fi
  mkdir -p "$(dirname "$HOST_V2OFF")"
  cat > "$HOST_V2OFF" <<'JSON'
{
  "strategy_parameters": {
    "TestDonchianFearGreedStrategyFG": {
      "guard_enable": 0
    }
  }
}
JSON
}

list_zip_names() {
  find user_data/backtest_results -maxdepth 1 -type f -name 'backtest-result-*.zip' -printf '%f\n' | sort
}

pick_new_zip() {
  local before="$1"
  local after="$2"
  comm -13 "$before" "$after" | while read -r f; do
    echo "user_data/backtest_results/$f"
  done
}

zip_verify() {
  local zip="$1"
  "$PY" -c 'import sys,zipfile,json
zp=sys.argv[1]
with zipfile.ZipFile(zp) as z:
  cfgs=[n for n in z.namelist() if n.endswith("_config.json")]
  if not cfgs:
    print("ZIP_VERIFY: NO _config.json"); raise SystemExit(1)
  cfg=max(cfgs, key=lambda n: z.getinfo(n).file_size)
  data=json.loads(z.read(cfg))
  sp=(data.get("strategy_parameters") or {})
  keys=list(sp.keys())
  timer=(data.get("timerange") or "")
  tf=(data.get("timeframe_detail") or data.get("timeframe") or "")
  fg = sp.get("TestDonchianFearGreedStrategyFG") or {}
  ge = fg.get("guard_enable", "<missing>")
  v4 = sp.get("TDFG_GuardV4") or {}
  cp = v4.get("guard_close_pos_min", "<missing>")
  vr = v4.get("guard_vol_ratio_min", "<missing>")
  vz = v4.get("guard_vol_z_min", "<missing>")
  rsi = v4.get("guard_rsi14_min", "<missing>")
  print(f"ZIP_VERIFY: cfg={cfg} timerange={timer} tf={tf}")
  print(f"ZIP_VERIFY: strategy_param_keys={keys}")
  print(f"ZIP_VERIFY: V2.guard_enable={ge}")
  print(f"ZIP_VERIFY: V4(close_pos={cp}, vol_ratio={vr}, vol_z={vz}, rsi14_min={rsi})")' "$zip"
}

run_one() {
  local label="$1"
  local ov="$2"

  echo ""
  echo "==== ${label} (TIMERANGE=${TIMERANGE}) ===="

  local before after
  before="$(mktemp)"
  after="$(mktemp)"
  list_zip_names > "$before"

  local log="${OUTDIR}/bt_${TIMERANGE}_${STRATEGY}_${label}_${TS}.log"

  # docker 커맨드 배열로 안전하게 구성(공백 토큰 문제 방지)
  local -a CMD
  CMD=(docker run --rm
    -v "$(pwd)/user_data:/freqtrade/user_data"
    "$IMG" backtesting
    --config "$CONFIG_BASE"
    --config "$OV_EXIT"
  )
  for x in "${EXTRA_OVS[@]}"; do
    CMD+=(--config "$x")
  done

  # ✅ V2 OFF + 케이스 override
  CMD+=(--config "$OV_V2OFF")
  CMD+=(--config "$ov")
  CMD+=(--strategy "$STRATEGY")
  CMD+=(--strategy-path /freqtrade/user_data/strategies)
  CMD+=(--timerange "$TIMERANGE")

  # 실행 (로그는 파일로만)
  set +e
  "${CMD[@]}" > "$log" 2>&1
  local rc=$?
  set -e

  list_zip_names > "$after"
  mapfile -t newzips < <(pick_new_zip "$before" "$after" || true)
  rm -f "$before" "$after"

  echo "RC=$rc"
  echo "LOG=$log"

  if [ "${#newzips[@]}" -eq 0 ]; then
    echo "ERROR: no new zip detected. (check user_data/backtest_results)"
    return 3
  fi

  # 여러개면 mtime 최신 1개 선택
  local zip
  zip="$(ls -1t "${newzips[@]}" 2>/dev/null | head -n1)"
  echo "ZIP=$zip"

  # summary 라인 1줄만(없어도 OK)
  local summary
  summary="$(grep -n -m1 -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│|\|[[:space:]]*'"$STRATEGY"'[[:space:]]*\|' "$log" || true)"
  echo "SUMMARY=${summary:-<not found>}"

  # zip 내부 검증 출력
  zip_verify "$zip" || true

  # ✅ 포렌식(report.txt 생성)
  local zbase
  zbase="$(basename "$zip" .zip)"
  local fdir="user_data/backtest_results/forensics/${zbase}"
  mkdir -p "$fdir"

  local flog="${OUTDIR}/for_${TIMERANGE}_${STRATEGY}_${label}_${TS}.log"
  set +e
  "$PY" tools/entry_forensics.py \
    --zip "$zip" \
    --strategy "$STRATEGY" \
    --bad_exit "stop_loss,ema_cross_exit" \
    --bad_profit_abs 0.0 \
    > "$flog" 2>&1
  set -e

  local rpt="${fdir}/report.txt"
  if [ -f "$rpt" ]; then
    echo "$(grep -m1 '^TOTAL=' "$rpt")"
  else
    echo "ERROR: report.txt not created. check $flog"
  fi
}

# ====== main ======
make_v2off_file

run_one "RSI70" "$OV_RSI70"
run_one "RSI75" "$OV_RSI75"

echo ""
echo "DONE. outdir=$OUTDIR"
