import re
with open('/home/ubuntu/main.py', 'r', encoding='utf-8') as f: c = f.read()

pattern = r'^([ \t]*)([a-zA-Z0-9_]+)[ \t]*=[ \t]*.*?\.text_input\([^\)]*종목명 또는 종목코드 입력[^\)]*\)'

def repl(m):
    i = m.group(1)
    v = m.group(2)
    return m.group(0) + f"""
{i}# [VIP Premium Ticker Auto-Mapping Engine]
{i}if {v} and not {v}.isdigit():
{i}    sn = str({v}).upper().replace(" ", "")
{i}    pd = {{'한화오션':'042660', 'HD한국조선해양':'009540', '한화에어로스페이스':'012450', 'LIG넥스원':'079550', 'HPSP':'403870', '풍산':'103140', 'HB테크놀러지':'078150', '삼성전자':'005930', 'SK하이닉스':'000660'}}
{i}    if sn in pd: {v} = pd[sn]
{i}    else:
{i}        try:
{i}            import FinanceDataReader as fdr
{i}            import streamlit as st
{i}            @st.cache_data(ttl=86400)
{i}            def get_krx():
{i}                df = fdr.StockListing('KRX')
{i}                return dict(zip(df['Name'].str.upper().str.replace(" ", ""), df['Code']))
{i}            kd = get_krx()
{i}            if sn in kd: {v} = kd[sn]
{i}        except: pass
"""

new_c, cnt = re.subn(pattern, repl, c, flags=re.MULTILINE)

with open('/home/ubuntu/main.py', 'w', encoding='utf-8') as f: f.write(new_c)

if cnt > 0: print("=== PREMIUM TICKER ENGINE INSTALLED ===")
else: print("=== ERROR: TARGET LINE NOT FOUND ===")
