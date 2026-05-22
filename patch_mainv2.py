import os
import re

try:
    with open("main.py", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 1. 만약의 사태를 대비한 2차 원본 백업
    with open("main.py.bak2", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("[성공] 원본 소스코드 2차 백업 완료 (main.py.bak2)")

    # 2. 뉴스 레이더 위치 기습 탐지
    radar_idx = -1
    for i, line in enumerate(lines):
        if "LIVE NEWS RADAR" in line:
            radar_idx = i
            break

    if radar_idx == -1:
        print("[오류] 'LIVE NEWS RADAR' 위치를 포획하지 못했습니다.")
        exit(1)

    # 3. 하단 데이터 에러 블록 위치 탐지
    data_error_idx = -1
    for i in range(len(lines)-1, -1, -1):
        if "Data Error. Check Ticker Code." in lines[i]:
            data_error_idx = i
            break

    if data_error_idx == -1:
        print("[오류] 'Data Error. Check Ticker Code.' 위치를 찾을 수 없습니다.")
        exit(1)

    # 그 위의 상위 else: 위치 자동 매칭
    else_idx = -1
    for j in range(data_error_idx - 1, -1, -1):
        if "else:" in lines[j]:
            else_idx = j
            break

    if else_idx == -1:
        print("[오류] 하단 마감 구조(else:)를 찾을 수 없습니다.")
        exit(1)

    # 4. 현재 파일의 들여쓰기(Indent) 깊이 자동 추출
    radar_line = lines[radar_idx]
    indentation = len(radar_line) - len(radar_line.lstrip())
    indent_str = " " * indentation

    # 5. 무오류 자가 치유형 뉴스 레이더 소스코드 주입 데이터 정의
    injected_news = f"""
{indent_str}# [자가 치유형 뉴스 레이더 엔진 이식]
{indent_str}import os, feedparser, re, urllib.parse
{indent_str}from dotenv import load_dotenv
{indent_str}load_dotenv()

{indent_str}nm_dict = {{
{indent_str}    "042660": "한화오션",
{indent_str}    "012450": "한화에어로스페이스",
{indent_str}    "079550": "LIG넥스원"
{indent_str}}}
{indent_str}search_keyword = nm_dict.get(tck, tck)

{indent_str}naver_id = os.getenv("NAVER_CLIENT_ID")
{indent_str}naver_secret = os.getenv("NAVER_CLIENT_SECRET")

{indent_str}show_news = False
{indent_str}if naver_id and naver_secret:
{indent_str}    try:
{indent_str}        h3 = {{"X-Naver-Client-Id": naver_id.strip(), "X-Naver-Client-Secret": naver_secret.strip()}}
{indent_str}        ns_res = r.get("https://openapi.naver.com/v1/search/news.json", headers=h3, params={{"query": f"{{search_keyword}} 뉴스", "display": 5}}, timeout=3)
{indent_str}        if ns_res.status_code == 200:
{indent_str}            ns = ns_res.json().get("items", [])
{indent_str}            if ns:
{indent_str}                for item in ns:
{indent_str}                    title_clean = re.sub('<.*?>', '', item['title']).replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
{indent_str}                    st.markdown(f"- [{{title_clean}}]({{item['link']}})")
{indent_str}                show_news = True
{indent_str}    except Exception as e:
{indent_str}        pass

{indent_str}if not show_news:
{indent_str}    try:
{indent_str}        rss_url = f"https://news.google.com/rss/search?q={{urllib.parse.quote(search_keyword + ' 뉴스')}}&hl=ko&gl=KR&ceid=KR:ko"
{indent_str}        feed = feedparser.parse(rss_url)
{indent_str}        if feed.entries:
{indent_str}            for entry in feed.entries[:5]:
{indent_str}                title_clean = re.sub('<.*?>', '', entry.title).replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
{indent_str}                st.markdown(f"- [{{title_clean}}]({{entry.link}})")
{indent_str}        else:
{indent_str}            st.warning("No News Found.")
{indent_str}    except Exception as rss_err:
{indent_str}        st.error(f"News System Error: {{rss_err}}")
"""

    # 6. 상단 로직 + 신형 뉴스 엔진 + 하단 예외 블록 정밀 결합
    top_part = lines[:radar_idx + 1]
    bottom_part = lines[else_idx:]
    
    new_code = "".join(top_part) + injected_news + "".join(bottom_part)

    with open("main.py", "w", encoding="utf-8") as f:
        f.write(new_code)
    print("[성공] 정밀 자가 치유 뉴스 엔진 이식이 최종 완료되었습니다!")

except Exception as e:
    print(f"[실패] 정밀 패치 중 예외 발생: {e}")
