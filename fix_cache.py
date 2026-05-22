with open("main.py", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("try: return _engine.collect_all_metrics()", "return _engine.collect_all_metrics()")
c = c.replace("except: return {}", "")
with open("main.py", "w", encoding="utf-8") as f:
    f.write(c)
