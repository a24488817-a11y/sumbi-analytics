import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = "st.markdown(f'<div class=\"card\" style=\"text-align:center;\">{txt_mapping}</div>', unsafe_allow_html=True)"

if "score_supply" in code:
    print("Score module already installed.")
else:
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        if target in line:
            indent = line[:len(line) - len(line.lstrip())]
            # ì ìˆ˜ ê³„ì‚° ë¡œì§ ì‚½ìž…
            new_lines.append(indent + "st.markdown('---')")
            new_lines.append(indent + "st.markdown('### í ¼í¾¯ \\uc228\\ube44 AI \\ub525 \\uc2a4\\uce94 \\uc810\\uc218')")
            new_lines.append(indent + "score_supply = 0")
            new_lines.append(indent + "if orgn > 0: score_supply += 15")
            new_lines.append(indent + "if frgn > 0: score_supply += 15")
            new_lines.append(indent + "score_chart = 0")
            new_lines.append(indent + "try:")
            new_lines.append(indent + "    if df_chart['Close'].iloc[-1] > df_chart['MA5'].iloc[-1]: score_chart += 10")
            new_lines.append(indent + "    if df_chart['Close'].iloc[-1] > df_chart['MA20'].iloc[-1]: score_chart += 10")
            new_lines.append(indent + "except: pass")
            new_lines.append(indent + "total_score = score_supply + score_chart")
            new_lines.append(indent + "col_s1, col_s2, col_s3 = st.columns(3)")
            new_lines.append(indent + "col_s1.metric('\\ud604\\uc7ac \\ud655\\ubcf4\\ub41c \\uc810\\uc218 (50\\uc810 \\ub9cc\\uc810)', f'{total_score}\\uc810')")
            new_lines.append(indent + "col_s2.metric('\\uc218\\uae09\\uc810\\uc218', f'{score_supply}\\uc810')")
            new_lines.append(indent + "col_s3.metric('\\ucc28\\ud2b8\\uc810\\uc218', f'{score_chart}\\uc810')")
            new_lines.append(indent + "st.info('\\u26a0\\ufe0f \\uacf5\\ub9e4\\ub3c4/\\ub300\\ucc28/\\uc2e0\\uc6a9 \\ubc0f \\uae30\\uc5c5\\uac00\\uce58 \\ub370\\uc774\\ud130\\ub294 API \\uc5f0\\ub3d9 \\ub300\\uae30 \\uc911\\uc785\\ub2c8\\ub2e4.')")
            new_lines.append(indent + "st.markdown('---')")
        new_lines.append(line)
        
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("Success! Scoring engine Phase 1 applied safely.")
