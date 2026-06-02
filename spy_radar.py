import re

clean_lines = []
with open("main.py", "r", encoding="utf-8") as f:
    for line in f:
        if any(k in line for k in ["st.", "streamlit", "layout=", "with c", "gold-header"]):
            clean_lines.append("# " + line.rstrip())
        else:
            clean_lines.append(line.rstrip())

diagnostic_code = "\n".join(clean_lines) + """
try:
    print("\\n======= [숨비 프리미엄 API 실시간 키 인양 결과] =======")
    token = get_token()
    data = get_data(token, '042660')
    print("🎯 증권사 서버가 반환한 정품 Key 목록:")
    import pprint
    pprint.pprint(list(data.keys()))
    print("========================================================\\n")
except Exception as e:
    print("❌ 인양 실패:", e)
"""
exec(diagnostic_code)
