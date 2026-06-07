#!/usr/bin/env python3
import ast, shutil, sys, os
F = os.path.expanduser("~/sumbi-analytics/killmove_rank.py")
OLD = "    get_true_short_data = None"
NEW = '''    def get_true_short_data(code):
        import os, csv
        fp = os.path.expanduser("~/sumbi-analytics/short_data/%s.csv" % code)
        if not os.path.exists(fp):
            return {}
        try:
            with open(fp, "r", newline="") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                return {}
            last = rows[-1]
            ratio = float(str(last.get("ssts_vol_rlim", "0")).replace(",", "").strip() or 0)
            return {"short_today": 0, "short_yesterday": 0, "short_ratio": ratio}
        except Exception:
            return {}'''
src = open(F).read()
if src.count(OLD) != 1:
    print("ABORT: marker count =", src.count(OLD)); sys.exit(1)
new_src = src.replace(OLD, NEW)
try:
    ast.parse(new_src)
except SyntaxError as e:
    print("ABORT: syntax error after patch:", e); sys.exit(1)
open(F, "w").write(new_src)
# re-verify written file
try:
    ast.parse(open(F).read())
    print("PATCH OK + AST OK")
except SyntaxError as e:
    bak = sorted([x for x in os.listdir(os.path.dirname(F)) if x.startswith("killmove_rank.py.bak_")])
    if bak:
        shutil.copy(os.path.join(os.path.dirname(F), bak[-1]), F)
        print("RESTORED from backup due to:", e)
    sys.exit(1)
