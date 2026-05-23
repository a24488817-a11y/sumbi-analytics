
python3 /home/ubuntu/add_v3_ui2.py
python3 -m py_compile ~/main.py && echo "문법 OK!"
pkill -f "streamlit run" && sleep 2 && cd ~ && nohup streamlit run main.py --server.port 8501 > stream_run.log 2>&1 &
sleep 10 && tail -5 ~/stream_run.log
pkill -f "streamlit run" && sleep 2 && cd ~ && nohup streamlit run main.py --server.port 8501 > stream_run.log 2>&1 &
grep -rn "def calc_sumbi_v3" ~/
grep -n "calc_sumbi" ~/main.py
grep -n "^def " ~/main.py
tail -50 ~/stream_run.log
ls -la ~/
wc -l ~/main.py && grep -n "^def \|^class \|^import \|^from " ~/main.py
grep -n "def calc_sumbi_v3" ~/v3_scorer.py
head -5 ~/v3_scorer.py
grep -n "def calc_sumbi_v3" ~/connect_v3.py ~/v3_scorer.py
sed -i 's/^import numpy as np$/import numpy as np\nfrom v3_scorer import calc_sumbi_v3/' ~/main.py
grep -n "from v3_scorer" ~/main.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f "streamlit run" && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
cat >> ~/main.py << 'EOF'

# ── Mock 데이터 함수 (V3용) ──────────────────
def get_short_data_mock():
    return {}

def get_sector_data_mock():
    return {}

def get_broker_data_mock():
    return {}
EOF

python3 -m py_compile ~/main.py && echo "OK"
pkill -f "streamlit run" && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
grep -n "mock()" ~/main.py
pkill -f streamlit && sleep 3 && find ~/. -name "*.pyc" -delete && find ~/. -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
grep -n "def get_short_data_mock\|def get_sector_data_mock\|def get_broker_data_mock" ~/main.py
# 1. 맨 끝에 추가된 mock 함수 3개 삭제 (마지막 10줄)
head -n -10 ~/main.py > /tmp/main_tmp.py && mv /tmp/main_tmp.py ~/main.py
# 2. 510번 줄 앞에 삽입
sed -i '510i\
def get_short_data_mock(): return {}\
def get_sector_data_mock(): return {}\
def get_broker_data_mock(): return {}\
' ~/main.py
# 3. 확인
grep -n "def get_short_data_mock\|def get_sector_data_mock\|def get_broker_data_mock" ~/main.py
# 4. 컴파일
python3 -m py_compile ~/main.py && echo "OK"
# 5. 재시작
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
sed -n '307,400p' ~/v3_scorer.py
grep -n "def.*investor\|def.*flow\|def.*short\|def.*sector\|def.*broker\|get_investor" ~/main.py
grep -n "investor_data\|short_data\|sector_data\|broker_data" ~/main.py | head -20
# 1. calc_flow_score가 investor에서 뭘 기대하는지
grep -n "def calc_flow_score" ~/v3_scorer.py
sed -n '1,100p' ~/v3_scorer.py
# 2. info가 뭔지
grep -n "info\s*=" ~/main.py | head -20
grep -n "def calc_flow_score\|def calc_fundamental_score\|def calc_short_score\|def calc_sector_score\|def calc_broker_score" ~/v3_scorer.py
sed -n '1,60p' ~/v3_scorer.py
grep -n "def get_investor_data" ~/main.py
sed -n '281,312p' ~/main.py
sed -n '117,220p' ~/v3_scorer.py
sed -n '117,155p' ~/v3_scorer.py
# API 실제 응답 테스트
python3 -c "
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_token, get_investor_data
token = get_token()
print('토큰:', token[:20] if token else 'None')
result = get_investor_data('042660')
print('수급데이터:', result)
"
# get_investor_data 캐시 데코레이터 확인
grep -n "cache\|@st" ~/main.py | head -20
# 506번 라인 주변 흐름 확인
sed -n '495,525p' ~/main.py
# 1. 캐시 완전 삭제
rm -rf ~/.streamlit/cache 2>/dev/null; find /tmp -name "*.cache" -delete 2>/dev/null
# 2. get_investor_data에서 st.error 대신 print로 변경 (에러 확인용)
sed -n '281,315p' ~/main.py
sed -i 's/@st.cache_data(ttl=86400)/@st.cache_data(ttl=60)/' ~/main.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
python3 -c "
import sys
sys.path.insert(0, '/home/ubuntu')
from main import get_token_cached
token = get_token_cached()
print('타입:', type(token))
print('토큰 전체:', token)
"
cat ~/.env | grep -i "app_key\|app_secret\|url_base"
# 1. URL_BASE 추가
echo 'URL_BASE="https://openapi.koreainvestment.com:9443"' >> ~/.env
# 2. get_token 함수 확인
sed -n '235,260p' ~/main.py
python3 -c "
import sys
sys.path.insert(0, '/home/ubuntu')
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/.env')
import os
print('URL_BASE:', os.getenv('URL_BASE'))
from main import get_token
token = get_token()
print('토큰:', token[:30] if token and len(str(token)) > 5 else token)
"
# main.py에서 환경변수 로드 부분 확인
grep -n "APP_KEY\|APP_SECRET\|URL_BASE\|os.getenv\|environ" ~/main.py | head -15
# load_dotenv 호출 위치 확인
grep -n "load_dotenv\|dotenv" ~/main.py | head -5
python3 -c "
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/.env')
import os
print('KEY:', os.environ.get('KIS_APP_KEY', 'NOT FOUND')[:10])
print('SECRET:', os.environ.get('KIS_APP_SECRET', 'NOT FOUND')[:10])
"
sed -i 's/load_dotenv()/load_dotenv("\/home\/ubuntu\/.env")/' ~/main.py
# 확인
grep -n "load_dotenv" ~/main.py
# 컴파일
python3 -m py_compile ~/main.py && echo "OK"
# 재시작
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
grep -n "v3_result\|SUMBI PRESTIGE SCORE\|v3_ui\|v3_tot\|v3_grd" ~/main.py | head -20
grep -n "SUMBI PRESTIGE SCORE" ~/main.py
grep -n "QUANT FLOW MATRIX" ~/main.py
sed -n '605,615p' ~/main.py
python3 << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

v3_ui = """
if "v3_result" in dir() and v3_result:
    v3 = v3_result
    v3_tot = v3["total"]
    v3_grd = v3["grade"]
    v3_lbl = v3["grade_label"]
    v3_brk = v3["breakdown"]
    gc = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}.get(v3_grd,"#FFD60A")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-label">| SUMBI PRESTIGE SCORE V3 <span class="sec-sub">/ 100점 종합</span></div>', unsafe_allow_html=True)
    st.markdown(f"""<div style='background:rgba(0,0,0,0.4);border:2px solid {gc}60;border-radius:20px;padding:24px;margin:12px 0;text-align:center;'>
        <div style='font-size:48px;font-weight:700;color:{gc};'>{v3_tot}</div>
        <div style='font-size:18px;color:#52525b;'>/100</div>
        <div style='background:{gc}20;border:1px solid {gc}60;border-radius:8px;padding:4px 14px;display:inline-block;font-size:14px;color:{gc};font-weight:700;'>{v3_grd}</div>
        <div style='font-size:14px;color:#a0a0a0;margin-top:8px;'>{v3_lbl}</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

"""

target = 'st.markdown(\'<div class="panel panel-glow">\''
if target in content:
    content = content.replace(target, v3_ui + "\n" + target, 1)
    with open('/home/ubuntu/main.py', 'w') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND")
EOF

cat > /tmp/inject_v3.py << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

v3_ui = """
if "v3_result" in dir() and v3_result:
    v3 = v3_result
    v3_tot = v3["total"]
    v3_grd = v3["grade"]
    v3_lbl = v3["grade_label"]
    gc_map = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}
    gc = gc_map.get(v3_grd, "#FFD60A")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-label">| SUMBI PRESTIGE SCORE V3 / 100점 종합</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;"><div style="font-size:48px;font-weight:700;color:{gc};">{v3_tot}</div><div style="color:#aaa;">/100 · {v3_grd} · {v3_lbl}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

