"""
SUMBI V3 SCORER
8개 항목 / 100점 만점
"""
import numpy as np
import pandas as pd


def calc_chart_score(df_chart):
    """차트·기술적 분석 (25점)"""
    if df_chart is None or len(df_chart) < 60:
        return 0, {}
    
    score = 0
    details = {}
    close = df_chart['Close']
    high = df_chart['High']
    low = df_chart['Low']
    vol = df_chart['Volume']
    
    # A. 추세 분석 (8점)
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else ma20
    ma120 = close.rolling(120).mean().iloc[-1] if len(close) >= 120 else ma60
    cur = close.iloc[-1]
    
    trend_score = 0
    if ma5 > ma20 > ma60: trend_score += 3
    if ma5 > close.rolling(5).mean().iloc[-5]: trend_score += 2
    if cur > ma120: trend_score += 2
    if cur > ma60 * 1.02: trend_score += 1
    score += min(trend_score, 8)
    details['추세'] = min(trend_score, 8)
    
    # B. 캔들 패턴 (6점)
    candle_score = 3  # 기본값
    o, c, h, l = df_chart['Open'].iloc[-1], cur, high.iloc[-1], low.iloc[-1]
    body = abs(c - o)
    upper = h - max(c, o)
    lower = min(c, o) - l
    
    # 망치형
    if lower > body * 2 and upper < body * 0.5 and c > o:
        candle_score += 2
    # 상승장악형
    if len(df_chart) >= 2:
        prev_o, prev_c = df_chart['Open'].iloc[-2], df_chart['Close'].iloc[-2]
        if prev_c < prev_o and c > o and c > prev_o and o < prev_c:
            candle_score += 2
    # 3연속 양봉
    if len(df_chart) >= 3:
        last3 = df_chart.iloc[-3:]
        if all(last3['Close'].values > last3['Open'].values):
            candle_score += 1
    score += min(candle_score, 6)
    details['캔들'] = min(candle_score, 6)
    
    # C. 보조지표 (6점)
    indi_score = 0
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    cur_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    if 30 <= cur_rsi <= 50: indi_score += 2
    elif cur_rsi > 70: indi_score -= 1
    
    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    if len(macd) >= 2 and macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
        indi_score += 2
    
    # 볼린저밴드
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_lower = bb_mid - 2 * bb_std
    if cur > bb_lower.iloc[-1] and close.iloc[-2] <= bb_lower.iloc[-2] if len(close) >= 2 else False:
        indi_score += 2
    
    score += max(0, min(indi_score, 6))
    details['보조지표'] = max(0, min(indi_score, 6))
    details['rsi'] = round(cur_rsi, 1)
    
    # D. 거래량 (3점)
    vol_score = 0
    vol_ma = vol.rolling(20).mean()
    vol_z = (vol.iloc[-1] - vol_ma.iloc[-1]) / vol.rolling(20).std().iloc[-1] if vol.rolling(20).std().iloc[-1] > 0 else 0
    if vol_z > 2: vol_score += 2
    elif vol_z > 1: vol_score += 1
    if len(vol) >= 5 and vol.rolling(5).mean().iloc[-1] > vol.rolling(20).mean().iloc[-1]:
        vol_score += 1
    score += min(vol_score, 3)
    details['거래량'] = min(vol_score, 3)
    
    # E. 지지·저항 (2점)
    sr_score = 0
    recent_low = low.rolling(20).min().iloc[-1]
    if cur < recent_low * 1.03:  # 지지선 근접
        sr_score += 1
    high_30 = high.rolling(60).max().iloc[-1] if len(high) >= 60 else high.max()
    low_30 = low.rolling(60).min().iloc[-1] if len(low) >= 60 else low.min()
    fib_382 = high_30 - (high_30 - low_30) * 0.382
    if abs(cur - fib_382) / fib_382 < 0.02:
        sr_score += 1
    score += sr_score
    details['지지저항'] = sr_score
    
    return min(score, 25), details


def calc_flow_score(investor):
    """메이저 수급 (25점)"""
    if not investor:
        return 0, {}
    
    score = 0
    details = {}
    inst = investor.get('orgn', investor.get('institution', 0))
    foreign = investor.get('frgn', investor.get('foreign', 0))
    indi = investor.get('prsn', investor.get('individual', 0))
    
    # 기관 매수 (10점)
    if inst > 100000: score += 10
    elif inst > 50000: score += 7
    elif inst > 10000: score += 5
    elif inst > 0: score += 3
    elif inst < -50000: score -= 3
    details['기관'] = inst
    
    # 외인 매수 (10점)
    if foreign > 100000: score += 10
    elif foreign > 50000: score += 7
    elif foreign > 10000: score += 5
    elif foreign > 0: score += 3
    elif foreign < -100000: score -= 5
    details['외인'] = foreign
    
    # 쌍끌이 보너스 (5점)
    if inst > 0 and foreign > 0:
        score += 5
        details['쌍끌이'] = True
    
    return max(0, min(score, 25)), details


def calc_fundamental_score(info):
    """기업 펀더멘털 (13점)"""
    if not info:
        return 6, {}  # 데이터 없으면 중립
    
    score = 0
    details = {}
    per = info.get('per')
    pbr = info.get('pbr')
    roe = info.get('roe')
    op_margin = info.get('operating_margin')
    
    # PER (4점)
    if per:
        if 0 < per < 10: score += 4
        elif 10 <= per < 15: score += 3
        elif 15 <= per < 25: score += 2
        elif per >= 25: score += 0
    
    # PBR (3점)
    if pbr:
        if 0 < pbr < 1: score += 3
        elif 1 <= pbr < 2: score += 2
        elif 2 <= pbr < 3: score += 1
    
    # ROE (3점)
    if roe:
        if roe > 20: score += 3
        elif roe > 15: score += 2
        elif roe > 10: score += 1
    
    # 영업이익률 (3점)
    if op_margin:
        if op_margin > 20: score += 3
        elif op_margin > 10: score += 2
        elif op_margin > 5: score += 1
    
    details = {'per': per, 'pbr': pbr, 'roe': roe}
    return min(score, 13), details


