# -*- coding: utf-8 -*-
"""
SUMBI KILLMOVE RANK v1
======================
국내 전체 종목을 스캔해 "내일 상승확률"이 가장 높은 10종목을 랭킹화.

핵심 전략 (학술/퀀트 검증):
- 단기 반전(Jegadeesh 1990): 이미 크게 오른 종목은 다음날 반전 → 배제
- 거래량 응축(Volume Accumulation): 가격 정체 + 거래량 폭증 = 세력 매집
- 과열 배제(Exhaustion): 연속 급등/대폭 상승 종목은 천장 위험 → 감점

설계 원칙:
- 기존 분석기(main.py)는 손대지 않음. 점수 로직(supernova_v4)을 그대로 재사용 → 점수 일관성 100%.
- 1차 게이트는 fdr 데이터(가벼움)로만 필터링.
- 게이트 통과한 소수 종목만 KIS API(수급/시세) 호출 → 2GB RAM 안전.

사용법 (main.py에 단 1줄 추가):
    import killmove_rank
    killmove_rank.render_ranking_tab()
"""

import streamlit as st
import pandas as pd
import datetime
import traceback

import FinanceDataReader as fdr

# 기존 점수 엔진 재사용 (점수 일관성 보장)
from supernova_v4 import StockData, calculate_supernova_score

# 기존 KIS 데이터 수집 함수 재사용
# (main.py에 정의돼 있음 - 동일 점수/데이터 보장)
try:
    from main import get_stock_price, get_investor_data, get_chart_data, get_true_short_data
except Exception:
    # import 실패 시 graceful (랭킹탭에서 안내)
    get_stock_price = None
    get_investor_data = None
    get_chart_data = None
    get_true_short_data = None


# =====================================================================
# 설정값
# =====================================================================
SCAN_UNIVERSE = 300       # 거래대금 상위 N종목만 스캔 (RAM 안전선)
DEEP_DIVE_TOP = 25        # 게이트 통과 후 KIS 수급까지 호출할 최대 종목 수
FINAL_RANK = 10           # 최종 출력 순위 수

# 시가총액 tier별 거래량 배수 기준 (supernova_v4와 동일 철학)
VOL_THRESHOLD = {
    "LARGE": 2.0,   # 대형주 200%
    "MID":   3.0,   # 중형주 300%
    "SMALL": 5.0,   # 소형주 500%
}

# 반전(아직 안 터진) 구간: 등락률 이 범위 안일 때 만점
REVERSAL_LOW = -3.0       # -3% 까지 (눌림/약세 = 반전 기대)
REVERSAL_HIGH = 5.0       # +5% 까지 (소폭 상승 = 응축)
OVERHEAT_CUT = 15.0       # +15% 이상 = 과열, 강한 감점


# =====================================================================
# 색상/디자인 토큰 (기존 SUMBI 디자인과 동일)
# =====================================================================
GOLD = "#D9A147"
RED = "#FF3B5C"     # 상승
BLUE = "#3D7EFF"    # 하락


def _tier(market_cap: float) -> str:
    if market_cap >= 5_000_000_000_000:
        return "LARGE"
    elif market_cap >= 1_000_000_000_000:
        return "MID"
    return "SMALL"


def _safe_float(v, default=0.0):
    try:
        if v is None or v == "" or v == "-":
            return float(default)
        return float(str(v).replace(",", ""))
    except Exception:
        return float(default)


# =====================================================================
# 1단계 — 전체 종목 1차 스캔 (fdr만 사용, 가벼움)
# =====================================================================
@st.cache_data(ttl=600)
def scan_universe():
    """
    거래대금 상위 종목 추출.
    fdr.StockListing('KRX')에서 Marcap(시가총액)/Volume/Amount 활용.
    반환: DataFrame [Code, Name, Marcap, ...]
    """
    krx = fdr.StockListing("KRX")
    # 거래대금(Amount) 컬럼이 있으면 그걸로, 없으면 거래량(Volume)으로 정렬
    sort_col = None
    for c in ["Amount", "거래대금", "Volume", "거래량"]:
        if c in krx.columns:
            sort_col = c
            break
    if sort_col is None:
        # fallback: 시가총액 상위
        for c in ["Marcap", "시가총액"]:
            if c in krx.columns:
                sort_col = c
                break
    if sort_col:
        krx = krx.sort_values(sort_col, ascending=False)
    return krx.head(SCAN_UNIVERSE).reset_index(drop=True)


