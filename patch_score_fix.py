import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 수급, 뉴스, 차트 데이터를 모두 불러온 가장 마지막 위치를 정밀 타겟팅
target = "st.write('\\ucc28\\ud2b8\\ub97c \\ubd88\\ub7ec\\uc62c \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.')"

lines = code.split('\n')
new_lines = []
for line in lines:
    new_lines.append(line)
    if target in line:
        indent = line[:len(line) - len(line.lstrip())]
        base = indent[:-4] if len(indent) >= 4 else indent
        new_lines.append(base + "st.markdown('---')")
        new_lines.append(base + "st.markdown('### \\uc228\\ube44 AI \\ub525 \\uc2a4\\uce94 \\uc810\\uc218')")
        new_lines.append(base + "score_supply = 0")
        new_lines.append(base + "if 'orgn' in locals() and orgn > 0: score_supply += 15")
        new_lines.append(base + "if 'frgn' in locals() and frgn > 0: score_supply += 15")
        new_lines.append(base + "score_chart = 0")
        new_lines.append(base + "try:")
        new_lines.append(base + "    if df_chart['Close'].iloc[-1] > df_chart['MA5'].iloc[-1]: score_chart += 10")
        new_lines.append(base + "    if df_chart['Close'].iloc[-1] > df_chart['MA20'].iloc[-1]: score_chart += 10")
        new_lines.append(base + "except:")
        new_lines.append(base + "    pass")
        new_lines.append(base + "total_score = score_supply + score_chart")
        new_lines.append(base + "col_s1, col_s2, col_s3 = st.columns(3)")
        new_lines.append(base + "col_s1.metric('\\ud604\\uc7ac \\uc810\\uc218(50\\uc810\\ub9cc\\uc810)', f'{total_score}\\uc810')")
        new_lines.append(base + "col_s2.metric('\\uc218\\uae09 \\uc810\\uc218', f'{score_supply}\\uc810')")
        new_lines.append(base + "col_s3.metric('\\ucc28\\ud2b8 \\uc810\\uc218', f'{score_chart}\\uc810')")
        new_lines.append(base + "st.info('\\uacf5\\ub9e4\\ub3c4/\\uc2e0\\uc6a9 \\ubc0f \\uae30\\uc5c5\\uac00\\uce58\\ub294 API \\uc5f0\\ub3d9 \\ub300\\uae30 \\uc911\\uc785\\ub2c8\\ub2e4.')")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("Success! Scoring engine Phase 1 applied perfectly.")
