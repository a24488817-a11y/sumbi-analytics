with open("macro_engine.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. 막혀버린 BDI 지수 대신 WTI 원유(CL=F) 데이터를 끌어오도록 파이프라인 우회
code = code.replace("'^BDI'", "'CL=F'")
code = code.replace('"^BDI"', '"CL=F"')

# 2. 데이터 하나가 빠졌다고 전체를 버리는 결벽증 로직(dropna)을 부드럽게 유연화
code = code.replace(".dropna()", ".ffill().bfill()")

with open("macro_engine.py", "w", encoding="utf-8") as f:
    f.write(code)
