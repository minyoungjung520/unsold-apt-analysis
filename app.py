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

st.set_page_config(page_title="미분양 아파트 감액가 판단 도구", layout="wide")
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
st.title("🏢 미분양 아파트 감액가 판단 보조 도구")

# 입력 섹션
st.header("📋 단지 정보 입력")
col1, col2, col3, col4 = st.columns(4)
with col1:
    location = st.text_input("소재지", placeholder="예: 대구 수성구 범어동")
with col2:
    apt_name = st.text_input("아파트명", placeholder="예: 범어자이")
with col3:
    area = st.selectbox("면적", ["59㎡", "74㎡", "84㎡", "101㎡", "114㎡", "기타"])
with col4:
    appraisal_value = st.number_input("감정가 (만원)", min_value=0, step=100)

search_btn = st.button("🔍 검색", type="primary", use_container_width=True)

if search_btn:
    if not location or not apt_name or not area or appraisal_value == 0:
        st.warning("소재지, 아파트명, 감정가를 모두 입력해주세요.")
    else:
        with st.spinner("정보 수집 중..."):
            st.info("⚠️ 현재 데모 버전입니다. 실제 데이터 수집 기능은 추후 연동 예정입니다.")

            # 데모 데이터
            demo_data = {
                "단지명": apt_name,
                "소재지": location,
                "검색일": str(date.today()),
                "면적": area,
                "감정가_만원": appraisal_value,
                "최초분양가_만원": 85000,
                "전체세대수": 648,
                "평형별세대수": {"59㎡": 200, "84㎡": 350, "101㎡": 98},
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
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("최초 분양가", f"{demo_data['최초분양가_만원']:,}만원")
            c2.metric("전체 세대수", f"{demo_data['전체세대수']:,}세대")
            c3.metric("미분양 세대", f"{demo_data['미분양세대수']}세대")
            c4.metric("미분양 비율", f"{demo_data['미분양비율_퍼센트']}%")

            st.subheader("평형별 세대수 / 미분양")
            cols = st.columns(len(demo_data["평형별세대수"]))
            for i, (size, count) in enumerate(demo_data["평형별세대수"].items()):
                unsold = demo_data["평형별미분양"].get(size, 0)
                unsold_pct = round(unsold / count * 100) if count > 0 else 0
                cols[i].metric(size, f"{count}세대", delta=f"미분양 {unsold}세대 ({unsold_pct}%)", delta_color="inverse")

            st.divider()
            st.header("💰 시세 참고")
            c1, c2 = st.columns(2)
            c1.metric("현재 할인율", f"{demo_data['현재할인율_퍼센트']}%")
            c2.metric("할인 후 가격", f"{demo_data['할인후가격_만원']:,}만원")

            st.subheader("할인가격 판단 근거")
            for src in demo_data["할인판단근거"]:
                icon = "📰" if src["출처유형"] == "뉴스" else ("▶️" if src["출처유형"] == "유튜브" else "📝")
                st.markdown(f"{icon} **[{src['매체']}]** [{src['제목']}]({src['링크']}) — {src['날짜']}")

            st.subheader("인근 아파트 시세 (같은 동 세대수 상위 3개)")
            for apt in demo_data["인근아파트시세"]:
                st.write(f"- **{apt['단지명']}** ({apt['세대수']:,}세대) — 84㎡ 기준 {apt['84㎡시세_만원']:,}만원")

            st.divider()
            st.header("🧠 감정가 적절성 의견")
            discount_price = demo_data["할인후가격_만원"]
            diff = appraisal_value - discount_price
            diff_pct = round(diff / discount_price * 100, 1)

            c1, c2, c3 = st.columns(3)
            c1.metric("입력 감정가", f"{appraisal_value:,}만원")
            c2.metric("시장 할인 후 가격", f"{discount_price:,}만원")
            c3.metric("차이", f"{diff:+,}만원", delta=f"{diff_pct:+}%", delta_color="inverse")

            if diff_pct > 10:
                st.error(f"⚠️ **추가 감액 검토 권고**\n\n해당 단지는 미분양 비율 {demo_data['미분양비율_퍼센트']}%, 할인율 {demo_data['현재할인율_퍼센트']}% 수준입니다. 입력 감정가는 현 시장 할인가 대비 {diff_pct}% 높아 고평가 가능성이 있습니다. 인근 시세 및 미분양 추이를 고려한 추가 감액 검토를 권고합니다.")
            elif diff_pct < -10:
                st.success(f"✅ **감정가 적정 수준**\n\n입력 감정가는 현 시장 할인가 대비 {abs(diff_pct)}% 낮아 보수적으로 평가된 상태입니다.")
            else:
                st.warning(f"🟡 **감정가 시장 수준 근접**\n\n입력 감정가는 현 시장 할인가와 유사한 수준입니다. 미분양 추이 변화를 모니터링할 것을 권고합니다.")

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
