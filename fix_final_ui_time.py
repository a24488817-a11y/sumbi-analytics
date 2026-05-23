import re

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 마크다운 코드블록 버그 원천 차단
    # <div style='flex:1;'> 바로 아래의 빈 줄과 깊은 들여쓰기를 정규식으로 완벽히 제거하여 태그 밀착
    content = re.sub(r"<div style='flex:1;'>\s*\n\s*<div", "<div style='flex:1;'>\n<div", content)
    
    # 내부 태그들의 불필요한 빈 줄 및 들여쓰기도 모두 압축
    content = re.sub(r"</div>\s*\n\s*<div", "</div>\n<div", content)
    content = re.sub(r"</div>\s*\n\s*</div", "</div>\n</div", content)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("✅ HTML 빈줄/들여쓰기 진공 압축 완료 (마크다운 버그 원천 차단)")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