def calc_news_score(news_list):
    """뉴스 모멘텀 (10점)"""
    if not news_list:
        return 5, {}
    
    score = 5  # 기본 중립
    positive_keywords = ['수주', '계약', '최대', '신기록', '돌파', '상한가', '급등', '호재', '성장', '확대', '체결']
    negative_keywords = ['하락', '감소', '손실', '부진', '리스크', '경고', '제재', '논란']
    
    pos_count = 0
    neg_count = 0
    for news in news_list[:10]:
        title = news.get('title', '')
        for kw in positive_keywords:
            if kw in title:
                pos_count += 1
                break
        for kw in negative_keywords:
            if kw in title:
                neg_count += 1
                break
    
    score += min(pos_count, 4)
    score -= min(neg_count, 3)
    
    return max(0, min(score, 10)), {'긍정': pos_count, '부정': neg_count}


def calc_short_score(short_data):
    """공매도 신호 (8점)"""
    if not short_data:
        return 4, {}  # 중립
    
    score = 4
    short_ratio = short_data.get('short_ratio', 0)
    loan_balance_change = short_data.get('loan_change', 0)
    
    # 공매도잔고비율
    if short_ratio < 2: score += 3
    elif short_ratio < 5: score += 1
    elif short_ratio > 10: score -= 3
    elif short_ratio > 7: score -= 1
    
    # 대차잔고 감소 = 숏커버링
    if loan_balance_change < -10: score += 1
    
    return max(0, min(score, 8)), {'공매도비율': short_ratio}


def calc_macro_score(macro):
    """매크로 환경 (7점)"""
    if not macro:
        return 4, {}
    
    score = 4
    wti = macro.get('wti')
    krw = macro.get('krw')
    dxy = macro.get('dxy')
    tnx = macro.get('tnx')
    
    if krw:
        if krw < 1300: score += 1
        elif krw > 1450: score -= 2
        elif krw > 1380: score -= 1
    if dxy:
        if dxy < 98: score += 1
        elif dxy > 107: score -= 1
    if tnx:
        if tnx < 3.5: score += 1
        elif tnx > 4.8: score -= 1
    if wti:
        if 60 < wti < 80: score += 0
        elif wti > 95: score -= 1
    
    return max(0, min(score, 7)), {}


def calc_sector_score(sector_data):
    """섹터·테마 강도 (7점)"""
    if not sector_data:
        return 4, {}
    
    score = 4
    relative_strength = sector_data.get('relative_strength', 0)
    foreign_sector_flow = sector_data.get('foreign_flow', 0)
    
    if relative_strength > 0.05: score += 2
    elif relative_strength > 0.02: score += 1
    elif relative_strength < -0.05: score -= 2
    
    if foreign_sector_flow > 1000: score += 1
    
    return max(0, min(score, 7)), {}


def calc_broker_score(broker_data):
    """거래원 분석 (5점)"""
    if not broker_data:
        return 3, {}
    
    score = 3
    foreign_buy_brokers = broker_data.get('foreign_buy', 0)
    top_buy_consensus = broker_data.get('top_buy_consensus', 0)
    
    # 외국계 매수창구 상위
    if foreign_buy_brokers >= 3: score += 2
    elif foreign_buy_brokers >= 2: score += 1
    
    # 상위 5개 창구 중 매수 우위
    if top_buy_consensus >= 4: score += 1
    
    return max(0, min(score, 5)), {}


def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None):
    """SUMBI V3 종합 점수 (100점)"""
    flow, flow_d = calc_flow_score(investor)
    chart, chart_d = calc_chart_score(df_chart)
    fund, fund_d = calc_fundamental_score(info)
    news, news_d = calc_news_score(news_list)
    short, short_d = calc_short_score(short_data)
    macro_s, macro_d = calc_macro_score(macro)
    sector, sector_d = calc_sector_score(sector_data)
    broker, broker_d = calc_broker_score(broker_data)
    
    total = flow + chart + fund + news + short + macro_s + sector + broker
    
    # 등급
    if total >= 95: grade, glabel = "S+", "DIAMOND 강력매수"
    elif total >= 85: grade, glabel = "S", "PLATINUM 매수"
    elif total >= 75: grade, glabel = "A+", "GOLD 매수권고"
    elif total >= 65: grade, glabel = "A", "SILVER 분할매수"
    elif total >= 50: grade, glabel = "B", "BRONZE 관망"
    elif total >= 35: grade, glabel = "C", "CAUTION 주의"
    else: grade, glabel = "D", "DANGER 회피"
    
    return {
        'total': total,
        'grade': grade,
        'grade_label': glabel,
        'breakdown': {
            'flow': (flow, 25, flow_d),
            'chart': (chart, 25, chart_d),
            'fundamental': (fund, 13, fund_d),
            'news': (news, 10, news_d),
            'short': (short, 8, short_d),
            'macro': (macro_s, 7, macro_d),
            'sector': (sector, 7, sector_d),
            'broker': (broker, 5, broker_d),
        }
    }
