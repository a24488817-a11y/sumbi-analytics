import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 중복된 점수판 항목들을 제거하고 하나로 통합
lines = code.split('\n')
new_lines = []
skip = False
for line in lines:
    if "st.markdown('### \\uc228\\ube44 AI \\ub525 \\uc2a4\\uce94 \\uc810\\uc218')" in line:
        skip = False # 새 점수판 시작
    if skip: continue
    new_lines.append(line)
    if "col_s1.metric('최종 딥스캔 점수 (100점)'" in line:
        skip = True # 이전의 지저분한 점수 출력 구간을 스킵

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("Success! Scoring UI cleaned.")
