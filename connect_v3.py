with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. import 추가 (1번째 import 줄 앞에)
import_line = -1
for i, line in enumerate(lines):
    if line.startswith('import os'):
        import_line = i
        break

if import_line >= 0:
    lines.insert(import_line, 'from v3_scorer import calc_sumbi_v3\n')
    print(f"import 추가: {import_line+1}줄")

# 2. calc_quant_score 호출 찾아서 V3 호출 추가
for i, line in enumerate(lines):
    if 'quant    = calc_quant_score' in line or 'quant = calc_quant_score' in line:
        # V3 호출을 바로 다음 줄에 추가
        v3_call = '    v3_result = calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)\n'
        lines.insert(i + 1, v3_call)
        print(f"V3 호출 추가: {i+2}줄")
        break

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("연결 완료!")
