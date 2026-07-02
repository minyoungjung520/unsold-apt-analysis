import streamlit as st
import json
import os
from datetime import date

DATA_FILE = "history.json"

def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(record):
    history = load_history()
    history.append(record)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="미분양 아파트 감정가 적정성 분석", layout="wide")
st.markdown("""
<style>
[data-testid="metric-container"] {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 15px;
}
[data-testid="metric-container"] label {
    font-size: 1rem !important;
    font-weight: 600;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)
st.title("🏢 미분양 아파트 감정가 적정성 분석")

# 입력 섹션
st.header("📋 단지 정보 입력")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    location = st.text_input("소재지", placeholder="예: 대구 수성구 범어동")
with col2:
    apt_name = st.text_input("아파트명", placeholder="예: 범어자이")
with col3:
    st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
    search_btn = st.button("🔍 검색", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if search_btn:
    if not location or not apt_name:
        st.warning("소재지와 아파트명을 입력해주세요.")
    else:
        with st.spinner("정보 수집 중..."):
            st.info("⚠️ 현재 데모 버전입니다. 실제 데이터 수집 기능은 추후 연동 예정입니다.")

            # 데모 데이터
            demo_data = {
                "단지명": apt_name,
                "소재지": location,
                "검색일": str(date.today()),
                "최초분양일자": "2023-03-15",
                "평형별분양가_만원": {"59㎡": 52000, "84㎡": 68000, "101㎡": 85000},
                "전체세대수": 648,
                "평형별세대수": {"59㎡": 200, "84㎡": 350, "101㎡": 98},
                "평형별최초미분양": {"59㎡": 120, "84㎡": 180, "101㎡": 60},
                "평형별미분양": {"59㎡": 85, "84㎡": 112, "101㎡": 30},
                "미분양세대수": 227,
                "미분양비율_퍼센트": 35,
                "현재할인율_퍼센트": 18,
                "할인후가격_만원": 69700,
                "할인판단근거": [
                    {"출처유형": "뉴스", "매체": "OO일보", "제목": f"{apt_name} 미분양 18% 할인 분양 중", "날짜": "2026-06-10", "링크": "https://example.com/news1"},
                    {"출처유형": "유튜브", "매체": "부동산스터디", "제목": f"[현장] {apt_name} 직접 가봤습니다", "날짜": "2026-06-05", "링크": "https://youtube.com/example"},
                    {"출처유형": "블로그", "매체": "네이버 블로그", "제목": f"{apt_name} 실거주 후기 + 할인 조건 공개", "날짜": "2026-05-28", "링크": "https://blog.naver.com/example"},
                ],
                "인근아파트시세": [
                    {"단지명": "인근A아파트", "세대수": 1200, "84㎡시세_만원": 72000},
                    {"단지명": "인근B아파트", "세대수": 980, "84㎡시세_만원": 68000},
                    {"단지명": "인근C아파트", "세대수": 750, "84㎡시세_만원": 65000},
                ],
            }

            # 결과 표시
            st.success("수집 완료!")
            st.divider()

            st.header("📊 단지 기본 정보")

            # 최초분양일자 + 전체세대수
            c1, c2 = st.columns(2)
            c1.metric("최초 분양일자", demo_data["최초분양일자"])
            c2.metric("전체 세대수", f"{demo_data['전체세대수']:,}세대")

            st.divider()

            # 평형별 테이블
            sizes = list(demo_data["평형별세대수"].keys())
            st.subheader("평형별 상세 현황")

            header_cols = st.columns(len(sizes) + 1)
            header_cols[0].markdown("**구분**")
            for i, size in enumerate(sizes):
                header_cols[i+1].markdown(f"**{size}**")

            # 최초분양가
            row1 = st.columns(len(sizes) + 1)
            row1[0].markdown("최초 분양가")
            for i, size in enumerate(sizes):
                price = demo_data["평형별분양가_만원"].get(size, 0)
                row1[i+1].markdown(f"{price:,}만원")

            # 전체세대수
            row2 = st.columns(len(sizes) + 1)
            row2[0].markdown("전체 세대수")
            for i, size in enumerate(sizes):
                count = demo_data["평형별세대수"].get(size, 0)
                row2[i+1].markdown(f"{count}세대")

            # 최초 미분양
            row3 = st.columns(len(sizes) + 1)
            row3[0].markdown("최초 미분양")
            for i, size in enumerate(sizes):
                count = demo_data["평형별세대수"].get(size, 0)
                unsold = demo_data["평형별최초미분양"].get(size, 0)
                pct = round(unsold / count * 100) if count > 0 else 0
                row3[i+1].markdown(f"<span style='color:#1E90FF'>{unsold}세대 ({pct}%)</span>", unsafe_allow_html=True)

            # 현 미분양
            row4 = st.columns(len(sizes) + 1)
            row4[0].markdown("현 미분양")
            for i, size in enumerate(sizes):
                count = demo_data["평형별세대수"].get(size, 0)
                unsold = demo_data["평형별미분양"].get(size, 0)
                pct = round(unsold / count * 100) if count > 0 else 0
                row4[i+1].markdown(f"<span style='color:#1E90FF; font-weight:bold'>{unsold}세대 ({pct}%)</span>", unsafe_allow_html=True)

            st.divider()
            st.header("💰 시세 참고")
            st.metric("현재 할인율", f"{demo_data['현재할인율_퍼센트']}%")

            st.subheader("할인가격 판단 근거")
            for src in demo_data["할인판단근거"]:
                icon = "📰" if src["출처유형"] == "뉴스" else ("▶️" if src["출처유형"] == "유튜브" else "📝")
                st.markdown(f"{icon} **[{src['매체']}]** [{src['제목']}]({src['링크']}) — {src['날짜']}")

            st.subheader("인근 아파트 시세 (같은 동 세대수 상위 3개)")
            for apt in demo_data["인근아파트시세"]:
                price = apt["84㎡시세_만원"]
                per_sqm = round(price / 84)
                st.write(f"- **{apt['단지명']}** ({apt['세대수']:,}세대) — 84㎡ 기준 {price:,}만원 [㎡당 {per_sqm:,}만원]")

            st.divider()
            st.header("🧠 종합 의견")
            st.warning(f"해당 단지는 미분양 비율 {demo_data['미분양비율_퍼센트']}%, 할인율 {demo_data['현재할인율_퍼센트']}% 수준입니다. 최근 할인율 확대 추세와 인근 시세를 고려할 때 감정가 산정 시 추가 감액 검토를 권고합니다.")

            # 이력 저장
            save_history(demo_data)

# 이력 섹션
st.divider()
st.header("📁 검색 이력")
history = load_history()
if history:
    for i, record in enumerate(reversed(history[-10:])):
        with st.expander(f"{record['검색일']} — {record['소재지']} {record['단지명']}"):
            st.json(record)
else:
    st.info("아직 검색 이력이 없습니다.")
