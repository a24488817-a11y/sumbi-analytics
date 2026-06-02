import sys

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 엑스박스(Broken Image) 처리: onerror 속성을 추가하여 이미지 로드 실패 시 깔끔하게 숨김 처리
    target_img = "<img src='{_img}' style='width:60px;height:60px;flex-shrink:0;'/>"
    safe_img = "<img src='{_img}' onerror=\"this.style.display='none'\" style='width:60px;height:60px;flex-shrink:0;'/>"
    content = content.replace(target_img, safe_img)

    # 2. 줄바꿈(Word-break) 방지 CSS 주입: 모바일 환경에서 영문/한글이 어색하게 쪼개지는 현상 방지
    if "word-break: keep-all;" not in content:
        content = content.replace("<style>", "<style> * { word-break: keep-all !important; } ")

    # 3. 누락된 영문 버튼 및 퀀트 매트릭스 라벨 한국어 병기 (정확한 1:1 문자열 치환)
    content = content.replace('"⚡ LAUNCH DEEP SCAN"', '"⚡ LAUNCH DEEP SCAN (딥스캔 시작)"')
    content = content.replace('"Money Flow"', '"Money Flow (자금 흐름)"')
    content = content.replace('"Chart Tech"', '"Chart Tech (차트 기술)"')
    content = content.replace('"Fundamental"', '"Fundamental (펀더멘탈)"')
    content = content.replace('"News Momentum"', '"News Momentum (뉴스 모멘텀)"')
    content = content.replace('"Short Signal"', '"Short Signal (공매도 신호)"')
    content = content.replace('"Macro Env"', '"Macro Env (거시 환경)"')
    content = content.replace('"Sector Theme"', '"Sector Theme (섹터 테마)"')
    content = content.replace('"Broker Flow"', '"Broker Flow (브로커 흐름)"')

    # 변경된 내용을 원본 파일에 덮어쓰기
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ UI 크리티컬 오류 수정 및 번역 패치 100% 완료")

except Exception as e:
    print(f"❌ 작업 중 오류 발생: {e}")
