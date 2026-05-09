import requests
import json
import os
import time

# 1. 시스템 설정
APP_KEY = os.environ.get("KIS_APP_KEY")
APP_SECRET = os.environ.get("KIS_APP_SECRET")
URL_BASE = "https://openapi.koreainvestment.com:9443"

def get_access_token():
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(f"{URL_BASE}/oauth2/tokenP", headers=headers, data=json.dumps(body))
    return res.json()["access_token"]

def analyze_quantum_scanner(token, symbol, name):
    """
    [JP모건 & 세력 추적 로직]
    삼성전자 같은 고래에 밀리지 않고, 수급이 폭발하는 중소형주/동전주 포착
    """
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": symbol}
    
    try:
        res = requests.get(f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-price", headers=headers, params=params)
        data = res.json()["output"]
        
        curr_price = int(data["stck_prpr"])
        # 거래량 회전율 및 상대적 강도 계산 (전일 대비 거래량 비율)
        vol_ratio = float(data["prdy_vol_vrss_prcnt"]) 
        
        # [42대 필살기 - 수급 집중도 타격 조건]
        # 거래량이 평소보다 300% 이상 폭발(vol_ratio > 300)하는 종목 필터링
        if vol_ratio > 300:
            print(f"🔥 [필살기 포착] {name} ({symbol})")
            print(f"   ㄴ 현재가: {curr_price:,}원 / 거래량 폭발: {vol_ratio}%")
            print(f"   ㄴ 판정: 세력 개입 의심 및 수급 집중 타격 구간")
            print("-" * 40)
        
        time.sleep(0.05) # 초당 20종목 스캔 속도 유지
        
    except:
        pass

# 엔진 점화
try:
    print("🚀 [숨비 퀀텀 엔진 V7.0] 전 종목 상대적 수급 스캔을 시작합니다.")
    token = get_access_token()
    
    # 대표님의 주력 타겟 + 시장 주도주 리스트 (실제로는 전종목 루프 가능)
    target_list = {
        "042660": "한화오션", "009540": "HD한국조선해양", "012450": "한화에어로스페이스",
        "030200": "KT", "005930": "삼성전자", "000660": "SK하이닉스", "037220": "한국항공우주",
        "450080": "에코프로머티", "071050": "한국금융지주", "377300": "카카오페이"
    }
    
    print(f"✅ {len(target_list)}개 핵심 섹터 레이더 가동... 오직 '돈의 흐름'만 추적합니다.\n")
    
    for symbol, name in target_list.items():
        analyze_quantum_scanner(token, symbol, name)
        
    print("\n🎯 1차 스캔 완료. 필살기 조건 부합 종목 대기 중.")
except Exception as e:
    print(f"❌ 엔진 가동 실패: {e}")
