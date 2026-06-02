#!/usr/bin/env python3
"""
V4 UI 패치 - 들여쓰기 자동 감지 버전
실행: python3 patch_v4_ui2.py
"""
from pathlib import Path
import shutil, re

MAIN = Path("/home/ubuntu/main.py")
shutil.copy(MAIN, MAIN.with_suffix(".py.bak_v4ui2"))

lines = MAIN.read_text(encoding="utf-8").splitlines(keepends=True)

TARGET = 'v3_bd = v3_result.get("breakdown", {}) if v3_result else {}'

new_lines = []
inserted = False

for line in lines:
    new_lines.append(line)
    if not inserted and TARGET in line:
        # 실제 들여쓰기 감지
        indent = len(line) - len(line.lstrip())
        pad = " " * indent
        inner = " " * (indent + 4)
        inner2 = " " * (indent + 8)

        insert = [
            f"{pad}# ── SUPER-NOVA V4 ──\n",
            f"{pad}try:\n",
            f"{inner}_raw = {{\n",
            f"{inner2}'market_cap': float((info or {{}}).get('시가총액', 0) or 0) * 1e8,\n",
            f"{inner2}'current_price': float((price or {{}}).get('stck_prpr', 0) or 0),\n",
            f"{inner2}'open': float((price or {{}}).get('stck_oprc', 0) or 0),\n",
            f"{inner2}'high': float((price or {{}}).get('stck_hgpr', 0) or 0),\n",
            f"{inner2}'low': float((price or {{}}).get('stck_lwpr', 0) or 0),\n",
            f"{inner2}'prev_close': float((price or {{}}).get('stck_sdpr', 0) or 0),\n",
            f"{inner2}'trading_value': float((price or {{}}).get('acml_tr_pbmn', 0) or 0),\n",
            f"{inner2}'avg_value_20d': max(float((price or {{}}).get('acml_tr_pbmn', 1) or 1), 1),\n",
            f"{inner2}'foreign_net': float((investor or {{}}).get('frgn', 0) or 0) * 1000,\n",
            f"{inner2}'inst_net': float((investor or {{}}).get('orgn', 0) or 0) * 1000,\n",
            f"{inner2}'ma5': 0, 'ma20': 0, 'days_above_ma20': 5, 'up_days': 1,\n",
            f"{inner2}'body_ratio': 0.6,\n",
            f"{inner2}'is_bullish': float((price or {{}}).get('stck_prpr', 0) or 0) >= float((price or {{}}).get('stck_oprc', 0) or 0),\n",
            f"{inner2}'short_today': 0, 'short_yesterday': 0, 'short_ratio': 0,\n",
            f"{inner2}'kospi_safe': True, 'macro_safe': True,\n",
            f"{inner}}}\n",
            f"{inner}_name = (info or {{}}).get('hts_kor_isnm', ticker)\n",
            f"{inner}render_supernova_panel(ticker, _name, _raw)\n",
            f"{pad}except Exception as _e:\n",
            f"{inner}import streamlit as _st\n",
            f"{inner}_st.warning(f'V4 오류: {{_e}}')\n",
            f"{pad}# ─────────────────────\n",
        ]
        new_lines.extend(insert)
        inserted = True
        print(f"✅ {indent}칸 들여쓰기로 V4 삽입 완료 (TARGET 줄 번호: {len(new_lines) - len(insert)})")

if not inserted:
    print(f"❌ TARGET 미발견")
    print(f"찾는 문자열: {TARGET}")
else:
    MAIN.write_text("".join(new_lines), encoding="utf-8")

    # 문법 검사
    import ast
    try:
        ast.parse(MAIN.read_text(encoding="utf-8"))
        print("✅ 문법 검사 통과!")
    except SyntaxError as e:
        print(f"❌ 문법 오류: {e.lineno}번째 줄 - {e.msg}")
        print("백업에서 복구합니다...")
        shutil.copy(MAIN.with_suffix(".py.bak_v4ui2"), MAIN)
        print("복구 완료")
