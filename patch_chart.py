import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

target = "st.write('\\ub274\\uc2a4\\ub97c \\ubd88\\ub7ec\\uc62c \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.')"

if "st.plotly_chart" in code:
    print("Chart module already installed.")
else:
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if target in line:
            curr_indent = line[:len(line) - len(line.lstrip())]
            base = curr_indent[:-4] if len(curr_indent) >= 4 else curr_indent
            
            new_lines.append(base + "st.markdown('---')")
            new_lines.append(base + "st.markdown('### \\ucc28\\ud2b8 \\ubd84\\uc11d (5\\uc77c/20\\uc77c\\uc120)')")
            new_lines.append(base + "try:")
            new_lines.append(base + "    import datetime")
            new_lines.append(base + "    import plotly.graph_objects as go")
            new_lines.append(base + "    start_date = (datetime.datetime.now() - datetime.timedelta(days=120)).strftime('%Y-%m-%d')")
            new_lines.append(base + "    df_chart = fdr.DataReader(ticker, start_date)")
            new_lines.append(base + "    df_chart['MA5'] = df_chart['Close'].rolling(window=5).mean()")
            new_lines.append(base + "    df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()")
            new_lines.append(base + "    fig = go.Figure()")
            new_lines.append(base + "    fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name='\\uc8fc\\uac00'))")
            new_lines.append(base + "    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA5'], line=dict(color='orange', width=1.5), name='5\\uc77c\\uc120'))")
            new_lines.append(base + "    fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], line=dict(color='blue', width=1.5), name='20\\uc77c\\uc120'))")
            new_lines.append(base + "    fig.update_layout(template='plotly_dark', margin=dict(l=0, r=0, t=30, b=0), height=400, xaxis_rangeslider_visible=False)")
            new_lines.append(base + "    st.plotly_chart(fig, use_container_width=True)")
            new_lines.append(base + "except Exception as e:")
            new_lines.append(base + "    st.write('\\ucc28\\ud2b8\\ub97c \\ubd88\\ub7ec\\uc62c \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.')")

    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("Success! Chart integration applied safely.")
