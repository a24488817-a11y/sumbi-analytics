import requests, os
from dotenv import load_dotenv

load_dotenv()
NAVER_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

def get_naver_news(query, display=10):
    """네이버 뉴스 검색 API"""
    try:
        headers = {
            "X-Naver-Client-Id": NAVER_ID,
            "X-Naver-Client-Secret": NAVER_SECRET
        }
        params = {"query": query, "display": display, "sort": "date"}
        r = requests.get("https://openapi.naver.com/v1/search/news.json",
                        headers=headers, params=params, timeout=5)
        items = r.json().get("items", [])
        return [{"title": i["title"].replace("<b>","").replace("</b>",""),
                 "link": i["link"],
                 "pub": i["pubDate"]} for i in items]
    except Exception as e:
        print(f"네이버 뉴스 오류: {e}")
        return []

if __name__ == "__main__":
    news = get_naver_news("삼성전자 주식", 5)
    print(f"뉴스 {len(news)}건:")
    for n in news:
        print(f"  - {n[title][:30]}")
