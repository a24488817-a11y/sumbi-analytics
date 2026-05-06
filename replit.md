# Workspace

## Overview

pnpm workspace monorepo (TypeScript) + Python Streamlit stock dashboard.
Primary product: **숨비 애널리틱스 (SOOMBI Analytics)** — Korean KRX stock market dashboard with 42대 필살기 AI scoring.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **Build**: esbuild (CJS bundle)
- **Stock Dashboard**: Python 3 + Streamlit, `artifacts/stock-dashboard/main.py` (~3100 lines)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

## KRX Investor Data Pipeline (핵심 발견)

**frgn.naver 데이터 반영 타임라인** (실측):
- `09:00~15:30` 장 중: 전일 확정치만 표시 → 잠정 행 삽입 (배지: `장중`)
- `15:30~18:00` 마감 후~집계: 확정치 미반영 → 배지 `가집계완료·확정대기`
- `~18:00` 이후: frgn.naver **당일 확정치 자동 반영** (D+1 아님, 당일 저녁)
- KRX 공식 가집계(per-종목 순매수)는 data.krx.co.kr 로그인 필요 — 공개 API 없음

**파이프라인 함수**:
- `get_investor_data_naver(ttl=60s)` — frgn.naver 확정 수급 (42대 점수에 사용)
- `_get_krx_ref_date(ttl=60s)` — frgn.naver em.date KRX 기준일 파싱 (표시 전용)
- `_get_sise_today_price(ttl=60s)` — sise_day.naver 당일 가격 (잠정 행 전용)
- `_investor_html_table()` — 잠정/확정 이원화 HTML 테이블 렌더러

## Architecture Decisions

- **GOLDEN RULE**: 42대 필살기 점수 로직 절대 불변. `get_investor_data_naver()`, `score_ticker()`, `calc_pullback_score()` 등 점수 함수는 절대 수정 금지.
- **CSS iframe 격리**: `st.html()` 은 별도 iframe으로 렌더링 → `st.markdown()` CSS 미적용. 스나이퍼 카드 등 `st.html()` 내부에 `<style>` 블록 직접 포함 필수.
- `get_investor_batch(ttl=60s)` — 배치 투자자 수집 (TTL 60s로 빠른 자동갱신)
- KRX 공휴일은 `_get_krx_holidays()` 함수가 open.krx.co.kr OTP API로 자동 취득
- 사이드바 ⚡ 버튼 = `st.cache_data.clear()` + `st.rerun()` (즉시 갱신)

## Product

- KOSPI / KOSDAQ 동시 분석 (거래대금 상위 15종목 자동 선별)
- 42대 필살기: 기관/연기금(30점) + 공매도상환(20점) + 눌림목(30점) + 뉴스호재(20점)
- 단일 종목 정밀 스나이퍼: 기관·외국인 수급 잠정/확정 이원화 표시
- 종목별 뉴스 호재·악재·중립 자동 분류
- KRX 시장 상태 실시간 표시 (장 중 / 장 마감 / 공휴일)
- **심층 팩트체크**: 블록딜·오버행·수주·유상증자 등 10+7종 키워드 자동 감지 → 핵심 분석 카드
- **기업 펀더멘털**: yfinance PER/PBR/ROE + 12개 섹터 해자 분석 3줄 (expander)
- **공매도 T+2 보정**: 점수 0 → `집계 중(T+2)` / 잔고율 확인 시 표기

## Display-Only Functions (42대 점수 무영향)

- `get_short_balance_naver(ticker, ttl=300s)` — 네이버 공매도 잔고 현황 (표시 전용)
- `get_fundamentals(ticker, market, ttl=3600s)` — yfinance PER/PBR/ROE (표시 전용)
- `_get_moat_analysis(sector)` — 12개 섹터 해자 DB 3줄 분석 (표시 전용)
- `_build_factcheck_alerts(news_list, stock_name)` — 블록딜·수주 등 키워드 감지 (표시 전용)

## Gotchas

- `_investor_html_table()` 는 표시 전용 — 42대 점수에 절대 사용하지 말 것
- `st.html()` 내부에 CSS 클래스 사용 시 반드시 해당 `st.html()` 블록 안에 `<style>` 포함
- frgn.naver는 당일 저녁(~18:00 KST)에 확정치 반영. TTL=60s가 자동 감지.
- sise_day.naver의 전일비 컬럼 형식: "상승33,500" / "하락1,000" — 숫자 파싱 시 한글 제거 필요
