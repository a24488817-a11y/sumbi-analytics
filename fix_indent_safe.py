import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

target = "st.markdown(f'<div class=\"card\">{txt_mapping}<br><div class=\"card-val\">{res}</div></div>', unsafe_allow_html=True)"

with io.open('main.py', 'w', encoding='utf-8') as f:
    for line in lines:
        if target in line:
            indent = line[:len(line) - len(line.lstrip())]
            f.write(indent + "st.markdown(f'<div class=\"card\" style=\"text-align:center;\">{txt_mapping}</div>', unsafe_allow_html=True)\n")
            f.write(indent + "orgn = int(res.get('orgn_ntby_qty', '0'))\n")
            f.write(indent + "frgn = int(res.get('frgn_ntby_qty', '0'))\n")
            f.write(indent + "prsn = int(res.get('prsn_ntby_qty', '0'))\n")
            f.write(indent + "c1, c2, c3 = st.columns(3)\n")
            f.write(indent + "c1.metric('\\uae30\\uad00 (\\uc8fc)', f'{orgn:,}')\n")
            f.write(indent + "c2.metric('\\uc678\\uad6d\\uc778 (\\uc8fc)', f'{frgn:,}')\n")
            f.write(indent + "c3.metric('\\uac1c\\uc778 (\\uc8fc)', f'{prsn:,}')\n")
        else:
            f.write(line)

print("Success! Code patched safely without Korean character corruption.")