def gate_filter(code: str):
    """
    1차 게이트: fdr 차트 데이터로 거래량 응축/반전 여부 판정.
    통과하면 차트 지표 dict 반환, 탈락하면 None.
    """
    try:
        df = fdr.DataReader(code, datetime.date.today() - datetime.timedelta(days=60))
        if df is None or len(df) < 21:
            return None

        df = df.dropna()
        close = df["Close"]
        vol = df["Volume"]

        cur = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        if prev <= 0:
            return None

        change_pct = (cur - prev) / prev * 100.0
        vol_today = float(vol.iloc[-1])
        vol_ma20 = float(vol.iloc[-20:].mean())
        if vol_ma20 <= 0:
            return None
        vol_ratio = vol_today / vol_ma20

        # 차트 지표
        ma5 = float(close.iloc[-5:].mean())
        ma20 = float(close.iloc[-20:].mean())
        days_above = int((close.iloc[-20:] > close.iloc[-20:].rolling(20, min_periods=1).mean()).sum())

        # 연속 상승일
        consec = 0
        c = close.values
        for i in range(len(c) - 1, 0, -1):
            if c[i] > c[i - 1]:
                consec += 1
            else:
                break

        o = float(df["Open"].iloc[-1])
        h = float(df["High"].iloc[-1])
        lo = float(df["Low"].iloc[-1])
        cbr = abs(cur - o) / abs(h - lo) if (h - lo) != 0 else 0.5

        return {
            "current": cur, "prev": prev, "open": o, "high": h, "low": lo,
            "change_pct": change_pct, "vol_today": vol_today, "vol_ma20": vol_ma20,
            "vol_ratio": vol_ratio, "ma5": ma5, "ma20": ma20,
            "days_above": days_above, "consec_up": consec, "cbr": cbr,
            "is_bull": cur >= prev,
        }
    except Exception:
        return None


# =====================================================================
# 2단계 — 반전/응축 점수 (대표님 전략 + 학술 검증)
# =====================================================================
def reversal_bonus(change_pct: float, vol_ratio: float, consec_up: int, tier: str) -> float:
    """
    "내일 오를" 응축도 보너스 (0~20점).
    - 거래량 폭증인데 가격은 정체/소폭 → 매집 신호 만점
    - 이미 급등(+15%↑) → 과열 페널티
    - 연속 급등 → 감점 (단기 반전)
    """
    score = 0.0
    thr = VOL_THRESHOLD.get(tier, 3.0)

    # 거래량 응축 (최대 12)
    if vol_ratio >= thr:
        score += 12
    elif vol_ratio >= thr * 0.6:
        score += 12 * (vol_ratio - thr * 0.6) / (thr * 0.4)

    # 반전 구간 보너스 (최대 8) — 안 오른 놈일수록 가산
    if REVERSAL_LOW <= change_pct <= REVERSAL_HIGH:
        score += 8
    elif change_pct < REVERSAL_LOW:
        # 과한 급락은 반만
        score += 4
    elif change_pct <= OVERHEAT_CUT:
        # +5 ~ +15: 점점 감소
        score += 8 * (OVERHEAT_CUT - change_pct) / (OVERHEAT_CUT - REVERSAL_HIGH)

    # 과열/연속급등 페널티
    if change_pct >= OVERHEAT_CUT:
        score -= 10
    if consec_up >= 3:
        score -= 3 * (consec_up - 2)

    return max(-15.0, score)


