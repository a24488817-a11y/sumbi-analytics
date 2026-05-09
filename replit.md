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
- **Stock Dashboard**: Python 3.11 + Streamlit, `artifacts/stock-dashboard/main.py` (~4300 lines)

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
- `get_investor_data_naver(ttl=60s)` — frgn.naver 확정 수급 (42대 점수에 사용) **GOLDEN RULE**
- `_get_investor_detail_naver(ttl=60s)` — 4주체(기관·외국인·개인·기타법인) 상세 수급 (표시 전용)
  - 기타법인 = -(개인 + 기관 + 외국인) 역산 — 블록딜 추적 핵심 지표
- `_get_krx_ref_date(ttl=60s)` — frgn.naver em.date KRX 기준일 파싱 (표시 전용)
- `_get_sise_today_price(ttl=60s)` — sise_day.naver 당일 가격 (잠정 행 전용)
- `_investor_html_table(inv_data, ticker)` — 잠정/확정 이원화 HTML 테이블 (기타법인 열 자동 표시)
- `_analyze_investor_flow(inv_data)` — 5거래일 누적 4주체 수급 분석 → 결론 도출 (표시 전용)
  - 블록딜 패턴: other<-200k + indiv>200k + inst<0 + frgn<0 → "최악 수급 구조" verdict
- `get_naver_news_full(ticker)` — URL 포함 뉴스 수집 `{title, url, date}` (표시 전용)
- `get_naver_news_api(query, display=100)` — **[V9.0 정식 채널]** 네이버 검색 오픈 API (NAVER_CLIENT_ID/SECRET), HTML태그+엔티티 완전 제거, TTL=300s
- `get_news(ticker, name, aliases)` — **[V9.0]** 1차=오픈API, 2차=크롤링 폴백, Flexible Match 필터 동일 적용; `{"items":[{title,url,date,description}], "status", "fetch_count"}`

## Architecture Decisions

- **배치 스캔 버그 수정 (2026-05-08)**: `NameError: name 'os' is not defined` in `get_naver_news_api()` — `import os` 누락으로 `quick_score()` 500종목 전부 `return None` → `scored=[]`. 수정: 파일 상단에 `import os` 추가. 추가 수정사항: `@st.cache_data` 제거 from `quick_score()` (ThreadPool 호환), `get_top_volume_tickers()`와 `_scan_top_cached()` TTL 300s로 조정 (스캔 시간 ~90초 vs 구 TTL=60초 불일치 해소).
- **수급 데이터 날짜 정렬 방어 (2026-05-09)**: `get_investor_flow()` — frgn.naver 파싱 후 `sort_values(by=날짜, ascending=False).reset_index(drop=True)` 적용. `inv[0]`이 항상 T-0(당일 최신) 데이터임을 명시적으로 보장. 과거 데이터 참조 원천 차단.
- **쌍끌이 매도 경보 추가 (2026-05-09)**: `score_investor()` — `inst_vals[0] < 0 and frgn_vals[0] < 0` 조건 시 `"⚠️ 기관·외국인 쌍끌이 매도 (주의)"` detail 텍스트 추가. 점수 영향 없음, 표시 전용. 소유자 제출 코드 반영.
- **증권 섹터 뉴스 노이즈 필터 (2026-05-09)**: `score_news(news, sector="일반")` — `sector="금융"` 시 `_SECURITIES_NOISE_KW`("매수 추천", "목표주가 유지", "투자의견", "종목 추천" 등 8개)에 걸리는 뉴스를 noise_list로 강제 이동, 점수 0. 타사 리포트 발간 뉴스가 해당 증권사 자체 호재로 오분류되는 문제 해소. `analyze_ticker()` + `quick_score()` 두 호출 지점 모두 `_detect_sector(name)` 전달. 기타 섹터는 무영향.
- **안전마진 Kill Switch (2026-05-09)**: `ui_score_card()` — `현재가 ≥ 목표주가(증권사)` 조건 발동 시 표시 점수만 -30 (`display_total = max(0, total-30)`). 원본 `r["total"]` 불변(랭킹 순위 영향 없음). 분할 매수(45점) 이상 판정 강제 취소 → badge="관망/매도 (안전마진 부족 및 고평가 구간)" 덮어쓰기. 히어로 배너·게이지·badge 모두 `display_total` 기준. 🚨 경보 카드 게이지 상단에 표시 (현재가·목표주가·괴리율 수치 포함).
- **뉴스 파이프라인 V9.0 (2026-05-08)**: `get_news()` 1차 채널을 웹 크롤링 → 네이버 검색 오픈 API로 전면 교체. 크롤링은 API 키 미설정 또는 API 오류 시에만 자동 폴백. `score_news()` NLP 엔진·Flexible Match 로직은 무변경. 아이템 구조에 `description` 필드 추가 (NLP 확장 대비).
- **GOLDEN RULE**: 42대 필살기 점수 로직 절대 불변. `get_investor_data_naver()`, `calc_pullback_score()` 등 점수 함수는 절대 수정 금지. ※ `score_investor()` 는 소유자 지시(2026-05-08)로 쌍끌이 15점 보너스 로직 추가 — 이후 수정은 소유자 명시적 승인 필요.
- **이중 파이프라인**: `_sinv` (GOLDEN RULE, 점수용) + `_sinv_detail` (기타법인 포함, 표시용) 분리 운영.
- **CSS iframe 격리**: `st.html()` 은 별도 iframe으로 렌더링 → `st.markdown()` CSS 미적용. 스나이퍼 카드 등 `st.html()` 내부에 `<style>` 블록 직접 포함 필수.
- `get_investor_batch(ttl=60s)` — 배치 투자자 수집 (TTL 60s로 빠른 자동갱신)
- KRX 공휴일은 `_get_krx_holidays()` 함수가 open.krx.co.kr OTP API로 자동 취득
- 사이드바 ⚡ 버튼 = `st.cache_data.clear()` + `st.rerun()` (즉시 갱신)

