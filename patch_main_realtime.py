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
