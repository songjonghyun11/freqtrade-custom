#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/freqtrade"

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

# python 경로 고정
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

# ✅ 확정 best pack (ema_exit_loss_thr=-0.0065, exit_fast_ema=3, exit_slow_ema=6)
HOST_BEST="user_data/overrides/exit_ema_best_pack.json"
OV_BEST="/freqtrade/user_data/overrides/exit_ema_best_pack.json"
if [ ! -f "$HOST_BEST" ]; then
  cat > "$HOST_BEST" <<'JSON'
{
  "strategy_parameters": {
    "ema_exit_loss_thr": -0.0065,
    "exit_fast_ema": 3,
    "exit_slow_ema": 6
  }
}
JSON
fi

# ✅ 스윕 대상 (5점)
BUFS=(0.0000 0.0005 0.0010 0.0020 0.0030)

TMPDIR_HOST="user_data/overrides/sweep_tmp"
mkdir -p "$TMPDIR_HOST"

CSV="$OUTDIR/_ema_buf_sweep_${TIMERANGE}_${TS}.csv"
echo "buf,zip,trades,profit_abs,dd_usdt,dd_pct,zip_buf,ema_cnt,ema_sum,sl_cnt,sl_sum,roi_cnt,roi_sum,trail_cnt,trail_sum" > "$CSV"

list_zip_names(){ ls -1 user_data/backtest_results/backtest-result-*.zip 2>/dev/null | xargs -n1 basename 2>/dev/null | sort || true; }
pick_new_zip(){ comm -13 "$1" "$2" | tail -n 1; }

make_buf_override() {
  local b="$1"
  local tag; tag="$(echo "$b" | sed 's/\./p/g')"
  local f_host="${TMPDIR_HOST}/ov_ema_buf_${tag}.json"
  cat > "$f_host" <<JSON
{
  "strategy_parameters": {
    "ema_exit_price_buf": ${b}
  }
}
JSON
  echo "/freqtrade/${f_host}"
}

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
line=os.environ["LINE"].replace("│","|")
parts=[p.strip() for p in line.split("|") if p.strip()]
trades = parts[1] if len(parts) > 1 else "?"
profit_abs = parts[3] if len(parts) > 3 else "?"
m=re.search(r'([0-9.]+)\s*USDT\s*([0-9.]+)%', line)
dd_usdt, dd_pct = (m.group(1), m.group(2)) if m else ("?","?")
print(f"TRADES={trades} PROFIT_ABS={profit_abs} DD_USDT={dd_usdt} DD_PCT={dd_pct}")
PY
}

# zip에서 config(ema_exit_price_buf) + exit_reason 합계
exit_reason_stats() {
  local zip="$1"
  ZIP="$zip" "$PY" - <<'PY'
import os, json, zipfile, sys
from collections import defaultdict

zip_path=os.environ.get("ZIP")
if not zip_path or not os.path.exists(zip_path):
    print("BUF=? EMA_CNT=? EMA_SUM=? SL_CNT=? SL_SUM=? ROI_CNT=? ROI_SUM=? TR_CNT=? TR_SUM=?")
    sys.exit(0)

def read_json(zf, name):
    return json.loads(zf.read(name))

def find_trades(obj):
    if isinstance(obj, dict):
        if "trades" in obj and isinstance(obj["trades"], list):
            return obj["trades"]
        for v in obj.values():
            r=find_trades(v)
            if r is not None:
                return r
    if isinstance(obj, list):
        for it in obj:
            r=find_trades(it)
            if r is not None:
                return r
    return None

buf="?"
trades=None

with zipfile.ZipFile(zip_path) as z:
    cfgs=[n for n in z.namelist() if n.endswith("_config.json")]
    if cfgs:
        cfg_name=max(cfgs, key=lambda n: z.getinfo(n).file_size)
        cfg=read_json(z, cfg_name)
        sp=cfg.get("strategy_parameters") or {}
        buf=sp.get("ema_exit_price_buf","?")

    roots=[n for n in z.namelist() if n.endswith(".json") and "/" not in n and not n.endswith("_config.json")]
    if roots:
        main=max(roots, key=lambda n: z.getinfo(n).file_size)
        data=read_json(z, main)
        trades=find_trades(data)

if trades is None:
    print(f"BUF={buf} EMA_CNT=? EMA_SUM=? SL_CNT=? SL_SUM=? ROI_CNT=? ROI_SUM=? TR_CNT=? TR_SUM=?")
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

print(f"BUF={buf} EMA_CNT={ema_cnt} EMA_SUM={ema_sum:.6f} SL_CNT={sl_cnt} SL_SUM={sl_sum:.6f} ROI_CNT={roi_cnt} ROI_SUM={roi_sum:.6f} TR_CNT={tr_cnt} TR_SUM={tr_sum:.6f}")
PY
}

