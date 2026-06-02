# -*- coding: utf-8 -*-
import re
with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 'Money Flow Score' 텍스트를 포함하는 st.markdown 구문 전체를 정규식으로 완벽 삭제
c = re.sub(r'st\.markdown\([fF]?[\'"]{1,3}[^\'"]*Money Flow Score[^\'"]*[\'"]{1,3}[^)]*unsafe_allow_html=True\)', '', c, flags=re.DOTALL)

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("=== OLD SCORE NUKED ===")
