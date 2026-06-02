import os
import re

try:
    with open("main.py", "r", encoding="utf-8") as f:
        code = f.read()

    # 1. 만약의 사태를 대비해 기존 원본 백업 파일 생성
    with open("main.py.bak", "w", encoding="utf-8") as f:
        f.write(code)
    print("[성공] 기존 main.py 원본 백업 완료 (main.py.bak)")

    # 2. 뉴스 레이더 시작 헤더 위치 포착
    header_marker = 'st.markdown("<h3>LIVE NEWS RADAR</h3>", unsafe_allow_html=True)'
    if header_marker not in code:
        header_marker = "st.markdown('<h3>LIVE NEWS RADAR</h3>', unsafe_allow_html=True)"
    
    if header_marker not in code:
        print("[오류] 뉴스 레이더 헤더 위치를 찾을 수 없습니다. 코드가 이미 변경되었는지 확인 필요.")
        exit(1)

    parts = code.split(header_marker)
    top_half = parts[0] + header_marker + "\n"

    # 3. 하단 데이터 에러 블록 위치 포착 및 분리
    remaining = parts[1]
    marker_str = 'Data Error. Check Ticker Code.'
    idx = remaining.find(marker_str)
    if idx == -1:
        print("[오류] 하단 에러 메시지 위치를 찾을 수 없습니다.")
        exit(1)

    else_idx = remaining.rfind('else:', 0, idx)
    if else_idx == -1:
        print("[오류] 하단 else 위치를 찾을 수 없습니다.")
        exit(1)

    bottom_half = remaining[else_idx:]

    # 4. 삽입할 무오류 자가 치유형 뉴스 엔진 소스코드 정의 (20칸 들여쓰기 최적화)
    injected_news = """
                    # [자가 치유형 뉴스 레이더 엔진 이식]
                    import os, feedparser, re, urllib.parse
                    from dotenv import load_dotenv
                    load_dotenv()
                    
                    nm_dict = {
                        "042660": "한화오션",
                        "012450": "한화에어로스페이스",
                        "079550": "LIG넥스원"
                    }
                    # 테크니컬 수정: URL 인코딩 대신 직관적인 한글 키워드 매칭 처리
                    search_keyword = nm_dict.get(tck, tck)
                    
                    # 1. 1순위 작동: 외부 .env에서 새 네이버 키 자동 주입
                    naver_id = os.getenv("NAVER_CLIENT_ID")
                    naver_secret = os.getenv("NAVER_CLIENT_SECRET")
                    
                    show_news = False
                    if naver_id and naver_secret:
                        try:
                            h3 = {"X-Naver-Client-Id": naver_id.strip(), "X-Naver-Client-Secret": naver_secret.strip()}
                            ns_res = r.get("https://openapi.naver.com/v1/search/news.json", headers=h3, params={"query": f"{search_keyword} 뉴스", "display": 5}, timeout=3)
                            if ns_res.status_code == 200:
                                ns = ns_res.json().get("items", [])
                                if ns:
                                    for item in ns:
                                        title_clean = re.sub('<.*?>', '', item['title']).replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
                                        st.markdown(f"- [{title_clean}]({item['link']})")
                                    show_news = True
                        except Exception as e:
                            pass
                    
                    # 2. 2순위 작동: 네이버 실패 시 구글 뉴스 RSS로 즉시 자가 치유(Fallback) 우회
                    if not show_news:
                        try:
                            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_keyword + ' 뉴스')}&hl=ko&gl=KR&ceid=KR:ko"
                            feed = feedparser.parse(rss_url)
                            if feed.entries:
                                for entry in feed.entries[:5]:
                                    title_clean = re.sub('<.*?>', '', entry.title).replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&')
                                    st.markdown(f"- [{title_clean}]({entry.link})")
                            else:
                                st.warning("No News Found.")
                        except Exception as rss_err:
                            st.error(f"News System Error: {rss_err}")
"""

    # 5. 소스코드 정밀 결합 (들여쓰기 12칸 매칭)
    new_code = top_half + injected_news + "            " + bottom_half

    with open("main.py", "w", encoding="utf-8") as f:
        f.write(new_code)
    print("[성공] 자가 치유 뉴스 레이더 엔진 이식이 최종 완료되었습니다!")

except Exception as e:
    print(f"[실패] 패치 도중 에러 발생: {e}")
