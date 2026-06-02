import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

if "news.google.com" in code:
    print("News module already installed.")
else:
    target = "c3.metric('\\uac1c\\uc778 (\\uc8fc)', f'{prsn:,}')"
    lines = code.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if target in line:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + "st.markdown('---')")
            # 이모티콘 완전 제거, 순수 유니코드 '최신 뉴스'만 출력
            new_lines.append(indent + "st.markdown('### \\ucd5c\\uc2e0 \\ub274\\uc2a4')")
            new_lines.append(indent + "try:")
            new_lines.append(indent + "    import requests, urllib.parse")
            new_lines.append(indent + "    import xml.etree.ElementTree as ET")
            new_lines.append(indent + "    q = urllib.parse.quote(user_input)")
            new_lines.append(indent + "    r = requests.get(f'https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko', timeout=5)")
            new_lines.append(indent + "    root = ET.fromstring(r.text)")
            new_lines.append(indent + "    items = root.findall('.//item')[:5]")
            new_lines.append(indent + "    for item in items:")
            new_lines.append(indent + "        title = item.find('title').text")
            new_lines.append(indent + "        link = item.find('link').text")
            new_lines.append(indent + "        st.markdown(f'- [{title}]({link})')")
            new_lines.append(indent + "except Exception as e:")
            new_lines.append(indent + "    st.write('\\ub274\\uc2a4\\ub97c \\ubd88\\ub7ec\\uc62c \\uc218 \\uc5c6\\uc2b5\\ub2c8\\ub2e4.')")
    
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("Success! News integration applied safely.")