## Product

- KOSPI / KOSDAQ 동시 분석 (거래대금 상위 15종목 자동 선별)
- 42대 필살기: 기관/연기금(30점) + 공매도상환(20점) + 눌림목(30점) + 뉴스호재(20점)
- **단일 종목 정밀 스나이퍼**: 기관·외국인·개인·기타법인(블록딜) 4주체 수급 잠정/확정 이원화 표시
- 종목별 뉴스 호재·악재·중립 자동 분류 (🔗 원문 링크 포함)
- **5거래일 수급 결론 카드**: 4주체 누적 → "세력 쌍끌이 매집" / "기타법인 블록딜 최악 수급" 등 직관적 판정
- KRX 시장 상태 실시간 표시 (장 중 / 장 마감 / 공휴일)
- **심층 팩트체크**: 블록딜·오버행·수주·유상증자 등 10+7종 키워드 자동 감지 → 핵심 분석 카드
- **기업 펀더멘털**: 네이버 모바일 API(PER/PBR) + 네이버 기업분석 HTML(ROE/배당수익률) + yfinance fallback, 12개 섹터 해자 분석 3줄 (expander)
- **공매도 T+2 보정**: 점수 0 → `T+2 집계 대기 중 (확정 데이터 미반영)` 명시
- **한화오션 특수 경보**: 기타법인 블록딜 + 개인 전량 수취 구조 자동 감지 → 최악 수급 서사 출력

## Display-Only Functions (42대 점수 무영향)

- `_get_investor_detail_naver(ticker, ttl=60s)` — 4주체 수급 상세 (기타법인 역산 포함)
- `get_short_balance_naver(ticker, ttl=300s)` — 네이버 공매도 잔고 현황
- `get_fundamentals(ticker, market, ttl=3600s)` — 네이버 모바일 JSON API(PER·PBR) → 네이버 기업분석 HTML(ROE·배당수익률) → yfinance fallback 순서로 수집
- `_get_moat_analysis(sector)` — 12개 섹터 해자 DB 3줄 분석
- `_build_factcheck_alerts(news_list, stock_name)` — 블록딜·수주 등 키워드 감지
- `_analyze_investor_flow(inv_data)` — 누적 수급 결론 도출

## Gotchas

- `_investor_html_table()` 는 표시 전용 — 42대 점수에 절대 사용하지 말 것
- `_sinv_detail`(기타법인 포함) vs `_sinv`(골든룰 점수용) 혼동 금지 — 점수 계산엔 반드시 `_sinv` 사용
- 기타법인 열은 `has_other = any(기타법인 != 0)` 조건에 맞을 때만 테이블에 표시됨
- `st.html()` 내부에 CSS 클래스 사용 시 반드시 해당 `st.html()` 블록 안에 `<style>` 포함
- frgn.naver는 당일 저녁(~18:00 KST)에 확정치 반영. TTL=60s가 자동 감지.
- sise_day.naver의 전일비 컬럼 형식: "상승33,500" / "하락1,000" — 숫자 파싱 시 한글 제거 필요
- Python 3.11: f-string 내 중첩 따옴표 불가 — 색상값은 반드시 변수로 미리 추출 후 참조
- 뉴스 아이템은 3-튜플 `(headline_str, kw_tag_html, url_str)` — 기존 2-튜플과 혼용 금지
- `_GOOD_KW`/`_BAD_KW`/`_UNREF_KW` 에 업종 특화 키워드 포함 (HBM, LNG선, K방산 등)
