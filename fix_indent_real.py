import os
filepath = os.path.expanduser("~/main.py")
with open(filepath, "r", encoding="utf-8") as f: lines = f.readlines()

# 들여쓰기가 필요한 줄번호를 찾아 강제로 4칸 공백을 넣습니다.
new_lines = []
for line in lines:
    if line.strip() in ["import streamlit as st", "st.markdown('''<style>"]:
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f: f.writelines(new_lines)
