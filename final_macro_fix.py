import sys

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 작은따옴표로 감싸진 거시경제 변수 정확한 타겟팅 치환
    content = content.replace("'US 10Y TREASURY'", "'US 10Y TREASURY (미 10년물 국채)'")
    content = content.replace("'USD / KRW'", "'USD / KRW (원/달러 환율)'")
    content = content.replace("'DOLLAR INDEX (DXY)'", "'DOLLAR INDEX (달러 인덱스)'")
    content = content.replace("'WTI CRUDE OIL'", "'WTI CRUDE OIL (WTI 원유)'")

    # 2. 엑스박스 유발 img 태그 완전 삭제 (흔적도 없이 날림)
    target_img_tag = "<img src='{_img}' onerror=\"this.style.display='none'\" style='width:60px;height:60px;flex-shrink:0;'/>"
    content = content.replace(target_img_tag, "")

    # 변경사항 저장
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ 거시경제 번역 완료 및 엑스박스 영구 제거 성공")

except Exception as e:
    print(f"❌ 작업 중 오류 발생: {e}")
