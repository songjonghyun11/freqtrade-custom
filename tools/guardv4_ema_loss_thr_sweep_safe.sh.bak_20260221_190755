#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/freqtrade"

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

# python 경로 고정 (WSL 삽질 방지)
PY="$HOME/freqtrade/venv311/bin/python"
if [ ! -x "$PY" ]; then
  command -v python3 >/dev/null 2>&1 && PY="$(command -v python3)" || { echo "ERROR: python3 not found"; exit 2; }
fi

need_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing cmd: $1"; exit 2; }; }
need_cmd docker; need_cmd mktemp; need_cmd comm; need_cmd ls; need_cmd head; need_cmd sed; need_cmd stat; need_cmd sort; need_cmd grep

IMG="freqtradeorg/freqtrade:stable"
STRATEGY="TDFG_GuardV4"
TIMERANGE="${TIMERANGE:-20250101-20260210}"

# 컨테이너 경로(마운트 기준)
CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"
OV_GUARD="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"

# 스윕 대상
THRS=(-0.002 -0.003 -0.004 -0.005 -0.006 -0.008 -0.010)

# override 임시 저장
TMPDIR_HOST="user_data/overrides/sweep_tmp"
mkdir -p "$TMPDIR_HOST"

CSV="$OUTDIR/_ema_loss_thr_sweep_${TIMERANGE}_${TS}.csv"
echo "thr,zip,trades,profit_abs,dd_usdt,dd_pct,zip_use_ema_exit,zip_ema_thr,ema_cnt,ema_sum,sl_cnt,sl_sum,roi_cnt,roi_sum,trail_cnt,trail_sum" > "$CSV"

list_zip_names(){ ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | xargs -n1 basename 2>/dev/null | sort || true; }
pick_new_zip(){ comm -13 "$1" "$2" | tail -n 1; }

# thr override 생성(최종 config에 ema_exit_loss_thr가 찍히는지 검증 가능)
make_thr_override() {
  local thr="$1"
  local tag
  tag="$(echo "$thr" | sed 's/-/n/g; s/\./p/g')"
  local f_host="${TMPDIR_HOST}/ov_ema_exit_loss_thr_${tag}.json"
  cat > "$f_host" <<JSON
{
  "strategy_parameters": {
    "ema_exit_loss_thr": ${thr}
  }
}
JSON
  echo "/freqtrade/${f_host}"
}

# 로그 summary line 파싱(마지막 요약줄 기준)
extract_summary_metrics() {
  local log="$1"
  local line
  line="$(grep -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│' "$log" | tail -n 1 || true)"
  if [ -z "${line:-}" ]; then
    echo "TRADES=? PROFIT_ABS=? DD_USDT=? DD_PCT=?"
    return 0
  fi

  LINE="$line" "$PY" - <<'PY'
import os, re
line=os.environ["LINE"]
line=line.replace("│","|")
# 예시: | STRAT | Trades | Avg Profit % | Tot Profit USDT | Tot Profit % | Avg Duration | ... | Drawdown |
parts=[p.strip() for p in line.split("|") if p.strip()]
trades="?"
profit_abs="?"
dd_usdt="?"
dd_pct="?"
if len(parts) >= 4:
    trades = parts[1]
    profit_abs = parts[3]
# drawdown 칼럼은 버전에 따라 뒤쪽이지만 "USDT + %" 패턴으로 안전 추출
m=re.search(r'([0-9.]+)\s*USDT\s*([0-9.]+)%', line)
if m:
    dd_usdt, dd_pct = m.group(1), m.group(2)
print(f"TRADES={trades} PROFIT_ABS={profit_abs} DD_USDT={dd_usdt} DD_PCT={dd_pct}")
PY
}

