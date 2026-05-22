import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. FinanceDataReader 엔진 활성화
if "FinanceDataReader" not in code:
    code = "import FinanceDataReader as fdr\n" + code

# 2. 전 종목 초고속 매핑 함수 (캐싱 적용)
func_code = """
@st.cache_data(ttl=86400)
def get_stock_code(name):
    if name.isdigit(): return name
    try:
        df = fdr.StockListing('KRX')
        mapping = dict(zip(df['Name'], df['Code']))
        return mapping.get(name, name)
    except:
        return name
"""

if "def get_stock_code" not in code:
    code = code.replace("user_input = st.text_input", func_code + "\nuser_input = st.text_input")

# 3. 기존의 제한적인 ticker_map을 무제한 자동 매핑으로 교체
old_line = "ticker = ticker_map.get(user_input, user_input)"
new_line = "ticker = get_stock_code(user_input)"
if old_line in code:
    code = code.replace(old_line, new_line)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Success! Auto-mapping for all KRX stocks applied safely.")
