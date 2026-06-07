import ast, shutil, datetime
f = "killmove_rank.py"
bak = f + ".bak_" + datetime.datetime.now().strftime("%H%M")
shutil.copy(f, bak)
src = open(f).read()
old = "        change_pct = (cur - prev) / prev * 100.0\n"
assert src.count(old) == 1, "FAIL count=%d" % src.count(old)
new = old + "        if not (REVERSAL_LOW <= change_pct <= REVERSAL_HIGH):\n            return None\n"
src2 = src.replace(old, new)
ast.parse(src2)
open(f, "w").write(src2)
print("PATCH OK + AST OK | backup=" + bak)