# ZIP 확정: diff 1순위 + mtime fallback
pick_zip_robust() {
  local beforef="$1" afterf="$2" start_epoch="$3"
  local fn
  fn="$(pick_new_zip "$beforef" "$afterf" || true)"
  if [ -n "${fn:-}" ]; then
    echo "user_data/backtest_results/${fn}"
    return 0
  fi

  local z
  z="$(ls -1t user_data/backtest_results/backtest-result-*.zip 2>/dev/null | head -n 1 || true)"
  [ -z "${z:-}" ] && { echo ""; return 0; }
  local mt
  mt="$(stat -c %Y "$z" 2>/dev/null || echo 0)"
  if [ "$mt" -ge "$start_epoch" ]; then
    echo "$z"
  else
    echo "$z"
  fi
}

run_case() {
  local b="$1"
  local tag; tag="$(echo "$b" | sed 's/\./p/g')"
  echo ""
  echo "==== BUF_${b} (TIMERANGE=$TIMERANGE) ===="

  local ov_b; ov_b="$(make_buf_override "$b")"

  local before after
  before="$(mktemp)"; after="$(mktemp)"
  list_zip_names > "$before" || true

  local log="${OUTDIR}/bt_emaBuf_${TIMERANGE}_${STRATEGY}_${tag}_${TS}.log"
  local start_epoch; start_epoch="$(date +%s)"

  set +e
  docker run --rm \
    -v "$(pwd)/user_data":/freqtrade/user_data \
    "$IMG" backtesting --no-color \
    --config "$CONFIG_BASE" \
    --config "$OV_EXIT" \
    --config "$OV_V2OFF" \
    --config "$OV_GUARD" \
    --config "$OV_BEST" \
    --config "$ov_b" \
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
    echo "${b},?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?" >> "$CSV"
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

  local zip_buf ema_cnt ema_sum sl_cnt sl_sum roi_cnt roi_sum tr_cnt tr_sum
  zip_buf="$(echo "$es" | sed -n 's/.*BUF=\([^ ]*\).*/\1/p')"
  ema_cnt="$(echo "$es" | sed -n 's/.*EMA_CNT=\([^ ]*\).*/\1/p')"
  ema_sum="$(echo "$es" | sed -n 's/.*EMA_SUM=\([^ ]*\).*/\1/p')"
  sl_cnt="$(echo "$es" | sed -n 's/.*SL_CNT=\([^ ]*\).*/\1/p')"
  sl_sum="$(echo "$es" | sed -n 's/.*SL_SUM=\([^ ]*\).*/\1/p')"
  roi_cnt="$(echo "$es" | sed -n 's/.*ROI_CNT=\([^ ]*\).*/\1/p')"
  roi_sum="$(echo "$es" | sed -n 's/.*ROI_SUM=\([^ ]*\).*/\1/p')"
  tr_cnt="$(echo "$es" | sed -n 's/.*TR_CNT=\([^ ]*\).*/\1/p')"
  tr_sum="$(echo "$es" | sed -n 's/.*TR_SUM=\([^ ]*\).*/\1/p')"

  echo "${b},${zip},${trades},${profit_abs},${dd_usdt},${dd_pct},${zip_buf},${ema_cnt},${ema_sum},${sl_cnt},${sl_sum},${roi_cnt},${roi_sum},${tr_cnt},${tr_sum}" >> "$CSV"
}

echo "START: ema_exit_price_buf sweep | STRATEGY=$STRATEGY TIMERANGE=$TIMERANGE"
echo "LOCKS: GUARD=close_pos0.90+RSI70+VOL(3.5/2.0), V2_OFF=ON, exit_ema_best_pack=ON"
echo "BUFS=${BUFS[*]}"
echo "CSV=$CSV"

for b in "${BUFS[@]}"; do
  run_case "$b"
done

echo ""
echo "DONE. CSV=$CSV"
echo "TOP5 by profit_abs:"
"$PY" - <<PY
import csv
p="$CSV"; rows=[]
with open(p,newline='',encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        try: row["profit_abs"]=float(row["profit_abs"])
        except: row["profit_abs"]=-1e18
        rows.append(row)
rows.sort(key=lambda x:x["profit_abs"], reverse=True)
for i,row in enumerate(rows[:5],1):
    print(f"{i}) buf={row['buf']} profit_abs={row['profit_abs']} sl_sum={row['sl_sum']} ema_sum={row['ema_sum']} dd={row['dd_usdt']}")
PY
