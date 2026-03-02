#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/freqtrade"

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="user_data/backtest_results/sweep_logs"
mkdir -p "$OUTDIR"

PY="$HOME/freqtrade/venv311/bin/python"
[ -x "$PY" ] || PY=python3

IMG="freqtradeorg/freqtrade:stable"
STRATEGY="TDFG_GuardV4"
TIMERANGE="${TIMERANGE:-20250101-20260210}"

CONFIG_BASE="/freqtrade/user_data/config/config_spot.json"
OV_EXIT="/freqtrade/user_data/overrides/exit_baseline.json"
OV_V2OFF="/freqtrade/user_data/overrides/guard_v2_off.json"
OV_GUARD="/freqtrade/user_data/overrides/guard_v4_closepos090_plus_vol_rsi70.json"

HOST_OV="user_data/overrides/exit_stoploss_0125.json"
OV_SL="/freqtrade/user_data/overrides/exit_stoploss_0125.json"
cat > "$HOST_OV" <<'JSON'
{
  "stoploss": -0.0125
}
JSON

need_cmd(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: missing $1"; exit 2; }; }
need_cmd docker; need_cmd find; need_cmd comm; need_cmd mktemp; need_cmd grep; need_cmd ls; need_cmd head

list_zip_names(){ find user_data/backtest_results -maxdepth 1 -type f -name 'backtest-result-*.zip' -printf '%f\n' | sort; }
pick_new_zip(){ comm -13 "$1" "$2" | while read -r f; do echo "user_data/backtest_results/$f"; done; }

exit_reason_pnl(){
  local zip="$1"
  export ZIP="$zip"
  "$PY" - <<'PY'
import json, zipfile, os, sys
from collections import defaultdict
zip_path=os.environ.get("ZIP")
if not zip_path or not os.path.exists(zip_path):
    print("ERROR: ZIP not found:", zip_path); sys.exit(2)

def find_trades(obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k=="trades" and isinstance(v,list) and v and isinstance(v[0],dict): return v
            r=find_trades(v)
            if r: return r
    if isinstance(obj, list):
        for it in obj:
            r=find_trades(it)
            if r: return r
    return None

def read_json(zf, name): return json.loads(zf.read(name))

with zipfile.ZipFile(zip_path) as z:
    cfgs=[n for n in z.namelist() if n.endswith("_config.json")]
    cfg=read_json(z, max(cfgs, key=lambda n: z.getinfo(n).file_size)) if cfgs else {}
    print("ZIP_CFG: stoploss =", (cfg.get("stoploss","<missing>")))
    trades=None
    js=[n for n in z.namelist() if n.endswith(".json") and not n.endswith("_config.json")]
    js.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
    for n in js[:25]:
        try: data=read_json(z,n)
        except Exception: continue
        trades=find_trades(data)
        if trades: break
    if not trades:
        print("ERROR: trades not found"); sys.exit(3)

rows=[]
for t in trades:
    er=t.get("exit_reason") or t.get("sell_reason") or t.get("exit_tag") or "unknown"
    pa=t.get("profit_abs")
    try: pa=float(pa) if pa is not None else None
    except Exception: pa=None
    if pa is not None: rows.append((er,pa))

g=defaultdict(list)
for er,pa in rows: g[er].append(pa)

out=[]
for er,pas in g.items():
    cnt=len(pas); s=sum(pas); m=s/cnt if cnt else 0.0
    win=sum(1 for x in pas if x>0); wr=win/cnt*100 if cnt else 0.0
    out.append((er,cnt,s,m,wr))
out.sort(key=lambda x:x[2], reverse=True)

print("\nEXIT_REASON PNL:")
for er,cnt,s,m,wr in out:
    print(f"- {er:20s} cnt={cnt:4d} sum={s:8.3f} mean={m:7.4f} win%={wr:5.1f}")
PY
}

run_one(){
  local label="$1"
  local extra="${2:-}"
  echo ""
  echo "==== CASE: $label (TIMERANGE=$TIMERANGE) ===="
  local before after
  before="$(mktemp)"; after="$(mktemp)"
  list_zip_names > "$before"

  local log="${OUTDIR}/bt_slAB_${TIMERANGE}_${STRATEGY}_${label}_${TS}.log"

  local -a CMD
  CMD=(docker run --rm -v "$(pwd)/user_data:/freqtrade/user_data" "$IMG" backtesting
    --config "$CONFIG_BASE"
    --config "$OV_EXIT"
    --config "$OV_V2OFF"
    --config "$OV_GUARD"
  )
  [ -n "$extra" ] && CMD+=(--config "$extra")
  CMD+=(--strategy "$STRATEGY" --strategy-path /freqtrade/user_data/strategies --timerange "$TIMERANGE")

  set +e
  "${CMD[@]}" > "$log" 2>&1
  local rc=$?
  set -e

  list_zip_names > "$after"
  mapfile -t newzips < <(pick_new_zip "$before" "$after" || true)
  rm -f "$before" "$after"

  echo "RC=$rc"
  echo "LOG=$log"
  local zip
  zip="$(ls -1t "${newzips[@]}" 2>/dev/null | head -n1)"
  echo "ZIP=$zip"

  local summary
  summary="$(grep -m1 -E '│[[:space:]]*'"$STRATEGY"'[[:space:]]*│|\|[[:space:]]*'"$STRATEGY"'[[:space:]]*\|' "$log" || true)"
  echo "SUMMARY=${summary:-<not found>}"

  exit_reason_pnl "$zip"
}

run_one "BASELINE" ""
run_one "STOPLOSS_0125" "$OV_SL"
echo "DONE."
