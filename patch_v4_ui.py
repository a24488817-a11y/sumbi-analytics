#!/usr/bin/env python3
"""
V4 UI 삽입 패치 - 들여쓰기 안전 버전
실행: python3 patch_v4_ui.py
"""
from pathlib import Path
import shutil

MAIN = Path("/home/ubuntu/main.py")
shutil.copy(MAIN, MAIN.with_suffix(".py.bak_v4ui"))

lines = MAIN.read_text(encoding="utf-8").splitlines(keepends=True)

TARGET = 'v3_bd = v3_result.get("breakdown", {}) if v3_result else {}'

# 삽입할 코드 (들여쓰기 8칸 = if st.button 블록 안)
INSERT = [
    "        # ── SUPER-NOVA V4 ──\n",
    "        try:\n",
    "            _raw = {\n",
    "                'market_cap': float((info or {}).get('시가총액', 0) or 0) * 1e8,\n",
    "                'current_price': float((price or {}).get('stck_prpr', 0) or 0),\n",
    "                'open': float((price or {}).get('stck_oprc', 0) or 0),\n",
    "                'high': float((price or {}).get('stck_hgpr', 0) or 0),\n",
    "                'low': float((price or {}).get('stck_lwpr', 0) or 0),\n",
    "                'prev_close': float((price or {}).get('stck_sdpr', 0) or 0),\n",
    "                'trading_value': float((price or {}).get('acml_tr_pbmn', 0) or 0),\n",
    "                'avg_value_20d': max(float((price or {}).get('acml_tr_pbmn', 1) or 1), 1),\n",
    "                'foreign_net': float((investor or {}).get('frgn', 0) or 0) * 1000,\n",
    "                'inst_net': float((investor or {}).get('orgn', 0) or 0) * 1000,\n",
    "                'ma5': 0, 'ma20': 0, 'days_above_ma20': 5, 'up_days': 1,\n",
    "                'body_ratio': 0.6,\n",
    "                'is_bullish': float((price or {}).get('stck_prpr', 0) or 0) >= float((price or {}).get('stck_oprc', 0) or 0),\n",
    "                'short_today': 0, 'short_yesterday': 0, 'short_ratio': 0,\n",
    "                'kospi_safe': True, 'macro_safe': True,\n",
    "            }\n",
    "            _name = (info or {}).get('hts_kor_isnm', ticker)\n",
    "            render_supernova_panel(ticker, _name, _raw)\n",
    "        except Exception as _e:\n",
    "            import streamlit as _st\n",
    "            _st.warning(f'V4 오류: {_e}')\n",
    "        # ─────────────────────\n",
]

new_lines = []
inserted = False
for line in lines:
    new_lines.append(line)
    if not inserted and TARGET in line:
        new_lines.extend(INSERT)
        inserted = True

if inserted:
    MAIN.write_text("".join(new_lines), encoding="utf-8")
    print("✅ V4 UI 삽입 완료")
else:
    print("❌ TARGET 미발견 - main.py 구조 확인 필요")
    print(f"찾는 문자열: {TARGET}")