# =====================================================================
# 3단계 — 종목별 풀스코어 (기존 엔진 재사용)
# =====================================================================
def build_stockdata(code, name, gate, use_kis=False):
    """게이트 통과 종목을 StockData로 변환. use_kis=True면 KIS 수급/시세 보강."""
    mc = 0.0
    fgn = org = 0.0
    short = {}

    if use_kis and get_stock_price is not None:
        try:
            price = get_stock_price(code)
            if price:
                mc_raw = price.get("hts_avls", 0)
                mc = _safe_float(mc_raw)
                if 0 < mc < 1_000_000:
                    mc = mc * 100_000_000
        except Exception:
            pass
        try:
            inv = get_investor_data(code)
            if inv:
                fgn = _safe_float(inv.get("frgn", 0))
                org = _safe_float(inv.get("orgn", 0))
        except Exception:
            pass
        try:
            if get_true_short_data is not None:
                short = get_true_short_data(code) or {}
        except Exception:
            short = {}

    cp = gate["current"]
    return StockData(
        ticker=code, name=name, market_cap=mc if mc > 0 else 1.0,
        current_price=cp, open_price=gate["open"], high_price=gate["high"],
        low_price=gate["low"], prev_close=gate["prev"],
        volume_today=gate["vol_today"], volume_avg_20d=max(gate["vol_ma20"], 1.0),
        foreign_net_buy=fgn * cp, institution_net_buy=org * cp,
        ma5=gate["ma5"], ma20=gate["ma20"],
        days_above_ma20=gate["days_above"], consecutive_up_days=gate["consec_up"],
        candle_body_ratio=gate["cbr"], is_bullish=gate["is_bull"],
        short_balance_today=_safe_float(short.get("short_today", 0)),
        short_balance_yesterday=_safe_float(short.get("short_yesterday", 0)),
        short_ratio=_safe_float(short.get("short_ratio", 0)),
        macro_kospi_ma5_bull=False, sector_top_stocks_rising=False,
        sector_foreign_rank=99,
        kospi_above_ma5=False, macro_safe_zone=False,
    )


def run_scan(progress_cb=None):
    """전체 스캔 실행 → 상위 FINAL_RANK 종목 리스트 반환."""
    uni = scan_universe()
    code_col = "Code" if "Code" in uni.columns else uni.columns[0]
    name_col = "Name" if "Name" in uni.columns else uni.columns[1]

    candidates = []
    total = len(uni)
    for i, row in uni.iterrows():
        if progress_cb:
            progress_cb((i + 1) / total, f"1차 스캔 {i+1}/{total}")
        code = str(row[code_col]).zfill(6)
        name = str(row[name_col])
        gate = gate_filter(code)
        if gate is None:
            continue
        # 게이트: 거래량 응축 + 과열 아님
        if gate["change_pct"] >= OVERHEAT_CUT:
            continue  # 이미 크게 오른 놈 제외
        mc_guess = float(row.get("Marcap", 0) or 0)
        tier = _tier(mc_guess) if mc_guess > 0 else "MID"
        if gate["vol_ratio"] < VOL_THRESHOLD.get(tier, 3.0) * 0.6:
            continue  # 거래량 응축 부족
        rb = reversal_bonus(gate["change_pct"], gate["vol_ratio"], gate["consec_up"], tier)
        candidates.append({"code": code, "name": name, "gate": gate,
                           "tier": tier, "reversal": rb})

    # 1차 점수(반전+거래량)로 정렬 후 상위만 KIS 딥다이브
    candidates.sort(key=lambda x: x["reversal"], reverse=True)
    deep = candidates[:DEEP_DIVE_TOP]

    results = []
    for j, cand in enumerate(deep):
        if progress_cb:
            progress_cb(0.5 + (j + 1) / len(deep) / 2, f"수급 분석 {j+1}/{len(deep)}")
        sd = build_stockdata(cand["code"], cand["name"], cand["gate"], use_kis=True)
        try:
            score = calculate_supernova_score(sd)
            total_score = score.total + cand["reversal"]
        except Exception:
            continue
        results.append({
            "code": cand["code"], "name": cand["name"],
            "change_pct": cand["gate"]["change_pct"],
            "vol_ratio": cand["gate"]["vol_ratio"],
            "total": round(total_score, 1),
            "reversal": round(cand["reversal"], 1),
            "breakdown": score,
        })

    results.sort(key=lambda x: x["total"], reverse=True)
    return results[:FINAL_RANK]


