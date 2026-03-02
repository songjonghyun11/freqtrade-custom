import os, sys, json, zipfile, csv
from collections import defaultdict, Counter
from datetime import datetime, timezone

def eprint(*a):  # minimal stderr helper
    print(*a, file=sys.stderr)

def to_sec(x):
    if x is None:
        return None
    # already datetime-like string? ignore here
    try:
        x = float(x)
    except Exception:
        return None
    # ms vs sec
    if x > 10_000_000_000:  # too large for seconds
        x = x / 1000.0
    return x

def find_trades(obj):
    # recursive search for first plausible trades list
    if isinstance(obj, dict):
        v = obj.get("trades")
        if isinstance(v, list) and (not v or isinstance(v[0], dict)):
            return v
        for vv in obj.values():
            r = find_trades(vv)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = find_trades(it)
            if r is not None:
                return r
    return None

def read_json_from_zip(z: zipfile.ZipFile, name: str):
    return json.loads(z.read(name))

def pick_best_config(z: zipfile.ZipFile):
    cfgs = [n for n in z.namelist() if n.endswith("_config.json")]
    if not cfgs:
        return None, {}
    # choose largest config (more complete)
    cfg_name = max(cfgs, key=lambda n: z.getinfo(n).file_size)
    try:
        cfg = read_json_from_zip(z, cfg_name)
    except Exception:
        return cfg_name, {}
    return cfg_name, cfg

def pick_trades(z: zipfile.ZipFile):
    # prefer root-level large json(s)
    candidates = [n for n in z.namelist()
                  if n.endswith(".json")
                  and not n.endswith("_config.json")
                  and "/" not in n]  # root only
    # fallback: any json
    if not candidates:
        candidates = [n for n in z.namelist()
                      if n.endswith(".json") and not n.endswith("_config.json")]
    candidates.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)

    for name in candidates[:20]:
        try:
            data = read_json_from_zip(z, name)
        except Exception:
            continue
        trades = find_trades(data)
        if trades is not None:
            return name, trades
    return None, None

def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def iso_from_ts(ts_sec):
    if ts_sec is None:
        return ""
    try:
        return datetime.fromtimestamp(ts_sec, tz=timezone.utc).isoformat()
    except Exception:
        return ""

