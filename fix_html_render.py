import re

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 정규식을 사용하여 빈 줄과 과도한 들여쓰기를 제거하고 태그를 밀착시킴
    # (gap:20px;'> 와 <div style='flex:1;'> 사이의 공백 및 줄바꿈 압축)
    broken_pattern = r"(align-items:center;gap:20px;'>)\s+(<div style='flex:1;'>)"
    fixed_pattern = r"\1\n<div style='flex:1;'>\n"
    
    content = re.sub(broken_pattern, fixed_pattern, content)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ HTML 코드 노출 버그 완벽 수리 완료")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
