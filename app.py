import streamlit as st
import json
import os
import requests
from datetime import date

DATA_FILE = "history.json"
API_KEY = "249ddd18120a1443dc20fe3d9357df0242b922635e560f018de66870572b548d"

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

def fetch_apt_info(apt_name):
    url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
    headers = {"Authorization": f"Infuser {API_KEY}"}
    params = {
        "page": 1,
        "perPage": 5,
        "cond[HOUSE_NM::LIKE]": apt_name,
        "returnType": "json"
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    if data.get("currentCount", 0) == 0:
        return None
    # 정확히 일치하는 단지 우선, 없으면 첫 번째
    for item in data["data"]:
        if item.get("HOUSE_NM", "") == apt_name:
            return item
    return data["data"][0]

def fetch_apt_cmpet(house_manage_no, pblanc_no):
    url = "https://api.odcloud.kr/api/ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet"
    headers = {"Authorization": f"Infuser {API_KEY}"}
    params = {
        "page": 1,
        "perPage": 100,
        "cond[HOUSE_MANAGE_NO::EQ]": house_manage_no,
        "cond[PBLANC_NO::EQ]": pblanc_no,
        "returnType": "json"
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("data", [])

def calc_initial_unsold(cmpet_data, house_ty, suply_hshldco):
    # △숫자 형태에서 미달 세대수 추출
    import re
    unsold = 0
    for item in cmpet_data:
        if item.get("HOUSE_TY", "").strip() == house_ty.strip():
            rate = item.get("CMPET_RATE", "")
            match = re.search(r'△(\d+)', rate)
            if match:
                unsold = max(unsold, int(match.group(1)))
    return unsold

def fetch_apt_model(house_manage_no, pblanc_no):
    url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancMdl"
    headers = {"Authorization": f"Infuser {API_KEY}"}
    params = {
        "page": 1,
        "perPage": 50,
        "cond[HOUSE_MANAGE_NO::EQ]": house_manage_no,
        "cond[PBLANC_NO::EQ]": pblanc_no,
        "returnType": "json"
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    return data.get("data", [])

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
        with st.spinner("청약홈 데이터 수집 중..."):
            try:
                apt_info = fetch_apt_info(apt_name)

                if not apt_info:
                    st.error("해당 아파트 정보를 찾을 수 없습니다. 아파트명을 확인해주세요.")
                else:
                    house_manage_no = apt_info.get("HOUSE_MANAGE_NO", "")
                    pblanc_no = apt_info.get("PBLANC_NO", "")
                    models = fetch_apt_model(house_manage_no, pblanc_no)
                    cmpet_data = fetch_apt_cmpet(house_manage_no, pblanc_no)

                    # 평형별 데이터 정리
                    평형별세대수 = {}
                    평형별분양가 = {}
                    평형별최초미분양 = {}
                    평형별타입키 = {}
                    for m in models:
                        house_type = m.get("HOUSE_TY", "")
                        size = m.get("SUPLY_AR", "")
                        if house_type:
                            size_label = f"{house_type}({float(size):.1f}㎡)" if size else house_type
                            count = int(m.get("SUPLY_HSHLDCO", 0) or 0)
                            평형별세대수[size_label] = count
                            평형별분양가[size_label] = int(m.get("LTTOT_TOP_AMOUNT", 0) or 0)
                            평형별타입키[size_label] = house_type
                            unsold = calc_initial_unsold(cmpet_data, house_type, count)
                            평형별최초미분양[size_label] = unsold

                    전체세대수 = int(apt_info.get("TOT_SUPLY_HSHLDCO", 0) or 0)
                    분양일자 = apt_info.get("RCRIT_PBLANC_DE", "-")
                    주소 = apt_info.get("HSSPLY_ADRES", location)

                    st.success(f"✅ '{apt_info.get('HOUSE_NM')}' 데이터 수집 완료!")
                    st.divider()

                    st.header("📊 단지 기본 정보")
                    c1, c2 = st.columns(2)
                    c1.metric("최초 분양일자", 분양일자)
                    c2.metric("전체 세대수", f"{전체세대수:,}세대")
                    st.caption(f"📍 {주소}")

                    if 평형별세대수:
                        st.divider()
                        st.subheader("평형별 상세 현황")
                        sizes = list(평형별세대수.keys())

                        header_cols = st.columns(len(sizes) + 1)
                        header_cols[0].markdown("**구분**")
                        for i, size in enumerate(sizes):
                            header_cols[i+1].markdown(f"**{size}**")

                        row1 = st.columns(len(sizes) + 1)
                        row1[0].markdown("최초 분양가")
                        for i, size in enumerate(sizes):
                            price = 평형별분양가.get(size, 0)
                            row1[i+1].markdown(f"{price:,}만원" if price else "-")

                        row2 = st.columns(len(sizes) + 1)
                        row2[0].markdown("전체 세대수")
                        for i, size in enumerate(sizes):
                            count = 평형별세대수.get(size, 0)
                            row2[i+1].markdown(f"{count}세대")

                        row3 = st.columns(len(sizes) + 1)
                        row3[0].markdown("최초 미분양")
                        for i, size in enumerate(sizes):
                            count = 평형별세대수.get(size, 0)
                            unsold = 평형별최초미분양.get(size, 0)
                            pct = round(unsold / count * 100, 1) if count > 0 else 0
                            if unsold > 0:
                                row3[i+1].markdown(f"<span style='color:#1E90FF'>{unsold}세대 ({pct}%)</span>", unsafe_allow_html=True)
                            else:
                                row3[i+1].markdown("<span style='color:#1E90FF'>-</span>", unsafe_allow_html=True)

                        row4 = st.columns(len(sizes) + 1)
                        row4[0].markdown("현 미분양")
                        for i, size in enumerate(sizes):
                            row4[i+1].markdown("<span style='color:#1E90FF; font-weight:bold'>-</span>", unsafe_allow_html=True)

                    st.divider()
                    st.header("💰 시세 참고")
                    st.metric("현재 할인율", "-")
                    st.caption("※ 할인율 및 인근 시세는 추후 연동 예정")

                    st.divider()
                    st.header("🧠 종합 의견")
                    st.info("수집된 데이터를 바탕으로 종합 의견을 제공할 예정입니다.")

                    # 이력 저장
                    record = {
                        "단지명": apt_info.get("HOUSE_NM", apt_name),
                        "소재지": 주소,
                        "검색일": str(date.today()),
                        "최초분양일자": 분양일자,
                        "전체세대수": 전체세대수,
                        "평형별세대수": 평형별세대수,
                        "평형별분양가_만원": 평형별분양가,
                    }
                    save_history(record)

            except Exception as e:
                st.error(f"데이터 수집 중 오류가 발생했습니다: {e}")

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
