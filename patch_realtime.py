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