"""

target = 'st.markdown(\'<div class="panel panel-glow">\''
if target in content:
    content = content.replace(target, v3_ui + "\n" + target, 1)
    with open('/home/ubuntu/main.py', 'w') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("NOT FOUND:", target[:50])
PYEOF

python3 /tmp/inject_v3.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
# 백업에서 복원
cp ~/main.py.backup_v3_20260521_152256 ~/main.py
# 컴파일 확인
python3 -m py_compile ~/main.py && echo "OK"
sed -n '600,615p' ~/main.py
cat > /tmp/inject_v3.py << 'PYEOF'
with open('/home/ubuntu/main.py', 'r') as f:
    lines = f.readlines()

v3_code = """
if "v3_result" in dir() and v3_result:
    v3 = v3_result
    v3_tot = v3["total"]
    v3_grd = v3["grade"]
    v3_lbl = v3["grade_label"]
    gc_map = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}
    gc = gc_map.get(v3_grd, "#FFD60A")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-label">| SUMBI PRESTIGE SCORE V3 / 100점 종합</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;"><div style="font-size:48px;font-weight:700;color:{gc};">{v3_tot}</div><div style="color:#aaa;">/100 · {v3_grd} · {v3_lbl}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

"""

insert_line = None
for i, line in enumerate(lines):
    if 'g_col1, g_col2 = st.columns(2)' in line:
        insert_line = i
        break

if insert_line is not None:
    lines.insert(insert_line, v3_code)
    with open('/home/ubuntu/main.py', 'w') as f:
        f.writelines(lines)
    print(f"SUCCESS at line {insert_line}")
else:
    print("NOT FOUND")
PYEOF

python3 /tmp/inject_v3.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
pkill -f streamlit && rm -rf ~/.streamlit/cache && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
grep -n "v3_result" ~/main.py | head -10
sed -i 's/if "v3_result" in dir() and v3_result:/if v3_result:/' ~/main.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
sed -i 's/if v3_result:/if locals().get("v3_result"):/' ~/main.py
python3 -m py_compile ~/main.py && echo "OK"
pkill -f streamlit && sleep 2 && nohup streamlit run ~/main.py --server.port 8501 > ~/stream_run.log 2>&1 &
# 웹 파일 위치 찾기
ls /var/www/html/
ls ~
pm2 list
wc -l main.py
ps aux | grep streamlit
cat main.py | head -200
cat main.py | grep -n "score\|Score\|SCORE\|서브\|money_flow\|chart_tech\|fundamental" | head -50
cat main.py | grep -n "Money Flow\|Chart Tech\|Fundamental\|News Momentum\|Short Signal\|Macro Env\|Sector Theme\|Broker Flow" | head -30
grep -n "메이저\|차트\|펀더\|모멘텀\|공매도\|매크로\|섹터\|거래원" main.py | head -30
sed -n '400,520p' main.py
sed -n '520,650p' main.py
sed -n '650,780p' main.py
sed -n '780,911p' main.py
grep -n "v3_result\|v3_scorer\|score_brain\|sub_score\|breakdown" main.py | head -20
sed -n '590,615p' main.py
grep -n "v3_scorer\|integrated_score\|run_v3\|v3_result\s*=" main.py
cat v3_scorer.py
head -20 main.py
sed -n '20,35p' main.py
sed -i 's/from dotenv import load_dotenv/from dotenv import load_dotenv\nfrom v3_scorer import calc_sumbi_v3/' main.py
grep -n "v3_scorer\|calc_sumbi_v3" main.py
grep -n "quant\s*=\|sentiment\s*=" main.py
sed -i '512a\v3_result = calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)' main.py
sed -n '510,516p' main.py
pkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 &
ps aux | grep streamlit
tail -50 nohup.out
sed -n '1,80p' v3_scorer.py
grep -n "def get_investor_data\|def get_stock_info" main.py
cp v3_scorer.py v3_scorer.py.backup_$(date +%Y%m%d_%H%M)
sed -n '281,340p' main.py
sed -n '388,510p' main.py
grep -n "def get_short\|def get_sector\|def get_broker\|short_data\|sector_data\|broker_data" main.py | head -20
sed -n '388,430p' main.py
cat > v3_scorer.py << 'PYEOF'
"""
SUMBI V3 SCORER - 8개 카테고리 100점 종합 평가
"""
import numpy as np
import pandas as pd

# ============================================================
# 1. Money Flow | 메이저 수급 (25pts)
# ============================================================
def calc_flow_score(investor):
    if not investor:
        return 0, {}
    score = 0
    details = {}
    orgn = investor.get('orgn', 0)
    frgn = investor.get('frgn', 0)
    prsn = investor.get('prsn', 0)
    total_abs = abs(orgn) + abs(frgn) + abs(prsn)

    # 기관 순매수 (10pts)
    if orgn > 50000:   score += 10
    elif orgn > 10000: score += 7
    elif orgn > 0:     score += 4
    elif orgn > -10000: score += 2
    else:              score += 0
    details['기관'] = min(10, max(0, score))

    # 외인 순매수 (10pts)
    f_score = 0
    if frgn > 50000:   f_score = 10
    elif frgn > 10000: f_score = 7
    elif frgn > 0:     f_score = 4
    elif frgn > -10000: f_score = 2
    score += f_score
    details['외인'] = f_score

    # 기관+외인 동반 매수 보너스 (5pts)
    if orgn > 0 and frgn > 0:
        bonus = 5
    elif orgn > 0 or frgn > 0:
        bonus = 2
    else:
        bonus = 0
    score += bonus
    details['동반매수'] = bonus

    return max(0, min(25, score)), details

# ============================================================
# 2. Chart Tech | 차트·기술적 (25pts)
# ============================================================
def calc_chart_score(df_chart):
    if df_chart is None or len(df_chart) < 20:
        return 0, {}
    score = 0
    details = {}
    close = df_chart['Close']
    high  = df_chart['High']
    low   = df_chart['Low']
    vol   = df_chart['Volume']

    ma5  = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else ma20
    cur  = close.iloc[-1]

    # 추세 (8pts)
    t = 0
    if cur > ma5 > ma20:   t += 4
    elif cur > ma20:        t += 2
    if ma5 > ma20 > ma60:   t += 4
    elif ma5 > ma20:        t += 2
    t = min(8, t)
    score += t
    details['추세'] = t

    # RSI (6pts)
    delta = close.diff()
    gain  = delta.where(delta > 0, 0).rolling(14).mean()
    loss  = -delta.where(delta < 0, 0).rolling(14).mean()
    rs    = gain / loss
    rsi   = (100 - (100 / (1 + rs))).iloc[-1]
    if not pd.isna(rsi):
        if 40 <= rsi <= 60:   r = 6
        elif 30 <= rsi < 40:  r = 4
        elif 60 < rsi <= 70:  r = 4
        elif rsi < 30:        r = 2
        else:                  r = 1
    else: r = 3
    score += r
    details['RSI'] = r

    # MACD (5pts)
    ema12  = close.ewm(span=12).mean()
    ema26  = close.ewm(span=26).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    if len(macd) >= 2:
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            m = 5
        elif macd.iloc[-1] > signal.iloc[-1]:
            m = 3
        else:
            m = 0
    else: m = 0
    score += m
    details['MACD'] = m

    # 거래량 (6pts)
    vol_ma = vol.rolling(20).mean().iloc[-1]
    v_today = vol.iloc[-1]
    if v_today > vol_ma * 2:   v = 6
    elif v_today > vol_ma * 1.5: v = 4
    elif v_today > vol_ma:     v = 2
    else:                      v = 0
    score += v
    details['거래량'] = v

    return max(0, min(25, score)), details

# ============================================================
# 3. Fundamental | 기업 펀더멘털 (13pts)
# ============================================================
def calc_fundamental_score(info, macro=None):
    if not info:
        return 0, {}
    score = 0
    details = {}

    # 시장 (3pts)
    market = info.get('market', '')
    if market == 'KOSPI':
        score += 3
        details['시장'] = 3
    else:
        score += 1
        details['시장'] = 1

    # 섹터 프리미엄 (5pts)
    sector = info.get('sector', '')
    premium_sectors = ['조선', '방산', '반도체', '2차전지', '바이오', 'IT', '전기전자']
    if any(s in sector for s in premium_sectors):
        score += 5
        details['섹터프리미엄'] = 5
    else:
        score += 2
        details['섹터프리미엄'] = 2

    # 매크로 환경 펀더멘털 영향 (5pts)
    if macro:
        krw = macro.get('krw', 1300)
        if krw and krw < 1300:
            score += 5
        elif krw and krw < 1380:
            score += 3
        else:
            score += 1
        details['환율영향'] = score - details.get('시장',0) - details.get('섹터프리미엄',0)

    return max(0, min(13, score)), details

# ============================================================
# 4. News Momentum | 뉴스 모멘텀 (10pts)
# ============================================================
def calc_news_score(news_list):
    if not news_list:
        return 0, {}
    score = 0
    details = {}
    n = len(news_list)

    # 뉴스 수 (5pts)
    if n >= 5:   score += 5
    elif n >= 3: score += 3
    elif n >= 1: score += 1
    details['뉴스수'] = min(5, score)

    # 긍정 키워드 (5pts)
    pos_kw = ['수주','강세','상승','급등','목표가','매수','호재','실적','증가','성장','수익']
    neg_kw = ['하락','급락','손실','적자','매도','위험','경고','감소']
    pos = neg = 0
    for item in news_list:
        title = item.get('title', '')
        if any(k in title for k in pos_kw): pos += 1
        if any(k in title for k in neg_kw): neg += 1
    kw_score = max(0, min(5, pos - neg + 2))
    score += kw_score
    details['키워드'] = kw_score

    return max(0, min(10, score)), details

# ============================================================
# 5. Short Signal | 공매도 신호 (8pts)
# ============================================================
def calc_short_score(investor, df_chart):
    score = 4  # 기본값
    details = {}

    if investor:
        prsn = investor.get('prsn', 0)
        orgn = investor.get('orgn', 0)
        # 개인 매도 + 기관 매수 = 공매도 적음
        if prsn < -10000 and orgn > 0:
            score = 6
        elif prsn < 0:
            score = 4
        else:
            score = 2
        details['수급패턴'] = score

    if df_chart is not None and len(df_chart) >= 20:
        close = df_chart['Close']
        vol   = df_chart['Volume']
        vol_ma = vol.rolling(20).mean().iloc[-1]
        # 거래량 급증 + 하락 = 공매도 신호
        if vol.iloc[-1] > vol_ma * 1.5 and close.iloc[-1] < close.iloc[-2]:
            score = max(0, score - 2)
        details['거래량패턴'] = score

    return max(0, min(8, score)), details

# ============================================================
# 6. Macro Env | 매크로 환경 (7pts)
# ============================================================
def calc_macro_score(macro):
    if not macro:
        return 3, {}
    score = 0
    details = {}
    krw = macro.get('krw')
    wti = macro.get('wti')
    tnx = macro.get('tnx')
    dxy = macro.get('dxy')

    # 환율 (2pts)
    if krw:
        if krw < 1300:   score += 2
        elif krw < 1380: score += 1
        else:            score += 0
        details['환율'] = min(2, score)

    # WTI (2pts)
    w = 0
    if wti:
        if wti < 70:    w = 2
        elif wti < 85:  w = 1
        else:           w = 0
    score += w
    details['WTI'] = w

    # 금리 (2pts)
    t = 0
    if tnx:
        if tnx < 3.5:   t = 2
        elif tnx < 4.3: t = 1
        else:           t = 0
    score += t
    details['금리'] = t

    # DXY (1pt)
    d = 0
    if dxy:
        if dxy < 100: d = 1
    score += d
    details['달러'] = d

    return max(0, min(7, score)), details

# ============================================================
# 7. Sector Theme | 섹터·테마 (7pts)
# ============================================================
def calc_sector_score(info, news_list):
    score = 3  # 기본값
    details = {}

    if info:
        sector = info.get('sector', '')
        hot_sectors = ['조선', '방산', '우주항공', '반도체', 'AI', '2차전지', '로봇']
        warm_sectors = ['바이오', '제약', 'IT', '전기전자', '화학']

        if any(s in sector for s in hot_sectors):
            score = 7
        elif any(s in sector for s in warm_sectors):
            score = 5
        else:
            score = 3
        details['섹터'] = score

    # 뉴스 테마 보너스
    if news_list:
        theme_kw = ['수주', 'KDDX', '잠수함', '방산', '수출', '계약', '협력']
        for item in news_list:
            if any(k in item.get('title','') for k in theme_kw):
                score = min(7, score + 1)
                break
        details['테마뉴스'] = score

    return max(0, min(7, score)), details

# ============================================================
# 8. Broker Flow | 거래원 분석 (5pts)
# ============================================================
def calc_broker_score(investor):
    score = 2  # 기본값
    details = {}

    if investor:
        orgn = investor.get('orgn', 0)
        frgn = investor.get('frgn', 0)
        prsn = investor.get('prsn', 0)

        # 기관+외인 동반매수
        if orgn > 100000 and frgn > 100000:
            score = 5
        elif orgn > 50000 and frgn > 0:
            score = 4
        elif orgn > 0 and frgn > 0:
            score = 3
        elif orgn > 0 or frgn > 0:
            score = 2
        else:
            score = 0
        details['거래원패턴'] = score

    return max(0, min(5, score)), details

# ============================================================
# MAIN: calc_sumbi_v3
# ============================================================
def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None,
                  short_data=None, sector_data=None, broker_data=None):
    """SUMBI V3 종합 평가 (100pts)"""

    flow,   flow_d   = calc_flow_score(investor)
    chart,  chart_d  = calc_chart_score(df_chart)
    fund,   fund_d   = calc_fundamental_score(info, macro)
    news,   news_d   = calc_news_score(news_list)
    short,  short_d  = calc_short_score(investor, df_chart)
    macro_s,macro_d  = calc_macro_score(macro)
    sector, sector_d = calc_sector_score(info, news_list)
    broker, broker_d = calc_broker_score(investor)

    total = flow + chart + fund + news + short + macro_s + sector + broker

    if   total >= 85: grade, glabel = "S+", "DIAMOND 최상위"
    elif total >= 75: grade, glabel = "S",  "PLATINUM 우수"
    elif total >= 65: grade, glabel = "A+", "GOLD 양호"
    elif total >= 55: grade, glabel = "A",  "SILVER 보통"
    elif total >= 45: grade, glabel = "B",  "BRONZE 주의"
    elif total >= 35: grade, glabel = "C",  "CAUTION 경계"
    else:             grade, glabel = "D",  "DANGER 위험"

    return {
        'total': total,
        'grade': grade,
        'grade_label': glabel,
        'breakdown': {
            'flow':    (flow,    25, flow_d),
            'chart':   (chart,   25, chart_d),
            'fundamental': (fund, 13, fund_d),
            'news':    (news,    10, news_d),
            'short':   (short,    8, short_d),
            'macro':   (macro_s,  7, macro_d),
            'sector':  (sector,   7, sector_d),
            'broker':  (broker,   5, broker_d),
        }
    }
PYEOFpkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 > nohup.out 2>&1 &

grep -n "breakdown\|flow\|chart\|fundamental\|news\|short\|sector\|broker" main.py | grep -v "def \|#" | head -30
sed -n '670,720p' main.py
sed -n '603,675p' main.py
wc -l v3_scorer.py && head -5 v3_scorer.py
rm -rf __pycache__ && pkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 > nohup.out 2>&1 &
grep -n "0/25\|0/13\|money\|flow_score\|breakdown" main.py | head -20
grep -n "score-card\|flow-card\|sec-score\|v3\[" main.py | head -20
sed -n '607,700p' main.py
grep -n "Money Flow\|Chart Tech\|Fundamental\|v3\[.breakdown" main.py
grep -rln "Money Flow\|Chart Tech\|메이저 수급" ~/
grep -n "add_v3_ui\|import.*v3_ui" main.py
cat add_v3_ui.py
grep -n "v3_bd" main.py
sed -i 's/v3_result = calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)/v3_result = calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)\nv3_bd = v3_result.get("breakdown", {})/' main.py && python3 add_v3_ui.py
python3 add_v3_ui2.py
grep -n "v3_result = calc_sumbi_v3" main.py
sed -i '513a\v3_bd = v3_result.get("breakdown", {}) if v3_result else {}' main.py
sed -n '511,516p' main.py
sed -i '515d' main.py && python3 add_v3_ui2.py
python3 add_v3_ui2.py
python3 -c "
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = 'st.markdown(\'<div class=\"sec-label\">| QUANT FLOW MATRIX'

v3_ui = '''
if v3_result:
    v3_tot = v3_result[\"total\"]
    v3_grd = v3_result[\"grade\"]
    v3_lbl = v3_result[\"grade_label\"]
    gc_map = {\"S+\":\"#00FF94\",\"S\":\"#34C759\",\"A+\":\"#FFD60A\",\"A\":\"#FFD60A\",\"B\":\"#FF9500\",\"C\":\"#FF6B35\",\"D\":\"#FF3B3B\"}
    gc = gc_map.get(v3_grd, \"#FFD60A\")
    st.markdown(\"<div class='panel'>\", unsafe_allow_html=True)
    st.markdown(f\"<div class='sec-label'>| SUMBI PRESTIGE SCORE V3 / 100점 종합</div>\", unsafe_allow_html=True)
    st.markdown(f\"\"\"<div style='text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;'>
    <div style='font-size:48px;font-weight:700;color:{gc};'>{v3_tot}</div>
    <div style='color:#aaa;'>/100 · {v3_grd} · {v3_lbl}</div></div>\"\"\", unsafe_allow_html=True)
    st.markdown(\"</div>\", unsafe_allow_html=True)
    labels = [
        (\"flow\",\"������\",\"메이저 수급\",\"Money Flow\",25),
        (\"chart\",\"������\",\"차트·기술적\",\"Chart Tech\",25),
        (\"fundamental\",\"������\",\"기업 펀더멘털\",\"Fundamental\",13),
        (\"news\",\"������\",\"뉴스 모멘텀\",\"News Momentum\",10),
        (\"short\",\"������\",\"공매도 신호\",\"Short Signal\",8),
        (\"macro\",\"������\",\"매크로 환경\",\"Macro Env\",7),
        (\"sector\",\"������\",\"섹터·테마\",\"Sector Theme\",7),
        (\"broker\",\"⚡\",\"거래원 분석\",\"Broker Flow\",5),
    ]
    rows = []
    for key, icon, kor, eng, max_s in labels:
        val, mx, _ = v3_bd.get(key, (0, max_s, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        bar_c = \"#34C759\" if pct >= 70 else \"#FFD60A\" if pct >= 40 else \"#FF3B3B\"
        rows.append(f\"\"\"<div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
        <span style='font-size:13px;color:#e0e0e0;'>{icon} {kor} <span style='color:#52525b;font-size:11px;'>/ {eng}</span></span>
        <span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span>
        </div>
        <div style='background:#1a1a1a;border-radius:4px;height:6px;'>
        <div style='background:{bar_c};width:{pct}%;height:6px;border-radius:4px;'></div>
        </div></div>\"\"\")
    st.markdown(f\"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>\", unsafe_allow_html=True)
    st.markdown(\"</div>\", unsafe_allow_html=True)

'''

if target in content:
    content = content.replace(target, v3_ui + target, 1)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS!')
else:
    print('Target not found')
"
cat > patch_v3_ui.py << 'EOF'
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "st.markdown('<div class=\"sec-label\">| QUANT FLOW MATRIX"

v3_ui = """
if v3_result:
    v3_tot = v3_result["total"]
    v3_grd = v3_result["grade"]
    v3_lbl = v3_result["grade_label"]
    gc_map = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}
    gc = gc_map.get(v3_grd, "#FFD60A")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='sec-label'>| SUMBI PRESTIGE SCORE V3 / 100pts</div>", unsafe_allow_html=True)
    st.markdown(f\"\"\"<div style='text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;'>
<div style='font-size:48px;font-weight:700;color:{gc};'>{v3_tot}</div>
<div style='color:#aaa;'>/100 {v3_grd} {v3_lbl}</div></div>\"\"\", unsafe_allow_html=True)
    labels = [
        ("flow",   "Money Flow",    25),
        ("chart",  "Chart Tech",    25),
        ("fundamental","Fundamental",13),
        ("news",   "News Momentum", 10),
        ("short",  "Short Signal",   8),
        ("macro",  "Macro Env",      7),
        ("sector", "Sector Theme",   7),
        ("broker", "Broker Flow",    5),
    ]
    rows = []
    for key, eng, max_s in labels:
        val, mx, _ = v3_bd.get(key, (0, max_s, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        rows.append(f\"\"\"<div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'>
<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>
<span style='font-size:13px;color:#e0e0e0;'>{eng}</span>
<span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span>
</div>
<div style='background:#1a1a1a;border-radius:4px;height:6px;'>
<div style='background:{bar_c};width:{pct}%;height:6px;border-radius:4px;'></div>
</div></div>\"\"\")
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

"""

if target in content:
    content = content.replace(target, v3_ui + target, 1)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS!')
else:
    print('Target not found - checking line 622:')
    lines = content.split('\n')
    print(lines[621][:80])
EOF

python3 patch_v3_ui.py
sed -i 's/target = .*/target = "st.markdown(\x27<div class=\\"sec-label\\">| QUANT FLOW MATRIX"/' patch_v3_ui.py
python3 patch_v3_ui.py
sed -n '622p' main.py
sed -i '621r /dev/stdin' main.py << 'INSERT'
if v3_result:
    v3_tot = v3_result["total"]
    v3_grd = v3_result["grade"]
    v3_lbl = v3_result["grade_label"]
    gc_map = {"S+":"#00FF94","S":"#34C759","A+":"#FFD60A","A":"#FFD60A","B":"#FF9500","C":"#FF6B35","D":"#FF3B3B"}
    gc = gc_map.get(v3_grd, "#FFD60A")
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown(f"<div class='sec-label'>| SUMBI PRESTIGE SCORE V3 / 100pts</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;padding:20px;border:2px solid {gc};border-radius:16px;margin:12px 0;'><div style='font-size:48px;font-weight:700;color:{gc};'>{v3_tot}</div><div style='color:#aaa;'>/100 {v3_grd} {v3_lbl}</div></div>", unsafe_allow_html=True)
    labels = [("flow","Money Flow",25),("chart","Chart Tech",25),("fundamental","Fundamental",13),("news","News Momentum",10),("short","Short Signal",8),("macro","Macro Env",7),("sector","Sector Theme",7),("broker","Broker Flow",5)]
    rows = []
    for key, eng, max_s in labels:
        val, mx, _ = v3_bd.get(key, (0, max_s, {}))
        pct = int(val / mx * 100) if mx > 0 else 0
        bar_c = "#34C759" if pct >= 70 else "#FFD60A" if pct >= 40 else "#FF3B3B"
        rows.append(f"<div style='background:rgba(255,255,255,0.03);border:1px solid #2a2a2a;border-radius:12px;padding:12px 16px;'><div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'><span style='font-size:13px;color:#e0e0e0;'>{eng}</span><span style='font-family:JetBrains Mono,monospace;font-size:14px;color:{bar_c};font-weight:700;'>{val}<span style='color:#52525b;font-size:10px;'>/{mx}</span></span></div><div style='background:#1a1a1a;border-radius:4px;height:6px;'><div style='background:{bar_c};width:{pct}%;height:6px;border-radius:4px;'></div></div></div>")
    st.markdown(f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:8px 0;'>{''.join(rows)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
INSERT

sed -n '619,625p' main.py && pkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 > nohup.out 2>&1 &
ls -la && find . -name "*.py" -o -name "*.html" -o -name "*.js" 2>/dev/null | head -50
ls -la ~/sumbi* 2>/dev/null || ls -la /home/ubuntu/
tar -czf ~/sumbi_backup_20260522.tar.gz ~/sumbi* *.py *.html 2>/dev/null
ls -lh ~/sumbi_backup_20260522.tar.gz
cat main.py
cat v3_scorer.py
cd ~
git init
git add *.py *.html
git commit -m "백업 20260522"
git remote add origin https://github.com/a24488817-a11y/sumbi-analytics.git
git branch -M main
git push -u origin main
git config --global user.email "a24488817@github.com"
git config --global user.name "a24488817-a11y"
git add *.py *.html
git commit -m "백업 20260522"
git push -u origin main
a24488817-a11y
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
git push https://a24488817-a11y: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@github.com/a24488817-a11y/sumbi-analytics.git main
git push --force https://a24488817-a11y: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@github.com/a24488817-a11y/sumbi-analytics.git main
ps aux | grep streamlit
tail -50 ~/streamlit.log
pip list | grep -E "streamlit|pandas|requests|yfinance"
cat main.py | grep -n "use_container_width" | head -20
sed -i 's/use_container_width=True/width="stretch"/g; s/use_container_width=False/width="content"/g' main.py && echo "수정완료"
pkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 > ~/streamlit.log 2>&1 &
sed -i 's/use_container_width=True/width="stretch"/g; s/use_container_width=False/width="content"/g' main.py && echo "수정완료"
pkill -f streamlit && sleep 2 && nohup streamlit run main.py --server.port 8501 > ~/streamlit.log 2>&1 & echo "재시작완료"
sudo nano /etc/systemd/system/sumbi.service
sudo systemctl daemon-reload
sudo systemctl enable sumbi
sudo systemctl start sumbi
sudo systemctl status sumbi
sudo tee /etc/systemd/system/sumbi.service << 'EOF'
[Unit]
Description=Sumbi Analytics
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/.local/bin/streamlit run main.py --server.port 8501
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload && sudo systemctl enable sumbi && sudo systemctl start sumbi && echo "완료"
sudo systemctl status sumbi
which streamlit
sudo tee /etc/systemd/system/sumbi.service << 'EOF'
[Unit]
Description=Sumbi Analytics
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="HOME=/home/ubuntu"
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/.local/bin/streamlit run main.py --server.port 8501 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload && sudo systemctl restart sumbi && sleep 3 && sudo systemctl status sumbi
sudo journalctl -u sumbi -n 20 --no-pager
pkill -f streamlit && sleep 3 && sudo systemctl restart sumbi && sleep 3 && sudo systemctl status sumbi
sudo systemctl status sumbi
crontab -e
(crontab -l 2>/dev/null; echo '0 3 * * * cd /home/ubuntu && git add *.py *.html && git commit -m "auto-backup" && git push --force https://a24488817-a11y:ghp_5KuKhNtjObY8
echo '0 3 * * * cd /home/ubuntu && git add *.py *.html && git commit -m "auto-backup" && git push --force https://a24488817-a11y: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@github.com/a24488817-a11y/sumbi-analytics.git main' > /tmp/mycron
crontab /tmp/mycron && crontab -l
cat main.py | head -200
grep -n "font-size:[89]px\|font-size:10px\|font-size:11px" main.py | head -30
sed -i 's/font-size:9px/font-size:13px/g; s/font-size:10px/font-size:14px/g; s/font-size:11px/font-size:15px/g' main.py && echo "완료"
sed -i 's/color:#71717a/color:#b0b0b0/g; s/color:#52525b/color:#a0a0a0/g' main.py && echo "색상완료"
sudo systemctl restart sumbi && echo "재시작완료"
sed -i 's/color:#a1a1aa/color:#c0c0c0/g; s/color:#d4d4d8/color:#e0e0e0/g; s/color:rgba(180,120,30,.8)/color:rgba(220,160,40,1)/g; s/color:rgba(180,120,30,.7)/color:rgba(220,160,40,1)/g' main.py && echo "완료"
sed -i 's/color:#a0a0a0/color:#c8c8c8/g; s/color:#b0b0b0/color:#d0d0d0/g' main.py && echo "완료2"
sudo systemctl restart sumbi && echo "재시작"
grep -oE '#[0-9a-fA-F]{6}' main.py | sort | uniq -c
grep -nE "rgba|opacity" main.py
sed -i 's/#71717a/#e0e0e0/g' main.py
sed -i 's/#52525b/#e0e0e0/g' main.py
sed -i 's/#a1a1aa/#e0e0e0/g' main.py
sed -i 's/#9CA3AF/#e0e0e0/g' main.py
sudo systemctl restart sumbi &
grep -nE "LAUNCH DEEP SCAN|PRICE ACTION CHART|QUANT FLOW MATRIX|AI SENTIMENT ENGINE" main.py
grep -nE "INSTITUTION|FOREIGNER|INDIVIDUAL|Money Flow|Chart Tech|PER" main.py
cat << 'EOF' > update_labels.py
import re

file_path = 'main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 안전한 치환을 위한 정규 표현식 및 딕셔너리
replacements = {
    r'("⚡ LAUNCH DEEP SCAN")': r'"⚡ LAUNCH DEEP SCAN (딥스캔 시작)"',
    r'(>\| QUANT FLOW MATRIX )': r'>| QUANT FLOW MATRIX (퀀트 자금 흐름) ',
    r'(>\| AI SENTIMENT ENGINE )': r'>| AI SENTIMENT ENGINE (AI 심리 엔진) ',
    r'(>\| PRICE ACTION CHART )': r'>| PRICE ACTION CHART (가격 차트) ',
    r'(">PER<")': r'">PER (주가수익비율)<"',
    r'("Money Flow")': r'"Money Flow (자금 흐름)"',
    r'("Chart Tech")': r'"Chart Tech (차트 기술)"',
    r"('������ INSTITUTION',)": r"('������ INSTITUTION (기관)',)",
    r"('������ FOREIGNER',)": r"('������ FOREIGNER (외국인)',)",
    r"('������ INDIVIDUAL',)": r"('������ INDIVIDUAL (개인)',)"
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("번역 텍스트 추가 완료")
EOF

python3 update_labels.py
sudo systemctl restart sumbi &
# 1. 엑스박스가 뜨는 AI MACRO SIGNAL 주변 코드 탐색 (이미지 태그 색출)
grep -nC 3 "AI MACRO SIGNAL" main.py
# 2. 번역이 적용되지 않은 딥스캔 버튼의 정확한 하드코딩 상태 재확인
grep -n "LAUNCH DEEP SCAN" main.py
cat << 'EOF' > fix_ui_errors.py
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
EOF

# 파이썬 스크립트 실행 및 앱 재시작
python3 fix_ui_errors.py
sudo systemctl restart sumbi &
sudo sh -c 'echo "127.0.0.1 $(hostname)" >> /etc/hosts'
grep -nE "US 10Y TREASURY|USD / KRW|DOLLAR INDEX|WTI CRUDE OIL" main.py
grep -n "img src" main.py
cat << 'EOF' > final_macro_fix.py
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
EOF

# 스크립트 실행 및 앱 재시작
python3 final_macro_fix.py
sudo systemctl restart sumbi &
grep -nC 7 "AI MACRO SIGNAL / 인공지능" main.py
cat << 'EOF' > fix_html_render.py
import re

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 정규식을 사용하여 빈 줄과 과도한 들여쓰기를 제거하고 태그를 밀착시킴
    # (gap:20px;'> 와 <div style='flex:1;'> 사이의 공백 및 줄바꿈 압축)
    broken_pattern = r"(align-items:center;gap:20px;'>)\s+(<div style='flex:1;'>)"
    fixed_pattern = r"\1\n<div style='flex:1;'>\n"
    
    content = re.sub(broken_pattern, fixed_pattern, content)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ HTML 코드 노출 버그 완벽 수리 완료")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
EOF

# 스크립트 실행 및 앱 재시작
python3 fix_html_render.py
sudo systemctl restart sumbi &
grep -nC 8 "div style='flex:1;'" main.py
timedatectl | grep "Time zone"
cat << 'EOF' > fix_final_ui_time.py
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
EOF

# 1. UI 복구 스크립트 실행
python3 fix_final_ui_time.py
# 2. AWS 서버 시계를 한국 시간(KST)으로 영구 동기화
sudo timedatectl set-timezone Asia/Seoul
# 3. 앱 재시작 (변경된 코드와 동기화된 시간 적용)
sudo systemctl restart sumbi &
cat ~/sumbi-analytics/v3_scorer.py
cat ~/sumbi-analytics/main.py
find / -name "main.py" 2>/dev/null | grep sumbi
ls ~/
cat ~/main.py
cat ~/v3_scorer.py
head -100 ~/v3_scorer.py
head -80 ~/main.py
cp ~/v3_scorer.py ~/v3_scorer.py.backup_$(date +%Y%m%d)
cat > ~/v3_scorer.py << 'EOF'
EOF

sudo systemctl restart sumbi.service && sudo systemctl status sumbi.service
cp ~/v3_scorer.py.backup_20260523 ~/v3_scorer.py
head -5 ~/v3_scorer.py
sudo systemctl restart sumbi.service
cd ~ && git init && git remote add origin https://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@github.com/a24488817-a11y/sumbi-analytics.git
git remote set-url origin https://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@github.com/a24488817-a11y/sumbi-analytics.git
git pull origin main
python3 ~/upload_scorer.py
cat > ~/upload_scorer.py << 'PYEOF'
import urllib.request, json, base64

token = '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'
repo = 'a24488817-a11y/sumbi-analytics'
url = f'https://api.github.com/repos/{repo}/contents/v3_scorer.py'

req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'sumbi'})
res = json.loads(urllib.request.urlopen(req).read())
sha = res['sha']
print('SHA:', sha)
PYEOF

python3 ~/upload_scorer.py
python3 -c "
import urllib.request, json, base64

token = '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'
repo = 'a24488817-a11y/sumbi-analytics'
sha = '03f24e452f6f7588b340579b9db392de2eec7d45'

with open('/home/ubuntu/v3_scorer.py', 'rb') as f:
    content = base64.b64encode(f.read()).decode()

data = json.dumps({'message': 'feat: 세력발자국 점수제 적용', 'content': content, 'sha': sha}).encode()
req = urllib.request.Request(
    f'https://api.github.com/repos/{repo}/contents/v3_scorer.py',
    data=data, method='PUT',
    headers={'Authorization': f'token {token}', 'Content-Type': 'application/json', 'User-Agent': 'sumbi'}
)
res = json.loads(urllib.request.urlopen(req).read())
print('업로드 완료:', res['content']['name'])
"
cd ~ && git pull origin main && sudo systemctl restart sumbi.service
sudo systemctl status sumbi.service
cat > ~/auto_push.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu
git add -A
git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
git push origin main
EOF

chmod +x ~/auto_push.sh
crontab -e
crontab -l
head -80 ~/main.py
cat > ~/kis_websocket.py << 'EOF'
"""
한투 WebSocket 실시간 체결 모듈
실시간 체결가/거래량 수신 → 세력 발자국 점수 즉시 반영
"""
import websocket, json, os, threading, time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
APP_KEY = os.environ.get("KIS_APP_KEY")
APP_SECRET = os.environ.get("KIS_APP_SECRET")

# 실시간 데이터 저장소
realtime_data = {}

def get_ws_approval_key():
    """WebSocket 접속키 발급"""
    url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    res = requests.post(url, headers=headers, json=body)
    return res.json().get("approval_key", "")

def on_message(ws, message):
    """실시간 체결 데이터 수신"""
    try:
        if message[0] == '0' or message[0] == '1':
            parts = message.split('|')
            if len(parts) >= 4:
                data = parts[3].split('^')
                if len(data) > 12:
                    ticker = data[0]
                    price = int(data[2])
                    volume = int(data[9])
                    strength = float(data[12]) if data[12] else 0

                    realtime_data[ticker] = {
                        'price': price,
                        'volume': volume,
                        'strength': strength,  # 체결강도
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
    except:
        pass

def on_error(ws, error):
    print(f"[WS ERROR] {error}")

def on_close(ws, *args):
    print("[WS] 연결 종료")

def on_open(ws, approval_key, tickers):
    """종목 구독 등록"""
    for ticker in tickers:
        msg = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": ticker
                }
            }
        }
        ws.send(json.dumps(msg))
        print(f"[WS] 구독: {ticker}")

def start_websocket(tickers):
    """WebSocket 시작"""
    approval_key = get_ws_approval_key()
    if not approval_key:
        print("[WS] 접속키 발급 실패")
        return

    ws = websocket.WebSocketApp(
        "ws://ops.koreainvestment.com:21000",
        on_open=lambda ws: on_open(ws, approval_key, tickers),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    t = threading.Thread(target=ws.run_forever)
    t.daemon = True
    t.start()
    print(f"[WS] 실시간 연결 시작: {tickers}")

def get_realtime(ticker):
    """종목 실시간 데이터 조회"""
    return realtime_data.get(ticker, {})
EOF

pip install websocket-client --break-system-packages
pip3 install websocket-client
python3 -c "
from kis_websocket import get_ws_approval_key
key = get_ws_approval_key()
if key:
    print('✅ 접속키 발급 성공:', key[:20], '...')
else:
    print('❌ 접속키 발급 실패 - API 키 확인 필요')
"
cat > ~/kofia_crawler.py << 'EOF'
"""
KOFIA 대차잔고 + KRX 공매도 자동 수집기
매일 장 마감 후 자동 실행 → v3_scorer에 반영
"""
import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def get_kofia_short_balance(ticker):
    """KOFIA 대차잔고 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://data.krx.co.kr'
        }
        params = {
            'bld': 'dbms/MDC/STAT/standard/MDCSTAT06301',
            'startDd': week_ago,
            'endDd': today,
            'isuCd': ticker,
            'share': '1',
            'money': '1'
        }
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        data = res.json()
        
        if 'output' in data and data['output']:
            latest = data['output'][0]
            prev = data['output'][1] if len(data['output']) > 1 else latest
            
            balance_today = int(latest.get('BALANCE', '0').replace(',', ''))
            balance_prev = int(prev.get('BALANCE', '0').replace(',', ''))
            change = balance_today - balance_prev
            
            return {
                'ticker': ticker,
                'balance': balance_today,
                'balance_change': change,
                'date': latest.get('TRD_DD', today)
            }
    except Exception as e:
        print(f"[KOFIA] 오류: {e}")
    return {}

def get_krx_short_ratio(ticker):
    """KRX 공매도 비율 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://data.krx.co.kr'
        }
        params = {
            'bld': 'dbms/MDC/STAT/standard/MDCSTAT06001',
            'startDd': week_ago,
            'endDd': today,
            'isuCd': ticker,
            'share': '1',
            'money': '1'
        }
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        data = res.json()
        
        if 'output' in data and data['output']:
            latest = data['output'][0]
            ratio = float(latest.get('RATIO', '0').replace(',', ''))
            return {
                'ticker': ticker,
                'short_ratio': ratio,
                'date': latest.get('TRD_DD', today)
            }
    except Exception as e:
        print(f"[KRX] 오류: {e}")
    return {}

def get_short_data(ticker):
    """대차잔고 + 공매도 통합 조회 → v3_scorer 형식으로 반환"""
    balance = get_kofia_short_balance(ticker)
    short = get_krx_short_ratio(ticker)
    
    result = {
        'short_ratio': short.get('short_ratio', 0),
        'balance_change': balance.get('balance_change', 0),
        'short_balance': balance.get('balance', 0),
        'credit_ratio': 0  # 추후 신용잔고 추가
    }
    
    print(f"[{ticker}] 공매도비율: {result['short_ratio']}% | 대차변화: {result['balance_change']:+,}")
    return result

if __name__ == "__main__":
    # 테스트
    tickers = ['005930', '000660', '035420']  # 삼성, SK하이닉스, 네이버
    print("=== KOFIA/KRX 대차잔고 수집 테스트 ===")
    for t in tickers:
        data = get_short_data(t)
        print(data)
        print()
EOF

python3 ~/kofia_crawler.py
cat > ~/kofia_crawler.py << 'EOF'
import requests
import json
from datetime import datetime, timedelta

def get_short_data(ticker):
    """KRX 공매도 데이터 조회"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        
        url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://data.krx.co.kr/contents/MDC/STAT/standard/MDCSTAT06001.cmd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*'
        }
        params = f"bld=dbms/MDC/STAT/standard/MDCSTAT06001&startDd={week_ago}&endDd={today}&isuCd={ticker}&share=1&money=1&csvxls_isNo=false"
        
        res = requests.post(url, headers=headers, data=params, timeout=10)
        print(f"[{ticker}] 상태코드: {res.status_code}")
        print(f"[{ticker}] 응답: {res.text[:200]}")
        
        data = res.json()
        if 'output' in data and data['output']:
            latest = data['output'][0]
            ratio = float(latest.get('RATIO', '0').replace(',', ''))
            print(f"[{ticker}] 공매도비율: {ratio}%")
            return {'short_ratio': ratio, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}
    except Exception as e:
        print(f"[{ticker}] 오류: {e}")
    
    return {'short_ratio': 0, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}

if __name__ == "__main__":
    get_short_data('005930')
EOF

python3 ~/kofia_crawler.py
cat > ~/kofia_crawler.py << 'EOF'
import requests
from datetime import datetime, timedelta

def get_short_data(ticker):
    """네이버 금융에서 공매도 데이터 조회 - 세션 불필요"""
    try:
        url = f"https://api.finance.naver.com/service/itemSummary.nhn?itemcode={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.naver.com'}
        res = requests.get(url, headers=headers, timeout=10)
        print(f"[{ticker}] 상태: {res.status_code}")
        print(f"[{ticker}] 응답: {res.text[:300]}")
    except Exception as e:
        print(f"오류: {e}")

    # yfinance로 대체 데이터
    try:
        import yfinance as yf
        stock = yf.Ticker(f"{ticker}.KS")
        info = stock.info
        short_ratio = info.get('shortPercentOfFloat', 0) or 0
        print(f"[{ticker}] yfinance 공매도비율: {short_ratio}")
        return {
            'short_ratio': short_ratio * 100,
            'balance_change': 0,
            'short_balance': 0,
            'credit_ratio': 0
        }
    except Exception as e:
        print(f"yfinance 오류: {e}")

    return {'short_ratio': 0, 'balance_change': 0, 'short_balance': 0, 'credit_ratio': 0}

if __name__ == "__main__":
    print(get_short_data('005930'))
EOF

python3 ~/kofia_crawler.py
python3 ~/kofia_crawler.py 2>&1 | tail -10
cat ~/sumbi-analytics/v3_scorer.py | head -100
ls ~/sumbi-analytics/
cat ~/.env 2>/dev/null || cat ~/sumbi-analytics/.env 2>/dev/null
ls /
ls /home/ubuntu/
find / -name "main.py" 2>/dev/null | head -5
cat ~/v3_scorer.py | head -150
cat ~/main.py | head -100
systemctl status sumbi.service
cat ~/v3_scorer.py | head -200
cat ~/kis_websocket.py | head -50
grep -n "realtime\|websocket\|kis_web" ~/v3_scorer.py
grep -n "realtime\|websocket" ~/main.py | head -20
wc -l ~/v3_scorer.py ~/main.py
tail -100 ~/v3_scorer.py
cat > ~/patch_realtime.py << 'EOF'
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

realtime_func = '''
def calc_realtime_score(realtime_data):
    """실시간 체결강도 점수 (10점) - KIS WebSocket"""
    if not realtime_data:
        return 5, {}
    score = 5
    details = {}
    strength = realtime_data.get('strength', 100)
    volume = realtime_data.get('volume', 0)
    avg_volume = realtime_data.get('avg_volume', 0)
    if strength > 130: score += 3
    elif strength > 115: score += 2
    elif strength > 105: score += 1
    elif strength < 85: score -= 2
    elif strength < 75: score -= 3
    if avg_volume > 0:
        ratio = volume / avg_volume
        if ratio > 3: score += 2
        elif ratio > 2: score += 1
        elif ratio < 0.3: score -= 1
    details['체결강도'] = round(strength, 1)
    return max(0, min(score, 10)), details

'''

content = content.replace('def calc_sumbi_v3(', realtime_func + 'def calc_sumbi_v3(')

content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):'
)

