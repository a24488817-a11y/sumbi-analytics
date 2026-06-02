import re
path = "/home/ubuntu/main.py"
with open(path, "r", encoding="utf-8") as f: code = f.read()

# 1. 들여쓰기된 디자인 코드 블록을 찾아 맨 앞으로 당깁니다 (Regex lookahead 사용)
fixed_code = re.sub(r'(st\.markdown\(\'\'\')\s+', r'\1', code)
fixed_code = re.sub(r'\n\s{4,}', r'\n', fixed_code)

with open(path, "w", encoding="utf-8") as f: f.write(fixed_code)
