import io
with io.open('main.py', 'r', encoding='utf-8') as f: code = f.read()
old = """st.markdown(f'<div class="card">{txt_mapping}<br><div class="card-val">{res}</div></div>', unsafe_allow_html=True)"""
new = """st.markdown(f'<div class="card" style="text-align:center;">{txt_mapping}</div>', unsafe_allow_html=True)
                    orgn = int(res.get("orgn_ntby_qty", "0"))
                    frgn = int(res.get("frgn_ntby_qty", "0"))
                    prsn = int(res.get("prsn_ntby_qty", "0"))
                    c1, c2, c3 = st.columns(3)
                    c1.metric("기관 (주)", f"{orgn:,}")
                    c2.metric("외국인 (주)", f"{frgn:,}")
                    c3.metric("개인 (주)", f"{prsn:,}")"""
if old in code:
    code = code.replace(old, new)
    with io.open('main.py', 'w', encoding='utf-8') as f: f.write(code)
    print("Success! UI Update Complete. Please refresh your browser.")
else:
    print("Error: Target code not found.")