content = content.replace(
    '    broker, broker_d = calc_broker_score(broker_data)\n\n    total = flow + chart + fund + news + short + macro_s + sector + broker',
    '    broker, broker_d = calc_broker_score(broker_data)\n    realtime, realtime_d = calc_realtime_score(realtime_data)\n\n    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime'
)

content = content.replace("        'broker': (broker, 5, broker_d),",
    "        'broker': (broker, 5, broker_d),\n            'realtime': (realtime, 10, realtime_d),")

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print("✅ 실시간 체결강도 연동 완료! 총점 110점으로 확장")
EOF

python3 ~/patch_realtime.py
grep -n "calc_sumbi_v3\|kis_websocket\|import" ~/main.py | head -30
grep -n "calc_sumbi_v3(" ~/main.py
cat > ~/patch_main_realtime.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# kis_websocket import 추가
content = content.replace(
    'from v3_scorer import calc_sumbi_v3',
    'from v3_scorer import calc_sumbi_v3\nfrom kis_websocket import realtime_data, start_websocket'
)

# calc_sumbi_v3 호출에 realtime_data 추가
content = content.replace(
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list)',
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker))'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("✅ main.py 패치 완료!")
EOF

python3 ~/patch_main_realtime.py
grep -n "start_websocket\|if __name__\|def main" ~/kis_websocket.py
cat > ~/patch_ws_start.py << 'EOF'
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# 앱 시작시 웹소켓 백그라운드 스레드 자동 실행
ws_init = '''
# KIS WebSocket 백그라운드 자동 시작
import threading as _threading
def _start_ws():
    try:
        from kis_websocket import start_websocket
        # 코스피 주요 종목 기본 구독
        default_tickers = ["005930", "000660", "035720", "035420", "051910"]
        start_websocket(default_tickers)
    except Exception as e:
        print(f"WebSocket 시작 오류: {e}")

_ws_thread = _threading.Thread(target=_start_ws, daemon=True)
_ws_thread.start()
'''