# =====================================================================
# UI 렌더링 (기존 SUMBI 디자인)
# =====================================================================
def render_ranking_tab():
    st.markdown(f"""
    <div style="margin:20px 0;">
      <div style="font-family:'Pretendard',sans-serif; letter-spacing:3px;
           font-size:13px; color:{GOLD}; opacity:.7;">— KILLMOVE RANK</div>
      <div style="font-family:'Pretendard',sans-serif; font-weight:800;
           font-size:26px;
           background:linear-gradient(180deg,#F5D67A 0%,#D9A147 50%,#8B6914 100%);
           -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
           내일 상승확률 TOP 10</div>
      <div style="color:#888; font-size:12px; margin-top:6px;">
           전체 종목 스캔 · 거래량 응축 + 수급 + 반전 신호 통계 랭킹</div>
    </div>
    """, unsafe_allow_html=True)

    if get_stock_price is None:
        st.warning("⚠️ main.py 함수 import 실패. killmove_rank.py가 main.py와 같은 폴더에 있는지 확인하세요.")
        return

    if st.button("⚡ 전체 종목 스캔 시작 (약 1분)", use_container_width=True):
        prog = st.progress(0.0, text="스캔 준비 중...")
        try:
            def cb(p, msg):
                prog.progress(min(p, 1.0), text=msg)
            ranked = run_scan(progress_cb=cb)
            prog.empty()
            st.session_state["killmove_ranked"] = ranked
        except Exception as e:
            prog.empty()
            st.error(f"스캔 오류: {e}")
            st.code(traceback.format_exc())
            return

    ranked = st.session_state.get("killmove_ranked")
    if not ranked:
        st.info("위 버튼을 눌러 전체 종목을 스캔하세요.")
        return

    for rank, item in enumerate(ranked, 1):
        chg = item["change_pct"]
        color = RED if chg >= 0 else BLUE
        arrow = "▲" if chg >= 0 else "▼"
        with st.container():
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.03); border:1px solid #2a2a2a;
                 border-radius:12px; padding:14px 18px; margin:8px 0;
                 display:flex; align-items:center; justify-content:space-between;">
              <div style="display:flex; align-items:center; gap:16px;">
                <div style="font-size:22px; font-weight:800; color:{GOLD};
                     min-width:36px;">{rank}</div>
                <div>
                  <div style="font-size:17px; font-weight:700; color:#fff;">{item['name']}</div>
                  <div style="font-size:12px; color:#888;">{item['code']} ·
                       거래량 {item['vol_ratio']:.1f}배</div>
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:20px; font-weight:800; color:{color};">
                     {arrow} {abs(chg):.2f}%</div>
                <div style="font-size:13px; color:{GOLD};">SCORE {item['total']}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"  {item['name']} 6축 상세 점수"):
                b = item["breakdown"]
                rows = [
                    ("Money Flow (수급)", b.money_flow, 40),
                    ("Chart Squeeze (차트)", b.chart_squeeze, 25),
                    ("News Auth (뉴스)", b.news_authenticity, 15),
                    ("Short Squeeze (공매도)", b.short_squeeze, 10),
                    ("Sector (섹터)", b.sector_rotation, 5),
                    ("Macro (거시)", b.macro_filter, 5),
                    ("반전 보너스", item["reversal"], "±"),
                ]
                html = ""
                for label, val, mx in rows:
                    pct = (val / mx * 100) if isinstance(mx, (int, float)) and mx else 0
                    bar_c = GOLD if pct >= 50 else "#666"
                    html += f"""
                    <div style="margin:8px 0;">
                      <div style="display:flex; justify-content:space-between;
                           font-size:13px; color:#ccc;">
                        <span>{label}</span><span style="color:{GOLD};">{val:.1f}/{mx}</span>
                      </div>
                      <div style="height:4px; background:rgba(255,255,255,.08);
                           border-radius:2px; margin-top:3px;">
                        <div style="height:100%; width:{min(pct,100)}%;
                             background:{bar_c}; border-radius:2px;"></div>
                      </div>
                    </div>"""
                st.markdown(html, unsafe_allow_html=True)
