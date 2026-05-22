import os, re
filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f: code = f.read()

# 1. 앱을 죽인 독극물(Monkey Patch) 완벽 도려내기
code = re.sub(r'# --- CORE ENGINE PATCH ---.*?# -------------------------\n', '', code, flags=re.DOTALL)
# 혹시 남아있을지 모르는 builtins 조작 코드 제거
code = re.sub(r'import builtins\n_orig_int = builtins\.int.*?', '', code, flags=re.DOTALL)

# 2. 꼬여버린 SyntaxError 강제 복원 (가장 무식하고 확실한 방법)
# 이전에 잘못 덮어씌워진 괴상한 int() 구문들을 모조리 찾아서 원상 복구
code = re.sub(r'\(int\([^)]+\) if str\([^)]+\)\.strip\(\) else 0\)', lambda m: m.group(0).replace(' if str', '').replace(').strip() else 0)', ')'), code)

# 3. 가장 안전한 정석 패치: '한화오션' 빈 데이터 에러 방어
# API 데이터(res.get)를 가져올 때, 만약 그 값이 없다면(None 이거나 "") '0'을 기본값으로 쓰도록 안전망 설치
code = re.sub(r'(res\.get\("[^"]+"\))', r'(\1 or "0")', code)

with open(filepath, "w", encoding="utf-8") as f: f.write(code)
print("--- FATAL TOXIN REMOVED & SAFE ENGINE PATCH APPLIED ---")
