"""SOOMBI Analytics v4.0
한국 주식 시장 KOSPI/KOSDAQ 전문 분석 엔진
SOOMBI ANALYST Impact Score — 세력 수급 역추적 & 매수 적합도 즉시 판단
데이터: FinanceDataReader + Naver Finance
"""
import streamlit as st
import pandas as pd
import numpy as np
import requests
import FinanceDataReader as fdr
import yfinance as yf
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import StringIO
import pytz
import re
import math
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# 1. 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
KST = pytz.timezone("Asia/Seoul")

st.set_page_config(
    page_title="숨비 애널리틱스",
    page_icon="🐋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── SOOMBI ANALYTICS v4.0 — Gold & Dark Luxury Theme ── */

/* 전체 배경 */
[data-testid="stApp"] { background:#0E1117; }
[data-testid="stAppViewContainer"] > .main { background:#0E1117; }

/* 헤더 골드 */
h1,h2,h3 { color:#D4AF37 !important; letter-spacing:.02em; }
h4,h5,h6 { color:#c8a227 !important; }

/* 사이드바 */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0d1526 0%,#0E1117 100%) !important;
  border-right:1px solid #2a2f3e;
}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,
[data-testid="stSidebar"] td,[data-testid="stSidebar"] th {
  color:#E8E8E8 !important;
}
[data-testid="stSidebar"] [data-testid="metric-container"] { background:#12192b !important; }

/* 메트릭 카드 */
div[data-testid="metric-container"] {
  background:#12192b !important;
  border:1px solid #2a2f3e;
  border-radius:12px;
  padding:14px 18px;
  box-shadow:0 2px 12px rgba(0,0,0,.4);
}
div[data-testid="metric-container"] label { color:#8fa3b8 !important; font-size:.82rem; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color:#F0F0F0 !important; font-weight:800;
}

/* 버튼 골드 */
[data-testid="stButton"] > button {
  background:linear-gradient(135deg,#b8960c,#D4AF37) !important;
  color:#0E1117 !important; font-weight:800;
  border:none !important; border-radius:8px !important;
  box-shadow:0 2px 8px rgba(212,175,55,.3);
  transition:all .2s;
}
[data-testid="stButton"] > button:hover {
  background:linear-gradient(135deg,#D4AF37,#f0d060) !important;
  box-shadow:0 4px 16px rgba(212,175,55,.5);
}

/* 탭 골드 */
[data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom:2px solid #2a2f3e; }
[data-testid="stTabs"] [data-baseweb="tab"] {
  color:#8fa3b8 !important; font-weight:600; background:transparent !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color:#D4AF37 !important; border-bottom:2px solid #D4AF37 !important;
}

/* 구분선 */
hr { border-color:#2a2f3e !important; }

/* 데이터프레임 */
[data-testid="stDataFrame"] { border:1px solid #2a2f3e; border-radius:12px; overflow:hidden; }

/* 텍스트인풋 */
[data-testid="stTextInput"] input {
  background:#12192b !important; border:1px solid #2a2f3e !important;
  color:#E8E8E8 !important; border-radius:8px !important;
}

/* 정보·경고 박스 */
[data-testid="stAlertContainer"] { border-radius:10px !important; }

/* 캡션 */
[data-testid="stCaptionContainer"] { color:#6b7c93 !important; }

/* 익스팬더 */
details summary { color:#D4AF37 !important; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. 상수 및 오버라이드 데이터
# ─────────────────────────────────────────────────────────────────────────────
NAVER_HDRS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 42대 필살기 뉴스 키워드
_GOOD_KW = [
    "수주", "흑자전환", "영업이익", "매출 증가", "실적 개선", "수출", "계약 체결",
    "신약", "허가", "목표주가 상향", "매수", "배당", "자사주 매입",
    "HBM", "LNG", "방산", "K방산", "수주 잔고", "기술 수출", "흑자",
    # 배거차숏: 배당/밸류업 + 거시쇼크 반전 + 차트심리 + 숏스퀴즈
    "밸류업", "숏스퀴즈", "주주환원", "자사주 소각", "분기배당", "특별배당",
    "공매도 환매", "숏커버링", "거시 반등", "금리 인하", "피벗", "저점 돌파",
    "52주 신고가", "골든크로스", "데드캣 반등", "바닥 확인", "반등 시작",
]
_BAD_KW = [
    "손실", "적자", "하향", "매도", "소송", "검찰", "횡령", "배임",
    "유상증자", "주가 하락", "블록딜", "오버행", "공매도 증가", "실적 악화",
    "금리 인상", "경기 침체", "파산", "상장폐지", "관리종목",
]

# Negative Override — 이 키워드가 제목에 있으면 Tier1·Tier2 승격 즉시 차단
# 긍정 키워드("수주", "목표가 상향")가 함께 있어도 악재 우선 강등 원칙
_HARD_NEG_KW = [
    "감소", "하락", "적자", "어닝쇼크", "어닝 쇼크", "지연", "취소",
    "철회", "실패", "부진", "미달", "급락", "손실 확대",
    "매출 감소", "영업손실", "전망 하향", "목표가 하향", "주가 급락",
]

# ── 뉴스 등급제 (News Tiering) ────────────────────────────────────────────────
# Tier 1: 확정적 사실 — 주가 직접 영향 (20점 만점)
_TIER1_KW = [
    # 법원·판결
    "기각", "승소", "판결", "가처분 기각", "특허 무효 기각",
    # 계약·공급·수주 확정
    "공급계약", "단일판매", "계약 체결", "독점 공급", "독점 계약",
    "최대 수주", "대규모 수주", "공급 확정", "수주 확정", "수주 성공",
    "수주", "클라우드 수주",
    # 상장·IPO
    "상장", "IPO", "상장 확정", "증시 입성", "공모가 확정", "상장 예정",
    "코스피 상장", "코스닥 상장", "기업공개",
    # 실적 서프라이즈
    "사상 최대", "역대 최대", "사상 최고", "어닝 서프라이즈", "어닝쇼크 반전",
    "사상 최고 실적", "연간 최대 흑자",
    # 기업 이벤트 확정
    "M&A", "인수 완료", "합병 완료", "원천기술", "세계 최초",
    "FDA 승인", "임상 성공", "양산 성공", "흑자 전환 확정", "적자 탈출",
    "상한가", "특허 등록", "IPO 확정",
    # 업종 특화 (KDDX·HBM·클라우드·로봇 등)
    "KDDX", "HBM 양산", "아틀라스", "AI 반도체 양산", "자율주행 계약",
    "클라우드", "AI 클라우드", "MSP 계약",
]
# Tier 2: 긍정적 기대감 — 미래 가치 (건당 5점, 최대 10점)
_TIER2_KW = [
    "목표주가 상향", "목표가 상향", "매수 추천", "신제품 출시", "박람회",
    "해외 진출", "신규 계약", "추가 수주", "증설", "MOU", "업무협약",
    "협력", "파트너십", "투자 유치", "신규 사업", "로드쇼", "호실적",
    "수주 기대", "협의 중", "검토 중", "협상 진행",
    # ── V8.1 신사업 모멘텀 확장 ─────────────────────────────────────────────
    # 신제품·기술·플랫폼 출범 이벤트 (미래 성장성 입증)
    "출시", "공개", "개발", "플랫폼", "AI", "혁신", "선언", "특허",
]
# Tier 3: 소음/중립 — 점수 반영 제외
_NOISE_KW = [
    "장마감", "마감시황", "오전시황", "오후시황", "시황", "주간 요약",
    "특징주", "기업 개요", "오늘의 주요", "증시 마감", "급등주 포착",
    "코스피 현황", "코스닥 현황", "주요 일정", "주간 브리핑",
]
# 하위 호환 — 기존 _IMPACT_KW 참조 코드가 있는 경우를 위해 별칭 유지
_IMPACT_KW = _TIER1_KW

# Tier 0 — 시장 구조 변경급 초강력 이벤트 (M&A·공개매수·이전상장 등)
_TIER0_KW = [
    "합병", "피인수", "공개매수", "MBO", "TOB", "상장폐지 기각",
    "코스피 이전", "이전상장", "인수합병", "주식 교환", "적대적 인수",
    "자진상장폐지 철회", "경영권 인수", "컨소시엄 구성",
]

# Tier 중립 (10점) — 일반 PR·채용·인사·IR·수상 등 주가 영향 미미한 기업 활동
_NEUTRAL_ARTICLE_KW = [
    "채용", "사회공헌", "CSR", "ESG", "기념식", "창립",
    "IR", "투자설명회", "NDR", "애널리스트데이", "기업설명회",
    "임원 선임", "대표이사 선임", "이사회", "사외이사", "경영진",
    "후원", "봉사", "캠페인", "홍보", "기부", "협약식",
    "시상", "수상", "선정", "인증", "인사 발령", "조직 개편",
]

# DART 공시 교차검증 키워드 — 공시 연동 뉴스 = 팩트 신뢰도 최고
_DART_KW = [
    "공시", "전자공시", "수시공시", "사업보고서",
    "분기보고서", "반기보고서", "DART", "금감원", "공시 접수",
]

# V8.0 Flexible Match — 종목코드별 영문 약칭 하드코딩 맵
_KNOWN_ENG_ALIAS: dict[str, list[str]] = {
    "064400": ["LG CNS", "LGCNS"],           # LG씨엔에스 (2025년 상장 실제 코드)
    "000660": ["SK Hynix", "SKHynix", "하이닉스"],
    "005930": ["Samsung Electronics", "Samsung", "삼성전자"],
    "005380": ["Hyundai Motor", "현대차"],
    "000270": ["Kia", "KIA"],
    "051910": ["LG Chem", "LGChem"],
    "035420": ["NAVER"],
    "035720": ["Kakao"],
    "066570": ["LG Electronics", "LG전자"],
    "015760": ["KEPCO", "한국전력"],
    "055550": ["Shinhan", "신한"],
    "105560": ["KB Financial", "KB금융"],
    "086790": ["Hana Financial", "하나금융"],
    "207940": ["Samsung Biologics", "삼성바이오"],
    "096770": ["SK Innovation", "SK이노"],
    "012330": ["Hyundai Mobis", "현대모비스"],
    "011070": ["LG Innotek", "LG이노텍"],
    "042700": ["Hanmi Semi", "한미반도체"],
    "009830": ["Hanwha Ocean", "한화오션"],
    "329180": ["Hyundai Heavy", "현대중공업"],
    "373220": ["LG Energy", "LG에너지솔루션", "LGES"],
}


def _build_eng_aliases(name: str, ticker: str) -> tuple[str, ...]:
    """종목명·코드로부터 영문 약칭 후보를 생성 — get_news() Flexible Match용 tuple."""
    aliases: list[str] = []
    # ① 하드코딩 맵 — 완전한 구절("LG CNS", "LGCNS")만, 부분 prefix 절대 없음
    aliases.extend(_KNOWN_ENG_ALIAS.get(ticker, []))
    # ② 이름 자체가 순수 영문(한글 0글자)인 경우만 추가 (NAVER, Kakao 등)
    #    "LG씨엔에스"처럼 한글 혼합명은 완전 제외 → "LG" 단독 prefix 오염 100% 차단
    if re.match(r"^[A-Za-z][A-Za-z0-9\s\-&\.]+$", name) and name not in aliases:
        aliases.append(name)
    return tuple(dict.fromkeys(aliases))   # 순서 보존·중복 제거


# KRX 휴장일 내장 폴백 테이블 (open.krx.co.kr API 불가 시 사용)
_KRX_HOLIDAYS_FALLBACK: dict[int, dict[str, str]] = {
    2025: {
        "2025-01-01": "신정",
        "2025-01-28": "설날 연휴",
        "2025-01-29": "설날",
        "2025-01-30": "설날 연휴",
        "2025-03-01": "삼일절",
        "2025-05-05": "어린이날",
        "2025-05-06": "어린이날 대체공휴일",
        "2025-06-06": "현충일",
        "2025-08-15": "광복절",
        "2025-10-03": "개천절",
        "2025-10-05": "추석 연휴",
        "2025-10-06": "추석",
        "2025-10-07": "추석 연휴",
        "2025-10-09": "한글날",
        "2025-12-25": "성탄절",
        "2025-12-31": "연말 휴장",
    },
    2026: {
        "2026-01-01": "신정",
        "2026-02-17": "설날 연휴",
        "2026-02-18": "설날",
        "2026-02-19": "설날 연휴",
        "2026-03-01": "삼일절",
        "2026-05-05": "어린이날",
        "2026-06-06": "현충일",
        "2026-08-17": "광복절 대체공휴일",
        "2026-10-05": "추석",
        "2026-10-09": "한글날",
        "2026-12-25": "성탄절",
        "2026-12-31": "연말 휴장",
    },
    2027: {
        "2027-01-01": "신정",
        "2027-02-05": "설날 연휴",
        "2027-02-08": "설날 대체공휴일",
        "2027-02-09": "설날 연휴 대체공휴일",
        "2027-03-01": "삼일절",
        "2027-05-05": "어린이날",
        "2027-06-07": "현충일 대체공휴일",
        "2027-08-16": "광복절 대체공휴일",
        "2027-09-30": "추석 연휴",
        "2027-10-01": "추석",
        "2027-10-04": "추석 연휴 대체공휴일",
        "2027-10-05": "개천절 대체공휴일",
        "2027-10-11": "한글날 대체공휴일",
        "2027-12-27": "성탄절 대체공휴일",
        "2027-12-31": "연말 휴장",
    },
    2028: {
        "2028-01-03": "신정 대체공휴일",
        "2028-01-25": "설날 연휴",
        "2028-01-26": "설날",
        "2028-01-27": "설날 연휴",
        "2028-03-01": "삼일절",
        "2028-05-05": "어린이날",
        "2028-06-06": "현충일",
        "2028-08-15": "광복절",
        "2028-09-18": "추석 연휴",
        "2028-09-19": "추석",
        "2028-09-20": "추석 연휴",
        "2028-10-03": "개천절",
        "2028-10-09": "한글날",
        "2028-12-25": "성탄절",
        "2028-12-31": "연말 휴장",
    },
}

# 블록딜·오버행 경보 — 실시간 수급 기반 자동 감지
# (특정 종목 하드코딩 폐기 → 수급 분석 엔진이 동적 감지)
_BLOCK_ALERT: dict[str, str] = {}

# ─────────────────────────────────────────────────────────────────────────────
# 경제적 해자 DB — 모듈 레벨 공유 함수 (ui_moat_expander + LEGENDARY 카드 공용)
# ─────────────────────────────────────────────────────────────────────────────
def _get_moat_info(ticker: str, name: str) -> dict:
    """경제적 해자 DB 조회 — 알려진 종목 상세 분석, 미등록 종목 범용 폴백."""
    _DB: dict[str, dict] = {
        "042660": {
            "title": "한화오션 — 조선·해양·방산 초격차 독점",
            "overview": "국내 대형 조선·해양 플랜트·특수선(방산) 건조 기업. 한화그룹 편입 이후 방산·에너지 시너지 확대 중.",
            "moat": [
                "**방산(함정) 독점력**: 국내 유일 잠수함 턴키 건조 능력(KSS-III). 북미 함정 MRO 진출.",
                "**친환경 스마트 선박**: 암모니아 추진선·LCO₂ 운반선 등 차세대 선박 기술 세계 최고 수준.",
                "**자율운항 기술**: HS-모빌리티 첨단 자율운항 선박 기술 적용 확대 중.",
            ],
        },
        "439260": {
            "title": "대한조선 — 중소형 특수선 전문",
            "overview": "중소형 탱커·벌크선 특화 조선소. 가격 경쟁력과 납기 준수율 강점.",
            "moat": [
                "**중소형 선박 특화**: 대형 조선소가 외면하는 중소형 틈새 시장 장악.",
                "**빠른 납기**: 소형 도크 특성상 회전율 빠름 → 수주잔고 대비 매출 인식 속도 유리.",
                "**원가 경쟁력**: 경남 고성 저렴한 부지 및 인건비 구조.",
            ],
        },
        "005930": {
            "title": "삼성전자 — 반도체·스마트폰 글로벌 1위",
            "overview": "메모리(DRAM·NAND)·파운드리·스마트폰·디스플레이·가전 수직계열화 글로벌 테크 대기업.",
            "moat": [
                "**메모리 반도체 점유율 1위**: DRAM 42%, NAND 31% 세계 1위 유지.",
                "**HBM·온디바이스 AI**: HBM3E 양산·On-device AI 기능 Galaxy 적용 선도.",
                "**수직계열화**: 소재·장비·팹·완제품 내재화 → 원가 및 공급 유연성 경쟁 우위.",
            ],
        },
        "000660": {
            "title": "SK하이닉스 — HBM 글로벌 1위",
            "overview": "DRAM·NAND·HBM 전문 반도체 기업. 엔비디아 HBM 단독 공급으로 AI 반도체 슈퍼사이클 최대 수혜.",
            "moat": [
                "**HBM 세계 1위**: HBM3E 12단 엔비디아 독점 공급 — AI 데이터센터 핵심 부품.",
                "**DRAM 기술 선도**: 1c nm 공정 전환 완료, 원가 절감 + 성능 우위 동시 확보.",
                "**엔비디아 파트너십**: GB200 NVL72 HBM 우선 공급권 확보.",
            ],
        },
        "035420": {
            "title": "NAVER — 국내 검색·AI 플랫폼 독점",
            "overview": "국내 검색점유율 65%+, 클로바X AI·클라우드·커머스·웹툰 등 디지털 생태계 통합 운영.",
            "moat": [
                "**검색 독점**: 한국어 특화 검색 알고리즘 + 지식iN·블로그 유저 생성 콘텐츠 해자.",
                "**AI·클라우드**: 하이퍼클로바X LLM 자체 개발 — 글로벌 빅테크 종속 탈피.",
                "**커머스 생태계**: 스마트스토어·네이버페이 MAU 4천만+ 폐쇄형 커머스 생태계.",
            ],
        },
        "035720": {
            "title": "카카오 — 모바일 메신저 생태계 독점",
            "overview": "카카오톡 MAU 4,700만+, 카카오페이·카카오뱅크·카카오엔터 등 핀테크·콘텐츠 수직 확장.",
            "moat": [
                "**메신저 독점**: 카카오톡 국민 메신저 지위 — 대체재 부재.",
                "**핀테크 시너지**: 카카오페이·카카오뱅크 고객 데이터·송금 채널 독점적 연계.",
                "**K-콘텐츠 IP**: 웹툰·음악(멜론)·영화·드라마 IP 수직계열화.",
            ],
        },
        "207940": {
            "title": "삼성바이오로직스 — CDMO 글로벌 톱3",
            "overview": "위탁개발생산(CDMO) 전문 기업. 글로벌 빅파마 수주 잔고 수조원 확보.",
            "moat": [
                "**CDMO 초대형 Capa**: 단일 공장 기준 세계 최대 규모 → 규모의 경제 선점.",
                "**빅파마 파트너십**: 글로벌 상위 20개 제약사 대부분 고객사 확보.",
                "**ADC·mRNA 차세대 CDMO**: 항체약물접합체·mRNA 백신 위탁생산 역량 확장.",
            ],
        },
        "068270": {
            "title": "셀트리온 — 바이오시밀러 글로벌 선도",
            "overview": "램시마·허쥬마·유플라이마 등 바이오시밀러 글로벌 판매. 미국·유럽 직판 체계 구축.",
            "moat": [
                "**바이오시밀러 개척자**: 램시마 최초 허가·출시 — 1위 선점 효과.",
                "**직판 채널**: 미국 셀트리온USA·유럽 직판법인 → 유통 마진 내재화.",
                "**파이프라인**: 줄기세포 치료제·신약 후보물질 다수 보유.",
            ],
        },
    }
    info = _DB.get(ticker)
    if info is None:
        info = {
            "title": f"{name} — 핵심 사업 개요",
            "overview": (
                f"{name}의 경쟁 우위 및 독점 기술은 실시간 수급 데이터로 역추적 중입니다. "
                "DART 전자공시(dart.fss.or.kr) 최신 사업보고서에서 IR 자료를 확인하세요."
            ),
            "moat": [
                f"{name} 핵심 경쟁력 — 수급 데이터 기반 세력 동향 실시간 추적 중.",
                "DART 전자공시에서 최신 IR 자료 확인 시 투자 판단에 도움이 됩니다.",
            ],
        }
    return info

# ─────────────────────────────────────────────────────────────────────────────
# 3. KRX 공휴일 조회 (open.krx.co.kr OTP API → 폴백 테이블)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _get_krx_holidays(year: int) -> tuple[dict[str, str], bool]:
    """
    KRX 휴장일 목록 조회.
    Returns (dates: dict[str "YYYY-MM-DD", str holiday_name], is_fallback: bool)
    is_fallback=True → open.krx.co.kr API 실패, 내장 테이블 사용 중
    """
    try:
        otp_resp = requests.get(
            "https://open.krx.co.kr/contents/COM/GenerateOTP.jspx",
            params={"bld": "MKD/01/0110/01100305/mkd01100305_01", "name": "form"},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://open.krx.co.kr/"},
            timeout=8,
        )
        otp = otp_resp.text.strip()
        if not otp or len(otp) < 10:
            raise ValueError("OTP 발급 실패")

        data_resp = requests.post(
            "https://open.krx.co.kr/contents/OPN/99/OPN99000001.jspx",
            data={
                "search_bas_yy": str(year),
                "gridTp": "KRX",
                "pagePath": "/contents/MKD/01/0110/01100305/MKD01100305.jsp",
                "code": otp,
            },
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://open.krx.co.kr/"},
            timeout=10,
        )
        items = data_resp.json().get("block1", [])
        if not items:
            raise ValueError("공휴일 데이터 없음")

        dates: dict[str, str] = {}
        for item in items:
            if "calnd_dd" not in item:
                continue
            date_str = datetime.strptime(item["calnd_dd"], "%Y%m%d").strftime("%Y-%m-%d")
            name = (
                item.get("calnd_dd_nm")
                or item.get("holdy_nm")
                or item.get("remark")
                or ""
            )
            dates[date_str] = name
        if not dates:
            raise ValueError("공휴일 파싱 실패")
        return dates, False
    except Exception:
        fallback = _KRX_HOLIDAYS_FALLBACK.get(year)
        if fallback is None:
            return {}, True
        return dict(fallback), True


# ─────────────────────────────────────────────────────────────────────────────
# 4. KRX 전종목 로드 (FDR, 앱 시작 시 1회)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="KRX 전종목 리스트 로딩 중…")
def load_krx_tickers() -> pd.DataFrame:
    """FDR StockListing('KRX') → 2880+ 종목. 앱 시작 시 1회 캐시."""
    try:
        raw = fdr.StockListing("KRX")
        cols = ["Code", "Name", "Market"] + (["Marcap"] if "Marcap" in raw.columns else [])
        df = raw[cols].copy()
        df = df[df["Code"].str.match(r"^\d{6}$", na=False)].reset_index(drop=True)
        df["Code"] = df["Code"].str.zfill(6)
        df["_key"] = df["Name"].str.lower() + " " + df["Code"]
        return df
    except Exception:
        return pd.DataFrame(columns=["Code", "Name", "Market", "_key"])


@st.cache_data(ttl=3600, show_spinner=False)
def _get_marcap_lookup() -> dict[str, float]:
    """
    FDR StockListing Marcap(원) → {code: 시총_억원} 딕셔너리.
    tab 필터링용 — 탭 클릭 시 즉시 사용 (TTL 1시간).
    """
    try:
        raw = fdr.StockListing("KRX")
        if "Marcap" not in raw.columns:
            return {}
        df = raw[["Code", "Marcap"]].copy()
        df = df[df["Code"].str.match(r"^\d{6}$", na=False)].copy()
        df["Code"] = df["Code"].str.zfill(6)
        df["cap_억"] = pd.to_numeric(df["Marcap"], errors="coerce").fillna(0) / 1e8
        return dict(zip(df["Code"], df["cap_억"]))
    except Exception:
        return {}


def search_ticker(query: str, tdf: pd.DataFrame) -> list[dict]:
    """종목명/코드 퍼지 검색 → 최대 8건."""
    q = query.strip()
    if not q or tdf.empty:
        return []
    # 6자리 코드 완전 일치
    if re.match(r"^\d{4,6}$", q):
        code = q.zfill(6)
        exact = tdf[tdf["Code"] == code]
        if not exact.empty:
            r = exact.iloc[0]
            return [{"code": r["Code"], "name": r["Name"], "market": r["Market"]}]
    # 이름 포함
    hits = tdf[tdf["Name"].str.contains(q, case=False, na=False)].head(8)
    return [{"code": r["Code"], "name": r["Name"], "market": r["Market"]} for _, r in hits.iterrows()]


# ─────────────────────────────────────────────────────────────────────────────
# 4. 실시간 현재가 (Naver 모바일 JSON API)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """Naver m.stock API → 현재가·등락률·시가총액."""
    try:
        url  = f"https://m.stock.naver.com/api/stock/{ticker}/basic"
        resp = requests.get(url, headers=NAVER_HDRS, timeout=8)
        d    = resp.json()
        cur  = int(str(d.get("closePrice", "0")).replace(",", "") or 0)
        chg  = float(d.get("fluctuationsRatio", 0))
        diff = str(d.get("compareToPreviousClosePrice", "0")).replace(",", "")
        cap_raw = d.get("marketValue", d.get("totalInfos", {}).get("marketValue", "0"))
        cap = float(str(cap_raw).replace(",", "") or 0) / 1e8
        return {
            "현재가": cur, "등락률": chg, "전일대비": int(diff or 0),
            "시가총액": round(cap, 1), "이름": d.get("stockName", ""),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 5. OHLCV (FinanceDataReader)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_ohlcv(ticker: str, days: int = 90) -> pd.DataFrame:
    """FDR → 최근 N 거래일 OHLCV. 한국 6자리 코드 직접 인식."""
    end   = datetime.now()
    start = end - timedelta(days=days + 30)
    try:
        df = fdr.DataReader(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
        )
        if df.empty or "Close" not in df.columns:
            return pd.DataFrame()
        return df.tail(days)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# 6. 수급 데이터 (Naver frgn.naver + 오버라이드)
# ─────────────────────────────────────────────────────────────────────────────
def _parse_int(val) -> int:
    if pd.isna(val):
        return 0
    try:
        return int(float(str(val).replace(",", "").replace("+", "")))
    except Exception:
        return 0


@st.cache_data(ttl=60, show_spinner=False)
def get_investor_flow(ticker: str) -> list[dict]:
    """
    Naver frgn.naver table[3] → 기관·외국인 순매매량 (가장 최근 확정 영업일 자동 수집).
    개인 = 零合 역산: -(기관+외국인)   [기타법인 ≈ 0 근사]
    기타법인은 별도 source 없을 시 역산 불가 → 0 표기.
    """
    # frgn.naver 파싱 — 가장 최근 확정 영업일 데이터 자동 수집
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    try:
        resp   = requests.get(url, headers=NAVER_HDRS, timeout=10)
        tables = pd.read_html(StringIO(resp.text), flavor="lxml")
        # table[3]: 날짜 | 종가 | 전일비 | 등락률 | 거래량 | 기관순매매 | 외국인순매매 | …
        if len(tables) <= 3:
            return []
        tbl = tables[3].copy()

        # MultiIndex → flat
        if isinstance(tbl.columns, pd.MultiIndex):
            tbl.columns = [
                "_".join(str(c) for c in col if "Unnamed" not in str(c)).strip("_")
                for col in tbl.columns
            ]
        cols = list(tbl.columns)

        # 날짜 컬럼
        date_col = next((c for c in cols if "날짜" in c), None)
        if not date_col:
            return []

        # 기관·외국인 컬럼
        inst_col = next((c for c in cols if "기관" in c and "매매" in c), None) or \
                   next((c for c in cols if "기관" in c), None)
        frgn_col = next((c for c in cols if "외국인" in c and "매매" in c), None) or \
                   next((c for c in cols if "외국인" in c and "보유" not in c and "율" not in c), None)

        rows: list[dict] = []
        for _, row in tbl.iterrows():
            dv = str(row[date_col]).strip()
            if not re.match(r"\d{4}\.\d{2}\.\d{2}", dv):
                continue
            inst = _parse_int(row[inst_col]) if inst_col else 0
            frgn = _parse_int(row[frgn_col]) if frgn_col else 0
            # 개인 역산 (零合: 기타법인 0 근사)
            indv = -(inst + frgn)
            rows.append({"날짜": dv, "기관": inst, "외국인": frgn, "개인": indv, "기타법인": 0})
            if len(rows) >= 5:
                break
        return rows
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 7. 펀더멘털 (frgn.naver 동일 HTML에서 파싱)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(ticker: str) -> dict:
    """
    frgn.naver 공통 사이드바 테이블에서 PER·PBR·목표주가·52주 파싱.
    table[5]=시총, table[7]=목표주가, table[8]=PER/PBR
    """
    url = f"https://finance.naver.com/item/frgn.naver?code={ticker}"
    try:
        resp   = requests.get(url, headers=NAVER_HDRS, timeout=10)
        tables = pd.read_html(StringIO(resp.text), flavor="lxml")
        out = {}

        def _str(tbl, row_kw, col=1):
            for _, row in tbl.iterrows():
                if row_kw in str(row.iloc[0]):
                    return str(row.iloc[col]).strip()
            return ""

        # table[5]: 시가총액
        if len(tables) > 5:
            t5 = tables[5]
            raw_cap = _str(t5, "시가총액")
            m = re.search(r"([\d,]+)\s*억", raw_cap)
            if m:
                out["시가총액(억)"] = int(m.group(1).replace(",", ""))

        # table[7]: 투자의견·목표주가·52주
        if len(tables) > 7:
            t7 = tables[7]
            raw_tp = _str(t7, "목표주가")
            m2 = re.search(r"l\s*([\d,]+)", raw_tp)
            if m2:
                out["목표주가"] = int(m2.group(1).replace(",", ""))
            raw_52 = _str(t7, "52주")
            m3 = re.findall(r"[\d,]+", raw_52)
            if len(m3) >= 2:
                out["52주최고"] = int(m3[0].replace(",", ""))
                out["52주최저"] = int(m3[1].replace(",", ""))

        # table[8]: PER·EPS·PBR·BPS
        if len(tables) > 8:
            t8 = tables[8]
            raw_per = _str(t8, "PER")
            m4 = re.search(r"([\d.]+)배", raw_per)
            if m4 and m4.group(1) not in ("N/A", "0"):
                out["PER"] = float(m4.group(1))
            raw_pbr = _str(t8, "PBR")
            m5 = re.search(r"([\d.]+)배", raw_pbr)
            if m5 and m5.group(1) not in ("N/A", "0"):
                out["PBR"] = float(m5.group(1))

        # ROE: main.naver 주요재무정보 table[4] — "ROE(지배주주)" 행, 최근 연간 확정치(col 3)
        try:
            main_resp = requests.get(
                f"https://finance.naver.com/item/main.naver?code={ticker}",
                headers=NAVER_HDRS, timeout=8,
            )
            main_tables = pd.read_html(StringIO(main_resp.text), flavor="lxml")
            if len(main_tables) > 4:
                mt = main_tables[4].copy()
                # MultiIndex → 마지막 레벨만 사용
                if isinstance(mt.columns, pd.MultiIndex):
                    mt.columns = [str(c[-1]) if "Unnamed" not in str(c[-1]) else str(c[0]) for c in mt.columns]
                for _, rrow in mt.iterrows():
                    if "ROE" in str(rrow.iloc[0]):
                        # col index 3 = 최근 확정 연간 (2025.12)
                        for ci in [3, 2, 1]:
                            raw_roe = rrow.iloc[ci] if ci < len(rrow) else None
                            if raw_roe is not None and str(raw_roe) not in ("nan", "NaN", "-", ""):
                                m_roe = re.search(r"(-?[\d.]+)", str(raw_roe))
                                if m_roe:
                                    out["ROE"] = float(m_roe.group(1))
                                    break
                        break
        except Exception:
            pass

        return out
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# 8. 뉴스 — 3단계 폴백 수집 엔진 (절대 실패 없음)
# ─────────────────────────────────────────────────────────────────────────────
def _news_parse_bs(html: str, seen: set[str]) -> list[dict]:
    """BeautifulSoup 파싱 — CSS 셀렉터 우선순위 순회."""
    items: list[dict] = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for sel in [
            ".news_dl dt a", ".articleSubject a", ".news_list li a",
            "dl dt a", ".type01 li dt a", "li.newline a", "a[href*='news']",
        ]:
            elems = soup.select(sel)
            if elems:
                for el in elems[:20]:
                    title = el.get_text(strip=True)
                    href  = el.get("href", "")
                    if title and len(title) > 5 and title not in seen:
                        if href and not href.startswith("http"):
                            href = "https://finance.naver.com" + href
                        seen.add(title)
                        items.append({"title": title, "url": href, "date": ""})
                if items:
                    break
    except Exception:
        pass
    return items


def _news_parse_rss(html: str, seen: set[str]) -> list[dict]:
    """RSS/XML 파싱 — <title> 태그 정규식 추출."""
    items: list[dict] = []
    try:
        # <item> 블록 추출
        item_blocks = re.findall(r"<item>(.*?)</item>", html, re.DOTALL)
        for block in item_blocks[:20]:
            t_m  = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", block)
            if not t_m:
                t_m = re.search(r"<title>(.*?)</title>", block)
            l_m  = re.search(r"<link>(.*?)</link>",  block)
            d_m  = re.search(r"<pubDate>(.*?)</pubDate>", block)
            title = t_m.group(1).strip() if t_m else ""
            href  = l_m.group(1).strip() if l_m else ""
            date  = d_m.group(1).strip()[:16] if d_m else ""
            if title and len(title) > 5 and title not in seen:
                seen.add(title)
                items.append({"title": title, "url": href, "date": date})
    except Exception:
        pass
    return items


def _news_parse_regex(html: str, seen: set[str]) -> list[dict]:
    """최후 수단 — <a> 태그 정규식 브루트포스 추출."""
    items: list[dict] = []
    try:
        anchors = re.findall(
            r'<a[^>]+href="([^"]*(?:news|article|view)[^"]*)"[^>]*>(.*?)</a>',
            html, re.DOTALL,
        )
        for href, raw in anchors[:30]:
            title = re.sub(r"<[^>]+>", "", raw).strip()
            if title and len(title) > 8 and title not in seen:
                if not href.startswith("http"):
                    href = "https://finance.naver.com" + href
                seen.add(title)
                items.append({"title": title, "url": href, "date": ""})
    except Exception:
        pass
    return items


def _fetch_with_fallback(url: str, seen: set[str],
                         hdrs: dict | None = None,
                         max_retry: int = 3) -> list[dict]:
    """단일 URL 수집 — BS → RSS → regex 3단계 폴백, 최대 max_retry회."""
    used_hdrs = hdrs or NAVER_HDRS
    for attempt in range(max_retry):
        try:
            resp = requests.get(url, headers=used_hdrs, timeout=8)
            if resp.status_code != 200:
                continue
            html = resp.text
            # ① BeautifulSoup
            items = _news_parse_bs(html, seen)
            if items:
                return items
            # ② RSS/XML
            items = _news_parse_rss(html, seen)
            if items:
                return items
            # ③ 정규식 브루트포스
            items = _news_parse_regex(html, seen)
            if items:
                return items
        except Exception:
            pass
    return []


def _fetch_mobile_naver(query: str, seen: set[str]) -> list[dict]:
    """모바일 Naver 뉴스 검색 JSON API — 독립 폴백 채널."""
    items: list[dict] = []
    enc_q = requests.utils.quote(query)
    urls = [
        f"https://m.search.naver.com/search.naver?where=m_news&query={enc_q}",
        f"https://search.naver.com/search.naver?where=news&query={enc_q}&sort=1",
    ]
    mob_hdrs = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://m.naver.com/",
    }
    for url in urls:
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=mob_hdrs, timeout=8)
                if resp.status_code != 200:
                    continue
                html = resp.text
                # JSON 응답 시도
                try:
                    data = __import__("json").loads(html)
                    for art in data.get("articles", data.get("items", [])):
                        title = art.get("title", "")
                        href  = art.get("originallink", art.get("link", ""))
                        if title and title not in seen:
                            seen.add(title)
                            items.append({"title": title, "url": href, "date": ""})
                    if items:
                        return items
                except Exception:
                    pass
                # HTML 응답: BS 우선, regex 폴백
                parsed = _news_parse_bs(html, seen)
                if not parsed:
                    parsed = _news_parse_regex(html, seen)
                items.extend(parsed)
                if items:
                    return items
            except Exception:
                pass
    return items


@st.cache_data(ttl=300, show_spinner=False)
def get_news(ticker: str, name: str, aliases: tuple[str, ...] = ()) -> dict:
    """검색 기반 종목 전용 뉴스 수집 엔진 (V8.0 Flexible Match).

    반환값: {"items": [...], "status": "ok"|"empty"|"error", "fetch_count": n}
    ┌──────────┬────────────────────────────────────────────────────────────┐
    │ "ok"     │ 수집 성공 + Flexible Match 통과 뉴스 1건 이상             │
    │ "empty"  │ 수집 성공 + 종목 전용 뉴스 0건 (시장 잡음으로 채우지 않음)│
    │ "error"  │ 모든 채널 네트워크 오류 — 재시도 필요                     │
    └──────────┴────────────────────────────────────────────────────────────┘
    Flexible Match: 한글 종목명 + 영문 alias + 종목코드 중 하나라도 포함 → 유효
    """
    enc          = requests.utils.quote
    seen:         set[str]   = set()
    raw:          list[dict] = []
    any_fetch_ok: bool       = False

    # ── 종목명 토큰화 ─────────────────────────────────────────────────────────
    _stopwords = {"주식회사", "(주)", "㈜", "홀딩스", "그룹", "코리아", "코퍼레이션", "인터내셔널"}
    name_clean = name
    for sw in _stopwords:
        name_clean = name_clean.replace(sw, "")
    name_tokens = [t.strip() for t in name_clean.split() if len(t.strip()) >= 2]

    # Flexible Match 토큰 풀: 한글 토큰 + 영문 alias
    all_tokens = name_tokens + [a for a in aliases if a and len(a) >= 2]

    def _is_stock_news(title: str) -> tuple[bool, str]:
        """(유효 여부, 매칭 토큰). 종목코드 또는 any(all_tokens) 포함 시 True."""
        if ticker in title:
            return True, ticker
        for tok in all_tokens:
            if tok in title:
                return True, tok
        return False, ""

    # ── 검색 쿼리 (한글 종목명 + 영문 alias 쿼리 병행) ───────────────────────
    search_queries: list[str] = [
        name, name + " 실적", name + " 수주",
        name + " 계약", name + " 영업이익",
        name + " 호재", name + " 상장", name + " 급등",
    ]
    for alias in list(aliases)[:2]:         # alias 쿼리 최대 2개 (과부하 방지)
        search_queries += [alias, alias + " 실적"]

    search_hdrs = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://search.naver.com/",
    }

    # ── 채널 1: Naver 뉴스 검색 (최신순 sort=1) ──────────────────────────────
    for q in search_queries:
        url = f"https://search.naver.com/search.naver?where=news&query={enc(q)}&sort=1&pd=1"
        try:
            resp = requests.get(url, headers=search_hdrs, timeout=8)
            if resp.status_code == 200:
                any_fetch_ok = True
                soup = BeautifulSoup(resp.text, "lxml")
                for el in soup.select("a.news_tit, a.title, .news_area a[href*='news']"):
                    title = el.get_text(strip=True)
                    href  = el.get("href", "")
                    if title and len(title) > 6 and title not in seen:
                        seen.add(title)
                        raw.append({"title": title, "url": href, "date": ""})
        except Exception:
            pass

    # ── 채널 2: Naver Finance 뉴스 검색 ───────────────────────────────────────
    for q in [name, name + " 실적", name + " 수주"]:
        url = f"https://finance.naver.com/news/news_search.naver?q={enc(q)}&pd=1&sm=tab_jum"
        items = _fetch_with_fallback(url, seen)
        if items:
            any_fetch_ok = True
        raw += items

    # ── 채널 3: Naver Finance 종목코드 직접 뉴스 ─────────────────────────────
    url_code = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
    code_items = _fetch_with_fallback(url_code, seen)
    if code_items:
        any_fetch_ok = True
    raw += code_items

    # ── Flexible Match Filter ─────────────────────────────────────────────────
    filtered: list[dict] = []
    dropped:  list[str]  = []
    for n in raw:
        ok, matched = _is_stock_news(n["title"])
        if ok:
            filtered.append(n)
        else:
            dropped.append(n["title"][:70])

    # ── 디버깅 로그 — 사장님 필터 탈락 원인 확인용 ───────────────────────────
    alias_str = ", ".join(aliases) if aliases else "없음"
    print(f"\n[SOOMBI NEWS] {name}({ticker}) | aliases=[{alias_str}]")
    print(f"  매칭 토큰: {all_tokens}")
    print(f"  수집 {len(raw)}건 → Flexible Match 통과 {len(filtered)}건 (탈락 {len(dropped)}건)")
    for i, n in enumerate(filtered[:20], 1):
        print(f"  ✅ [{i:02d}] {n['title'][:70]}")
    if dropped:
        print(f"  ── 탈락 뉴스 (필터 미통과, 상위 {min(len(dropped),15)}건) ──")
        for t in dropped[:15]:
            print(f"  ❌ {t}")
    if not any_fetch_ok:
        print(f"  ⚠ 모든 수집 채널 실패 — Network Error")

    # ── 상태 판정 ─────────────────────────────────────────────────────────────
    if not any_fetch_ok:
        status = "error"
    elif filtered:
        status = "ok"
    else:
        status = "empty"

    return {"items": filtered[:40], "status": status, "fetch_count": len(raw)}


def classify_news(title: str) -> str:
    """뉴스 제목 → 호재(T1·T2)/악재/중립 — Tier 등급제 적용."""
    t = title
    # 소음 필터 → 무조건 중립
    if any(kw in t for kw in _NOISE_KW):
        return "중립"
    # Tier 1 확정 호재
    if any(kw in t for kw in _TIER1_KW):
        return "호재"
    # Tier 2 기대감 호재
    if any(kw in t for kw in _TIER2_KW):
        return "호재"
    # 악재·호재 키워드 비교
    g = sum(1 for kw in _GOOD_KW if kw in t)
    b = sum(1 for kw in _BAD_KW  if kw in t)
    if b > g:  return "악재"
    if g > 0:  return "호재"
    return "중립"


def _news_tier(title: str) -> int:
    """뉴스 제목 → Tier 번호 반환 (1/2/3). 3 = 소음·중립."""
    if any(kw in title for kw in _NOISE_KW):
        return 3
    if any(kw in title for kw in _TIER1_KW):
        return 1
    if any(kw in title for kw in _TIER2_KW):
        return 2
    b = sum(1 for kw in _BAD_KW if kw in title)
    g = sum(1 for kw in _GOOD_KW if kw in title)
    if b > g: return 3   # 악재는 별도 처리, 여기선 소음으로 처리
    if g > 0: return 2
    return 3


# ─────────────────────────────────────────────────────────────────────────────
# 9. 기술 분석 (RSI + 눌림목 점수)   ← GOLDEN RULE 유지
# ─────────────────────────────────────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta).clip(lower=0).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1) if not rsi.empty else 50.0


def calc_pullback_score(close: pd.Series, vol: pd.Series) -> dict:
    """눌림목 매수 타이밍 점수 (30점 만점)."""
    empty = {"score": 0, "signal": "데이터 부족", "rsi": 50.0,
             "ma5": 0, "ma20": 0, "ma60": 0}
    if len(close) < 22:
        return empty

    ma5  = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    n60  = min(60, len(close))
    ma60 = close.rolling(n60).mean()
    rsi  = calc_rsi(close)
    cur  = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    score = 0

    # 정배열 (MA5 > MA20 > MA60)
    if float(ma5.iloc[-1]) > float(ma20.iloc[-1]) > float(ma60.iloc[-1]):
        score += 8
    elif float(ma5.iloc[-1]) > float(ma20.iloc[-1]):
        score += 4

    # 눌림목: MA5 근처 터치 후 당일 반등
    ma5_prev = float(ma5.iloc[-2]) if len(ma5) >= 2 else float(ma5.iloc[-1])
    if cur > prev and prev <= ma5_prev * 1.02:
        score += 10

    # RSI 구간
    if   30 <= rsi <= 50: score += 8
    elif 50 <  rsi <= 65: score += 5
    elif rsi < 30:        score += 3

    # 거래량 폭발
    if len(vol) >= 10 and not vol.empty:
        avg10 = float(vol.tail(10).mean())
        if avg10 > 0 and float(vol.iloc[-1]) / avg10 >= 2.0:
            score += 4

    score = min(score, 25)  # V5.0: 차트 25점 만점
    if   score >= 20: sig = "🔴 즉시 매수 (HIGH)"
    elif score >= 13: sig = "🟡 매수 준비 (MID)"
    elif score >= 7:  sig = "⚪ 관망 (LOW)"
    else:             sig = "❌ 진입 불가"

    return {
        "score": score, "signal": sig, "rsi": rsi,
        "ma5":  round(float(ma5.iloc[-1])),
        "ma20": round(float(ma20.iloc[-1])),
        "ma60": round(float(ma60.iloc[-1])),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 10. 42대 필살기 점수 계산
# ─────────────────────────────────────────────────────────────────────────────
def score_investor(inv: list[dict]) -> dict:
    """수급 점수 40점 — 42대 필살기 수급 역추적 엔진 V7.0.
    기관 Streak·연기금 추정·외국인 누적·기관 가속도·쌍끌이·개인 역매수 6개 시그널 통합.
    ※ 소유자 승인 수정 가능 함수 (2026-05-08).
    """
    if not inv:
        return {"score": 0, "detail": "수급 데이터 없음",
                "inst_5d": 0, "frgn_5d": 0, "streak": 0}

    inst_vals = [r.get("기관", 0)   for r in inv]
    frgn_vals = [r.get("외국인", 0) for r in inv]
    # 개인: 데이터 있으면 직접 사용, 없으면 역산
    indv_vals = [r.get("개인", -(r.get("기관", 0) + r.get("외국인", 0))) for r in inv]
    inst_5d   = sum(inst_vals)
    frgn_5d   = sum(frgn_vals)
    streak    = sum(1 for v in inst_vals if v > 0)

    score   = 0
    details: list[str] = []

    # ① 기관 연속 매수 Streak (최대 15점 — 5일 연속 만점)
    score += [0, 2, 6, 10, 13, 15][min(streak, 5)]

    # ② 외국인 누적 순매수 (최대 10점)
    if   frgn_5d > 500_000:  score += 10
    elif frgn_5d > 100_000:  score += 7
    elif frgn_5d > 0:        score += 3
    elif frgn_5d < -500_000: score -= 5

    # ③ 기관 총량 보정 (최대 5점)
    if   inst_5d > 1_000_000: score += 5
    elif inst_5d > 300_000:   score += 3
    elif inst_5d > 0:         score += 1

    # ④ 연기금·패시브 추정: 5일 전일 양수 + 누적 100만주 이상 → 지수편입·연기금 가능성
    if streak == 5 and inst_5d > 1_000_000:
        score += 5
        details.append("🏦 연기금·패시브 매집 추정 (+5)")

    # ⑤ 기관 가속 매집: 오늘 > 어제 > 0 (세력 가속 구조)
    if len(inst_vals) >= 2 and inst_vals[0] > 0 and inst_vals[1] > 0 and inst_vals[0] > inst_vals[1]:
        score += 3
        details.append(f"⚡ 기관 가속 매집 ({inst_vals[0]:+,} > {inst_vals[1]:+,}, +3)")

    # ⑥ 🔥 [핵심 필살기] 당일 쌍끌이 — 소유자 승인 보너스 로직 (2026-05-08)
    if inst_vals[0] > 0 and frgn_vals[0] > 0:
        score += 15
        details.append("🔥당일 쌍끌이 대량 매집 (+15점)🔥")

        # ⑦ 세력 쌍끌이 + 개인 매도 = 완벽 수급 구조 (추가 +2점)
        if indv_vals[0] < 0:
            score += 2
            details.append("🎯 개인 매도·세력 수취 완벽 구조 (+2)")

    score = max(0, min(score, 40))  # 40점 만점 캡

    if streak >= 2 and not any("연속" in d for d in details):
        details.append(f"기관 {streak}일 연속 매수")
    if frgn_5d > 100_000 and not any("외국인" in d for d in details):
        details.append(f"외국인 순매수 {frgn_5d:+,}")
    if not details:
        details.append(f"기관 {inst_5d:+,} / 외국인 {frgn_5d:+,}")

    return {"score": score, "detail": " | ".join(details),
            "inst_5d": inst_5d, "frgn_5d": frgn_5d, "streak": streak}


def score_fundamentals(fund: dict) -> dict:
    """가치/재무 점수 20점 — ROE 수익성 + PBR 저평가 + PER 업종비교."""
    if not fund:
        return {"score": 0, "detail": "재무 데이터 없음"}

    score   = 0
    details = []

    roe = fund.get("ROE")
    pbr = fund.get("PBR")
    per = fund.get("PER")

    # ROE 수익성 (최대 8점)
    if roe is not None:
        if   roe >= 15: score += 8; details.append(f"ROE {roe:.1f}% ★우량")
        elif roe >= 10: score += 5; details.append(f"ROE {roe:.1f}%")
        elif roe >= 5:  score += 3; details.append(f"ROE {roe:.1f}%")
        elif roe < 0:   score -= 3; details.append(f"ROE {roe:.1f}% (적자)")

    # PBR 저평가 (최대 7점)
    if pbr is not None and pbr > 0:
        if   pbr <= 0.8: score += 7; details.append(f"PBR {pbr:.2f} 극저평가")
        elif pbr <= 1.0: score += 5; details.append(f"PBR {pbr:.2f} 저평가")
        elif pbr <= 1.5: score += 3; details.append(f"PBR {pbr:.2f} 적정")

    # PER 상대 저평가 (최대 5점)
    if per is not None and per > 0:
        if   per <= 10: score += 5; details.append(f"PER {per:.1f} 저평가")
        elif per <= 15: score += 3; details.append(f"PER {per:.1f}")
        elif per <= 25: score += 1; details.append(f"PER {per:.1f} 적정")

    score  = max(0, min(score, 20))
    detail = " | ".join(details) if details else "재무 데이터 수집 중"
    return {"score": score, "detail": detail}


def _extract_news_reason(title: str) -> str:
    """제목에서 수치/사실을 NLP 추출 → '이유: X% 수치 확인' 팩트 근거 문장 생성."""
    parts: list[str] = []
    # 조원 규모
    trln = re.findall(r"(\d+\.?\d*)조", title)
    if trln:
        parts.append(f"{trln[0]}조원 규모")
    # 억원 규모
    amts = re.findall(r"(\d[\d,]*)억", title)
    if amts:
        parts.append(f"{amts[0]}억원 규모 확인")
    # 백분율 수치
    pcts = re.findall(r"(\d+\.?\d*)%", title)
    if pcts:
        parts.append(f"{pcts[0]}% 수치 확인")
    # 배수(배) 성장
    times = re.findall(r"(\d+\.?\d*)배", title)
    if times and not parts:
        parts.append(f"{times[0]}배 성장 수치")
    # 키워드 기반 문맥 근거 (수치 없을 때)
    if not parts:
        _ctx = {
            "사상 최대": "역대 최대 실적 확인",
            "역대 최대": "역대 최대 실적 확인",
            "어닝 서프라이즈": "컨센서스 상회 실적 서프라이즈",
            "흑자전환": "적자→흑자 전환 확정",
            "흑자 전환": "적자→흑자 전환 확정",
            "독점": "독점 공급·계약 체결 확정",
            "세계 최초": "세계 최초 기술·제품 확정",
            "FDA 승인": "미국 FDA 공식 승인 확인",
            "임상 성공": "임상시험 성공 공식 확인",
            "양산 성공": "양산 체계 구축 확인",
            "상한가": "당일 가격제한폭 상한 도달",
            "목표주가 상향": "증권사 목표주가 상향 조정",
            "목표가 상향": "증권사 목표주가 상향 조정",
            "MOU": "MOU·업무협약 공식 체결",
            "수주 성공": "신규 수주 계약 체결 확인",
            "계약 체결": "계약 체결 사실 확인",
            "특허": "핵심 특허 등록·확보 확인",
            "허가": "당국 공식 허가 취득 확인",
        }
        for kw, reason in _ctx.items():
            if kw in title:
                parts.append(reason)
                break
    return ("이유: " + " · ".join(parts)) if parts else ""


def _is_dart_news(title: str) -> bool:
    """제목에 전자공시·DART 키워드가 있으면 True (팩트 신뢰도 최고 등급)."""
    return any(kw in title for kw in _DART_KW)


def score_news(news: list[dict]) -> dict:
    """뉴스 팩트체크 점수 30점 — V8.0 Tiered Fact-Check 등급제.

    등급 체계 (사장님 42대 필살기 함해물 원칙 100% 준수):
    ┌─────────┬─────┬──────────────────────────────────────────┐
    │ Tier 0  │ 30점│ M&A·합병·공개매수 등 시장구조 변경급     │
    │ Tier 1  │ 30점│ 실적 서프라이즈·대형수주·독점기술 확정   │
    │ Tier 2  │ 20점│ 목표가 상향·파트너십·중소 공급계약        │
    │ Neutral │ 10점│ PR·채용·IR·수상 등 주가 영향 미미         │
    │ Bad/None│  0점│ 악재 우세 또는 종목 전용 호재 0건        │
    └─────────┴─────┴──────────────────────────────────────────┘
    news 리스트는 get_news() Hard Filter가 적용된 종목 전용 뉴스여야 함.
    """
    empty = {
        "score": 0, "score_label": "0점 (호재 없음)",
        "good": [], "bad": [], "neutral": [],
        "impact_hits": [], "tier0_news": [], "tier1_news": [],
        "tier2_news": [], "neutral_news": [],
        "velocity": 0, "velocity_label": "뉴스 없음",
    }
    if not news:
        return empty

    tier0_news:   list[dict] = []
    tier1_news:   list[dict] = []
    tier2_news:   list[dict] = []
    neutral_news: list[dict] = []   # 10점 — PR·채용·IR
    bad_news:     list[dict] = []
    noise_list:   list[dict] = []   # 0점 — 순수 시황 잡음
    impact_hits:  list[str]  = []

    for n in news:
        t      = n["title"]
        reason = _extract_news_reason(t)
        is_dart = _is_dart_news(t)
        item   = {**n, "reason": reason, "dart": is_dart}

        # ① 순수 시황 잡음 — 점수 계산에서 완전 배제
        if any(kw in t for kw in _NOISE_KW):
            noise_list.append(n)
            continue

        # ② Tier 0 — 시장 구조 변경급 (M&A·공개매수·이전상장)
        t0_hits = [kw for kw in _TIER0_KW if kw in t]
        if t0_hits:
            tier0_news.append(item)
            for kw in t0_hits:
                if kw not in impact_hits:
                    impact_hits.append(kw)
            continue

        # ③ Negative Override 선탐지 — 부정 핵심 키워드가 있으면 Tier1/Tier2 승격 즉시 차단
        _neg_hits = [kw for kw in _HARD_NEG_KW if kw in t]
        _hard_neg  = len(_neg_hits) > 0

        # ④ Tier 1 — 확정 팩트 (실적 서프라이즈·대형 수주·독점 기술)
        t1_hits = [kw for kw in _TIER1_KW if kw in t]
        if t1_hits:
            if _hard_neg:
                # Negative Override 발동: 긍정 키워드 무효화 → 즉시 악재 강등
                override_reason = (
                    f"⚠ Negative Override: '{_neg_hits[0]}' 감지 "
                    f"→ Tier1 승격 차단·악재 강등"
                )
                bad_news.append({**item, "reason": override_reason})
            else:
                tier1_news.append(item)
                for kw in t1_hits:
                    if kw not in impact_hits:
                        impact_hits.append(kw)
            continue

        # ⑤ 악재 감지 (긍정 신호보다 부정이 우세할 때만 악재 분류)
        b_score = sum(1 for kw in _BAD_KW if kw in t)
        g_score = (sum(1 for kw in _GOOD_KW if kw in t)
                   + sum(1 for kw in _TIER2_KW if kw in t))
        if b_score > 0 and b_score >= g_score:
            bad_news.append(item)
            continue

        # ⑥ Tier 2 — 긍정 기대감 (목표가 상향·파트너십·중소 계약)
        if any(kw in t for kw in _TIER2_KW) or g_score > 0:
            if _hard_neg:
                # Negative Override 발동: Tier2 승격 차단 → 악재 강등
                override_reason = (
                    f"⚠ Negative Override: '{_neg_hits[0]}' 감지 "
                    f"→ Tier2 승격 차단·악재 강등"
                )
                bad_news.append({**item, "reason": override_reason})
            else:
                tier2_news.append(item)
            continue

        # ⑥ Neutral (10점) — PR·채용·IR 등 주가 영향 미미 기업 활동
        if any(kw in t for kw in _NEUTRAL_ARTICLE_KW):
            neutral_news.append({
                **item,
                "reason": "일반 기업 활동 — 주가 영향 미미 (IR·PR·인사·수상 등)",
            })
            continue

    # ── 점수 산출 (사장님 팩트체크 등급표 100% 준수) ──────────────────────────
    if tier0_news:
        score = 30
        score_label = "30점 ★★ Tier 0 — 시장구조 변경급 (M&A·합병·공개매수)"
    elif tier1_news:
        score = 30
        score_label = "30점 ★★ Tier 1 — 확정 팩트 (실적·수주·독점기술)"
    elif tier2_news:
        score = 20
        # 악재가 Tier2 건수 이상이면 0점 (냉정한 0점 원칙)
        if len(bad_news) >= len(tier2_news):
            score = 0
            score_label = "0점 — 악재 우세로 호재 상쇄"
        elif bad_news:
            score = max(10, 20 - len(bad_news) * 5)
            score_label = f"{score}점 Tier 2 — 기대감 호재 (악재 {len(bad_news)}건 감점)"
        else:
            score_label = "20점 ★ Tier 2 — 성장 가시성 확보 (목표가·파트너십·계약)"
    elif neutral_news and not bad_news:
        score = 10
        score_label = "10점 Neutral — PR·IR·채용 기업 활동 (주가 영향 미미)"
    elif news and not bad_news:
        # Zero-Point 방어: 종목 관련 뉴스 ≥1건이지만 Tier 키워드 미해당 → 악재 없음 확인 후 10점 보호
        # 0점은 오직 ① 종목 관련 뉴스 0건 또는 ② 명백한 악재 우세 시에만 적용
        score = 10
        score_label = "10점 ▶ 기본 중립 호재 — 종목 뉴스 수집됨 (Tier 키워드 미해당, 악재 없음)"
    else:
        score = 0
        score_label = "0점 — 종목 전용 호재 없음 또는 악재 우세"

    # ── 뉴스 속도(Sentiment Velocity) 산출 ──────────────────────────────────
    positive_cnt = len(tier0_news) + len(tier1_news) + len(tier2_news)
    if   positive_cnt >= 6: velocity = 2; vel_label = "🚀 뉴스 랠리 — 호재 집중 살포 (세력 주가 부양 패턴)"
    elif positive_cnt >= 3: velocity = 1; vel_label = "📈 호재 집중 — 기대감 형성 구간"
    elif positive_cnt >= 1: velocity = 0; vel_label = "📰 단발성 호재 — 모멘텀 지속 확인 필요"
    else:                   velocity = 0; vel_label = "— 종목 전용 호재 뉴스 없음"

    score    = min(score, 30)   # Hard Cap: 뉴스 최대 30점 전역 보장
    good_all = tier0_news + tier1_news + tier2_news
    return {
        "score":        score,
        "score_label":  score_label,
        "good":         good_all[:5],
        "bad":          bad_news[:3],
        "neutral":      noise_list,
        "neutral_news": neutral_news[:3],
        "impact_hits":  impact_hits,
        "tier0_news":   tier0_news[:3],
        "tier1_news":   tier1_news[:5],
        "tier2_news":   tier2_news[:5],
        "velocity":     velocity,
        "velocity_label": vel_label,
    }


def score_risk_squeeze(price_data: dict, inv_data: list[dict], pb: dict) -> dict:
    """V7.0 리스크/숏스퀴즈 점수 10점 — 공매도역발상·신용잔고·프로그램매매."""
    score:   int       = 0
    signals: list[str] = []

    chg_rate = float((price_data or {}).get("등락률", 0))
    rsi      = pb.get("rsi", 50.0)
    ma5      = pb.get("ma5",  0)
    ma20     = pb.get("ma20", 0)

    # ── ① 숏커버링 시그널 ──────────────────────────────────────────────────────
    # 가격 급등 + RSI 과매도권 탈출 → 대차잔고 감소 대용 시그널
    if chg_rate >= 3.0 and rsi < 45:
        score += 5
        signals.append(f"⚡ 숏커버링 강력 시그널 (+{chg_rate:.1f}%, RSI {rsi:.0f})")
    elif chg_rate >= 1.5 and rsi < 50:
        score += 3
        signals.append(f"🟡 숏커버링 초기 신호 (+{chg_rate:.1f}%, RSI {rsi:.0f})")

    # ── ② 숏스퀴즈 최적 구조 ───────────────────────────────────────────────────
    # 당일 기관+외국인 쌍끌이 + 개인 매도 = 세력 수취 + 숏스퀴즈 세팅
    if inv_data:
        inst_d = inv_data[0].get("기관",   0)
        frgn_d = inv_data[0].get("외국인", 0)
        indv_d = inv_data[0].get("개인",   0)
        if inst_d > 0 and frgn_d > 0 and indv_d < 0:
            score += 5
            signals.append("🔴 숏스퀴즈 최적 구조 (세력 쌍끌이·개인 매도)")

    # ── ③ 신용잔고 위험 감점 ───────────────────────────────────────────────────
    # 3일 연속 개인 대량 순매수 + 기관 이탈 → 신용 반대매매 위험
    if inv_data and len(inv_data) >= 3:
        indv_3 = [r.get("개인",   0) for r in inv_data[:3]]
        inst_3 = [r.get("기관",   0) for r in inv_data[:3]]
        if all(v > 100_000 for v in indv_3) and all(v < 0 for v in inst_3):
            score -= 5
            signals.append("⚠ 신용잔고 위험 — 개인 연속 대량 매수 / 기관 3일 이탈")

    # ── ④ 장막판 프로그램 매수 추정 ────────────────────────────────────────────
    # 단기선(MA5) > 중기선(MA20) + 당일 상승 = 프로그램 매수 유입 추정
    if ma5 > 0 and ma20 > 0 and ma5 > ma20 and chg_rate > 0:
        score += 2
        signals.append("📈 단기선 우위·상승 = 프로그램 매수 유입 추정 (+2)")

    score  = max(0, min(score, 10))
    detail = " | ".join(signals) if signals else "리스크 중립 — 이상 신호 없음"
    return {"score": score, "signals": signals, "detail": detail}


def calc_tomorrow_prob(result: dict) -> tuple[int, str]:
    """내일 상승 확률(%) + 타점 레이블 산출 — V7.0 Quantum Vanguard."""
    total = result.get("total", 0)
    ns    = result.get("news_score",  {})
    iv    = result.get("inv_score",   {})
    rs    = result.get("risk_score",  {"score": 0})

    # ── 전설적 타점: Tier 1 뉴스 + 쌍끌이 + 숏스퀴즈 동시 포착 ────────────────
    legendary = (
        bool(ns.get("tier1_news")) and
        "쌍끌이" in iv.get("detail", "") and
        rs.get("score", 0) >= 8
    )
    if legendary:
        return 98, "전설적 타점 — Tier1 뉴스·쌍끌이·숏스퀴즈 동시 포착"

    # ── 점수 기반 확률 산출 ─────────────────────────────────────────────────────
    if   total >= 80: prob = 85 + min(int((total - 80) * 1.3), 12)
    elif total >= 65: prob = 68 + int((total - 65) * 1.1)
    elif total >= 45: prob = 45 + int((total - 45) * 1.15)
    elif total >= 30: prob = 25 + int((total - 30) * 1.3)
    else:             prob = max(10, int(total * 0.8))

    if   total >= 80: tag = "최상위 매집 구간"
    elif total >= 65: tag = "고신뢰 진입 구간"
    elif total >= 45: tag = "분할 매수 구간"
    elif total >= 30: tag = "관망 구간"
    else:             tag = "진입 금지 구간"

    return int(min(prob, 97)), tag


def check_block_deal(ticker: str, inv: list[dict]) -> str | None:
    """블록딜·오버행 경보 반환 (None = 정상)."""
    if ticker in _BLOCK_ALERT:
        return _BLOCK_ALERT[ticker]
    if not inv:
        return None
    other_vals = [r.get("기타법인", 0) for r in inv]
    indv_vals  = [r["개인"]            for r in inv]
    if (min(other_vals) < -200_000 and max(indv_vals) > 200_000 and
            sum(r["기관"]   for r in inv) < 0 and
            sum(r["외국인"] for r in inv) < 0):
        return "기타법인 블록딜 대규모 매도 + 개인 전량 수취 구조 — 오버행·설거지 위험"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# V8.0 GOD MODE — 매크로 상관관계 · VWAP Smart Money · 숏스퀴즈 임계가 엔진
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_macro_data() -> dict:
    """실시간 매크로 지표: 환율(USDKRW=X)·금(GC=F)·유가(CL=F)·미국채10Y(^TNX)."""
    symbols = {"환율": "USDKRW=X", "금": "GC=F", "유가": "CL=F", "금리": "^TNX"}
    out: dict = {}
    for label, sym in symbols.items():
        try:
            df = yf.download(sym, period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            if df is not None and not df.empty and "Close" in df.columns:
                close = df["Close"].dropna()
                if len(close) >= 2:
                    cur  = float(close.iloc[-1])
                    prev = float(close.iloc[-2])
                    chg  = (cur - prev) / prev * 100 if prev else 0.0
                    out[label] = {"cur": round(cur, 4), "chg": round(chg, 3), "sym": sym}
        except Exception:
            pass
    return out


def _detect_sector(name: str) -> str:
    """종목명 기반 섹터 자동 추정."""
    _MAP = [
        (["조선", "해양", "선박", "드라이독", "잠수함"], "조선"),
        (["반도체", "HBM", "DRAM", "낸드", "파운드리", "하이닉스", "마이크론"], "반도체"),
        (["바이오", "제약", "의약", "헬스", "메디", "셀트리온", "삼바", "임상"], "바이오"),
        (["에너지", "정유", "석유", "가스", "LNG", "오일", "원유"], "에너지"),
        (["방산", "항공", "우주", "한화", "LIG", "현대로템", "무기"], "방산"),
        (["은행", "금융", "증권", "보험", "카드", "캐피탈", "저축"], "금융"),
        (["클라우드", "AI", "플랫폼", "소프트", "데이터", "네이버", "카카오", "IT"], "IT"),
        (["건설", "부동산", "건축", "토목", "아파트", "시공"], "건설"),
        (["자동차", "부품", "전기차", "배터리", "이차전지", "현대차", "기아"], "자동차"),
        (["통신", "KT", "SKT", "LG유플", "인터넷", "케이블"], "통신"),
    ]
    for keywords, sector in _MAP:
        if any(kw in name for kw in keywords):
            return sector
    return "일반"


# 섹터별 매크로 민감도 (Beta 추정치 — 학술 연구 및 시장 관찰 기반)
_MACRO_BETA: dict[str, dict[str, float]] = {
    "조선":   {"환율": +1.8, "유가": -0.4, "금리": -0.3},
    "반도체": {"환율": +1.2, "유가": -0.1, "금리": -0.6},
    "바이오": {"환율": -0.4, "유가":  0.0, "금리": -1.1},
    "에너지": {"환율": +0.5, "유가": +1.5, "금리": +0.2},
    "방산":   {"환율": +0.8, "유가": +0.2, "금리": -0.2},
    "금융":   {"환율": -0.3, "유가":  0.0, "금리": +1.2},
    "IT":     {"환율": +0.9, "유가": -0.1, "금리": -0.8},
    "건설":   {"환율": +0.3, "유가": +0.5, "금리": -1.5},
    "자동차": {"환율": +1.0, "유가": -0.6, "금리": -0.5},
    "통신":   {"환율": -0.1, "유가": -0.1, "금리": -0.5},
    "일반":   {"환율": +0.5, "유가": -0.1, "금리": -0.3},
}


def calc_macro_sensitivity(name: str, macro_data: dict) -> dict:
    """섹터 Beta × 매크로 등락률 → 종목 예상 영향도 산출 (달국금공 실시간 상관관계 엔진)."""
    sector = _detect_sector(name)
    betas  = _MACRO_BETA.get(sector, _MACRO_BETA["일반"])
    items: list[dict] = []
    sym_label = {"환율": "USD/KRW", "금": "Gold(oz)", "유가": "WTI(bbl)", "금리": "US10Y(%)"}
    unit      = {"환율": "원",       "금": "$",        "유가": "$",          "금리": "%"}
    for key, beta in betas.items():
        m = macro_data.get(key)
        if not m:
            continue
        chg    = m["chg"]
        cur    = m["cur"]
        impact = round(chg * beta, 2)
        col    = "#27ae60" if impact > 0.05 else "#e74c3c" if impact < -0.05 else "#6b7c93"
        arrow  = "▲ 수혜" if impact > 0.05 else "▼ 역풍" if impact < -0.05 else "— 중립"
        items.append({
            "label": key, "sym": sym_label.get(key, key),
            "cur": cur, "unit": unit.get(key, ""),
            "macro_chg": chg, "beta": beta,
            "impact": impact, "direction": arrow, "col": col,
        })
    return {"sector": sector, "items": items}


def calc_vwap_smart_money(ohlcv: pd.DataFrame) -> dict:
    """20일 VWAP·OBV·CMF 기반 Smart Money Flow 분석 (세력 심리 역추적)."""
    _e = {"vwap": 0, "gap_pct": 0.0, "obv_trend": "—", "cmf": 0.0,
          "verdict": "데이터 부족", "score": 0}
    try:
        if ohlcv.empty or len(ohlcv) < 10:
            return _e
        if not {"High", "Low", "Close", "Volume"}.issubset(set(ohlcv.columns)):
            return _e
        hi  = ohlcv["High"].astype(float)
        lo  = ohlcv["Low"].astype(float)
        cl  = ohlcv["Close"].astype(float)
        vol = ohlcv["Volume"].astype(float)

        # 20일 VWAP (Typical Price 가중)
        tp   = (hi + lo + cl) / 3
        w20  = vol.tail(20)
        vwap = float((tp.tail(20) * w20).sum() / w20.sum()) if w20.sum() > 0 else float(cl.iloc[-1])
        cur_px = float(cl.iloc[-1])
        gap    = (cur_px - vwap) / vwap * 100 if vwap > 0 else 0.0

        # OBV 5일 추세
        obv = [0.0]
        for i in range(1, len(cl)):
            if float(cl.iloc[i]) > float(cl.iloc[i - 1]):
                obv.append(obv[-1] + float(vol.iloc[i]))
            elif float(cl.iloc[i]) < float(cl.iloc[i - 1]):
                obv.append(obv[-1] - float(vol.iloc[i]))
            else:
                obv.append(obv[-1])
        obv_s     = pd.Series(obv)
        obv5      = float(obv_s.iloc[-1]) - float(obv_s.iloc[-6]) if len(obv_s) >= 6 else 0.0
        obv_trend = "Smart Money 순유입 ▲" if obv5 > 0 else "매도 우세 ▼"

        # CMF (Chaikin Money Flow 20일)
        hl  = (hi - lo).replace(0, 1)
        mfm = ((cl - lo) - (hi - cl)) / hl
        mfv = mfm * vol
        cmf = float(mfv.tail(20).sum() / vol.tail(20).sum()) if vol.tail(20).sum() > 0 else 0.0

        score = 0
        parts: list[str] = []
        if gap < -1.0:
            score += 4; parts.append(f"VWAP 하단 {gap:.1f}% — 세력 저점 매집 구간")
        elif gap > 3.0:
            score -= 2; parts.append(f"VWAP 상단 {gap:+.1f}% — 단기 과매수 주의")
        else:
            parts.append(f"VWAP 근접 {gap:+.1f}% — 균형 구간")
        if obv5 > 0:
            score += 3; parts.append("OBV 상승 — Smart Money 순유입 확인")
        else:
            parts.append("OBV 하락 — 매도세 우세")
        if cmf > 0.10:
            score += 3; parts.append(f"CMF {cmf:.3f} — 자금 집중 유입")
        elif cmf < -0.10:
            score -= 2; parts.append(f"CMF {cmf:.3f} — 자금 유출")

        score = max(0, min(score, 10))
        return {
            "vwap": round(vwap), "gap_pct": round(gap, 2),
            "obv_trend": obv_trend, "cmf": round(cmf, 3),
            "verdict": " | ".join(parts), "score": score,
        }
    except Exception:
        return _e


def calc_short_squeeze_trigger(price_data: dict, ohlcv: pd.DataFrame) -> dict:
    """숏스퀴즈 임계가 자동 산출 — ATR14·20일 저항선 기반 (배거차숏 엔진)."""
    _e = {"trigger": 0, "atr": 0, "resistance": 0,
          "gap_pct": 0.0, "zone": "데이터 부족", "verdict": "데이터 부족"}
    try:
        cur = int((price_data or {}).get("현재가", 0))
        if cur == 0 or ohlcv.empty or len(ohlcv) < 14:
            return _e
        hi = ohlcv["High"].astype(float)
        lo = ohlcv["Low"].astype(float)
        cl = ohlcv["Close"].astype(float)

        hl  = hi - lo
        hc  = (hi - cl.shift(1)).abs()
        lc  = (lo - cl.shift(1)).abs()
        tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        atr = float(tr.tail(14).mean())

        resistance = int(hi.tail(20).max())
        trigger    = int(resistance + atr * 0.5)
        gap_pct    = (trigger - cur) / cur * 100 if cur > 0 else 0.0

        if   gap_pct <= 1.0: zone = "🔴 임박 — 즉시 숏커버링 발동 가능"
        elif gap_pct <= 3.0: zone = "🟡 근접 — 1~3% 내 돌파 시 숏스퀴즈"
        elif gap_pct <= 7.0: zone = "⚪ 대기 — 임계가까지 여유 있음"
        else:                zone = "❌ 원거리 — 숏스퀴즈 가능성 낮음"

        verdict = f"임계가 {trigger:,}원 (현재 대비 +{gap_pct:.1f}%) — {zone}"
        return {"trigger": trigger, "atr": round(atr), "resistance": resistance,
                "gap_pct": round(gap_pct, 1), "zone": zone, "verdict": verdict}
    except Exception:
        return _e


def analyze_ticker(ticker: str, name: str, market: str) -> dict:
    """42대 필살기 전수조사 — 병렬 수집 후 종합 점수 산출."""
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")

    _news_aliases = _build_eng_aliases(name, ticker)   # Flexible Match 영문 약칭
    with ThreadPoolExecutor(max_workers=6) as ex:
        f_price = ex.submit(get_realtime_price, ticker)
        f_ohlcv = ex.submit(get_ohlcv, ticker, 90)
        f_inv   = ex.submit(get_investor_flow, ticker)
        f_fund  = ex.submit(get_fundamentals, ticker)
        f_news  = ex.submit(get_news, ticker, name, _news_aliases)
        f_macro = ex.submit(get_macro_data)

    # ── Zero-Error 방어: 각 Future 개별 try-except + 안전 기본값 ────────────
    try:
        price_data = f_price.result() or {}
    except Exception:
        price_data = {}
    try:
        ohlcv = f_ohlcv.result()
        if ohlcv is None or not isinstance(ohlcv, pd.DataFrame):
            ohlcv = pd.DataFrame()
    except Exception:
        ohlcv = pd.DataFrame()
    try:
        inv_data = f_inv.result() or []
    except Exception:
        inv_data = []
    try:
        fund_data = f_fund.result() or {}
    except Exception:
        fund_data = {}
    try:
        _news_raw     = f_news.result() or {}
        news_list     = _news_raw.get("items", [])
        news_status   = _news_raw.get("status", "error")   # "ok"|"empty"|"error"
    except Exception:
        news_list   = []
        news_status = "error"
    try:
        macro_data = f_macro.result() or {}
    except Exception:
        macro_data = {}

    # ── V8.0 God Mode 추가 분석 (매크로·VWAP·숏스퀴즈) ──────────────────────
    macro_sens   = calc_macro_sensitivity(name, macro_data)
    vwap_result  = calc_vwap_smart_money(ohlcv)
    squeeze_data = calc_short_squeeze_trigger(price_data, ohlcv)

    # ── V7.0 Quantum Vanguard 4축 점수 체계 ─────────────────────────────────
    # 차트/신호 (20점 기여) — GOLDEN RULE: calc_pullback_score 함수 불변
    pb_result = calc_pullback_score(
        ohlcv["Close"],
        ohlcv["Volume"] if "Volume" in ohlcv.columns else pd.Series(dtype=float),
    ) if not ohlcv.empty and len(ohlcv) >= 22 else \
        {"score": 0, "signal": "데이터 부족", "rsi": 50.0, "ma5": 0, "ma20": 0, "ma60": 0}
    pb_contrib = min(pb_result["score"], 20)   # 차트 기여 최대 20점 캡

    # 수급 (40점) — 기관·외국인·쌍끌이
    inv_result = score_investor(inv_data)

    # 가치/재무 — 표시 전용 (총점 미반영, 브리핑용 보조 데이터)
    fund_result = score_fundamentals(fund_data)

    # 뉴스/미반영호재 (30점) — Tier 1 즉시 만점
    news_result = score_news(news_list)
    news_result["news_status"] = news_status   # 수집 상태 주입 → ui_news() 표시용

    # 리스크/숏스퀴즈 (10점) — 공매도·신용잔고·프로그램매매
    risk_result = score_risk_squeeze(price_data, inv_data, pb_result)

    # ── Hard Cap 전역 적용 — 각 축 상한 강제 후 총점 산출 ───────────────────
    _inv_sc  = min(inv_result["score"],    40)   # 수급  최대 40점
    _news_sc = min(news_result["score"],   30)   # 뉴스  최대 30점
    _pb_sc   = pb_contrib                        # 이미 min(pb_result["score"], 20) 적용
    _risk_sc = min(risk_result["score"],   10)   # 리스크 최대 10점
    # V7.0 총점: 수급40 + 뉴스30 + 차트20 + 리스크10 = 100
    total = min(_inv_sc + _news_sc + _pb_sc + _risk_sc, 100)

    if   total >= 80: verdict = "👑 전 세계 1등 매수 적기 (LEGENDARY)"
    elif total >= 65: verdict = "🔴 즉시 진입 가능 (HIGH CONFIDENCE)"
    elif total >= 45: verdict = "🟡 진입 검토 (MID)"
    elif total >= 30: verdict = "⚪ 관망 권고 (LOW)"
    else:             verdict = "❌ 진입 불가"

    block_alert = check_block_deal(ticker, inv_data)

    return {
        "ticker": ticker, "name": name, "market": market,
        "price": price_data, "ohlcv": ohlcv,
        "inv_data": inv_data, "fund": fund_data, "news": news_list,
        "pb": pb_result, "inv_score": inv_result,
        "fund_score": fund_result, "news_score": news_result,
        "risk_score": risk_result,
        "short_score": _news_sc,     # 하위 호환 — Hard Cap 적용 값
        "pb_contrib":  _pb_sc,       # SSOT: 20-cap 확정치 (배치·상세 일치 보장)
        "total": total, "verdict": verdict,
        "block_alert": block_alert, "collected_at": now_kst,
        # V8.0 God Mode
        "macro_data":  macro_data,
        "macro_sens":  macro_sens,
        "vwap_result": vwap_result,
        "squeeze":     squeeze_data,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 10. 글로벌 지수 + 배치 스캐너 (Top 15 랭킹)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_market_indices() -> dict:
    """KOSPI·KOSDAQ·NASDAQ·S&P500 실시간 지수."""
    out: dict = {}

    # 국내 지수 — Naver 모바일 index API
    for label, code in [("KOSPI", "KOSPI"), ("KOSDAQ", "KOSDAQ")]:
        try:
            r = requests.get(
                f"https://m.stock.naver.com/api/index/{code}/basic",
                headers=NAVER_HDRS, timeout=6,
            )
            d = r.json()
            val = float(str(d.get("closePrice", "0")).replace(",", "") or 0)
            chg = float(d.get("fluctuationsRatio", 0))
            out[label] = {"value": val, "change": chg}
        except Exception:
            out[label] = {"value": 0.0, "change": 0.0}

    # 해외 지수 — Yahoo Finance chart API (인증 불필요)
    for label, sym in [("NASDAQ", "%5EIXIC"), ("S&P500", "%5EGSPC")]:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                "?interval=1d&range=1d",
                headers={"User-Agent": "Mozilla/5.0"}, timeout=6,
            )
            meta = r.json()["chart"]["result"][0]["meta"]
            val  = float(meta.get("regularMarketPrice", 0))
            prev = float(meta.get("previousClose", val) or val)
            chg  = round((val - prev) / prev * 100, 2) if prev else 0.0
            out[label] = {"value": val, "change": chg}
        except Exception:
            out[label] = {"value": 0.0, "change": 0.0}

    return out


_ETF_ETN_KW = (
    "ETF", "ETN", "KODEX", "TIGER", "KINDEX", "KOSEF", "ARIRANG",
    "HANARO", "TIMEFOLIO", "PLUS", "ACE", "SOL", "RISE",
    "레버리지", "인버스", "선물", "채권", "달러", "원유",
)

@st.cache_data(ttl=300, show_spinner=False)
def get_top_volume_tickers() -> list[dict]:
    """
    Volume Anomaly 상위 500종목 — Naver sise_quant 5페이지 확장 수집.

    [이상 거래 징후 Composite Score]
    기준 A (회전율): 거래대금(백만) / 시가총액(억) → % (시총 대비 얼마나 돌았나)
    기준 B (거래대금): 절대 유동성 (전통 지표, 보조)
    Composite = norm_turnover * 0.6 + norm_tvol * 0.4  ← 회전율 가중 우선
    → 소형주 매집 포착 특화 (절대 거래대금 작아도 회전율 폭증 시 상위 편입)
    """
    rows_by_market: dict[str, list[dict]] = {}

    for sosok, market in [("0", "KOSPI"), ("1", "KOSDAQ")]:
        pool: list[dict] = []
        seen: set[str] = set()

        for page in range(1, 6):   # 5페이지 ≈ 시장당 400~500 후보 수집
            try:
                url  = (f"https://finance.naver.com/sise/sise_quant.naver"
                        f"?sosok={sosok}&page={page}")
                resp = requests.get(url, headers=NAVER_HDRS, timeout=10)
                soup = BeautifulSoup(resp.text, "lxml")
                tbl  = soup.select_one("table.type_2")
                if not tbl:
                    break

                for tr in tbl.select("tr"):
                    a = tr.select_one('a[href*="/item/main.naver?code="]')
                    if not a:
                        continue
                    m = re.search(r"code=(\d{6})", a.get("href", ""))
                    if not m:
                        continue
                    code = m.group(1)
                    if code in seen:
                        continue
                    name = a.get_text(strip=True)
                    if not name or len(name) < 2:
                        continue
                    if any(kw in name for kw in _ETF_ETN_KW):
                        continue

                    # ── 시가총액·거래대금 파싱 (td[5]=거래대금 백만, td[6]=시총 억) ──
                    tds = tr.select("td")
                    tvol_백만 = 0.0   # 거래대금 (백만원)
                    cap_억    = 0.0   # 시가총액 (억원)
                    try:
                        def _td_num(idx: int) -> float:
                            txt = tds[idx].get_text(strip=True).replace(",", "")
                            return float(txt) if txt.lstrip("-").isdigit() else 0.0
                        v5, v6 = _td_num(5), _td_num(6)
                        # sise_quant 열 순서: 거래대금(5) → 시가총액(6)
                        # 두 값 모두 양수일 때만 사용
                        if v5 > 0 and v6 > 0:
                            tvol_백만, cap_억 = v5, v6
                    except Exception:
                        pass

                    # turnover_pct (%) = 거래대금(백만) / 시가총액(억)
                    # [단위 검증] 1억=100백만 → tvol(백만)/cap(억) = tvol(백만)/(cap(백만)/100) *1/100*100 = tvol/cap
                    turnover_pct = (tvol_백만 / cap_억) if cap_억 > 0 else 0.0

                    pool.append({
                        "code":         code,
                        "name":         name,
                        "market":       market,
                        "cap_억":       cap_억,
                        "tvol_백만":    tvol_백만,
                        "turnover_pct": turnover_pct,
                    })
                    seen.add(code)
            except Exception:
                break   # 페이지 없으면 중단

        rows_by_market[market] = pool

    # ── Composite Anomaly Score 정규화 → 시장별 상위 100종목 추출 ─────────────
    candidates: list[dict] = []
    for market, pool in rows_by_market.items():
        if not pool:
            continue
        max_tv = max((r["tvol_백만"]    for r in pool), default=1) or 1
        max_tr = max((r["turnover_pct"] for r in pool), default=1) or 1
        for r in pool:
            norm_tv = r["tvol_백만"]    / max_tv
            norm_tr = r["turnover_pct"] / max_tr
            r["anomaly_score"] = norm_tr * 0.6 + norm_tv * 0.4   # 회전율 가중

        pool.sort(key=lambda x: x["anomaly_score"], reverse=True)
        candidates.extend(pool[:250])   # 시장별 상위 250종목 = 전체 500종목

    return candidates


@st.cache_data(ttl=180, show_spinner=False)
def quick_score(ticker: str, name: str, market: str, turnover_pct: float = 0.0) -> dict | None:
    """
    배치 스캐너용 점수 산출 — analyze_ticker()와 100% 동일한 42대 필살기 4축 공식.

    ┌──────────┬─────┬──────────────────────────────────┐
    │ 수급     │ 40점│ score_investor()  GOLDEN RULE    │
    │ 뉴스     │ 30점│ score_news()  ← V8.1 Tier2 포함  │
    │ 차트     │ 20점│ calc_pullback_score()  GOLDEN RULE│
    │ 리스크   │ 10점│ score_risk_squeeze()              │
    └──────────┴─────┴──────────────────────────────────┘
    get_news()는 @st.cache_data(ttl=300)이므로 배치 성능에 최소 영향.
    """
    try:
        price_data = get_realtime_price(ticker)
        if not price_data or price_data.get("현재가", 0) == 0:
            return None

        ohlcv    = get_ohlcv(ticker, 90)
        inv_data = get_investor_flow(ticker)

        # 뉴스 수집 — get_news()는 캐시됨(ttl=300), 단일 분석과 동일 Flexible Match 적용
        _news_aliases = _build_eng_aliases(name, ticker)
        _news_raw     = get_news(ticker, name, _news_aliases)
        news_list     = _news_raw.get("items", []) if isinstance(_news_raw, dict) else []

        pb = (
            calc_pullback_score(
                ohlcv["Close"],
                ohlcv["Volume"] if "Volume" in ohlcv.columns else pd.Series(dtype=float),
            )
            if not ohlcv.empty and len(ohlcv) >= 22
            else {"score": 0, "signal": "데이터 부족", "rsi": 50.0,
                  "ma5": 0, "ma20": 0, "ma60": 0}
        )
        inv         = score_investor(inv_data)
        news_result = score_news(news_list)         # V8.1 Tier2 모멘텀 키워드 완전 동일
        risk_result = score_risk_squeeze(price_data, inv_data, pb)

        # ── 상대 거래량 급증률 (vol_ratio) — OHLCV 이미 보유, 추가 API 없음 ──
        vol_ratio = 1.0
        if not ohlcv.empty and "Volume" in ohlcv.columns and len(ohlcv) >= 21:
            vols = ohlcv["Volume"].dropna()
            if len(vols) >= 21:
                today_vol  = float(vols.iloc[-1])
                avg20_vol  = float(vols.iloc[-21:-1].mean())   # 최근 20일 평균 (당일 제외)
                vol_ratio  = round(today_vol / avg20_vol, 2) if avg20_vol > 0 else 1.0

        pb_cap = min(pb["score"], 20)   # 차트 기여 최대 20점 캡
        # analyze_ticker()와 100% 동일한 공식: 수급40 + 뉴스30 + 차트20 + 리스크10
        total  = min(inv["score"] + news_result["score"] + pb_cap + risk_result["score"], 100)

        # ── rank_score: 신호 강도 가중치 적용 (정렬 전용, 표시 점수와 별도) ──
        _SIG_MULT = {"즉시 매수": 2.5, "매수 준비": 1.2, "관망": 0.3, "데이터 부족": 0.2}
        pb_sig   = pb.get("signal", "관망")
        sig_mult = next((v for k, v in _SIG_MULT.items() if k in pb_sig), 0.3)
        _RANK_DENOM = 30 * 2.5 + 30 * 2.0 + 20   # 최대 가중 합산 = 155
        rank_raw   = pb["score"] * sig_mult + inv["score"] * 2.0 + news_result["score"]
        rank_score = int(min(rank_raw / _RANK_DENOM * 100, 100))

        # ── Hard Cap 전역 적용 — 렌더링 전 각 축 상한 강제 ────────────────────
        _inv_sc  = min(inv["score"],          40)   # 수급  최대 40점
        _news_sc = min(news_result["score"],  30)   # 뉴스  최대 30점
        _pb_sc   = min(pb["score"],           20)   # 차트  최대 20점 (raw 최대 25 → 20-cap)
        _risk_sc = min(risk_result["score"],  10)   # 리스크 최대 10점

        # ── 소형주 세력 입질 가산점 (+15, inv_sc 40점 캡 유지) ──────────────────
        # 조건: 시총 3,000억 미만 AND (거래량 3배+ OR 회전율 10%+) AND RSI 40~65 AND 수급 최소
        _cap_억 = price_data.get("시가총액", 0)
        if 0 < _cap_억 < 3_000:
            _vol_bomb      = vol_ratio  >= 3.0
            _turnover_bomb = turnover_pct >= 10.0
            _rsi_zone_ok   = 40.0 <= pb["rsi"] <= 65.0
            if (_vol_bomb or _turnover_bomb) and _rsi_zone_ok and inv["score"] >= 5:
                _inv_sc = min(_inv_sc + 15, 40)   # 가산 후 40점 캡 재적용

        _total   = min(_inv_sc + _news_sc + _pb_sc + _risk_sc, 100)

        # ── 시총 규모 레이블 ──────────────────────────────────────────────────
        _cap_label = (
            "대형" if _cap_억 >= 10_000
            else ("중형" if _cap_억 >= 3_000 else "소형")
        )

        return {
            "ticker":        ticker,
            "name":          name,
            "market":        market,
            "price":         price_data.get("현재가", 0),
            "change":        float(price_data.get("등락률", 0)),
            "cap":           _cap_억,
            "pb_score":      _pb_sc,    # 20점 상한 적용된 확정치
            "inv_score":     _inv_sc,   # 40점 상한 적용된 확정치 (소형주 가산 포함)
            "news_score":    _news_sc,  # 30점 상한 적용된 확정치
            "risk_score":    _risk_sc,  # 10점 상한 적용된 확정치
            "total":         _total,    # 100점 상한 적용된 확정치
            "rank_score":    rank_score,
            "signal":        pb["signal"],
            "rsi":           pb["rsi"],
            # ── 스텔스 모드 전용 필드 ──────────────────────────────────────────
            "ma5":           pb.get("ma5",  0),
            "ma20":          pb.get("ma20", 0),
            "is_ssankkl":    "쌍끌이" in inv.get("detail", ""),
            # ── Volume Anomaly 필드 (UI 표기·스텔스 필터링용) ─────────────────
            "vol_ratio":     vol_ratio,          # 당일 / 20일 평균 거래량 배수
            "turnover_pct":  round(turnover_pct, 2),  # 시총 대비 회전율 (%)
            "cap_label":     _cap_label,         # 대형/중형/소형
        }
    except Exception:
        return None


def scan_top_stocks(candidates: list[dict]) -> list[dict]:
    """후보 종목 병렬 스코어링 → FDR Marcap 병합 → 점수 내림차순 정렬."""
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs = {
            ex.submit(
                quick_score,
                c["code"], c["name"], c["market"],
                c.get("turnover_pct", 0.0),
            ): c
            for c in candidates
        }
        results = []
        for f in futs:
            try:
                r = f.result(timeout=20)
                if r:
                    results.append(r)
            except Exception:
                pass

    # ── FDR Marcap 병합: Naver API cap이 0/소액인 경우 보완 ──────────────────
    cap_lookup = _get_marcap_lookup()
    for r in results:
        code = r["ticker"]
        if r.get("cap", 0) < 100 and code in cap_lookup:
            r["cap"] = round(cap_lookup[code], 0)
        # cap_label을 병합 후 최종 시총 기준으로 재계산 (Naver API 0 반환 오류 보정)
        cap_억 = r.get("cap", 0)
        r["cap_label"] = (
            "대형" if cap_억 >= 10_000
            else ("중형" if cap_억 >= 3_000 else "소형")
        )

    # ── 정렬: 1순위 차트신호(HIGH→MID→LOW→진입불가), 2순위 총점 ─────────────
    _SIG_PRI = {"즉시 매수": 3, "매수 준비": 2, "관망": 1}

    def _sig_key(r: dict) -> tuple:
        sig = r.get("signal", "")
        pri = next((v for k, v in _SIG_PRI.items() if k in sig), 0)
        return (pri, r.get("total", 0))

    return sorted(results, key=_sig_key, reverse=True)


@st.cache_data(ttl=60, show_spinner=False)
def _scan_top_cached(candidate_tuples: tuple) -> list[dict]:
    """scan_top_stocks의 캐시 래퍼 — tuple 입력으로 hashable 처리 (TTL 60s).
    TTL을 60s로 단축 → 코드 변경 후 최대 1분 내 새 로직 자동 반영 보장.
    tuple 형식: (code, name, market, turnover_pct) — 4-tuple
    """
    candidates = [
        {"code": c[0], "name": c[1], "market": c[2], "turnover_pct": c[3] if len(c) > 3 else 0.0}
        for c in candidate_tuples
    ]
    return scan_top_stocks(candidates)


@st.cache_data(ttl=300, show_spinner=False)
def get_index_sparkline(yf_sym: str) -> list[float]:
    """Yahoo Finance v8 — 최근 10거래일 종가 스파크라인 데이터."""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_sym}?interval=1d&range=20d",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=8,
        )
        closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        return closes[-10:] if len(closes) >= 10 else closes
    except Exception:
        return []


def _sparkline_svg(prices: list[float], up: bool = True) -> str:
    """SVG 인라인 스파크라인 (80×30 px)."""
    if len(prices) < 2:
        return "<svg width='80' height='30'></svg>"
    mn, mx = min(prices), max(prices)
    rng = mx - mn if mx != mn else 1.0
    n   = len(prices)
    pts = []
    for i, p in enumerate(prices):
        x = i / (n - 1) * 76 + 2
        y = 27 - (p - mn) / rng * 23 + 1
        pts.append(f"{x:.1f},{y:.1f}")
    col = "#27ae60" if up else "#e74c3c"
    return (
        f'<svg width="80" height="30" viewBox="0 0 80 30" style="display:block">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
        f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def _gauge_svg(score: int) -> str:
    """반원형 속도계 SVG — SOOMBI ANALYST Impact Score."""
    p  = max(0, min(score, 100)) / 100
    cx, cy, r = 120, 112, 90
    angle = math.pi * (1 - p)
    ex = cx + r * math.cos(angle)
    ey = cy - r * math.sin(angle)
    nr = 64
    nx = cx + nr * math.cos(angle)
    ny = cy - nr * math.sin(angle)
    laf = 1 if p > 0.5 else 0

    def _zarc(p0: float, p1: float, col: str, opa: str = "0.22") -> str:
        a0 = math.pi * (1 - p0)
        a1 = math.pi * (1 - p1)
        x0 = cx + r * math.cos(a0); y0 = cy - r * math.sin(a0)
        x1 = cx + r * math.cos(a1); y1 = cy - r * math.sin(a1)
        lf = 1 if (p1 - p0) > 0.5 else 0
        return (f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {lf} 1 {x1:.1f} {y1:.1f}" '
                f'stroke="{col}" stroke-width="20" fill="none" stroke-linecap="butt" opacity="{opa}"/>')

    zones = (
        _zarc(0.00, 0.35, "#e74c3c") +
        _zarc(0.35, 0.55, "#f39c12") +
        _zarc(0.55, 0.75, "#D4AF37") +
        _zarc(0.75, 1.00, "#27ae60")
    )
    sc = "#e74c3c" if score < 35 else ("#f39c12" if score < 55 else ("#D4AF37" if score < 75 else "#27ae60"))
    score_arc = ""
    if p > 0.005:
        score_arc = (f'<path d="M 30.0 {cy:.1f} A {r} {r} 0 {laf} 1 {ex:.1f} {ey:.1f}" '
                     f'stroke="{sc}" stroke-width="20" fill="none" stroke-linecap="round"/>')
    return (
        f'<svg viewBox="0 0 240 140" width="220" style="display:block;margin:0 auto">'
        f'{zones}{score_arc}'
        f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity="0.95"/>'
        f'<circle cx="{cx}" cy="{cy}" r="7" fill="#0E1117"/>'
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#ffffff" opacity="0.9"/>'
        f'<text x="22" y="134" font-size="9" fill="#e74c3c" font-weight="700" text-anchor="middle">0</text>'
        f'<text x="68" y="50" font-size="9" fill="#f39c12" font-weight="700" text-anchor="middle">35</text>'
        f'<text x="{cx}" y="16" font-size="9" fill="#D4AF37" font-weight="700" text-anchor="middle">55</text>'
        f'<text x="172" y="50" font-size="9" fill="#27ae60" font-weight="700" text-anchor="middle">75</text>'
        f'<text x="218" y="134" font-size="9" fill="#27ae60" font-weight="700" text-anchor="middle">100</text>'
        f'</svg>'
    )


_INDEX_YF = {
    "KOSPI":  "%5EKS11",
    "KOSDAQ": "%5EKQ11",
    "NASDAQ": "%5EIXIC",
    "S&P500": "%5EGSPC",
}


def ui_market_header(indices: dict):
    """글로벌/국내 증시 전광판 — 스파크라인 카드 4열."""
    cards_html = ""
    for label in ["KOSPI", "KOSDAQ", "NASDAQ", "S&P500"]:
        d    = indices.get(label, {"value": 0.0, "change": 0.0})
        val  = d["value"]
        chg  = d["change"]
        up   = chg >= 0
        val_str = f"{val:,.2f}" if val else "—"
        chg_str = f"{'▲' if up else '▼'} {abs(chg):.2f}%"
        chg_col = "#FF5050" if up else "#3399FF"
        spark   = get_index_sparkline(_INDEX_YF.get(label, ""))
        svg     = _sparkline_svg(spark, up=up)
        cards_html += f"""
<div class="ic">
  <div class="ic-label">{label}</div>
  <div class="ic-val">{val_str}</div>
  <div class="ic-row">
    <span class="ic-chg" style="color:{chg_col}">{chg_str if val else '—'}</span>
    <span class="ic-spark">{svg}</span>
  </div>
</div>"""

    _html_block(f"""
<style>
  .ic-wrap {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:4px; }}
  .ic {{ background:#12192b; border:1px solid #2a2f3e; border-radius:14px;
          padding:18px 22px 14px; box-shadow:0 2px 12px rgba(0,0,0,.5); }}
  .ic-label {{ font-size:.78rem; font-weight:700; letter-spacing:.12em;
                color:#D4AF37; text-transform:uppercase; margin-bottom:6px; }}
  .ic-val   {{ font-size:1.7rem; font-weight:900; color:#F0F0F0; line-height:1.1; }}
  .ic-row   {{ display:flex; align-items:center; justify-content:space-between; margin-top:8px; }}
  .ic-chg   {{ font-size:.88rem; font-weight:700; }}
  .ic-spark {{ display:flex; align-items:center; }}
</style>
<div class="ic-wrap">{cards_html}</div>
""")


def ui_top15_tabs(scored: list[dict]):
    """투자 지표 정밀 분석 Top 15 — 탭(전체 / 대형주 / 우량주 / 신규관심)."""

    def _to_df(items: list[dict]) -> pd.DataFrame:
        if not items:
            return pd.DataFrame()
        rows = []
        for i, s in enumerate(items[:15], 1):
            vr  = s.get("vol_ratio", 1.0)
            vr_str = f"{vr:.1f}x" if vr >= 1.0 else "—"
            rows.append({
                "순위":           i,
                "종목명":         s["name"],
                "코드":           s["ticker"],
                "시장":           s["market"],
                "규모":           s.get("cap_label", "—"),
                "현재가":         f"{s['price']:,}원" if s["price"] else "—",
                "등락률":         f"{s['change']:+.2f}%" if s["price"] else "—",
                "거래량급증":     vr_str,
                "숨비 점수":      s["total"],
                "수급 점수":      s["inv_score"],
                "차트 점수":      s["pb_score"],
                "RSI":            s.get("rsi", "—"),
                "차트 신호":      s.get("signal", "—"),
            })
        return pd.DataFrame(rows)

    _prog_col = st.column_config.ProgressColumn(
        "숨비 점수", min_value=0, max_value=100, format="%d점"
    )

    def _show(df: pd.DataFrame, tab_key: str, sort_mode: str = "total"):
        """데이터프레임 행 선택(on_select) → 단일 종목 정밀 해부 100% 동기화.
        sort_mode:
          'total'  — 주도주 모드: 숨비 점수(총점) 내림차순
          'ma_dev' — 스텔스 모드: MA20 이격도 오름차순 (이격도 컬럼이 없으면 total로 fallback)
        """
        if df.empty:
            st.info("데이터 동기화 중 — 잠시 후 재시도하세요.")
            return

        display_df = df.copy()

        if sort_mode == "total":
            # 주도주 모드: 숨비 점수 내림차순 정렬
            display_df = display_df.sort_values(by="숨비 점수", ascending=False)
        # (스텔스 모드는 _to_df 호출 전 이미 정렬 완료 → 현 순서 유지)

        # 정렬 후 순위 1, 2, 3… 재부여 (핵심)
        display_df = display_df.reset_index(drop=True)
        display_df["순위"] = range(1, len(display_df) + 1)

        # 데이터프레임 출력 및 선택 이벤트 감지
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={"숨비 점수": _prog_col},
            selection_mode="single-row",
            on_select="rerun",
            key=f"df_select_{tab_key}"
        )

        # 1% 오차 없는 세션 동기화 (선택한 행의 '코드'를 추출하여 세션에 강제 저장)
        if event and len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            st.session_state.selected_stock_code = display_df.iloc[selected_idx]["코드"]

    # ── 대형주: 시가총액 5,000억+ 엄격 적용 (주가 기준 혼용 금지) ───────────
    large = sorted(
        [s for s in scored if s.get("cap", 0) >= 5_000],
        key=lambda x: x["total"], reverse=True,   # 총점 내림차순 정렬
    )
    # fallback 없음 — 필터 누수 방지: 5,000억 미만은 대형주 탭 진입 불가

    # ── 우량주: 숨비 45점+ AND (수급 12+ OR 차트 12+) ────────────────────
    qual = sorted(
        [s for s in scored if s["total"] >= 45
         and (s["pb_score"] >= 12 or s["inv_score"] >= 12)],
        key=lambda x: x["total"], reverse=True,
    )
    if len(qual) < 5:
        qual = sorted(
            [s for s in scored if s["total"] >= 40],
            key=lambda x: x["pb_score"] + x["inv_score"], reverse=True,
        )
    if not qual:
        qual = sorted(scored, key=lambda x: x["pb_score"] + x["inv_score"], reverse=True)

    # ── 소형/중형주: 시가총액 5,000억 미만 엄격 적용 (주가 기준 혼용 금지) ──
    small_mid = sorted(
        [s for s in scored if 0 < s.get("cap", 0) < 5_000],
        key=lambda x: x["total"], reverse=True,
    )
    if not small_mid:
        small_mid = sorted(
            [s for s in scored if s["total"] > 0],
            key=lambda x: x["total"], reverse=True,
        )

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 전체 Top 15",
        "🏢 대형주 (시총 5,000억+)",
        "💎 우량주 (숨비 45점+)",
        "🪙 소형/중형주 (시총 5,000억 미만)",
    ])
    with tab1: _show(_to_df(scored),    "all",   sort_mode="total")
    with tab2: _show(_to_df(large),     "large", sort_mode="total")
    with tab3: _show(_to_df(qual),      "qual",  sort_mode="total")
    with tab4: _show(_to_df(small_mid), "penny", sort_mode="total")


def ui_stealth_mode(scored: list[dict]):
    """💎 눌림목/스텔스 모드 — Rule 2 Kill Switch 하드 필터링.

    [3 AND 조건 동시 충족 — 단 하나라도 미충족 시 drop()]
    ① 가격 억제 : 등락률 ≤ +3.0%  (양봉 턴어라운드 허용, 급등주만 차단)
    ② 과열 방지 : RSI ≤ 65        (눌림목 + 초기 반등 포착, 과매수 구간만 배제)
    ③ 수급 다이버전스: 수급 15점 이상 OR 기관+외인 쌍끌이
       (주가↓·보합이지만 세력은 매수 = 진짜 바닥 매집 포착)
    정렬: MA20 이격도 음수 우선, 0에 가장 가까운 순 (최적 눌림목 진입 타이밍 순)
    """

    # ── Rule 2 Kill Switch: 3 AND 조건 — 미충족 즉시 drop() ────────────────
    passed: list[dict] = []
    for s in scored:
        chg    = s.get("change", 0.0)
        rsi    = float(s.get("rsi", 50.0))
        inv_ok = s.get("is_ssankkl") or s["inv_score"] >= 15

        if chg > 3.0:   continue   # ① 급등주 차단 (등락률 +3.0% 초과 즉시 drop) — 양봉 턴어라운드 허용
        if rsi > 65:    continue   # ② 과열 배제 (RSI 65 초과 즉시 drop) — 초기 반등 포착
        if not inv_ok:  continue   # ③ 수급 다이버전스 없음 즉시 drop

        passed.append(s)

    # ── 정렬: 음수 이격도 우선 → 0 근접 순 ──────────────────────────────────
    def _sort_key(s: dict) -> tuple[int, float]:
        ma20  = s.get("ma20", 0)
        price = s.get("price", 0)
        dev   = (price - ma20) / ma20 * 100 if (ma20 > 0 and price > 0) else 999.0
        # 음수(0) 먼저, 양수(1) 나중 → 각각 절댓값 오름차순 (0% 가장 가까운 순)
        return (0 if dev < 0 else 1, abs(dev))

    ranked = sorted(passed, key=_sort_key)[:15]

    # ── Kill Switch 통과 결과 배너 ──────────────────────────────────────────
    n_total  = len(scored)
    n_passed = len(passed)
    n_drop   = n_total - n_passed
    banner_color = "#D4AF37" if n_passed > 0 else "#e74c3c"
    _html_block(f"""
<style>
  .sm-banner {{
    background:linear-gradient(135deg,#0d1a2b,#0f2235);
    border:1px solid #1a3a5c; border-radius:12px;
    padding:14px 20px; margin:4px 0 12px;
  }}
  .sm-banner-title {{
    font-size:.82rem; font-weight:800; color:{banner_color};
    letter-spacing:.12em; text-transform:uppercase; margin-bottom:6px;
  }}
  .sm-banner-body {{ font-size:.82rem; color:#A0AEC0; line-height:1.65; }}
  .sm-hl  {{ color:#FF5050; font-weight:700; }}
  .sm-hl2 {{ color:#D4AF37; font-weight:700; }}
  .sm-rule {{ color:#8fa3b8; font-size:.75rem; margin-top:6px; }}
</style>
<div class="sm-banner">
  <div class="sm-banner-title">💎 Kill Switch 필터링 완료</div>
  <div class="sm-banner-body">
    전체 <strong>{n_total}</strong>종목 스캔 →
    <span class="sm-hl">{n_drop}종목 탈락</span>
    (급등·과열·수급부재) →
    <span class="sm-hl2">{n_passed}종목 통과</span>
    → 상위 <strong>{min(n_passed, 15)}</strong>종목 표출
  </div>
  <div class="sm-rule">
    Kill Switch: ① 등락률 ≤ +3.0% &amp; ② RSI ≤ 65 &amp;
    ③ 수급 15점+ 또는 쌍끌이 (3개 AND 충족 필수) &nbsp;|&nbsp;
    정렬: MA20 이격도 음수 우선·0 근접 순
  </div>
</div>
""")

    # ── 통과 종목 없음 ────────────────────────────────────────────────────────
    if not ranked:
        _html_block("""
<style>
  .sm-empty {{
    background:#12192b; border:1px solid #2a3a50; border-radius:14px;
    padding:28px 32px; text-align:center; margin:8px 0;
  }}
  .sm-empty-title {{ font-size:1.05rem; font-weight:800; color:#D4AF37; margin-bottom:10px; }}
  .sm-empty-body  {{ font-size:.86rem; color:#8fa3b8; line-height:1.75; }}
</style>
<div class="sm-empty">
  <div class="sm-empty-title">💎 현재 스텔스 조건 충족 종목 없음</div>
  <div class="sm-empty-body">
    시장이 전반적 과열 구간이거나 세력 매집이 미발생 상태입니다.<br>
    ⚡ 즉시 갱신으로 재수집하거나, 조정 구간에서 다시 확인하세요.
  </div>
</div>
""")
        return

    # ── 스텔스 데이터프레임 구성 ─────────────────────────────────────────────
    rows = []
    for i, s in enumerate(ranked, 1):
        ma20  = s.get("ma20", 0)
        price = s.get("price", 0)
        chg   = s.get("change", 0.0)
        rsi   = float(s.get("rsi", 50.0))

        if ma20 > 0 and price > 0:
            dev_val = (price - ma20) / ma20 * 100
            dev_str = f"{dev_val:+.2f}%"
        else:
            dev_str = "—"

        badge = (
            "🔥 쌍끌이" if s.get("is_ssankkl")
            else ("💪 수급강" if s["inv_score"] >= 30 else "📈 수급+")
        )

        vr      = s.get("vol_ratio", 1.0)
        vr_str  = f"{vr:.1f}x" if vr >= 1.0 else "—"
        tr_pct  = s.get("turnover_pct", 0.0)
        tr_str  = f"{tr_pct:.1f}%" if tr_pct > 0 else "—"
        rows.append({
            "순위":           i,
            "종목명":         s["name"],
            "코드":           s["ticker"],
            "규모":           s.get("cap_label", "—"),
            "현재가":         f"{price:,}원" if price else "—",
            "등락률":         f"{chg:+.2f}%",
            "거래량급증":     vr_str,
            "회전율":         tr_str,
            "세력 매집 강도": s["inv_score"],
            "RSI":            round(rsi, 1),
            "눌림목 이격도":  dev_str,
            "매집 유형":      badge,
        })

    df = pd.DataFrame(rows)

    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "세력 매집 강도": st.column_config.ProgressColumn(
                "세력 매집 강도", min_value=0, max_value=40, format="%d점"
            )
        },
        selection_mode="single-row",
        on_select="rerun",
        key="df_stealth_main",
    )

    if event and len(event.selection.rows) > 0:
        st.session_state.selected_stock_code = df.iloc[event.selection.rows[0]]["코드"]

    st.markdown(
        '<p style="color:#6b7c93;font-size:0.75rem;margin:8px 0 0;">'
        "🔥 쌍끌이 = 기관·외인 당일 동시 순매수 &nbsp;·&nbsp; "
        "💪 수급강 = 수급 25~39점 &nbsp;·&nbsp; "
        "거래량급증 = 당일/20일평균 배수 (3x+ 세력 입질 경보) &nbsp;·&nbsp; "
        "회전율 = 시총 대비 거래대금 % (10%+ 소형주 폭발 경보) &nbsp;·&nbsp; "
        "Kill Switch: 등락률 ≤+3% &amp; RSI ≤65 &amp; 수급15+ (3개 AND) &nbsp;·&nbsp; "
        "표의 행 클릭 → 하단 정밀 해부 즉시 실행</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 11. UI 컴포넌트
# ─────────────────────────────────────────────────────────────────────────────
def _html_block(html: str):
    """st.html() — iframe 격리. CSS는 블록 내 <style>에 직접 포함."""
    st.html(html)


# ── 자동 브리핑 헬퍼 ─────────────────────────────────────────────────────────
_SECTOR_KW_MAP: list[tuple[str, str, list[str]]] = [
    ("반도체·AI칩",
     "메모리·파운드리·시스템 반도체 설계·제조 기업으로, AI·HPC·데이터센터 수요 확대의 직접 수혜 섹터입니다.",
     ["반도체", "하이닉스", "DB하이텍", "팹리스", "파운드리", "웨이퍼", "칩"]),
    ("조선·방산·해양",
     "대형 선박·군함·LNG선 건조 전문 기업으로, K-방산 수출 확대 및 친환경 선박 전환의 핵심 수혜 섹터입니다.",
     ["조선", "오션", "중공업", "함정", "방산", "항공우주", "LIG"]),
    ("자동차·모빌리티",
     "완성차·부품·전기차 플랫폼 기업으로, 글로벌 전동화 전환과 SDV(소프트웨어 정의 차량) 패러다임 수혜 섹터입니다.",
     ["자동차", "현대차", "기아", "모터스", "모빌리티"]),
    ("바이오·제약·헬스케어",
     "신약·의료기기·진단키트 개발 기업으로, 고령화 사회 및 글로벌 헬스케어 수요 확대의 장기 수혜 섹터입니다.",
     ["바이오", "제약", "생명", "헬스", "메디", "의료", "치료", "백신"]),
    ("2차전지·소재",
     "배터리셀·양극재·음극재·전해질 기업으로, 전기차·ESS 시장 확대와 에너지 전환의 핵심 소재 공급 섹터입니다.",
     ["배터리", "에코프로", "양극재", "전지", "셀", "2차전지"]),
    ("IT·플랫폼·소프트웨어",
     "인터넷·게임·SaaS·AI 소프트웨어 기업으로, 디지털 전환·AI 기반 수익화·구독경제 성장의 직접 수혜 섹터입니다.",
     ["소프트", "플랫폼", "게임", "네이버", "카카오", "솔루션"]),
    ("화학·정유·소재",
     "범용·특수 화학 및 정유 기업으로, 원자재 스프레드와 글로벌 산업 사이클에 수익성이 연동되는 경기민감 섹터입니다.",
     ["화학", "정유", "케미칼", "소재"]),
    ("건설·플랜트·인프라",
     "건축·토목·해외 플랜트 수주 기업으로, 국내외 인프라 투자 확대 및 정책 모멘텀의 직접 수혜 섹터입니다.",
     ["건설", "엔지니어링", "플랜트", "GS건설"]),
    ("금융·증권·보험",
     "은행·증권·보험·캐피탈 기업으로, 금리 환경 변화 및 자본시장 활성화에 수익성이 연동되는 섹터입니다.",
     ["금융", "은행", "보험", "증권", "캐피탈"]),
    ("에너지·환경·유틸리티",
     "태양광·풍력·원자력·가스 발전 기업으로, 탄소중립 전환 및 에너지 안보 강화 정책의 장기 수혜 섹터입니다.",
     ["에너지", "태양광", "풍력", "원자력", "발전"]),
    ("유통·소비재·식품",
     "유통·식품·생활용품 브랜드 기업으로, 내수 소비 회복 및 K-소비재 글로벌 수출 확대 수혜 섹터입니다.",
     ["유통", "마트", "식품", "소비", "롯데", "신세계"]),
    ("통신·미디어·콘텐츠",
     "이동통신·방송·OTT·K-콘텐츠 기업으로, 구독경제·AI B2B 통신 인프라·한류 글로벌 확산 수혜 섹터입니다.",
     ["통신", "KT", "SKT", "LGU", "미디어", "방송", "콘텐츠"]),
]


def _infer_sector_overview(name: str) -> tuple[str, str]:
    """종목명 키워드 → (섹터명, 섹터 설명) 추론."""
    for sector, desc, kws in _SECTOR_KW_MAP:
        if any(kw in name for kw in kws):
            return sector, desc
    return "종합주식", (
        f"{name}는 다양한 사업을 영위하는 기업입니다. "
        "정밀 업종 정보는 DART 공시(dart.fss.or.kr) 및 공식 IR 자료를 참고하세요."
    )


def _per_label_comment(per: float | None) -> tuple[str, str, str]:
    """PER → (레이블, 해설, 색상코드)."""
    if per is None or per <= 0:
        return "산출 불가", "현재 적자 상태이거나 PER 집계가 미완료 상태입니다. 다음 분기 실적 발표 후 재확인하세요.", "#6b7c93"
    if per < 5:
        return "극심한 저평가 ★★★", f"PER {per:.1f}x — 이익 대비 주가가 극단적으로 낮은 저평가 구간. 안전마진 극대화, 리스크 대비 기대수익 최고 구간입니다.", "#27ae60"
    if per < 10:
        return "저평가 매력 ★★", f"PER {per:.1f}x — 업종 평균 하단 수준의 매력적 가격대. 중장기 가치투자 매수 기회 구간입니다.", "#27ae60"
    if per < 15:
        return "적정 가치권 ★", f"PER {per:.1f}x — 시장 평균 PER에 근접한 합리적 가격대. 안정적 투자 영역입니다.", "#D4AF37"
    if per < 25:
        return "성장 프리미엄", f"PER {per:.1f}x — 성장 기대치가 선반영된 구간. 실적 성장 지속 여부 확인이 핵심입니다.", "#f39c12"
    return "고밸류에이션", f"PER {per:.1f}x — 높은 밸류에이션. 고성장 기대 또는 턴어라운드 전망이 전제된 가격 수준입니다.", "#e74c3c"


def _pbr_label_comment(pbr: float | None) -> tuple[str, str, str]:
    """PBR → (레이블, 해설, 색상코드)."""
    if pbr is None or pbr <= 0:
        return "산출 불가", "PBR 집계가 미완료 상태이거나 자본잠식 여부를 점검하세요.", "#6b7c93"
    if pbr < 0.5:
        return "청산가치 이하 ★★★", f"PBR {pbr:.2f}x — 장부 순자산의 절반 이하. 자산 대비 극단 저평가로 청산가치 미만 구간입니다.", "#27ae60"
    if pbr < 1.0:
        return "자산 안전마진 ★★", f"PBR {pbr:.2f}x — 순자산보다 주가가 낮아 하방 리스크가 제한적인 안전마진 구간입니다.", "#27ae60"
    if pbr < 2.0:
        return "적정 자산가치 ★", f"PBR {pbr:.2f}x — 순자산 대비 합리적 프리미엄 수준입니다.", "#D4AF37"
    return "프리미엄 자산", f"PBR {pbr:.2f}x — 브랜드·기술력·성장성 기반 프리미엄. 실적 유지 여부가 밸류에이션의 관건입니다.", "#f39c12"


def _momentum_lines(result: dict) -> list[str]:
    """수급·뉴스 기반 모멘텀 요인 리스트 생성."""
    lines: list[str] = []
    inv     = result.get("inv_score", {})
    streak  = inv.get("streak", 0)
    inst_5d = inv.get("inst_5d", 0)
    frgn_5d = inv.get("frgn_5d", 0)
    total   = result.get("total", 0)
    good_news = result.get("news_score", {}).get("good", [])

    if streak >= 4:
        lines.append(f"🔴 기관 {streak}일 연속 순매수 — 세력 장기 매집 패턴 감지")
    elif streak >= 2:
        lines.append(f"🟡 기관 {streak}일 연속 순매수 — 단기 매집 신호")
    if frgn_5d > 1_000_000:
        lines.append(f"🔴 외국인 대규모 유입 ({frgn_5d:+,}주) — 외국계 기관 적극 매수")
    elif frgn_5d > 200_000:
        lines.append(f"🟡 외국인 순매수 ({frgn_5d:+,}주) — 외국계 관심 포착")
    if inst_5d > 1_000_000:
        lines.append(f"🔴 기관 대량 누적 ({inst_5d:+,}주) — 5거래일 총량 대형")
    for n in good_news[:2]:
        title = n.get("title", "")
        if title:
            short = title[:32] + ("…" if len(title) > 32 else "")
            lines.append(f"📰 호재 뉴스: {short}")
    if total >= 75:
        lines.append(f"⭐ 숨비 종합 {total}점 — 즉시 진입 가능 HIGH CONFIDENCE")
    elif total >= 55:
        lines.append(f"🔵 숨비 종합 {total}점 — 진입 검토 MID 구간")
    if not lines:
        lines.append("현재 수집된 수급·뉴스 모멘텀 신호 없음 — 관망 권고")
    return lines


def ui_auto_briefing(result: dict, name: str, ticker: str):
    """기업 정밀 브리핑 — ①실시간호재 ②섹터 ③저평가해설 ④모멘텀 자동 생성."""
    fund = result.get("fund", {})
    per  = fund.get("PER")
    pbr  = fund.get("PBR")

    sector, sector_desc          = _infer_sector_overview(name)
    per_lbl, per_cmt, per_col    = _per_label_comment(per)
    pbr_lbl, pbr_cmt, pbr_col    = _pbr_label_comment(pbr)
    mom_lines                    = _momentum_lines(result)
    mom_html = "".join(
        f'<div class="ab-item">{ln}</div>' for ln in mom_lines
    )

    # 실시간 호재 Impact Alpha 카드 생성
    ns           = result.get("news_score", {})
    impact_hits  = ns.get("impact_hits", [])
    impact_block = ""
    if impact_hits:
        kw_tags = "".join(
            f'<span style="background:#2a1f00;color:#D4AF37;border:1px solid #D4AF37;'
            f'border-radius:6px;padding:3px 10px;font-size:.78rem;font-weight:800;'
            f'margin:2px 3px;display:inline-block;">⚡ {kw}</span>'
            for kw in impact_hits[:8]
        )
        impact_block = f"""
  <!-- ⓪ 실시간 호재 감지 — Impact Alpha 카드 -->
  <div class="ab-card" style="border:2px solid #D4AF37;background:#1a1600;">
    <div class="ab-badge" style="color:#D4AF37;font-size:.8rem;">
      ⚡ 실시간 호재 감지 — Impact Alpha (뉴스/공매도 점수 20점 만점 강제 적용)
    </div>
    <div style="margin-top:4px;">{kw_tags}</div>
    <div class="ab-body" style="color:#FFD700;margin-top:6px;font-size:.9rem;">
      시장 미반영 초강력 이벤트 포착 — 즉시 매집 주목 대상
    </div>
  </div>"""

    _html_block(f"""
<style>
  .ab-wrap  {{ display:flex; flex-direction:column; gap:12px; margin:4px 0 14px; }}
  .ab-card  {{ background:#12192b; border:1px solid #2a3550; border-radius:14px;
               padding:22px 28px; display:flex; flex-direction:column; gap:8px; }}
  .ab-row2  {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .ab-badge {{ font-size:.72rem; font-weight:800; letter-spacing:.16em;
               text-transform:uppercase; color:#D4AF37; margin-bottom:4px; }}
  .ab-title {{ font-size:1.1rem; font-weight:800; color:#F5F5F5; line-height:1.4; }}
  .ab-body  {{ font-size:1.0rem; color:#E0E0E0; line-height:1.75; font-weight:500; }}
  .ab-lbl   {{ display:inline-block; font-size:.76rem; font-weight:700;
               border-radius:6px; padding:4px 12px; margin:4px 0;
               background:rgba(255,255,255,.08); }}
  .ab-item  {{ font-size:.95rem; color:#E0E0E0; line-height:1.7; font-weight:500;
               border-bottom:1px solid #1e2a3a; padding:7px 0; }}
  .ab-item:last-child {{ border-bottom:none; }}
</style>
<div class="ab-wrap">
  {impact_block}
  <!-- ① 기업 핵심 요약 — 전체 폭 단독 카드 -->
  <div class="ab-card">
    <div class="ab-badge">① 기업 핵심 요약</div>
    <div class="ab-title">{sector}</div>
    <div class="ab-body">{sector_desc}</div>
  </div>
  <!-- ② 저평가 해설 + ③ 모멘텀 — 2열 나란히 -->
  <div class="ab-row2">
    <div class="ab-card">
      <div class="ab-badge">② 저평가 및 수익률 해설</div>
      <div class="ab-lbl" style="color:{per_col}">{per_lbl}</div>
      <div class="ab-body">{per_cmt}</div>
      <div class="ab-lbl" style="color:{pbr_col}">{pbr_lbl}</div>
      <div class="ab-body">{pbr_cmt}</div>
    </div>
    <div class="ab-card">
      <div class="ab-badge">③ 독점 기술 &amp; 모멘텀</div>
      {mom_html}
    </div>
  </div>
</div>
""")


def ui_price_header(r: dict):
    """상단: 현재가 Gold·Dark 럭셔리 카드."""
    p   = r["price"]
    cur = p.get("현재가", 0)
    chg = float(p.get("등락률", 0))
    dif = p.get("전일대비", 0)
    cap = p.get("시가총액", 0)
    sign = "▲" if chg >= 0 else "▼"
    up   = chg >= 0
    c_price = "#FF5050" if up else "#3399FF"
    c_chg   = c_price
    mkt_bg  = "#1a2a4a" if r["market"] == "KOSPI" else "#1a3a2a"
    mkt_col = "#5ba3f5" if r["market"] == "KOSPI" else "#4ec76a"

    fund = r["fund"]
    tp   = fund.get("목표주가", 0)
    per  = fund.get("PER", None)
    pbr  = fund.get("PBR", None)
    hi52 = fund.get("52주최고", 0)
    lo52 = fund.get("52주최저", 0)

    tp_str  = f"{tp:,}원" if tp else "—"
    per_str = f"{per:.1f}x" if per else "—"
    pbr_str = f"{pbr:.2f}x" if pbr else "—"
    hi_str  = f"{hi52:,}" if hi52 else "—"
    lo_str  = f"{lo52:,}" if lo52 else "—"
    cap_str = f"{cap:,.0f}억" if cap else "—"

    _html_block(f"""
<style>
  .ph {{
    background: linear-gradient(135deg,#0d1526 0%,#12192b 100%);
    border: 1px solid #2a3550;
    border-left: 4px solid #D4AF37;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,.6);
    margin-bottom: 4px;
  }}
  .ph-top  {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:10px; }}
  .ph-name {{ font-size:1.65rem; font-weight:900; color:#D4AF37; letter-spacing:.01em; }}
  .ph-code {{ font-size:1rem; color:#8fa3b8; }}
  .ph-mkt  {{ background:{mkt_bg}; color:{mkt_col}; border:1px solid {mkt_col};
               border-radius:6px; padding:2px 12px; font-size:.8rem; font-weight:700;
               letter-spacing:.06em; }}
  .ph-price {{ font-size:3.6rem; font-weight:900; color:{c_price};
                line-height:1.1; margin:4px 0; font-variant-numeric:tabular-nums; }}
  .ph-chg   {{ font-size:1.3rem; font-weight:700; color:{c_chg}; margin-bottom:16px; }}
  .ph-meta  {{ display:flex; gap:0; flex-wrap:wrap;
                border-top:1px solid #2a3550; padding-top:14px; }}
  .ph-kv    {{ display:flex; flex-direction:column; padding:0 20px 0 0;
                margin-right:20px; border-right:1px solid #2a3550; }}
  .ph-kv:last-child {{ border-right:none; }}
  .ph-k     {{ font-size:.72rem; color:#6b7c93; letter-spacing:.08em;
                text-transform:uppercase; margin-bottom:2px; }}
  .ph-v     {{ font-size:.95rem; font-weight:800; color:#E8E8E8; }}
  .ph-ts    {{ font-size:.75rem; color:#4a5568; margin-top:10px; }}
</style>
<div class="ph">
  <div class="ph-top">
    <span class="ph-name">{r['name']}</span>
    <span class="ph-code">{r['ticker']}</span>
    <span class="ph-mkt">{r['market']}</span>
  </div>
  <div class="ph-price">{cur:,}<span style="font-size:1.4rem;color:#8fa3b8;font-weight:400"> 원</span></div>
  <div class="ph-chg">{sign} {abs(chg):.2f}% &nbsp;({dif:+,}원)</div>
  <div class="ph-meta">
    <div class="ph-kv"><span class="ph-k">시가총액</span><span class="ph-v">{cap_str}</span></div>
    <div class="ph-kv"><span class="ph-k">PER</span><span class="ph-v">{per_str}</span></div>
    <div class="ph-kv"><span class="ph-k">PBR</span><span class="ph-v">{pbr_str}</span></div>
    <div class="ph-kv"><span class="ph-k">목표주가</span><span class="ph-v" style="color:#D4AF37">{tp_str}</span></div>
    <div class="ph-kv"><span class="ph-k">52주 고/저</span><span class="ph-v">{hi_str} / {lo_str}</span></div>
  </div>
  <div class="ph-ts">{r['collected_at']}</div>
</div>
""")


def ui_fundamentals_card(r: dict):
    """SOOMBI ANALYST Insight — PER·PBR·ROE·목표주가 카드."""
    fund       = r["fund"]
    price_data = r["price"]
    cur = price_data.get("현재가", 0)

    per  = fund.get("PER")
    pbr  = fund.get("PBR")
    roe  = fund.get("ROE")
    tp   = fund.get("목표주가", 0)
    cap  = price_data.get("시가총액", 0)

    per_str = f"{per:.1f}x" if per else "—"
    pbr_str = f"{pbr:.2f}x" if pbr else "—"
    roe_str = f"{roe:.1f}%" if roe else "—"
    tp_str  = f"{tp:,}원"    if tp   else "—"
    cap_str = f"{cap:,.0f}억" if cap else "—"

    upside = None
    if tp and cur:
        upside = round((tp - cur) / cur * 100, 1)

    upside_str = f"{upside:+.1f}%" if upside is not None else ""
    upside_col = "#27ae60" if (upside or 0) >= 0 else "#e74c3c"

    items = [
        ("시가총액",                    cap_str, "",         ""),
        ("수익 대비 주가 (PER)",        per_str, "낮을수록 매수 기회", "#27ae60"),
        ("자산 대비 주가 (PBR)",        pbr_str, "1 미만시 안전마진",  "#27ae60"),
        ("자본 활용 능력 (ROE)",        roe_str, "높을수록 우량기업",  "#D4AF37"),
        ("목표주가",                    tp_str,  upside_str,  upside_col),
    ]
    cells = ""
    for k, v, hint, hcol in items:
        hint_html = f'<div class="fi-hint" style="color:{hcol}">{hint}</div>' if hint else ""
        cells += f"""
<div class="fi-cell">
  <div class="fi-key">{k}</div>
  <div class="fi-val">{v}</div>
  {hint_html}
</div>"""

    _html_block(f"""
<style>
  .fi-wrap  {{ background:#12192b; border:1px solid #2a3550; border-radius:14px;
               padding:22px 26px; margin:4px 0; }}
  .fi-title {{ font-size:.72rem; font-weight:800; letter-spacing:.14em; color:#D4AF37;
               text-transform:uppercase; margin-bottom:16px; }}
  .fi-grid  {{ display:grid; grid-template-columns:repeat(5,1fr); gap:16px; }}
  .fi-cell  {{ display:flex; flex-direction:column;
               background:#0d1526; border:1px solid #1e2a3a;
               border-radius:10px; padding:14px 16px; }}
  .fi-key   {{ font-size:.72rem; color:#8fa3b8; line-height:1.3; margin-bottom:6px; }}
  .fi-val   {{ font-size:1.25rem; font-weight:900; color:#E8E8E8; }}
  .fi-hint  {{ font-size:.75rem; font-weight:700; margin-top:4px; }}
  .fi-note  {{ font-size:.72rem; color:#4a5568; margin-top:12px; }}
</style>
<div class="fi-wrap">
  <div class="fi-title">⚡ 숨비 가치 평가 분석</div>
  <div class="fi-grid">{cells}</div>
  <div class="fi-note">※ 네이버 파이낸스 기준 · 수익/자산 대비 주가는 현재 기준, 자본 활용 능력은 최근 결산 기준 · 투자 권유 아님</div>
</div>
""")


def ui_moat_expander(name: str, ticker: str):
    """핵심 사업 및 초격차 독점 기술 아코디언 (모듈 레벨 _get_moat_info 사용)."""
    info = _get_moat_info(ticker, name)

    with st.expander(f"◈ 정밀 사업 분석 — {info['title']}", expanded=False):
        _bold_pat = re.compile(r"\*\*(.+?)\*\*")
        _strong   = '<strong style="color:#D4AF37;">\\1</strong>'

        def _md2html(text: str) -> str:
            return _bold_pat.sub(_strong, text)

        moat_items = "".join(
            '<li style="color:#D8E0EC;font-size:.87rem;line-height:1.7;margin:4px 0;">'
            + _md2html(p) + "</li>"
            for p in info["moat"]
        )
        overview_html = _md2html(info["overview"])
        html = (
            '<div style="padding:4px 0;">'
            '<p style="color:#E8E8E8;font-size:.9rem;line-height:1.7;margin-bottom:14px;">'
            '<strong style="color:#D4AF37;">기업 개요</strong> — ' + overview_html + "</p>"
            '<p style="color:#D4AF37;font-size:.8rem;font-weight:800;'
            'letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">'
            "핵심 경쟁 우위 (경제적 해자)</p>"
            '<ul style="margin:0;padding-left:18px;">' + moat_items + "</ul>"
            '<p style="color:#4a5568;font-size:.72rem;margin-top:14px;">'
            "※ 공개 IR·뉴스·사업보고서 기반 분석. 투자 권유 아님.</p>"
            "</div>"
        )
        st.markdown(html, unsafe_allow_html=True)


def ui_block_alert(msg: str):
    """세력 동향 경보 카드 — Gold & Dark Luxury."""
    _html_block(f"""
<style>
  .ba {{
    background: linear-gradient(135deg,#1a0d0d 0%,#250f0f 100%);
    border: 1px solid #8b2020;
    border-left: 4px solid #e74c3c;
    border-radius: 14px;
    padding: 20px 24px; margin: 8px 0;
    box-shadow: 0 4px 20px rgba(231,76,60,.2);
  }}
  .ba-title {{
    font-size:.72rem; font-weight:800; letter-spacing:.15em;
    color:#e74c3c; text-transform:uppercase; margin-bottom:8px;
  }}
  .ba-body {{ font-size:.97rem; line-height:1.75; color:#E8E8E8; }}
</style>
<div class="ba">
  <div class="ba-title">⚠ 세력 동향 경보 — 블록딜 오버행 및 개인 설거지 주의</div>
  <div class="ba-body">{msg}</div>
</div>
""")


def ui_score_card(r: dict):
    """V7.0 Quantum Vanguard — 숨비 종합 진단 + 내일 상승 확률 히어로 배너."""
    total   = r["total"]
    pb      = r["pb"]
    iv      = r["inv_score"]
    ns      = r["news_score"]
    rs      = r.get("risk_score", {"score": 0, "detail": "—"})
    verdict = r["verdict"]

    prob, prob_tag = calc_tomorrow_prob(r)

    if total >= 80:
        vd_col = "#D4AF37"; vd_bg = "#1a1600"; vd_border = "#D4AF37"
        badge  = "전 세계 1등 매수 적기 (LEGENDARY)"; sc = "#D4AF37"
        emoji  = "👑"
    elif total >= 65:
        vd_col = "#FF5050"; vd_bg = "#1e0a0a"; vd_border = "#FF5050"
        badge  = "즉시 진입 가능 (HIGH)"; sc = "#FF5050"
        emoji  = "🔴"
    elif total >= 45:
        vd_col = "#FFB300"; vd_bg = "#1e1600"; vd_border = "#FFB300"
        badge  = "분할 매수 (MID)";  sc = "#FFB300"
        emoji  = "🟡"
    elif total >= 30:
        vd_col = "#f39c12"; vd_bg = "#221600"; vd_border = "#f39c12"
        badge  = "관망 (LOW)";        sc = "#f39c12"
        emoji  = "⚪"
    else:
        vd_col = "#6b7c93"; vd_bg = "#0d1120"; vd_border = "#4a5568"
        badge  = "진입 불가";         sc = "#6b7c93"
        emoji  = "❌"

    # 확률 색상
    if   prob >= 90: prob_col = "#D4AF37"
    elif prob >= 70: prob_col = "#FF5050"
    elif prob >= 50: prob_col = "#FFB300"
    else:            prob_col = "#6b7c93"

    prob_label = prob_tag if prob_tag else badge
    is_legendary_shot = (prob >= 98)
    legendary_txt = (
        f'<div style="color:#D4AF37;font-size:1.05rem;font-weight:900;'
        f'margin-top:10px;letter-spacing:.05em;">'
        f'⚡ 내일 상승 확률 {prob}% — {prob_label}</div>'
        if is_legendary_shot else
        f'<div style="color:{prob_col};font-size:.95rem;font-weight:800;margin-top:10px;">'
        f'내일 상승 확률 {prob}% — {prob_label}</div>'
    )

    # ── 히어로 점수 배너 (전체 폭, 중앙 정렬) ─────────────────────────────
    st.markdown(
        f"""
<div style="
  background:#1a1a2e;
  border:4px solid {vd_border};
  border-top:4px solid {vd_col};
  border-radius:16px;
  padding:28px 32px;
  text-align:center;
  margin-bottom:18px;
  box-shadow:0 4px 24px rgba(0,0,0,.5);
">
  <div style="font-size:.78rem;font-weight:800;letter-spacing:.2em;
              text-transform:uppercase;color:#8fa3b8;margin-bottom:8px;">
    SOOMBI V7.0 Quantum Vanguard — 종합 진단
  </div>
  <div style="font-size:80px;font-weight:900;color:{sc};
              line-height:1;margin-bottom:8px;">
    {total}<span style="font-size:40px;">점</span>
  </div>
  <div style="font-size:1.3rem;font-weight:800;color:{vd_col};">
    {emoji} {badge}
  </div>
  {legendary_txt}
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Plotly 속도계 게이지 ───────────────────────────────────────────────
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total,
        number={
            "font": {"size": 64, "color": sc, "family": "Arial Black"},
            "suffix": "점",
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#4a5568",
                "tickvals": [0, 30, 45, 65, 80, 100],
                "ticktext": ["0", "30", "45", "65", "80", "100"],
                "tickfont": {"color": "#8fa3b8", "size": 11},
            },
            "bar":  {"color": sc, "thickness": 0.30},
            "bgcolor": "#12192b",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   30],  "color": "#200d0d"},
                {"range": [30,  45],  "color": "#201700"},
                {"range": [45,  65],  "color": "#1c1a00"},
                {"range": [65,  80],  "color": "#0c1f10"},
                {"range": [80, 100],  "color": "#1a1500"},
            ],
            "threshold": {
                "line": {"color": "#D4AF37", "width": 3},
                "thickness": 0.78,
                "value": 80,
            },
        },
        title={
            "text": (
                "숨비 종합 진단 점수<br>"
                f"<span style='font-size:14px;color:{vd_col}'>"
                f"● {badge} 판정</span>"
            ),
            "font": {"size": 17, "color": "#D4AF37", "family": "Arial"},
        },
    ))
    fig.update_layout(
        height=310,
        paper_bgcolor="#0E1117",
        font={"color": "#E8E8E8", "family": "Arial"},
        margin={"t": 90, "b": 10, "l": 50, "r": 50},
    )

    col_gauge, col_verdict = st.columns([1, 1])
    with col_gauge:
        st.plotly_chart(fig, use_container_width=True)
    with col_verdict:
        _html_block(f"""
<style>
  .vd {{
    background:{vd_bg}; border:1px solid {vd_border};
    border-left:4px solid {vd_col};
    border-radius:14px; padding:22px 24px; margin-top:8px;
    box-shadow: 0 2px 12px rgba(0,0,0,.4);
  }}
  .vd-badge {{
    font-size:.72rem; font-weight:900; letter-spacing:.18em;
    color:{vd_col}; text-transform:uppercase; margin-bottom:10px;
  }}
  .vd-text {{ font-size:1.02rem; font-weight:700; color:#E8E8E8; line-height:1.65; }}
</style>
<div class="vd">
  <div class="vd-badge">숨비 종합 판정 ― {badge}</div>
  <div class="vd-text">{verdict}</div>
</div>
""")

    # ── 4분할 세부 분석 카드 ──────────────────────────────────────────────
    st.markdown("#### 📊 4대 핵심 지표 세부 분석")
    c1, c2, c3, c4 = st.columns(4)

    def _mini_card(col, title: str, score: int, max_score: int, detail: str):
        pct   = int(score / max_score * 100)
        col_c = ("#27ae60" if pct >= 75 else
                 "#D4AF37" if pct >= 50 else
                 "#f39c12" if pct >= 25 else "#e74c3c")
        with col:
            _html_block(f"""
<style>
  .mc {{
    background:#12192b; border:1px solid #2a3550;
    border-top:3px solid {col_c};
    border-radius:12px; padding:18px 16px;
  }}
  .mc-title {{ font-size:.7rem; font-weight:800; letter-spacing:.1em;
               color:#D4AF37; text-transform:uppercase; margin-bottom:10px; }}
  .mc-score {{ font-size:2.1rem; font-weight:900; color:{col_c}; line-height:1; }}
  .mc-max   {{ font-size:.82rem; color:#6b7c93; font-weight:400; }}
  .mc-bar   {{ background:#1a2236; border-radius:4px; height:6px; margin:10px 0 8px; }}
  .mc-fill  {{ background:{col_c}; height:6px; border-radius:4px; width:{pct}%; }}
  .mc-det   {{ font-size:.76rem; color:#8fa3b8; line-height:1.45; }}
</style>
<div class="mc">
  <div class="mc-title">{title}</div>
  <div class="mc-score">{score}<span class="mc-max"> / {max_score}점</span></div>
  <div class="mc-bar"><div class="mc-fill"></div></div>
  <div class="mc-det">{detail}</div>
</div>
""")

    pb_contrib_disp = min(pb["score"], 20)
    _mini_card(c1, "수급 (40점)",      iv["score"],        40,
               f"기관·외국인·쌍끌이<br>{iv['detail']}")
    _mini_card(c2, "뉴스/호재 (30점)", ns["score"],        30,
               f"Tier1 {len(ns.get('tier1_news',[]))}건 · Tier2 {len(ns.get('tier2_news',[]))}건<br>악재 {len(ns['bad'])}건")
    _mini_card(c3, "차트/신호 (20점)", pb_contrib_disp,    20,
               f"눌림목 패턴<br>RSI {pb['rsi']} · MA5 {pb['ma5']:,}")
    _mini_card(c4, "리스크/숏스퀴즈 (10점)", rs["score"], 10,
               rs.get("detail", "—"))

    # ── LEGENDARY 판정 상세 근거 카드 (80점 이상 시 자동 출력) ────────────────
    if total >= 80:
        ticker_r = r.get("ticker", "")
        name_r   = r.get("name", "")

        # ── 4대 근거 수집 ─────────────────────────────────────────────────────
        ev: list[tuple[str, str, str]] = []   # (아이콘, 축, 근거 텍스트)

        # 수급 근거
        streak = iv.get("streak", 0)
        frgn5  = iv.get("frgn_5d", 0)
        if "쌍끌이" in iv.get("detail", ""):
            ev.append(("🔴", "수급", "당일 기관·외국인 쌍끌이 대량 매집 포착"))
        if "연기금" in iv.get("detail", ""):
            ev.append(("🏦", "수급", "연기금·패시브 매집 추정 — 5일 연속·100만주 이상"))
        if "가속" in iv.get("detail", ""):
            ev.append(("⚡", "수급", "기관 가속 매집 — 오늘 매수량 > 어제"))
        if streak >= 3:
            ev.append(("🔴", "수급", f"기관 {streak}일 연속 순매수 — 세력 장기 매집"))
        if frgn5 > 300_000:
            ev.append(("🔴", "수급", f"외국인 5일 누적 {frgn5:+,}주 대규모 유입"))
        if "완벽 구조" in iv.get("detail", ""):
            ev.append(("🎯", "수급", "개인 매도·세력 수취 완벽 수급 구조"))

        # 뉴스·미반영 호재 근거
        t1 = ns.get("tier1_news", [])
        t2 = ns.get("tier2_news", [])
        ih = ns.get("impact_hits", [])
        if t1:
            kw_str = ", ".join(ih[:3]) if ih else ""
            ev.append(("🔥", "미반영 호재", f"Tier 1 확정 호재 {len(t1)}건 — 키워드: {kw_str}"))
        if t2:
            ev.append(("📈", "미반영 호재", f"Tier 2 기대감 뉴스 {len(t2)}건 집중 포착"))

        # 차트 근거
        sig = pb.get("signal", "")
        rsi = pb.get("rsi", 50.0)
        if "즉시 매수" in sig or "눌림목" in sig:
            ev.append(("📊", "차트", f"눌림목 매수 타점 포착 — RSI {rsi:.0f}"))
        elif pb_contrib_disp >= 14:
            ev.append(("📊", "차트", f"차트 고득점 {pb_contrib_disp}점 — RSI {rsi:.0f}"))

        # 리스크·숏스퀴즈 근거
        for sig_txt in rs.get("signals", [])[:2]:
            ev.append(("⚡", "리스크", sig_txt))

        # ── 미반영 호재 뉴스 제목 목록 ────────────────────────────────────────
        unrefl_titles: list[str] = []
        for n in (t1 + t2)[:5]:
            title = n.get("title", "")
            if title:
                unrefl_titles.append(title[:55])

        # ── 경제적 해자 정보 ──────────────────────────────────────────────────
        moat_info   = _get_moat_info(ticker_r, name_r)
        moat_lines  = moat_info.get("moat", [])
        moat_title  = moat_info.get("title", f"{name_r} 핵심 사업")
        _bold_re    = re.compile(r"\*\*(.+?)\*\*")

        def _strip_bold(text: str) -> str:
            return _bold_re.sub(r"\1", text)

        if ev:
            rows_html = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:10px;'
                f'padding:8px 0;border-bottom:1px solid #2a2000;">'
                f'<span style="font-size:1.05rem;width:22px;flex-shrink:0;">{ico}</span>'
                f'<span style="background:#2a1f00;color:#D4AF37;font-size:.65rem;'
                f'font-weight:800;border-radius:4px;padding:2px 7px;'
                f'white-space:nowrap;flex-shrink:0;min-width:70px;text-align:center;">{axis}</span>'
                f'<span style="color:#E8E8E8;font-size:.86rem;line-height:1.5;">{txt}</span>'
                f'</div>'
                for ico, axis, txt in ev
            )

            # 미반영 호재 뉴스 목록 HTML
            unrefl_html = ""
            if unrefl_titles:
                items_html = "".join(
                    f'<li style="color:#E8D8A0;font-size:.82rem;line-height:1.6;'
                    f'margin:3px 0;list-style:none;padding-left:0;">'
                    f'📰 {t}</li>'
                    for t in unrefl_titles
                )
                unrefl_html = (
                    f'<div style="margin-top:16px;padding-top:14px;'
                    f'border-top:1px solid #3a2d00;">'
                    f'<div style="font-size:.68rem;font-weight:900;letter-spacing:.14em;'
                    f'color:#D4AF37;text-transform:uppercase;margin-bottom:8px;">'
                    f'📰 미반영 호재 뉴스 — 시장 미반영 기대 이벤트</div>'
                    f'<ul style="margin:0;padding:0;">{items_html}</ul>'
                    f'</div>'
                )

            # 경제적 해자 HTML
            moat_items_html = "".join(
                f'<li style="color:#C8D8EC;font-size:.82rem;line-height:1.6;'
                f'margin:3px 0;list-style:disc;margin-left:16px;">'
                f'{_strip_bold(m)}</li>'
                for m in moat_lines
            )
            moat_html = (
                f'<div style="margin-top:16px;padding-top:14px;'
                f'border-top:1px solid #3a2d00;">'
                f'<div style="font-size:.68rem;font-weight:900;letter-spacing:.14em;'
                f'color:#D4AF37;text-transform:uppercase;margin-bottom:8px;">'
                f'🏰 경제적 해자 — {moat_title}</div>'
                f'<ul style="margin:0;padding:0;">{moat_items_html}</ul>'
                f'</div>'
            )

            _html_block(f"""
<style>
  .leg-wrap {{
    background:#1a1200; border:2px solid #D4AF37;
    border-radius:14px; padding:22px 26px; margin-top:16px;
    box-shadow: 0 4px 24px rgba(212,175,55,.18);
  }}
  .leg-title {{
    font-size:.72rem; font-weight:900; letter-spacing:.18em;
    color:#D4AF37; text-transform:uppercase; margin-bottom:14px;
  }}
</style>
<div class="leg-wrap">
  <div class="leg-title">👑 LEGENDARY 판정 근거 — 42대 필살기 수급·뉴스·차트·리스크 전수 확인</div>
  {rows_html}
  {unrefl_html}
  {moat_html}
</div>
""")


def ui_investor_table(inv_data: list[dict]):
    """하단: 투자자별 5거래일 수급표 — 순수 HTML + CSS 클래스 방식 (색상 !important 완전 보장)."""
    if not inv_data:
        st.info("수급 데이터를 수집할 수 없습니다.")
        return

    has_other = any(r.get("기타법인", 0) != 0 for r in inv_data)
    num_cols  = ["기관", "외국인", "개인"] + (["기타법인"] if has_other else [])
    all_cols  = ["날짜"] + num_cols

    def _fmt(v: int) -> str:
        return "—" if v == 0 else f"{v:+,}"

    def _cls(v: int) -> str:
        if v > 0: return "up"
        if v < 0: return "down"
        return "steady-stock"

    # 헤더
    th_cells = "".join(
        f"<th style='background:#0d1526;color:#D4AF37;font-size:13px;font-weight:800;"
        f"letter-spacing:.1em;text-transform:uppercase;text-align:center;"
        f"padding:11px 18px;border-bottom:1px solid #2a3550;'>{c}</th>"
        for c in all_cols
    )

    # 데이터 행
    body_rows = []
    for r in inv_data:
        date_td = (
            f"<td style='text-align:center;padding:10px 18px;"
            f"border-bottom:1px solid #1e2a3a;font-size:15px;'>{r['날짜']}</td>"
        )
        num_tds = []
        for key in num_cols:
            val = int(r.get(key, 0))
            css = _cls(val)
            num_tds.append(
                f"<td class='{css}' style='text-align:center;padding:10px 18px;"
                f"border-bottom:1px solid #1e2a3a;font-size:15px;'>{_fmt(val)}</td>"
            )
        body_rows.append(f"<tr>{date_td}{''.join(num_tds)}</tr>")

    note_html = "" if has_other else (
        "<p style='font-size:13px;color:#5a6a7a;margin-top:8px;'>"
        "※ 개인 = 역산(기관+외국인+기타법인 零合). 기타법인 별도 집계 없음.</p>"
    )

    html = f"""
<p style='font-size:.72rem;font-weight:800;letter-spacing:.14em;
color:#D4AF37;text-transform:uppercase;margin-bottom:8px;'>
◈ 세력 수급 역추적 — 4주체 5거래일 확정 수급 (단위: 주)</p>
<table style='width:100%;border-collapse:collapse;background:#12192b;
border-radius:12px;overflow:hidden;'>
  <thead><tr>{th_cells}</tr></thead>
  <tbody>{''.join(body_rows)}</tbody>
</table>
{note_html}
"""
    st.markdown(html, unsafe_allow_html=True)


def _ui_news_item(n: dict, badge_html: str):
    """뉴스 단일 항목 — 배지 + 제목(링크) + 이유 + DART 배지."""
    title   = n.get("title", "")
    href    = n.get("url", "")
    reason  = n.get("reason", "")
    is_dart = n.get("dart", False)

    dart_badge = (
        '<span style="background:#1a4a2a;color:#4ec76a;border:1px solid #27ae60;'
        'font-size:.64rem;font-weight:700;border-radius:4px;padding:1px 5px;'
        'margin-left:5px;">📋 DART 공시</span>'
        if is_dart else ""
    )
    title_md = f"[{title}]({href})" if href else title
    reason_html = (
        f'<div style="color:#8fa3b8;font-size:.74rem;margin:1px 0 5px 6px;">'
        f'└ {reason}</div>'
        if reason else ""
    )
    st.markdown(
        f'{badge_html} {title_md}{dart_badge}',
        unsafe_allow_html=True,
    )
    if reason_html:
        st.markdown(reason_html, unsafe_allow_html=True)


def ui_news(news_result: dict, all_news: list[dict]):
    """뉴스 팩트체크 등급제 UI — V8.0 Tiered Fact-Check 시스템."""
    score        = news_result.get("score", 0)
    score_label  = news_result.get("score_label", f"{score}점")
    tier0_news   = news_result.get("tier0_news",  [])
    tier1_news   = news_result.get("tier1_news",  [])
    tier2_news   = news_result.get("tier2_news",  [])
    neutral_news = news_result.get("neutral_news",[])
    bad          = news_result.get("bad",          [])
    impact_hits  = news_result.get("impact_hits",  [])
    vel_label    = news_result.get("velocity_label", "")

    news_status = news_result.get("news_status", "ok" if all_news else "empty")
    if not all_news:
        if news_status == "error":
            st.error(
                "⚠ 뉴스 수집 중 네트워크 오류가 발생했습니다. "
                "⚡ 버튼으로 캐시를 초기화한 후 다시 조회해 주세요."
            )
        else:
            st.info(
                "현재 이 종목에 대한 실시간 호재 뉴스가 없습니다. "
                "(뉴스 점수 0점 적용 — 시장 잡음으로 채우지 않는 0점 원칙)"
            )
        return

    # ── 점수 레이블 헤더 ─────────────────────────────────────────────────────
    score_col = (
        "#D4AF37" if score == 30 else
        "#27ae60" if score >= 20 else
        "#f39c12" if score >= 10 else
        "#e74c3c" if bad else "#6b7c93"
    )
    st.markdown(
        f'<div style="background:#0d1526;border:1px solid {score_col};'
        f'border-left:4px solid {score_col};border-radius:8px;'
        f'padding:10px 16px;margin:4px 0 12px;">'
        f'<span style="color:{score_col};font-weight:800;font-size:.88rem;">'
        f'📊 뉴스 팩트체크 결과: {score_label}</span>'
        f'<span style="color:#6b7c93;font-size:.75rem;margin-left:10px;">{vel_label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Tier 0 🔵 — 시장 구조 변경급 이벤트 ─────────────────────────────────
    if tier0_news:
        st.markdown(
            '<div style="color:#4ec76a;font-weight:800;font-size:.82rem;'
            'letter-spacing:.06em;margin:8px 0 4px;">🔵 TIER 0 — 시장 구조 변경급 (M&A·합병·공개매수)</div>',
            unsafe_allow_html=True,
        )
        t0_badge = (
            '<span style="background:#1a4a2a;color:#4ec76a;border:1px solid #27ae60;'
            'font-size:.68rem;font-weight:800;border-radius:4px;'
            'padding:1px 7px;margin-right:6px;">T0</span>'
        )
        for n in tier0_news:
            _ui_news_item(n, t0_badge)

    # ── Tier 1 🔴 — 확정 팩트 호재 ───────────────────────────────────────────
    if tier1_news:
        kw_str = " · ".join(impact_hits[:5]) if impact_hits else "핵심 이벤트"
        st.markdown(
            f'<div style="background:#1a1600;border:1px solid #D4AF37;border-radius:8px;'
            f'padding:8px 14px;margin:8px 0 6px;">'
            f'<span style="color:#D4AF37;font-weight:800;font-size:.82rem;">'
            f'🔥 TIER 1 — 확정 팩트 호재 · {kw_str}</span></div>',
            unsafe_allow_html=True,
        )
        t1_badge = (
            '<span style="background:#D4AF37;color:#000;font-size:.68rem;'
            'font-weight:800;border-radius:4px;padding:1px 7px;margin-right:6px;">T1</span>'
        )
        for n in tier1_news:
            _ui_news_item(n, t1_badge)

    # ── Tier 2 🟢 — 성장 가시성 호재 ────────────────────────────────────────
    if tier2_news:
        st.markdown(
            '<div style="color:#8fa3b8;font-weight:700;font-size:.8rem;'
            'letter-spacing:.04em;margin:10px 0 4px;">🟡 TIER 2 — 성장 가시성 (목표가·파트너십·중소 계약)</div>',
            unsafe_allow_html=True,
        )
        t2_badge = (
            '<span style="background:#2a3550;color:#8fa3b8;font-size:.68rem;'
            'font-weight:700;border-radius:4px;padding:1px 7px;margin-right:6px;">T2</span>'
        )
        for n in tier2_news:
            _ui_news_item(n, t2_badge)

    # ── Neutral 10pt — PR·채용·IR ────────────────────────────────────────────
    if neutral_news and not (tier0_news or tier1_news or tier2_news):
        st.markdown(
            '<div style="color:#6b7c93;font-size:.78rem;margin:8px 0 4px;">'
            '⬜ NEUTRAL (10점) — 일반 기업 활동 (주가 영향 미미)</div>',
            unsafe_allow_html=True,
        )
        nt_badge = (
            '<span style="background:#1a1f2e;color:#6b7c93;font-size:.68rem;'
            'font-weight:600;border-radius:4px;padding:1px 7px;margin-right:6px;">NT</span>'
        )
        for n in neutral_news[:2]:
            _ui_news_item(n, nt_badge)

    # ── 악재 경보 ────────────────────────────────────────────────────────────
    if bad:
        st.markdown(
            '<div style="color:#e74c3c;font-weight:700;font-size:.8rem;margin:10px 0 4px;">'
            '📉 악재 경보 — 리스크 요인 감지</div>',
            unsafe_allow_html=True,
        )
        bd_badge = (
            '<span style="background:#2a1010;color:#e74c3c;font-size:.68rem;'
            'font-weight:700;border-radius:4px;padding:1px 7px;margin-right:6px;">BAD</span>'
        )
        for n in bad:
            _ui_news_item(n, bd_badge)

    # ── 0점 안내 ─────────────────────────────────────────────────────────────
    if score == 0 and not (tier0_news or tier1_news or tier2_news or neutral_news or bad):
        st.markdown(
            '<div style="color:#6b7c93;font-size:.82rem;padding:8px 0;">'
            '종목 전용 호재 뉴스가 없습니다. 현재 뉴스 점수 0점 적용.</div>',
            unsafe_allow_html=True,
        )

    # ── 전체 뉴스 — 소음 제외, Tier 배지 포함 ─────────────────────────────────
    noise_filtered = [n for n in all_news if not any(kw in n["title"] for kw in _NOISE_KW)]
    if noise_filtered:
        with st.expander(f"전체 뉴스 {len(noise_filtered)}건 (소음 제외) — 팩트체크 등급 표시"):
            for n in noise_filtered:
                t    = n["title"]
                href = n.get("url", "")
                reason = _extract_news_reason(t)
                dart   = _is_dart_news(t)
                dart_s = " 📋" if dart else ""
                reason_s = f"\n  └ *{reason}*" if reason else ""

                if any(kw in t for kw in _TIER0_KW):
                    badge = "🔵 **[T0]**"
                elif any(kw in t for kw in _TIER1_KW):
                    badge = "🔴 **[T1]**"
                elif any(kw in t for kw in _TIER2_KW):
                    badge = "🟡 [T2]"
                elif any(kw in t for kw in _BAD_KW):
                    badge = "🔻 [악재]"
                elif any(kw in t for kw in _NEUTRAL_ARTICLE_KW):
                    badge = "⬜ [NT]"
                else:
                    badge = "— "

                title_md = f"[{t}]({href}){dart_s}" if href else f"{t}{dart_s}"
                st.markdown(f"{badge} {title_md}{reason_s}", unsafe_allow_html=True)


def ui_ma_strip(pb: dict):
    """이동평균 3개 카드 행 — 다크모드 가독성 보장."""
    def _v(val: int) -> str:
        return f"{val:,}원" if val else "—"

    _html_block(f"""
<style>
  .ma-row  {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:4px 0; }}
  .ma-card {{ background:#12192b; border:1px solid #2a3550; border-radius:12px;
              padding:18px 22px; display:flex; flex-direction:column; gap:6px; }}
  .ma-lbl  {{ font-size:.72rem; font-weight:700; letter-spacing:.1em;
              text-transform:uppercase; color:#8fa3b8; }}
  .ma-val  {{ font-size:1.3rem; font-weight:900; color:#FFFFFF; }}
</style>
<div class="ma-row">
  <div class="ma-card">
    <div class="ma-lbl">MA5 (5일선)</div>
    <div class="ma-val">{_v(pb.get("ma5", 0))}</div>
  </div>
  <div class="ma-card">
    <div class="ma-lbl">MA20 (20일선)</div>
    <div class="ma-val">{_v(pb.get("ma20", 0))}</div>
  </div>
  <div class="ma-card">
    <div class="ma-lbl">MA60 (60일선)</div>
    <div class="ma-val">{_v(pb.get("ma60", 0))}</div>
  </div>
</div>
""")


# ─────────────────────────────────────────────────────────────────────────────
# V8.0 GOD MODE UI — 매크로·Smart Money·숏스퀴즈 카드
# ─────────────────────────────────────────────────────────────────────────────
def ui_macro_godmode_card(result: dict):
    """달국금공 매크로 상관관계 + Smart Money + 숏스퀴즈 임계가 통합 카드."""
    ms   = result.get("macro_sens", {})
    vr   = result.get("vwap_result", {})
    sq   = result.get("squeeze", {})
    ns   = result.get("news_score", {})   # Tier 0/1 뉴스 + velocity (f-string 내 변수 참조용)
    name = result.get("name", "")

    sector  = ms.get("sector", "일반")
    items   = ms.get("items", [])
    vwap    = vr.get("vwap", 0)
    gap     = vr.get("gap_pct", 0.0)
    obv_t   = vr.get("obv_trend", "—")
    cmf     = vr.get("cmf", 0.0)
    vverdict = vr.get("verdict", "—")
    trigger = sq.get("trigger", 0)
    gap_sq  = sq.get("gap_pct", 0.0)
    zone    = sq.get("zone", "—")
    atr     = sq.get("atr", 0)

    # 매크로 행 HTML 생성 (f-string 내 중첩 따옴표 회피 — 변수 추출)
    macro_rows_html = ""
    if items:
        for it in items:
            col   = it["col"]
            lbl   = it["label"]
            sym   = it["sym"]
            cur   = it["cur"]
            unit  = it["unit"]
            mchg  = it["macro_chg"]
            beta  = it["beta"]
            imp   = it["impact"]
            direc = it["direction"]
            cur_s = f"{cur:,.2f}" if cur < 5000 else f"{cur:,.0f}"
            mchg_s  = f"{mchg:+.2f}%"
            beta_s  = f"{beta:+.1f}x"
            imp_s   = f"{imp:+.2f}%"
            macro_rows_html += (
                f'<tr><td class="mc-lbl">{lbl}</td>'
                f'<td class="mc-val">{cur_s} {unit}</td>'
                f'<td class="mc-chg">{mchg_s}</td>'
                f'<td class="mc-beta">{beta_s}</td>'
                f'<td class="mc-imp" style="color:{col};">{imp_s}</td>'
                f'<td class="mc-dir" style="color:{col};font-weight:700;">{direc}</td></tr>'
            )
    else:
        macro_rows_html = '<tr><td colspan="6" style="color:#6b7c93;padding:8px;">매크로 데이터 수집 중 (Yahoo Finance)</td></tr>'

    # VWAP 색상
    gap_col = "#27ae60" if gap < -1.0 else "#e74c3c" if gap > 3.0 else "#D4AF37"
    gap_s   = f"{gap:+.2f}%"
    cmf_col = "#27ae60" if cmf > 0.1 else "#e74c3c" if cmf < -0.1 else "#6b7c93"
    cmf_s   = f"{cmf:+.3f}"

    # 숏스퀴즈 색상
    sq_col    = "#e74c3c" if gap_sq <= 1.0 else "#f39c12" if gap_sq <= 3.0 else "#6b7c93"
    trig_s    = f"{trigger:,}" if trigger else "—"
    gap_sq_s  = f"+{gap_sq:.1f}%" if trigger else "—"
    atr_s     = f"{atr:,}" if atr else "—"
    vwap_s    = f"{vwap:,}" if vwap else "—"

    _html_block(f"""
<style>
  .gm {{ background:linear-gradient(135deg,#0a1428 0%,#0e1c3a 100%);
         border:1px solid #1e3060; border-left:4px solid #D4AF37;
         border-radius:14px; padding:22px 26px; margin:6px 0 10px; }}
  .gm-title {{ color:#D4AF37; font-size:1.0rem; font-weight:700; letter-spacing:.08em; margin-bottom:14px; }}
  .gm-sub   {{ color:#8899bb; font-size:.75rem; letter-spacing:.05em; text-transform:uppercase; margin-bottom:8px; }}
  .gm-grid  {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
  .gm-sect  {{ background:#0d1830; border:1px solid #1e2e50; border-radius:10px; padding:14px 16px; }}
  .mc-tbl   {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
  .mc-tbl th {{ color:#8899bb; font-size:.7rem; letter-spacing:.06em; padding:3px 6px;
                border-bottom:1px solid #1e2e50; text-align:left; }}
  .mc-lbl   {{ color:#c0cce0; padding:5px 6px; }}
  .mc-val   {{ color:#ffffff; padding:5px 6px; font-weight:600; }}
  .mc-chg   {{ color:#a0aec0; padding:5px 6px; }}
  .mc-beta  {{ color:#D4AF37; padding:5px 6px; font-weight:600; }}
  .mc-imp   {{ padding:5px 6px; font-weight:700; }}
  .mc-dir   {{ padding:5px 6px; }}
  .vw-row   {{ display:flex; justify-content:space-between; align-items:center; margin:6px 0; }}
  .vw-lbl   {{ color:#8899bb; font-size:.8rem; }}
  .vw-val   {{ font-weight:700; font-size:.9rem; }}
  .sq-big   {{ color:{sq_col}; font-size:1.25rem; font-weight:900; margin:6px 0 2px; }}
  .sq-zone  {{ color:{sq_col}; font-size:.82rem; margin:2px 0; }}
  .gm-verdict {{ color:#c0cce0; font-size:.8rem; margin-top:10px;
                  border-top:1px solid #1e2e50; padding-top:8px; line-height:1.5; }}
</style>
<div class="gm">
  <div class="gm-title">⚡ V8.0 GOD MODE — 기관급 초정밀 분석 엔진 [{sector} 섹터]</div>
  <div class="gm-grid">

    <!-- 달국금공 매크로 상관관계 -->
    <div class="gm-sect">
      <div class="gm-sub">🌐 달국금공 매크로 실시간 상관관계</div>
      <table class="mc-tbl">
        <tr>
          <th>지표</th><th>현재가</th><th>등락</th>
          <th>Beta</th><th>영향도</th><th>판정</th>
        </tr>
        {macro_rows_html}
      </table>
    </div>

    <!-- VWAP Smart Money Flow -->
    <div class="gm-sect">
      <div class="gm-sub">🧠 세력 심리 역추적 — VWAP Smart Money</div>
      <div class="vw-row">
        <span class="vw-lbl">20일 VWAP</span>
        <span class="vw-val" style="color:#D4AF37;">{vwap_s}원</span>
      </div>
      <div class="vw-row">
        <span class="vw-lbl">현재가 괴리율</span>
        <span class="vw-val" style="color:{gap_col};">{gap_s}</span>
      </div>
      <div class="vw-row">
        <span class="vw-lbl">OBV 추세</span>
        <span class="vw-val" style="color:#c0cce0;">{obv_t}</span>
      </div>
      <div class="vw-row">
        <span class="vw-lbl">CMF 자금흐름</span>
        <span class="vw-val" style="color:{cmf_col};">{cmf_s}</span>
      </div>
      <div class="gm-verdict">{vverdict}</div>
    </div>

    <!-- 숏스퀴즈 임계가 -->
    <div class="gm-sect">
      <div class="gm-sub">💣 배거차숏 — 숏스퀴즈 임계가 자동 산출</div>
      <div class="sq-big">임계가 {trig_s}원</div>
      <div class="vw-row">
        <span class="vw-lbl">현재가 대비</span>
        <span class="vw-val" style="color:{sq_col};">{gap_sq_s}</span>
      </div>
      <div class="vw-row">
        <span class="vw-lbl">20일 저항선</span>
        <span class="vw-val" style="color:#D4AF37;">{sq.get("resistance",0):,}원</span>
      </div>
      <div class="vw-row">
        <span class="vw-lbl">ATR(14)</span>
        <span class="vw-val" style="color:#a0aec0;">{atr_s}원</span>
      </div>
      <div class="sq-zone">{zone}</div>
    </div>

    <!-- 뉴스 속도 (Sentiment Velocity) -->
    <div class="gm-sect">
      <div class="gm-sub">📡 감성 속도 분석 — News Sentiment Velocity</div>
      {''.join([
          f'<div style="background:#0a2a1a;border:1px solid #27ae60;border-radius:6px;'
          f'padding:6px 10px;margin:4px 0;font-size:.78rem;color:#fff;">'
          f'🔵 TIER 0 | {n["title"][:55]}</div>'
          for n in ns.get("tier0_news", [])[:2]
      ] or [
          '<div style="color:#6b7c93;font-size:.8rem;margin:4px 0;">Tier 0 이벤트 없음 (M&amp;A·합병·공개매수)</div>'
      ])}
      {''.join([
          f'<div style="background:#1a2a0a;border:1px solid #D4AF37;border-radius:6px;'
          f'padding:5px 10px;margin:3px 0;font-size:.77rem;color:#fff;">'
          f'🟡 TIER 1 | {n["title"][:55]}</div>'
          for n in ns.get("tier1_news", [])[:2]
      ])}
      <div style="color:#D4AF37;font-size:.82rem;font-weight:700;margin-top:8px;
                  border-top:1px solid #1e2e50;padding-top:6px;">
        {ns.get("velocity_label", "—")}
      </div>
    </div>

  </div>
</div>
""")


# ─────────────────────────────────────────────────────────────────────────────
# 12. 메인 앱
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── 전종목 로드 ──────────────────────────────────────────────────────────
    tickers_df = load_krx_tickers()

    # ── 세션 스테이트 초기화 ─────────────────────────────────────────────────
    if "auto_analyze" not in st.session_state:
        st.session_state["auto_analyze"] = False

    # ── 전역 CSS: SOOMBI 마스터 테마 ─────────────────────────────────────────
    st.markdown("""
<style>
/* ① 기본 배경 + 글자색 (전역 !important 색상 강제 완전 제거) */
.stApp { background-color: #111111; color: #FFFFFF; }
p, span, h1, h2, h3, label { color: #FFFFFF; font-weight: bold; }

/* ① 투명도 — 색상 강제 없이 가시성만 보장 */
html, body, [class*="css"], [class*="st-"],
p, span, label, div, th, td, li {
    opacity: 1 !important;
    visibility: visible !important;
}

/* ① 전광판 st.metric 상승(빨강) / 하락(파랑) */
[data-testid="stMetricDelta"] > div {
    font-weight: 900 !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] svg[title="Price up"] + div  { color: #FF5050 !important; }
[data-testid="stMetricDelta"] svg[title="Price up"] path   { fill:  #FF5050 !important; }
[data-testid="stMetricDelta"] svg[title="Price down"] + div { color: #3399FF !important; }
[data-testid="stMetricDelta"] svg[title="Price down"] path  { fill:  #3399FF !important; }

/* ② 마크다운 일반 텍스트 + 기본 p/th/td — 16px, #F8F9FA */
p,
.stMarkdown p,
.stText,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em,
[data-testid="stText"],
[data-testid="stCaptionContainer"] p,
table th, table td {
    color: #F8F9FA !important;
    font-size: 20px !important;
    line-height: 1.6 !important;
    font-weight: 600 !important;
}

/* ③ 익스팬더 내부 텍스트 */
section[data-testid="stExpander"] p,
section[data-testid="stExpander"] li,
section[data-testid="stExpander"] span,
[data-testid="stExpander"] p {
    color: #F0F2F6 !important;
    font-size: 1.05rem !important;
    line-height: 1.7 !important;
    font-weight: 500 !important;
}

/* ④ 익스팬더 헤더 골드 강조 */
button[data-testid="stBaseButton-header"] p,
summary p { color: #D4AF37 !important; font-weight: 700 !important; }

/* ⑤ 메트릭 라벨 — 골드 강조, 심층 타겟 전체 */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] label,
[data-testid="stMetricLabel"] p,
[data-testid="stText"] p,
[data-testid="stMarkdown"] p,
.st-emotion-cache-1wivap2 {
    color: #FFD700 !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* ⑤-b 수급표 + 등락 + 뉴스 HTML 클래스 — 색상 100% 보장 */
.red-val    { color: #FF5050 !important; font-weight: 700 !important; }
.blue-val   { color: #3399FF !important; font-weight: 700 !important; }
.red-plus   { color: #FF5050 !important; font-weight: 700 !important; }
.blue-minus { color: #3399FF !important; font-weight: 700 !important; }
.up-stock   { color: #FF5050 !important; font-weight: 700 !important; }
.down-stock { color: #3399FF !important; font-weight: 700 !important; }
.up         { color: #FF5050 !important; font-weight: 700 !important; }
.up-red     { color: #FF5050 !important; font-weight: 700 !important; font-size: 24px !important; }
.down       { color: #3399FF !important; font-weight: 700 !important; }
.down-blue  { color: #3399FF !important; font-weight: 700 !important; font-size: 24px !important; }
.label      { color: #FFD700 !important; font-weight: 700 !important; }
.gold       { color: #FFD700 !important; font-weight: 700 !important; }
.white      { color: #FFFFFF !important; }
.steady-stock { color: #FFFFFF !important; }
.news-box   { color: #00FF00 !important; font-weight: 700 !important;
              border-left: 5px solid #00FF00; padding-left: 12px; }

/* ⑥ 메트릭 수치 — 크기 유지, 색상 완전 선명 */
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.7rem !important;
    font-weight: 900 !important;
    opacity: 1 !important;
}
[data-testid="stMetricDeltaIcon"] { display: none; }

/* ⑦ 헤딩 — 완전 흰색 선명 유지 */
h1, h2, h3, h4 {
    color: #FFFFFF !important;
    opacity: 1 !important;
}

/* ⑧ 데이터프레임 테이블 — 1.3배 확대 */
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] td,
table th, table td {
    font-size: 1.0rem !important;
    color: #FFFFFF !important;
    opacity: 1 !important;
}

/* ⑨ 기업 설명 / 브리핑 본문 커스텀 클래스 */
.sumbi-description {
    color: #E0E0E0 !important;
    font-size: 1.05rem !important;
    line-height: 1.75 !important;
    padding: 15px 0 !important;
    font-weight: 500 !important;
}

/* ⑩ 캡션 */
[data-testid="stCaptionContainer"] p { color: #6b7c93 !important; font-size: .85rem !important; }

/* ⑪ 경고/정보 박스 */
[data-testid="stAlert"] p { color: #F0F2F6 !important; font-size: 1.0rem !important; }

/* ⑫ 탭 텍스트 */
button[data-baseweb="tab"] p { color: #A0AEC0 !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #D4AF37 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

    # ── 사이드바 ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## SOOMBI ANALYTICS")
        st.markdown("**v4.0 — 세력 역추적 터미널**")
        now_kst = datetime.now(KST)
        holidays, hol_fallback = _get_krx_holidays(now_kst.year)
        today_str = now_kst.strftime("%Y-%m-%d")
        is_holiday = today_str in holidays
        is_mkt  = (
            not is_holiday
            and (9, 0) <= (now_kst.hour, now_kst.minute) <= (15, 30)
            and now_kst.weekday() < 5
        )
        if is_mkt:
            mkt_label = "🟢 장 중"
        elif is_holiday:
            hol_name = holidays.get(today_str, "")
            mkt_label = f"🔴 공휴일 휴장 ({hol_name})" if hol_name else "🔴 공휴일 휴장"
        else:
            mkt_label = "🔴 장 마감"
        st.markdown(f"**KRX 시장**: {mkt_label}")
        if is_holiday:
            _KOR_WEEKDAY = ["월", "화", "수", "목", "금", "토", "일"]
            _candidate = now_kst.date() + timedelta(days=1)
            _next_yr_hols: dict[str, str] = {}
            while True:
                _c_str = _candidate.strftime("%Y-%m-%d")
                if _candidate.year != now_kst.year:
                    if not _next_yr_hols:
                        _next_yr_hols, _ = _get_krx_holidays(_candidate.year)
                    _all_hols = _next_yr_hols
                else:
                    _all_hols = holidays
                if _candidate.weekday() < 5 and _c_str not in _all_hols:
                    break
                _candidate += timedelta(days=1)
            _next_day_label = f"{_candidate.strftime('%Y-%m-%d')} ({_KOR_WEEKDAY[_candidate.weekday()]})"
            st.markdown(f"**다음 거래일**: {_next_day_label}")
        if hol_fallback:
            if not holidays:
                st.warning(
                    f"{now_kst.year}년 공휴일 기본 테이블 미구성 연도 — 시간/요일만 판단",
                    icon="⚠️",
                )
            else:
                st.warning("시장 캘린더 동기화 중 — 기본 데이터 사용", icon="⚠️")
        st.markdown(f"**기준 시각**: {now_kst.strftime('%Y-%m-%d %H:%M KST')}")
        st.markdown(f"**커버리지**: {len(tickers_df):,}개 전종목")
        st.divider()
        if st.button("⚡ 즉시 갱신 (캐시 초기화)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.markdown("#### 숨비 종합 진단 점수")
        st.markdown("""
| 분석 지표 | 배점 |
|---|---|
| 세력 수급 역추적 | 30점 |
| 공매도 잔고 분석 | 20점 |
| 정밀 눌림목 패턴 | 30점 |
| 미반영 호재 뉴스 | 20점 |
| **총점** | **100점** |
""")
        st.markdown("**75점 이상 → 강력 매수 판정**")
        st.divider()
        st.caption("ENGINE: FDR + Naver Finance\nDATA: 실시간 역추적 파이프라인")

    # ── 하이엔드 로고 헤더 ────────────────────────────────────────────────────
    _html_block("""
<style>
  .hdr-wrap {
    padding: 32px 0 24px;
    border-bottom: 1px solid #2a3550;
    margin-bottom: 0;
  }
  .hdr-logo {
    font-size: 2.0rem;
    font-weight: 900;
    letter-spacing: .22em;
    background: linear-gradient(90deg,#B8942A 0%,#D4AF37 30%,#F5E882 55%,#C9A020 80%,#D4AF37 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Georgia','Times New Roman',serif;
    line-height: 1.15;
    display: inline-block;
  }
  .hdr-ver {
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .38em;
    color: #6b7c93;
    text-transform: uppercase;
    margin-top: 6px;
  }
  .hdr-rule {
    width: 56px; height: 2px;
    background: linear-gradient(90deg,#D4AF37,transparent);
    margin: 10px 0;
  }
  .hdr-sub {
    font-size: .95rem;
    font-weight: 500;
    color: #c0c8d8;
    letter-spacing: .04em;
    line-height: 1.5;
  }
  .hdr-accent { color: #D4AF37; font-weight: 700; }
</style>
<div class="hdr-wrap">
  <div class="hdr-logo">SOOMBI ANALYTICS</div>
  <div class="hdr-ver">v4.0 &nbsp;·&nbsp; Private Terminal &nbsp;·&nbsp; KRX Intelligence Engine</div>
  <div class="hdr-rule"></div>
  <div class="hdr-sub">
    <span class="hdr-accent">0.1%</span> 세력 역추적 &amp; 매수 적합도 즉시 판단
    &nbsp;—&nbsp; <span class="hdr-accent">숨비 종합 진단 점수</span> 실시간 자동 산출
  </div>
</div>
""")

    # ── 글로벌/국내 증시 전광판 ─────────────────────────────────────────────
    with st.spinner("시장 데이터 동기화 중…"):
        indices = get_market_indices()
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:20px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 2px;">글로벌 시장 실시간 전광판</h2>',
        unsafe_allow_html=True,
    )
    ui_market_header(indices)
    st.divider()

    # ── 투자 지표 정밀 분석 Top 15 ───────────────────────────────────────────
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:22px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 2px;">투자 지표 정밀 분석 Top 15</h2>'
        '<p style="color:#A0AEC0;font-size:0.82rem;margin:2px 0 8px;">'
        "Volume Anomaly 상위 500종목 자동 스캔 (KOSPI·KOSDAQ 거래량 급증·시총 대비 회전율 이상 포착) &nbsp;|&nbsp; "
        "<strong style='color:#FF5050;'>🔥 주도주/돌파</strong> → 총점 최강 종목 &nbsp;|&nbsp; "
        "<strong style='color:#D4AF37;'>💎 눌림목/스텔스</strong> → 세력 매집 중 + 아직 안 오른 바닥 종목</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("데이터 동기화 중 — 전종목 세력 수급 역추적 파이프라인 가동 중 (최대 60초)…"):
        candidates = get_top_volume_tickers()
        if candidates:
            candidate_tuples = tuple(
                (c["code"], c["name"], c["market"], c.get("turnover_pct", 0.0))
                for c in candidates
            )
            scored = _scan_top_cached(candidate_tuples)
        else:
            scored = []

    if scored:
        # 코드 기준 역추적을 위한 scored 캐시 세션 저장 (detail 뷰 점수 동기화)
        st.session_state["scored_cache"] = {r["ticker"]: r for r in scored}

        # ── 듀얼 랭킹 모드 토글 ──────────────────────────────────────────────
        mode_tab1, mode_tab2 = st.tabs([
            "🔥 주도주 / 돌파 모드",
            "💎 눌림목 / 스텔스 모드",
        ])
        with mode_tab1:
            st.markdown(
                '<p style="color:#FF5050;font-size:0.8rem;font-weight:700;margin:4px 0 6px;">'
                "총점(42대 필살기) 최강 종목 — 수급·뉴스·차트·리스크 4축 합산 최고점 순</p>",
                unsafe_allow_html=True,
            )
            ui_top15_tabs(scored)
        with mode_tab2:
            st.markdown(
                '<p style="color:#D4AF37;font-size:0.8rem;font-weight:700;margin:4px 0 6px;">'
                "세력 매집 中 + 주가 아직 눌린 종목 — 추격 매수 금지 · 눌림목 진입 전용</p>",
                unsafe_allow_html=True,
            )
            ui_stealth_mode(scored)
    else:
        st.warning("실시간 데이터 수급 대기 중 (KRX / Yahoo Finance) — ⚡ 즉시 갱신 버튼으로 재시도하세요.")
    st.divider()

    # ── 검색 영역 ─────────────────────────────────────────────────────────────
    st.markdown(
        '<h2 style="color:#D4AF37;font-size:22px;font-weight:700;'
        'letter-spacing:.05em;margin:4px 0 8px;">단일 종목 정밀 해부</h2>',
        unsafe_allow_html=True,
    )

    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input(
            "종목명 또는 6자리 코드 입력",
            placeholder="예: 한화오션 / 042660 / 삼성전자 — 또는 위 표에서 종목 클릭",
            label_visibility="collapsed",
            key="search_query",
        )
    with col_btn:
        go = st.button("🔍 해부 시작", use_container_width=True, type="primary")

    # 클릭-투-애널라이즈: Top15 행 클릭 시 자동 트리거
    auto_go = bool(st.session_state.pop("auto_analyze", False))

    # 새 _show 방식: selected_stock_code → search_query 자동 주입
    _clicked_code = st.session_state.pop("selected_stock_code", None)
    if _clicked_code:
        query   = _clicked_code
        auto_go = True

    # ── 검색 → 선택 → 분석 ───────────────────────────────────────────────────
    if query:
        results = search_ticker(query, tickers_df)
        if not results:
            st.warning(f"'{query}' 검색 결과 없음 — 종목명 또는 6자리 코드를 확인하세요.")
            return

        if len(results) > 1 and not auto_go:
            opts = [f"{r['name']} ({r['code']}) [{r['market']}]" for r in results]
            sel_i = st.selectbox("종목 선택", range(len(opts)),
                                  format_func=lambda i: opts[i], key="sel_stock")
            selected = results[sel_i]
        else:
            selected = results[0]
            if not auto_go:
                st.success(f"✅ {selected['name']} ({selected['code']}) [{selected['market']}] 즉시 검색됨")

        if go or auto_go or len(results) == 1:
            ticker = selected["code"]
            name   = selected["name"]
            market = selected["market"]

            with st.spinner(f"{name}({ticker}) — 세력 역추적 파이프라인 가동 중…"):
                result = analyze_ticker(ticker, name, market)

            # ── 데이터 동기화 검증: analyze_ticker 4축 총점이 권위적 소스 ────────
            # (quick_score 캐시 총점 덮어쓰기 금지 — 뉴스/재무 완전 반영된 총점 보존)
            _cached_qs = st.session_state.get("scored_cache", {}).get(ticker)
            if _cached_qs is not None:
                result["pb_cached"]  = _cached_qs["pb_score"]
                result["inv_cached"] = _cached_qs["inv_score"]
                # total은 analyze_ticker의 완전한 4축 점수 그대로 사용

            # ① 현재가 Gold·Dark 카드
            ui_price_header(result)

            # ② 숨비 종합 진단 점수 — Plotly 속도계 게이지
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:18px;font-weight:700;margin:8px 0 2px;">'
                '숨비 종합 진단 점수</h3>',
                unsafe_allow_html=True,
            )
            ui_score_card(result)

            # ② V8.0 GOD MODE — 매크로·Smart Money·숏스퀴즈·Sentiment Velocity
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:17px;font-weight:700;'
                'letter-spacing:.06em;margin:10px 0 2px;">'
                '⚡ V8.0 God Mode — 기관급 초정밀 4대 엔진</h3>',
                unsafe_allow_html=True,
            )
            ui_macro_godmode_card(result)
            st.divider()

            # ③ 기업 정밀 브리핑 — ①섹터 ②저평가해설 ③모멘텀 3카드
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '숨비 기업 정밀 브리핑</h3>',
                unsafe_allow_html=True,
            )
            ui_auto_briefing(result, name, ticker)
            st.divider()

            # ④ 4주체 확정 수급표 (기관·외국인·개인·기타법인)
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '세력 수급 역추적 — 최근 5거래일 확정 데이터</h3>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="color:#D4AF37;font-weight:700;font-size:13px;'
                'letter-spacing:.08em;margin:0 0 8px;opacity:.9;">'
                '💰 수천조 가치의 세력 역추적 중 — 기관 · 외국인 · 개인 · 기타법인 4주체 확정 매집/매도 데이터'
                '</div>',
                unsafe_allow_html=True,
            )
            ui_investor_table(result["inv_data"])
            st.divider()

            # ⑤ 펀더멘털 & 가치 평가 (한글 용어)
            ui_fundamentals_card(result)

            # ⑥ 정밀 사업 분석 아코디언
            ui_moat_expander(name, ticker)

            # ⑦ 세력 동향 경보 (해당 시)
            if result["block_alert"]:
                st.divider()
                ui_block_alert(result["block_alert"])

            # ⑧ 차트 이동평균 지표
            st.divider()
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '기술적 이동평균 지표</h3>',
                unsafe_allow_html=True,
            )
            ui_ma_strip(result["pb"])

            # ⑨ 미반영 호재 뉴스 & 팩트체크
            st.markdown(
                '<h3 style="color:#D4AF37;font-size:16px;font-weight:600;margin:8px 0 2px;">'
                '미반영 호재 뉴스 & 팩트 분석</h3>',
                unsafe_allow_html=True,
            )
            ui_news(result["news_score"], result["news"])

    else:
        # 시작 화면
        _html_block("""
<style>
  .start-wrap {
    background:#12192b; border:1px solid #2a3550; border-radius:16px;
    padding:28px 32px; margin:16px 0;
  }
  .start-title {
    font-size:.72rem; font-weight:800; letter-spacing:.18em;
    color:#D4AF37; text-transform:uppercase; margin-bottom:16px;
  }
  .start-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  .start-card {
    background:#0d1526; border:1px solid #1e2a3a; border-radius:10px;
    padding:16px 18px;
  }
  .start-card-title {
    font-size:.7rem; color:#D4AF37; font-weight:800;
    letter-spacing:.1em; text-transform:uppercase; margin-bottom:8px;
  }
  .start-card-body { font-size:.85rem; color:#c0c8d8; line-height:1.6; }
  .start-code { color:#F5E882; font-weight:700; font-family:monospace; }
  .start-algo {
    background:linear-gradient(135deg,#0d1526,#12192b);
    border:1px solid #D4AF37; border-radius:10px;
    padding:16px 18px; margin-top:16px;
  }
  .start-algo-title {
    font-size:.7rem; color:#D4AF37; font-weight:800;
    letter-spacing:.14em; text-transform:uppercase; margin-bottom:8px;
  }
  .start-algo-body { font-size:.84rem; color:#c0c8d8; line-height:1.7; }
  .gold { color:#D4AF37; font-weight:700; }
</style>
<div class="start-wrap">
  <div class="start-title">🔍 단일 종목 정밀 해부 — 검색 가이드</div>
  <div class="start-grid">
    <div class="start-card">
      <div class="start-card-title">KOSPI 대형주 예시</div>
      <div class="start-card-body">
        <span class="start-code">005930</span> 또는 <span class="start-code">삼성전자</span><br>
        <span class="start-code">000660</span> 또는 <span class="start-code">SK하이닉스</span><br>
        <span class="start-code">042660</span> 또는 <span class="start-code">한화오션</span>
      </div>
    </div>
    <div class="start-card">
      <div class="start-card-title">KOSDAQ 성장주 예시</div>
      <div class="start-card-body">
        <span class="start-code">086520</span> 또는 <span class="start-code">에코프로</span><br>
        <span class="start-code">247540</span> 또는 <span class="start-code">에코프로비엠</span><br>
        <span class="start-code">439260</span> 또는 <span class="start-code">대한조선</span>
      </div>
    </div>
  </div>
  <div class="start-algo">
    <div class="start-algo-title">⚙️ 숨비 종합 진단 점수 — 자동 산출 알고리즘</div>
    <div class="start-algo-body">
      <span class="gold">세력 수급 역추적 (30점)</span> — 기관·외국인 5거래일 순매매 방향성 자동 감지<br>
      <span class="gold">공매도 잔고 분석 (20점)</span> — 외국인잔고율 변화 기반 쇼트 포지션 역추적<br>
      <span class="gold">정밀 눌림목 패턴 (30점)</span> — RSI·MA5·MA20·MA60 이동평균 정배열 자동 산출<br>
      <span class="gold">미반영 호재 뉴스 (20점)</span> — 42개 호재/악재 키워드 NLP 자동 분류<br>
      <br>
      종목명 또는 6자리 코드를 입력하고 <span class="gold">해부 시작</span>을 누르세요.
    </div>
  </div>
</div>
""")


if __name__ == "__main__":
    main()