# load_dotenv() 바로 다음에 삽입
content = content.replace('load_dotenv()\n', 'load_dotenv()\n' + ws_init)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print("✅ WebSocket 자동시작 패치 완료!")
EOF

python3 ~/patch_ws_start.py
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -20
sudo systemctl status sumbi.service | tail -25
grep -n "news_list\|get_news\|naver_news\|fetch_news" ~/main.py | head -20
sed -n '369,420p' ~/main.py
grep -i "dart\|DART" ~/.env
echo 'DART_API_KEY=4e3bc950251d3631af3da6fcd3661b6a3828e9ed' >> ~/.env
cat > ~/dart_connector.py << 'EOF'
import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache

load_dotenv()
DART_KEY = os.environ.get("DART_API_KEY")

@lru_cache(maxsize=500)
def get_corp_code(ticker):
    """종목코드 → DART 고유번호 변환"""
    try:
        import zipfile, io, xml.etree.ElementTree as ET
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}"
        r = requests.get(u

EOF
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functools import lru_cache

load_dotenv()
DART_KEY = os.environ.get(\"DART_API_KEY\")

@lru_cache(maxsize=500)
def get_corp_code(ticker):
    try:
        import zipfile, io, xml.etree.ElementTree as ET
        url = f\"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_KEY}\"
        r = requests.get(url, timeout=15)
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        xml_data = zf.read(\"CORPCODE.xml\")
        root = ET.fromstring(xml_data)
        for corp in root.findall(\"list\"):
            stock = corp.findtext(\"stock_code\", \"\").strip()
            if stock == ticker:
                return corp.findtext(\"corp_code\", \"\").strip()
    except Exception as e:
        print(f\"corp_code 오류: {e}\")
    return None

def get_dart_disclosures(ticker, days=3):
    try:
        corp_code = get_corp_code(ticker)
        if not corp_code:
            return []
        start = (datetime.now() - timedelta(days=days)).strftime(\"%Y%m%d\")
        end = datetime.now().strftime(\"%Y%m%d\")
        params = {\"crtfc_key\": DART_KEY, \"corp_code\": corp_code,
                  \"bgn_de\": start, \"end_de\": end, \"sort\": \"date\",
                  \"sort_mth\": \"desc\", \"page_count\": 10}
        r = requests.get(\"https://opendart.fss.or.kr/api/list.json\", params=params, timeout=10)
        data = r.json()
        if data.get(\"status\") != \"000\":
            return []
        return [{ \"title\": i.get(\"report_nm\",\"\"), \"date\": i.get(\"rcept_dt\",\"\") } for i in data.get(\"list\",[])]
    except Exception as e:
        print(f\"DART 공시 오류: {e}\")
        return []

def calc_dart_score(ticker):
    disclosures = get_dart_disclosures(ticker)
    if not disclosures:
        return 2, {}
    score = 2
    positive = [\"자사주\",\"배당\",\"수주\",\"계약\",\"자기주식취득\"]
    negative = [\"횡령\",\"배임\",\"조사\",\"상장폐지\",\"감사의견\",\"과징금\"]
    titles = []
    for d in disclosures[:5]:
        t = d[\"title\"]
        titles.append(t[:15])
        if any(k in t for k in positive): score += 1
        if any(k in t for k in negative): score -= 2
    return max(0, min(score, 5)), {\"공시수\": len(disclosures), \"최근\": titles}

if __name__ == \"__main__\":
    print(\"삼성전자 테스트:\")
    s, d = calc_dart_score(\"005930\")
    print(f\"점수: {s}/5, {d}\")
'''
with open('/home/ubuntu/dart_connector.py', 'w') as f:
    f.write(content)
print('파일 생성 완료')
"
python3 ~/dart_connector.py
ls -la ~/dart_connector.py && python3 ~/dart_connector.py
cat >> ~/v3_scorer.py << 'DARTEOF'

def calc_dart_score_wrapper(ticker):
    """DART 공시 점수 래퍼 (5점)"""
    try:
        from dart_connector import calc_dart_score
        score, details = calc_dart_score(ticker)
        return score, details
    except Exception as e:
        return 2, {}
DARTEOF

grep -n "def calc_sumbi_v3" ~/v3_scorer.py
python3 -c "
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

# 파라미터에 ticker 추가
content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None, ticker=None):'
)

# DART 점수 계산 추가
content = content.replace(
    '    realtime, realtime_d = calc_realtime_score(realtime_data)',
    '    realtime, realtime_d = calc_realtime_score(realtime_data)\n    dart, dart_d = calc_dart_score_wrapper(ticker) if ticker else (2, {})'
)

# total에 dart 추가
content = content.replace(
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime',
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime + dart'
)

# breakdown에 dart 추가
content = content.replace(
    \"            'realtime': (realtime, 10, realtime_d),\",
    \"            'realtime': (realtime, 10, realtime_d),\\n            'dart': (dart, 5, dart_d),\"
)

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print('DART 점수 통합 완료! 총점 115점')
"
python3 -c "
with open('/home/ubuntu/v3_scorer.py', 'r') as f:
    content = f.read()

# 파라미터에 ticker 추가
content = content.replace(
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None):',
    'def calc_sumbi_v3(investor, macro, df_chart, info=None, news_list=None, short_data=None, sector_data=None, broker_data=None, realtime_data=None, ticker=None):'
)

# DART 점수 계산 추가
content = content.replace(
    '    realtime, realtime_d = calc_realtime_score(realtime_data)',
    '    realtime, realtime_d = calc_realtime_score(realtime_data)\n    dart, dart_d = calc_dart_score_wrapper(ticker) if ticker else (2, {})'
)

# total에 dart 추가
content = content.replace(
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime',
    '    total = flow + chart + fund + news + short + macro_s + sector + broker + realtime + dart'
)

# breakdown에 dart 추가
content = content.replace(
    \"            'realtime': (realtime, 10, realtime_d),\",
    \"            'realtime': (realtime, 10, realtime_d),\\n            'dart': (dart, 5, dart_d),\"
)

with open('/home/ubuntu/v3_scorer.py', 'w') as f:
    f.write(content)
print('DART 점수 통합 완료! 총점 115점')
"
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

content = content.replace(
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker))',
    'calc_sumbi_v3(investor, macro, df_chart, info=info, news_list=news_list, realtime_data=realtime_data.get(ticker), ticker=ticker)'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('main.py ticker 전달 완료!')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -10
sudo systemctl status sumbi.service | tail -15
cd ~ && git add -A && git commit -m "DART+WebSocket 연동 완료 115점" && git push origin main
ls -la ~/sumbi_backup_*.tar.gz | tail -3
grep -i "naver\|CLIENT\|NAVER" ~/.env
cat ~/.env
echo 'NAVER_CLIENT_ID=Sdoj3I5WetzzjmyJAmen' >> ~/.env
echo 'NAVER_CLIENT_SECRET=d_dkWCKTKu' >> ~/.env
grep NAVER ~/.env
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv

load_dotenv()
NAVER_ID = os.environ.get(\"NAVER_CLIENT_ID\")
NAVER_SECRET = os.environ.get(\"NAVER_CLIENT_SECRET\")

def get_naver_news(query, display=10):
    \"\"\"네이버 뉴스 검색 API\"\"\"
    try:
        headers = {
            \"X-Naver-Client-Id\": NAVER_ID,
            \"X-Naver-Client-Secret\": NAVER_SECRET
        }
        params = {\"query\": query, \"display\": display, \"sort\": \"date\"}
        r = requests.get(\"https://openapi.naver.com/v1/search/news.json\",
                        headers=headers, params=params, timeout=5)
        items = r.json().get(\"items\", [])
        return [{\"title\": i[\"title\"].replace(\"<b>\",\"\").replace(\"</b>\",\"\"),
                 \"link\": i[\"link\"],
                 \"pub\": i[\"pubDate\"]} for i in items]
    except Exception as e:
        print(f\"네이버 뉴스 오류: {e}\")
        return []

if __name__ == \"__main__\":
    news = get_naver_news(\"삼성전자 주식\", 5)
    print(f\"뉴스 {len(news)}건:\")
    for n in news:
        print(f\"  - {n[title][:30]}\")
'''
with open(\"/home/ubuntu/naver_news.py\", \"w\") as f:
    f.write(content)
print(\"완료\")
"
python3 ~/naver_news.py
python3 -c "
from naver_news import get_naver_news
news = get_naver_news('삼성전자 주식', 5)
print(f'뉴스 {len(news)}건:')
for n in news:
    print(f\"  - {n['title'][:30]}\")
"
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_news 함수에 네이버 뉴스 추가
old = '''def get_news(query):'''
new = '''def get_news(query):'''

# import 추가
content = content.replace(
    'from kis_websocket import realtime_data, start_websocket',
    'from kis_websocket import realtime_data, start_websocket\nfrom naver_news import get_naver_news'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

# get_news 함수 확인
import subprocess
result = subprocess.run(['grep', '-n',
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

# get_news 함수에 네이버 뉴스 추가
old = '''def get_news(query):'''
new = '''def get_news(query):'''

# import 추가
content = content.replace(
    'from kis_websocket import realtime_data, start_websocket',
    'from kis_websocket import realtime_data, start_websocket\nfrom naver_news import get_naver_news'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)

# get_news 함수 확인
import subprocess
result = subprocess.run(['grep', '-n',

grep -n "def get_news" ~/main.py
sed -n '369,395p' ~/main.py
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

old = '''    except:
        return []

@st.cache_data(ttl=3600)
def get_chart_data'''

new = '''    except:
        return []

def get_news_combined(query):
    \"\"\"구글 RSS + 네이버 뉴스 통합\"\"\"
    results = get_news(query)
    try:
        from naver_news import get_naver_news
        naver = get_naver_news(query, 10)
        results = results + naver
    except Exception as e:
        pass
    return results[:20]

@st.cache_data(ttl=3600)
def get_chart_data'''

content = content.replace(old, new)

# news_list 호출을 combined로 교체
content = content.replace(
    'news_list= get_news(info[\\'name\\'] or ticker)',
    'news_list= get_news_combined(info[\\'name\\'] or ticker)'
)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('네이버+구글 뉴스 병합 완료! 최대 20건')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -10
cd ~ && git add -A && git commit -m "네이버뉴스+DART+WebSocket 완전연동" && git push origin main
cd ~ && git log --oneline -3
grep -n "macro\|fred\|FRED" ~/main.py | head -10
sed -n '271,320p' ~/main.py
grep -i "fred\|FRED" ~/.env
echo 'FRED_API_KEY=66f8e6a39938571b83bcdf4bae9b9418' >> ~/.env
grep FRED ~/.env
python3 -c "
content = '''import requests, os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
FRED_KEY = os.environ.get(\"FRED_API_KEY\")

def get_fred_series(series_id):
    try:
        url = f\"https://api.stlouisfed.org/fred/series/observations\"
        params = {\"series_id\": series_id, \"api_key\": FRED_KEY,
                  \"file_type\": \"json\", \"limit\": 1, \"sort_order\": \"desc\"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        val = data[\"observations\"][0][\"value\"]
        return float(val) if val != \".\" else None
    except:
        return None

def get_macro_fred():
    return {
        \"ffr\": get_fred_series(\"FEDFUNDS\"),
        \"tnx\": get_fred_series(\"DGS10\"),
        \"dxy\": get_fred_series(\"DTWEXBGS\"),
        \"cpi\": get_fred_series(\"CPIAUCSL\"),
        \"vix\": get_fred_series(\"VIXCLS\"),
        \"krw\": get_fred_series(\"DEXKOUS\"),
        \"wti\": get_fred_series(\"DCOILWTICO\"),
    }

if __name__ == \"__main__\":
    data = get_macro_fred()
    print(\"FRED 매크로 데이터:\")
    for k, v in data.items():
        print(f\"  {k}: {v}\")
'''
with open(\"/home/ubuntu/fred_conne
ls ~/fred_connector.py && python3 ~/fred_connector.py
cat > /home/ubuntu/fred_connector.py << 'FREDEOF'
import requests, os
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.environ.get("FRED_API_KEY")

def get_fred_series(series_id):
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {"series_id": series_id, "api_key": FRED_KEY,
                  "file_type": "json", "limit": 1, "sort_order": "desc"}
        r = requests.get(url, params=params, timeout=10)
        val = r.json()["observations"][0]["value"]
        return float(val) if val != "." else None
    except:
        return None

def get_macro_fred():
    return {
        "ffr": get_fred_series("FEDFUNDS"),
        "tnx": get_fred_series("DGS10"),
        "cpi": get_fred_series("CPIAUCSL"),
        "vix": get_fred_series("VIXCLS"),
        "krw": get_fred_series("DEXKOUS"),
        "wti": get_fred_series("DCOILWTICO"),
    }

if __name__ == "__main__":
    data = get_macro_fred()
    print("FRED 매크로:")
    for k, v in data.items():
        print(f"  {k}: {v}")
FREDEOF

python3 /home/ubuntu/fred_connector.py
python3 -c "
with open('/home/ubuntu/main.py', 'r') as f:
    content = f.read()

content = content.replace(
    'from naver_news import get_naver_news',
    'from naver_news import get_naver_news\nfrom fred_connector import get_macro_fred'
)

old = '''def get_macro():
    \"\"\"yfinance'''
new = '''def get_macro():
    \"\"\"FRED API + yfinance 병합\"\"\"
    try:
        fred = get_macro_fred()
        if fred and fred.get(\"tnx\"):
            return fred
    except:
        pass
    \"\"\"yfinance'''

content = content.replace(old, new)

with open('/home/ubuntu/main.py', 'w') as f:
    f.write(content)
print('FRED 매크로 연동 완료!')
"
sudo systemctl restart sumbi.service && sleep 5 && sudo systemctl status sumbi.service | tail -8
