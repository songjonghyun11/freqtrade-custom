#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# GuardV4 VOL 미세 스윕 (V2 OFF + RSI70 고정)
# - zip 확정: pick_new_zip(before/after)
# - python: venv311 우선, 없으면 python3
# - docker 로그는 파일로만 저장 (WSL 다운 방지)
# ==========================================

ROOT="${HOME}/freqtrade"
cd "$ROOT"

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing cmd: $1"; exit 2; }; }
need_cmd docker
need_cmd find
need_cmd comm
need_cmd mktemp
need_cmd grep
need_cmd ls
need_cmd head
need_cmd date

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

# ✅ python 고정 (python 금지)
PY="python3"
if [ -x "${ROOT}/venv311/bin/python" ]; then
  PY="${ROOT}/venv311/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "ERROR: python3 not found"
  exit 2
fi

# ====== 고정값 ======
IMG="freqtradeorg/freqtrade:stable"
STRATEGY="TDFG_GuardV4"
TIMERANGE="${TIMERANGE:-20250101-20260210}"

CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"

# ✅ V2 OFF (없으면 자동 생성)
HOST_V2OFF="user_data/overrides/guard_v2_off.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"

# ✅ RSI70 + close_pos=0.90 고정 베이스(여기에서 RSI70 유지)
OV_RSI70_BASE="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"

# (선택) 추가 override(필요시만)
# 예: EXTRA_OVS=( "/freqtrade/user_data/overrides/pairs_8.json" )
EXTRA_OVS=()

make_v2off_file() {
  if [ -f "$HOST_V2OFF" ]; then return 0; fi
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
  fg = sp.get("TestDonchianFearGreedStrategyFG") or {}
  ge = fg.get("guard_enable", "<missing>")
  v4 = sp.get("TDFG_GuardV4") or {}
  cp = v4.get("guard_close_pos_min", "<missing>")
  vr = v4.get("guard_vol_ratio_min", "<missing>")
  vz = v4.get("guard_vol_z_min", "<missing>")
  rsi = v4.get("guard_rsi14_min", "<missing>")
  print(f"ZIP_VERIFY: V2.guard_enable={ge}")
  print(f"ZIP_VERIFY: V4(close_pos={cp}, vol_ratio={vr}, vol_z={vz}, rsi14_min={rsi})")' "$zip"
}

make_case_override() {
  local ratio="$1"
  local zmin="$2"
  local dir="user_data/overrides/sweep_tmp"
  mkdir -p "$dir"
  local f="${dir}/guard_v4_VOL_r${ratio}_z${zmin}.json"
  # ✅ 케이스 오버라이드에는 VOL만 넣어서 "베이스(RSI70+close_pos)" 위에 덮는다
  cat > "$f" <<JSON
{
  "strategy_parameters": {
    "TDFG_GuardV4": {
      "guard_vol_ratio_min": ${ratio},
      "guard_vol_z_min": ${zmin}
    }
  }
}
JSON
  echo "/freqtrade/${f}"
}

run_case() {
  local ratio="$1"
  local zmin="$2"
  local label="VOL_r${ratio}_z${zmin}"

  local ov_case
  ov_case="$(make_case_override "$ratio" "$zmin")"

  echo ""
  echo "==== ${label} (TIMERANGE=${TIMERANGE}) ===="

  local before after
  before="$(mktemp)"
  after="$(mktemp)"
  list_zip_names > "$before"

  local btlog="${OUTDIR}/bt_${TIMERANGE}_${STRATEGY}_${label}_${TS}.log"

  # docker cmd (배열로 안전 구성)
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

  # ✅ V2 OFF + RSI70 베이스 + VOL 케이스
  CMD+=(--config "$OV_V2OFF")
  CMD+=(--config "$OV_RSI70_BASE")
  CMD+=(--config "$ov_case")

  CMD+=(--strategy "$STRATEGY")
  CMD+=(--strategy-path /freqtrade/user_data/strategies)
  CMD+=(--timerange "$TIMERANGE")

  set +e
  "${CMD[@]}" > "$btlog" 2>&1
  local rc=$?
  set -e

  list_zip_names > "$after"
  mapfile -t newzips < <(pick_new_zip "$before" "$after" || true)
  rm -f "$before" "$after"

  echo "RC=$rc"
  echo "LOG=$btlog"

  if [ "${#newzips[@]}" -eq 0 ]; then
    echo "ERROR: no new zip detected."
    return 3
  fi

  local zip
  zip="$(ls -1t "${newzips[@]}" 2>/dev/null | head -n1)"
  echo "ZIP=$zip"

  # summary 1줄만(없어도 OK)
  local summary
  summary="$(grep -n -m1 -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│|\|[[:space:]]*'"$STRATEGY"'[[:space:]]*\|' "$btlog" || true)"
  echo "SUMMARY=${summary:-<not found>}"

  # zip 검증 (V2 OFF + V4 파라미터 확인)
  zip_verify "$zip" || true

  # 포렌식
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
    # TOTAL 라인 1줄만 출력 (핵심)
    echo "$(grep -m1 '^TOTAL=' "$rpt")"
  else
    echo "ERROR: report.txt not created. check $flog"
  fi
}

# ===== main =====
make_v2off_file

# ✅ 3x3 미세 스윕 (baseline=ratio 3.5 / z 2.0 근처)
RATIOS=(2.5 3.0 3.5)
ZMINs=(1.5 2.0 2.5)

echo "START: STRATEGY=$STRATEGY TIMERANGE=$TIMERANGE"
echo "GRID: RATIOS=${RATIOS[*]} | ZMINs=${ZMINs[*]}"
echo "BASE: RSI70+close_pos=0.90 fixed via $OV_RSI70_BASE"
echo "V2_OFF: $OV_V2OFF"

for r in "${RATIOS[@]}"; do
  for z in "${ZMINs[@]}"; do
    run_case "$r" "$z"
  done
done

echo ""
echo "DONE. outdir=$OUTDIR"