# zip에서 config(ema_exit_loss_thr/use_ema_exit) + exit_reason 합계
exit_reason_stats() {
  local zip="$1"
  ZIP="$zip" "$PY" - <<'PY'
import os, json, zipfile, sys
from collections import defaultdict

zip_path=os.environ.get("ZIP")
if not zip_path or not os.path.exists(zip_path):
    print("USE_EMA=? EMA_THR=? EMA_CNT=? EMA_SUM=? SL_CNT=? SL_SUM=? ROI_CNT=? ROI_SUM=? TR_CNT=? TR_SUM=?")
    sys.exit(0)

def read_json(zf, name):
    return json.loads(zf.read(name))

def find_trades(obj):
    # 가장 흔한 구조: root.strategy.<STRAT>.trades
    if isinstance(obj, dict):
        if "trades" in obj and isinstance(obj["trades"], list) and (not obj["trades"] or isinstance(obj["trades"][0], dict)):
            return obj["trades"]
        for v in obj.values():
            r=find_trades(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r=find_trades(it)
            if r is not None:
                return r
    return None

use_ema="?"
ema_thr="?"
trades=None

with zipfile.ZipFile(zip_path) as z:
    cfgs=[n for n in z.namelist() if n.endswith("_config.json")]
    if cfgs:
        cfg=read_json(z, cfgs[0])
        sp=cfg.get("strategy_parameters") or {}
        use_ema=sp.get("use_ema_exit","?")
        ema_thr=sp.get("ema_exit_loss_thr","?")

    # 가장 큰 메인 json에서 trades 탐색
    roots=[n for n in z.namelist() if n.endswith(".json") and "/" not in n and "meta" not in n and not n.endswith("_config.json")]
    if roots:
        main=max(roots, key=lambda n: z.getinfo(n).file_size)
        data=read_json(z, main)
        trades=find_trades(data)

if not trades:
    print(f"USE_EMA={use_ema} EMA_THR={ema_thr} EMA_CNT=? EMA_SUM=? SL_CNT=? SL_SUM=? ROI_CNT=? ROI_SUM=? TR_CNT=? TR_SUM=?")
    sys.exit(0)

cnt=defaultdict(int); sm=defaultdict(float)
for t in trades:
    er=t.get("exit_reason") or t.get("sell_reason") or t.get("exit_tag") or "unknown"
    pa=t.get("profit_abs")
    try:
        pa=float(pa) if pa is not None else None
    except Exception:
        pa=None
    if pa is None:
        continue
    cnt[er]+=1
    sm[er]+=pa

def g(k): return cnt.get(k,0), sm.get(k,0.0)
ema_cnt, ema_sum = g("ema_cross_exit")
sl_cnt, sl_sum   = g("stop_loss")
roi_cnt, roi_sum = g("roi")
tr_cnt, tr_sum   = g("trailing_stop_loss")

print(f"USE_EMA={use_ema} EMA_THR={ema_thr} EMA_CNT={ema_cnt} EMA_SUM={ema_sum:.6f} SL_CNT={sl_cnt} SL_SUM={sl_sum:.6f} ROI_CNT={roi_cnt} ROI_SUM={roi_sum:.6f} TR_CNT={tr_cnt} TR_SUM={tr_sum:.6f}")
PY
}

# “이번 실행 zip” 확정: (1) before/after diff 1순위, (2) 실패시 mtime 기반 fallback
pick_zip_robust() {
  local beforef="$1" afterf="$2" start_epoch="$3"
  local fn
  fn="$(pick_new_zip "$beforef" "$afterf" || true)"
  if [ -n "${fn:-}" ]; then
    echo "user_data/backtest_results/${fn}"
    return 0
  fi

  # fallback: start 이후에 생성된 최신 zip
  local z
  z="$(ls -1t user_data/backtest_results/backtest-result-*.zip 2>/dev/null | head -n 1 || true)"
  if [ -z "${z:-}" ]; then
    echo ""
    return 0
  fi
  local mt
  mt="$(stat -c %Y "$z" 2>/dev/null || echo 0)"
  if [ "$mt" -ge "$start_epoch" ]; then
    echo "$z"
  else
    # 그래도 없으면 그냥 최신을 반환(최악의 경우라도 진행은 계속)
    echo "$z"
  fi
}

run_case() {
  local thr="$1"
  local tag; tag="$(echo "$thr" | sed 's/-/n/g; s/\./p/g')"
  echo ""
  echo "==== THR_${thr} (TIMERANGE=$TIMERANGE) ===="

  local ov_thr; ov_thr="$(make_thr_override "$thr")"

  local before after
  before="$(mktemp)"; after="$(mktemp)"
  list_zip_names > "$before" || true

  local log="${OUTDIR}/bt_emaLossThr_${TIMERANGE}_${STRATEGY}_${tag}_${TS}.log"

  local start_epoch; start_epoch="$(date +%s)"

  set +e
  docker run --rm \
    -v "$(pwd)/user_data":/freqtrade/user_data \
    "$IMG" backtesting --no-color \
    --config "$CONFIG_BASE" \
    --config "$OV_EXIT" \
    --config "$OV_V2OFF" \
    --config "$OV_GUARD" \
    --config "$ov_thr" \
    --strategy "$STRATEGY" \
    --strategy-path /freqtrade/user_data/strategies \
    --timerange "$TIMERANGE" \
    > "$log" 2>&1
  local rc=$?
  set -e

  echo "RC=$rc"
  echo "LOG=$log"

  list_zip_names > "$after" || true

  local zip
  zip="$(pick_zip_robust "$before" "$after" "$start_epoch")"
  rm -f "$before" "$after"

  if [ -z "${zip:-}" ]; then
    echo "ZIP=? (ERROR: could not detect any zip)"
    # 끊지 말고 다음 케이스로
    echo "${thr},?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?" >> "$CSV"
    return 0
  fi
  echo "ZIP=$zip"

  local sm es
  sm="$(extract_summary_metrics "$log")"
  es="$(exit_reason_stats "$zip")"
  echo "SUMMARY_METRICS: $sm"
  echo "EXIT_STATS: $es"

  local trades profit_abs dd_usdt dd_pct
  trades="$(echo "$sm" | sed -n 's/.*TRADES=\([^ ]*\).*/\1/p')"
  profit_abs="$(echo "$sm" | sed -n 's/.*PROFIT_ABS=\([^ ]*\).*/\1/p')"
  dd_usdt="$(echo "$sm" | sed -n 's/.*DD_USDT=\([^ ]*\).*/\1/p')"
  dd_pct="$(echo "$sm" | sed -n 's/.*DD_PCT=\([^ ]*\).*/\1/p')"

  local use_ema ema_thr ema_cnt ema_sum sl_cnt sl_sum roi_cnt roi_sum tr_cnt tr_sum
  use_ema="$(echo "$es" | sed -n 's/.*USE_EMA=\([^ ]*\).*/\1/p')"
  ema_thr="$(echo "$es" | sed -n 's/.*EMA_THR=\([^ ]*\).*/\1/p')"
  ema_cnt="$(echo "$es" | sed -n 's/.*EMA_CNT=\([^ ]*\).*/\1/p')"
  ema_sum="$(echo "$es" | sed -n 's/.*EMA_SUM=\([^ ]*\).*/\1/p')"
  sl_cnt="$(echo "$es" | sed -n 's/.*SL_CNT=\([^ ]*\).*/\1/p')"
  sl_sum="$(echo "$es" | sed -n 's/.*SL_SUM=\([^ ]*\).*/\1/p')"
  roi_cnt="$(echo "$es" | sed -n 's/.*ROI_CNT=\([^ ]*\).*/\1/p')"
  roi_sum="$(echo "$es" | sed -n 's/.*ROI_SUM=\([^ ]*\).*/\1/p')"
  tr_cnt="$(echo "$es" | sed -n 's/.*TR_CNT=\([^ ]*\).*/\1/p')"
  tr_sum="$(echo "$es" | sed -n 's/.*TR_SUM=\([^ ]*\).*/\1/p')"

  echo "${thr},${zip},${trades},${profit_abs},${dd_usdt},${dd_pct},${use_ema},${ema_thr},${ema_cnt},${ema_sum},${sl_cnt},${sl_sum},${roi_cnt},${roi_sum},${tr_cnt},${tr_sum}" >> "$CSV"
}

echo "START: ema_exit_loss_thr sweep | STRATEGY=$STRATEGY TIMERANGE=$TIMERANGE"
echo "CSV=$CSV"
echo "THRS=${THRS[*]}"

for thr in "${THRS[@]}"; do
  run_case "$thr"
done

echo ""
echo "DONE. CSV=$CSV"
echo "TOP5 by profit_abs (higher is better):"
"$PY" - <<PY
import csv
p="$CSV"
rows=[]
with open(p,newline='',encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        try: row["profit_abs"]=float(row["profit_abs"])
        except: row["profit_abs"]=-1e18
        rows.append(row)
rows.sort(key=lambda x:x["profit_abs"], reverse=True)
for i,row in enumerate(rows[:5],1):
    print(f"{i}) thr={row['thr']} profit_abs={row['profit_abs']} trades={row['trades']} zip_ema_thr={row['zip_ema_thr']} use_ema={row['zip_use_ema_exit']}")
PY