def main():
    zip_path = None
    if len(sys.argv) >= 2:
        zip_path = sys.argv[1]
    else:
        zip_path = os.environ.get("ZIP")

    if not zip_path:
        print("ERROR: ZIP not provided (argv1 or env ZIP)")
        sys.exit(2)
    if not os.path.exists(zip_path):
        print(f"ERROR: zip not found: {zip_path}")
        sys.exit(2)

    zbase = os.path.basename(zip_path).replace(".zip", "")
    outdir = os.path.join("user_data", "backtest_results", "forensics", zbase)
    os.makedirs(outdir, exist_ok=True)

    csv_path = os.path.join(outdir, "stoploss_trades.csv")
    rpt_path = os.path.join(outdir, "stoploss_report.txt")

    with zipfile.ZipFile(zip_path) as z:
        cfg_name, cfg = pick_best_config(z)
        trades_json_name, trades = pick_trades(z)

    if trades is None:
        print("ERROR: trades not found in zip")
        sys.exit(3)

    # collect stop_loss trades
    rows = []
    for t in trades:
        er = t.get("exit_reason") or t.get("sell_reason") or t.get("exit_tag") or "unknown"
        if er != "stop_loss":
            continue

        pair = t.get("pair") or t.get("trade_pair") or t.get("symbol") or ""
        enter_tag = t.get("enter_tag") or t.get("buy_tag") or t.get("entry_tag") or ""
        exit_tag  = t.get("exit_tag") or ""

        o_ts = to_sec(t.get("open_date_timestamp") or t.get("open_timestamp") or t.get("open_time"))
        c_ts = to_sec(t.get("close_date_timestamp") or t.get("close_timestamp") or t.get("close_time"))
        hold_min = ((c_ts - o_ts) / 60.0) if (o_ts is not None and c_ts is not None) else None

        profit_abs   = safe_float(t.get("profit_abs"))
        profit_ratio = safe_float(t.get("profit_ratio"))
        open_rate    = safe_float(t.get("open_rate"))
        close_rate   = safe_float(t.get("close_rate"))
        min_rate     = safe_float(t.get("min_rate") or t.get("min_rate_abs") or t.get("min_rate_value"))
        max_rate     = safe_float(t.get("max_rate") or t.get("max_rate_abs") or t.get("max_rate_value"))

        dd_from_open = None
        if open_rate and min_rate:
            dd_from_open = (min_rate / open_rate) - 1.0
        up_from_open = None
        if open_rate and max_rate:
            up_from_open = (max_rate / open_rate) - 1.0

        rows.append({
            "pair": pair,
            "enter_tag": enter_tag,
            "exit_reason": er,
            "exit_tag": exit_tag,
            "open_time_utc": iso_from_ts(o_ts),
            "close_time_utc": iso_from_ts(c_ts),
            "hold_min": round(hold_min, 2) if hold_min is not None else "",
            "profit_abs": profit_abs if profit_abs is not None else "",
            "profit_ratio": profit_ratio if profit_ratio is not None else "",
            "open_rate": open_rate if open_rate is not None else "",
            "close_rate": close_rate if close_rate is not None else "",
            "min_rate": min_rate if min_rate is not None else "",
            "max_rate": max_rate if max_rate is not None else "",
            "dd_from_open": round(dd_from_open, 6) if dd_from_open is not None else "",
            "up_from_open": round(up_from_open, 6) if up_from_open is not None else "",
        })

    # write csv
    fieldnames = [
        "pair","enter_tag","exit_reason","exit_tag",
        "open_time_utc","close_time_utc","hold_min",
        "profit_abs","profit_ratio",
        "open_rate","close_rate","min_rate","max_rate",
        "dd_from_open","up_from_open"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # summary stats
    total_sl = len(rows)
    by_pair = Counter(r["pair"] for r in rows if r["pair"])
    by_tag  = Counter(r["enter_tag"] for r in rows if r["enter_tag"])
    hold_list = [float(r["hold_min"]) for r in rows if r["hold_min"] != ""]
    pa_list   = [float(r["profit_abs"]) for r in rows if r["profit_abs"] != ""]
    dd_list   = [float(r["dd_from_open"]) for r in rows if r["dd_from_open"] != ""]

    def pct(lst, p):
        if not lst:
            return None
        s = sorted(lst)
        i = int(round((p/100)*(len(s)-1)))
        return s[i]

    def fmt(x, nd=3):
        if x is None:
            return "?"
        try:
            return f"{x:.{nd}f}"
        except Exception:
            return str(x)

    # config highlights (best-effort)
    sp = (cfg.get("strategy_parameters") or {}) if isinstance(cfg, dict) else {}
    cfg_use_ema = sp.get("use_ema_exit", "<missing>")
    cfg_thr     = sp.get("ema_exit_loss_thr", "<missing>")
    cfg_fast    = sp.get("exit_fast_ema", "<missing>")
    cfg_slow    = sp.get("exit_slow_ema", "<missing>")
    cfg_buf     = sp.get("ema_exit_price_buf", "<missing>")

    with open(rpt_path, "w", encoding="utf-8") as f:
        f.write(f"ZIP={zip_path}\n")
        f.write(f"CONFIG_FILE={cfg_name}\n")
        f.write(f"TRADES_JSON={trades_json_name}\n\n")

        f.write("[CONFIG CHECK]\n")
        f.write(f"use_ema_exit={cfg_use_ema}\n")
        f.write(f"ema_exit_loss_thr={cfg_thr}\n")
        f.write(f"exit_fast_ema={cfg_fast}\n")
        f.write(f"exit_slow_ema={cfg_slow}\n")
        f.write(f"ema_exit_price_buf={cfg_buf}\n\n")

        f.write("[STOP_LOSS SUMMARY]\n")
        f.write(f"stop_loss_count={total_sl}\n")
        f.write(f"profit_abs_sum={fmt(sum(pa_list) if pa_list else None)}\n")
        f.write(f"profit_abs_mean={fmt((sum(pa_list)/len(pa_list)) if pa_list else None)}\n")
        f.write(f"hold_min_min/med/max={fmt(min(hold_list) if hold_list else None,2)}/{fmt(pct(hold_list,50),2)}/{fmt(max(hold_list) if hold_list else None,2)}\n")
        f.write(f"hold_min_p25/p75={fmt(pct(hold_list,25),2)}/{fmt(pct(hold_list,75),2)}\n")
        f.write(f"dd_from_open_min/med/max={fmt(min(dd_list) if dd_list else None,4)}/{fmt(pct(dd_list,50),4)}/{fmt(max(dd_list) if dd_list else None,4)}\n\n")

        f.write("[TOP PAIRS]\n")
        for k,v in by_pair.most_common(10):
            f.write(f"{k}\t{v}\n")
        f.write("\n[TOP ENTER_TAGS]\n")
        for k,v in by_tag.most_common(10):
            f.write(f"{k}\t{v}\n")

        # worst trades (by profit_abs most negative)
        f.write("\n[WORST STOP_LOSS TRADES]\n")
        worst = sorted(
            [r for r in rows if r["profit_abs"] != ""],
            key=lambda r: float(r["profit_abs"])
        )[:10]
        for r in worst:
            f.write(f"{r['pair']} hold={r['hold_min']}m pa={r['profit_abs']} dd={r['dd_from_open']} tag={r['enter_tag']} open={r['open_time_utc']}\n")

        f.write("\n[FILES]\n")
        f.write(f"CSV={csv_path}\n")
        f.write(f"REPORT={rpt_path}\n")

    # minimal stdout
    print(f"SAVED_CSV={csv_path}")
    print(f"SAVED_REPORT={rpt_path}")
    print(f"STOP_LOSS_COUNT={total_sl}")

if __name__ == "__main__":
    main()
