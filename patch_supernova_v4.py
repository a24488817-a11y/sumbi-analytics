#!/usr/bin/env python3
"""
SUMBI Analytics - SUPER-NOVA V4 통합 패치
실행: python3 patch_supernova_v4.py

기존 V3 점수제(8개 항목)를 V4(6개 항목)로 교체
"""

import re
import shutil
from pathlib import Path

MAIN_PY = Path("/home/ubuntu/main.py")
SCORER = Path("/home/ubuntu/supernova_v4.py")

if not MAIN_PY.exists():
    print(f"❌ {MAIN_PY} 없음")
    exit(1)

# 백업
shutil.copy(MAIN_PY, MAIN_PY.with_suffix(".py.backup_v3"))
print(f"✅ 백업: {MAIN_PY}.backup_v3")

src = MAIN_PY.read_text(encoding="utf-8")

# ═══════════════════════════════════════════════════════════════
# [1] import 추가
# ═══════════════════════════════════════════════════════════════
IMPORT_LINE = """
# ── SUPER-NOVA V4 통합 ──────────────────────
from supernova_v4 import (
    StockData, ScoreBreakdown,
    calculate_supernova_score,
    is_final_pick,
    generate_score_report,
    get_market_cap_tier,
)
# ──────────────────────────────────────────
"""

if "from supernova_v4 import" not in src:
    # streamlit import 다음에 추가
    m = re.search(r'^import streamlit[^\n]*\n', src, re.MULTILINE)
    if m:
        src = src[:m.end()] + IMPORT_LINE + src[m.end():]
        print("✅ [1] supernova_v4 import 추가 완료")
    else:
        # 그냥 맨 위에 추가
        src = IMPORT_LINE + src
        print("✅ [1] supernova_v4 import 맨 위에 추가")
else:
    print("⚠️  [1] 이미 import됨")

# ═══════════════════════════════════════════════════════════════
# [2] V4 점수 산출 헬퍼 함수 추가
# ═══════════════════════════════════════════════════════════════
HELPER_FUNC = '''
def build_stockdata_from_kis(ticker: str, name: str, raw: dict) -> StockData:
    """KIS API 응답을 StockData로 변환"""
    from datetime import datetime
    
    return StockData(
        ticker=ticker,
        name=name,
        market_cap=float(raw.get("market_cap", 0)),
        current_price=float(raw.get("current_price", 0)),
        open_price=float(raw.get("open", 0)),
        high_price=float(raw.get("high", 0)),
        low_price=float(raw.get("low", 0)),
        prev_close=float(raw.get("prev_close", 0)),
        volume_today=float(raw.get("trading_value", 0)),
        volume_avg_20d=float(raw.get("avg_value_20d", 1)),
        foreign_net_buy=float(raw.get("foreign_net", 0)),
        institution_net_buy=float(raw.get("inst_net", 0)),
        ma5=float(raw.get("ma5", 0)),
        ma20=float(raw.get("ma20", 0)),
        days_above_ma20=int(raw.get("days_above_ma20", 0)),
        consecutive_up_days=int(raw.get("up_days", 0)),
        candle_body_ratio=float(raw.get("body_ratio", 0)),
        is_bullish=bool(raw.get("is_bullish", False)),
        short_balance_today=float(raw.get("short_today", 0)),
        short_balance_yesterday=float(raw.get("short_yesterday", 0)),
        short_ratio=float(raw.get("short_ratio", 0)),
        news_time=raw.get("news_time"),
        news_has_concrete_terms=bool(raw.get("news_concrete", False)),
        news_has_speculation=bool(raw.get("news_speculation", False)),
        news_is_policy_confirmed=bool(raw.get("news_policy", False)),
        sector_top_stocks_rising=bool(raw.get("sector_rising", False)),
        sector_foreign_rank=int(raw.get("sector_rank", 99)),
        kospi_above_ma5=bool(raw.get("kospi_safe", True)),
        macro_safe_zone=bool(raw.get("macro_safe", True)),
    )


@st.cache_data(ttl=60)
def get_supernova_score(ticker: str, name: str, raw_data: dict) -> dict:
    """캐싱된 V4 점수 산출 (60초 캐시)"""
    stock_data = build_stockdata_from_kis(ticker, name, raw_data)
    score = calculate_supernova_score(stock_data)
    
    grade, color, action = score.grade
    
    return {
        "total": round(score.total, 1),
        "grade": grade,
        "color": color,
        "action": action,
        "accuracy": score.expected_accuracy,
        "breakdown": {
            "money_flow": round(score.money_flow, 1),
            "chart_squeeze": round(score.chart_squeeze, 1),
            "news_authenticity": round(score.news_authenticity, 1),
            "short_squeeze": round(score.short_squeeze, 1),
            "sector_rotation": round(score.sector_rotation, 1),
            "macro_filter": round(score.macro_filter, 1),
            "bonus": round(score.bonus_short_cover, 1),
        },
    }


def render_supernova_panel(ticker: str, name: str, raw_data: dict):
    """SUPER-NOVA V4 점수판 렌더링"""
    result = get_supernova_score(ticker, name, raw_data)
    
    st.markdown(f"### ⚡ SUMBI SUPER-NOVA V4")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.metric("종합 점수", f"{result['total']}/100")
    with col2:
        st.markdown(f"### {result['grade']}")
        st.caption(result['action'])
    with col3:
        st.metric("예상 적중률", result['accuracy'])
    
    st.markdown("---")
    st.markdown("#### 📊 6대 핵심 지표")
    
    b = result['breakdown']
    
    # 진행 바로 표시
    items = [
        ("① 수급 가속도", b['money_flow'], 40),
        ("② 차트 응축·돌파", b['chart_squeeze'], 25),
        ("③ 뉴스 진위", b['news_authenticity'], 15),
        ("④ 공매도 신호", b['short_squeeze'], 10),
        ("⑤ 섹터 순환", b['sector_rotation'], 5),
        ("⑥ 거시 필터", b['macro_filter'], 5),
    ]
    
    for label, val, max_val in items:
        pct = val / max_val if max_val > 0 else 0
        st.progress(min(1.0, pct), text=f"{label}: {val}/{max_val}점")
    
    if b['bonus'] > 0:
        st.success(f"🎯 숏커버 보너스 +{b['bonus']}점 적용!")

'''

if "def build_stockdata_from_kis" not in src:
    # 첫 번째 @st.cache_data 앞에 삽입
    m = re.search(r'@st\.cache_data', src)
    if m:
        src = src[:m.start()] + HELPER_FUNC + "\n" + src[m.start():]
        print("✅ [2] V4 헬퍼 함수 추가 완료")
    else:
        # streamlit import 다음
        m = re.search(r'^import streamlit[^\n]*\n', src, re.MULTILINE)
        if m:
            insert_pos = src.find("\n\n", m.end()) + 2
            src = src[:insert_pos] + HELPER_FUNC + src[insert_pos:]
            print("✅ [2] V4 헬퍼 함수 추가 완료")
else:
    print("⚠️  [2] 이미 추가됨")

# ═══════════════════════════════════════════════════════════════
# 저장
# ═══════════════════════════════════════════════════════════════
MAIN_PY.write_text(src, encoding="utf-8")
print(f"\n✅ main.py 패치 완료")
print(f"\n다음 단계:")
print(f"  1. supernova_v4.py를 /home/ubuntu/에 업로드")
print(f"  2. sudo systemctl restart sumbi")
print(f"  3. 브라우저에서 확인: http://43.202.40.117:8501")
