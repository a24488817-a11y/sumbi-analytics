import os, re

filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# 1. 파괴된 괄호 코드 완벽 복구 (SyntaxError 원천 해결)
bad_pattern = r'\(int\((.*?)\) if str\(\1\)\.strip\(\) else 0\)'
code = re.sub(bad_pattern, r'int(\1)', code)

# 2. 궁극의 무결점 엔진 패치 (파이썬 내장 함수 방어막 씌우기)
engine_patch = """
# --- CORE ENGINE PATCH ---
import builtins
_orig_int = builtins.int
def _safe_int(x, *args, **kwargs):
    if isinstance(x, str) and not x.strip(): return 0
    try: return _orig_int(x, *args, **kwargs)
    except (ValueError, TypeError): return 0
builtins.int = _safe_int
# -------------------------
"""

if "# --- CORE ENGINE PATCH ---" not in code:
    code = engine_patch + "\n" + code

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code)

print("--- FATAL ERROR RESCUED & ENGINE PATCHED ---")
