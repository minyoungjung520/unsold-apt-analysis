import streamlit as st
import json
import os
import requests
from datetime import date

DATA_FILE = "history.json"
API_KEY = st.secrets.get("API_KEY", "")
KOSIS_KEY = st.secrets.get("KOSIS_KEY", "")
NAVER_CLIENT_ID = st.secrets.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = st.secrets.get("NAVER_CLIENT_SECRET", "")
KAKAO_API_KEY = st.secrets.get("KAKAO_API_KEY", "")

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

def fetch_sigungu_unsold(sido, sigungu):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": KOSIS_KEY,
        "itmId": "13103871087T1+",
        "objL1": "ALL",
        "objL2": "ALL",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "M",
        "newEstPrdCnt": "1",
        "orgId": "116",
        "tblId": "DT_MLTM_2082",
    }
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    if not isinstance(data, list):
        return None, []

    target = None
    all_sigungu = []
    기준월 = ""

    for item in data:
        c1 = item.get("C1_NM", "")
        c2 = item.get("C2_NM", "")
        dt = int(item.get("DT", 0) or 0)
        prd = item.get("PRD_DE", "")
        if sido in c1:
            기준월 = prd
            all_sigungu.append({"시군구": c2, "미분양세대수": dt})
            if sigungu and sigungu in c2:
                target = {"시도": c1, "시군구": c2, "미분양세대수": dt, "기준월": prd}

    all_sigungu.sort(key=lambda x: -x["미분양세대수"])
    sido_total = sum(x["미분양세대수"] for x in all_sigungu)

    return target, {
        "시도": sido,
        "전체세대수": sido_total,
        "기준월": 기준월,
        "구별현황": all_sigungu,
    }

SIDO_LINKS = {
    "서울": "https://www.seoul.go.kr",
    "부산": "https://www.busan.go.kr",
    "대구": "https://www.daegu.go.kr",
    "인천": "https://www.incheon.go.kr",
    "광주": "https://www.gwangju.go.kr",
    "대전": "https://www.daejeon.go.kr",
    "울산": "https://www.ulsan.go.kr",
    "세종": "https://www.sejong.go.kr",
    "경기": "https://www.gg.go.kr",
    "강원": "https://www.gwd.go.kr",
    "충북": "https://www.cb.go.kr",
    "충남": "https://www.chungnam.go.kr",
    "전북": "https://www.jeonbuk.go.kr",
    "전남": "https://www.jeonnam.go.kr",
    "경북": "https://www.gb.go.kr",
    "경남": "https://www.gyeongnam.go.kr",
    "제주": "https://www.jeju.go.kr",
}

def fetch_kakao_apt_name(query):
    """주소 또는 아파트명으로 카카오 검색 → 후보 목록 반환"""
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    results = []

    # 1) 주소 검색 → 건물명 추출
    res = requests.get("https://dapi.kakao.com/v2/local/search/address.json",
                       headers=headers, params={"query": query}, timeout=10)
    if res.status_code == 200:
        for doc in res.json().get("documents", []):
            road = doc.get("road_address") or {}
            building = road.get("building_name", "").strip()
            addr = road.get("address_name", doc.get("address_name", ""))
            if building:
                results.append({"아파트명": building, "주소": addr})

    # 2) 키워드 검색
    res2 = requests.get("https://dapi.kakao.com/v2/local/search/keyword.json",
                        headers=headers, params={"query": query}, timeout=10)
    if res2.status_code == 200:
        for doc in res2.json().get("documents", [])[:5]:
            name = doc.get("place_name", "").strip()
            addr = doc.get("address_name", "")
            if name and not any(r["아파트명"] == name for r in results):
                results.append({"아파트명": name, "주소": addr})

    return results

def fetch_naver_search(query, search_type="news", display=5):
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "sort": "date"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    if res.status_code != 200:
        return []
    import re
    items = res.json().get("items", [])
    result = []
    for item in items:
        title = re.sub(r"<[^>]+>", "", item.get("title", ""))
        desc = re.sub(r"<[^>]+>", "", item.get("description", ""))
        result.append({
            "제목": title,
            "링크": item.get("link", ""),
            "날짜": item.get("pubDate", item.get("postdate", "")),
            "출처": item.get("bloggername", item.get("originallink", "")),
            "설명": desc,
        })
    return result

LAWD_CD_MAP = {
    ("서울","종로구"):11110,("서울","중구"):11140,("서울","용산구"):11170,("서울","성동구"):11200,
    ("서울","광진구"):11215,("서울","동대문구"):11230,("서울","중랑구"):11260,("서울","성북구"):11290,
    ("서울","강북구"):11305,("서울","도봉구"):11320,("서울","노원구"):11350,("서울","은평구"):11380,
    ("서울","서대문구"):11410,("서울","마포구"):11440,("서울","양천구"):11470,("서울","강서구"):11500,
    ("서울","구로구"):11530,("서울","금천구"):11545,("서울","영등포구"):11560,("서울","동작구"):11590,
    ("서울","관악구"):11620,("서울","서초구"):11650,("서울","강남구"):11680,("서울","송파구"):11710,("서울","강동구"):11740,
    ("부산","중구"):26110,("부산","서구"):26140,("부산","동구"):26170,("부산","영도구"):26200,
    ("부산","부산진구"):26230,("부산","동래구"):26260,("부산","남구"):26290,("부산","북구"):26320,
    ("부산","해운대구"):26350,("부산","사하구"):26380,("부산","금정구"):26410,("부산","강서구"):26440,
    ("부산","연제구"):26470,("부산","수영구"):26500,("부산","사상구"):26530,("부산","기장군"):26710,
    ("대구","중구"):27110,("대구","동구"):27140,("대구","서구"):27170,("대구","남구"):27200,
    ("대구","북구"):27230,("대구","수성구"):27260,("대구","달서구"):27290,("대구","달성군"):27710,
    ("인천","중구"):28110,("인천","동구"):28140,("인천","미추홀구"):28177,("인천","연수구"):28185,
    ("인천","남동구"):28200,("인천","부평구"):28237,("인천","계양구"):28245,("인천","서구"):28260,
    ("광주","동구"):29110,("광주","서구"):29140,("광주","남구"):29155,("광주","북구"):29170,("광주","광산구"):29200,
    ("대전","동구"):30110,("대전","중구"):30140,("대전","서구"):30170,("대전","유성구"):30200,("대전","대덕구"):30230,
    ("울산","중구"):31110,("울산","남구"):31140,("울산","동구"):31170,("울산","북구"):31200,("울산","울주군"):31710,
    ("경기","수원시 장안구"):41111,("경기","수원시 권선구"):41113,("경기","수원시 팔달구"):41115,("경기","수원시 영통구"):41117,
    ("경기","성남시 수정구"):41131,("경기","성남시 중원구"):41133,("경기","성남시 분당구"):41135,
    ("경기","의정부시"):41150,("경기","안양시 만안구"):41171,("경기","안양시 동안구"):41173,
    ("경기","광명시"):41210,("경기","평택시"):41220,("경기","안산시 상록구"):41271,("경기","안산시 단원구"):41273,
    ("경기","고양시 덕양구"):41281,("경기","고양시 일산동구"):41285,("경기","고양시 일산서구"):41287,
    ("경기","구리시"):41310,("경기","남양주시"):41360,("경기","시흥시"):41390,("경기","군포시"):41410,
    ("경기","용인시 처인구"):41461,("경기","용인시 기흥구"):41463,("경기","용인시 수지구"):41465,
    ("경기","파주시"):41480,("경기","화성시"):41590,("경기","김포시"):41570,("경기","하남시"):41450,
    ("경북","포항시 남구"):47111,("경북","포항시 북구"):47113,("경북","경주시"):47130,("경북","구미시"):47190,
    ("경북","안동시"):47170,("경북","김천시"):47150,("경북","영주시"):47210,("경북","상주시"):47250,
    ("경남","창원시 의창구"):48121,("경남","창원시 성산구"):48123,("경남","창원시 마산합포구"):48125,
    ("경남","창원시 마산회원구"):48127,("경남","창원시 진해구"):48129,("경남","진주시"):48170,("경남","김해시"):48250,
    ("경남","양산시"):48330,("경남","거제시"):48310,("경남","통영시"):48220,("경남","사천시"):48240,
    ("세종","세종시"):36110,
    ("강원","춘천시"):51110,("강원","원주시"):51130,("강원","강릉시"):51150,("강원","동해시"):51170,
    ("강원","속초시"):51210,("강원","삼척시"):51230,
    ("충북","청주시 상당구"):43111,("충북","청주시 서원구"):43112,("충북","청주시 흥덕구"):43113,
    ("충북","청주시 청원구"):43114,("충북","충주시"):43130,("충북","제천시"):43150,
    ("충남","천안시 동남구"):44131,("충남","천안시 서북구"):44133,("충남","공주시"):44150,
    ("충남","아산시"):44200,("충남","서산시"):44210,("충남","당진시"):44270,("충남","보령시"):44180,
    ("전북","전주시 완산구"):52111,("전북","전주시 덕진구"):52113,("전북","군산시"):52130,
    ("전북","익산시"):52140,("전북","정읍시"):52180,("전북","남원시"):52190,("전북","김제시"):52210,
    ("전남","목포시"):46110,("전남","여수시"):46130,("전남","순천시"):46150,("전남","나주시"):46170,
    ("전남","광양시"):46230,
    ("제주","제주시"):50110,("제주","서귀포시"):50130,
}

def fetch_realtrade(lawd_cd, deal_ymd, apt_name_filter=""):
    import xml.etree.ElementTree as ET
    from urllib.parse import quote
    encoded_key = quote(API_KEY, safe='')
    url = f"https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev?serviceKey={encoded_key}&LAWD_CD={lawd_cd}&DEAL_YMD={deal_ymd}&numOfRows=100&pageNo=1"
    res = requests.get(url, timeout=15)
    try:
        root = ET.fromstring(res.content.decode('utf-8'))
    except Exception:
        return []
    items = root.findall(".//item")
    result = []
    for item in items:
        name = (item.findtext("aptNm") or "").strip()
        if apt_name_filter and apt_name_filter not in name:
            continue
        result.append({
            "아파트": name,
            "거래금액(만원)": (item.findtext("dealAmount") or "").replace(",","").strip(),
            "전용면적(㎡)": item.findtext("excluUseAr") or "",
            "층": item.findtext("floor") or "",
            "년": item.findtext("dealYear") or "",
            "월": item.findtext("dealMonth") or "",
            "일": item.findtext("dealDay") or "",
            "법정동": (item.findtext("umdNm") or "").strip(),
        })
    return result

def fetch_nearby_prices(lawd_cd, dong, months=3, area_low=79, area_high=90):
    from datetime import datetime
    from collections import defaultdict
    now = datetime.now()
    all_trades = []
    for i in range(months):
        m = now.month - i
        y = now.year
        if m <= 0:
            m += 12
            y -= 1
        trades = fetch_realtrade(lawd_cd, f"{y}{str(m).zfill(2)}")
        all_trades.extend(trades)

    # 같은 동 + 면적 범위 필터
    filtered = []
    for t in all_trades:
        try:
            area = float(t["전용면적(㎡)"])
            if area_low <= area <= area_high and dong in t.get("법정동", ""):
                filtered.append(t)
        except:
            pass

    # 아파트별 최신 거래 추출
    apt_trades = defaultdict(list)
    for t in filtered:
        apt_trades[t["아파트"]].append(t)

    result = []
    for name, trades in apt_trades.items():
        trades.sort(key=lambda x: f"{x['년']}{x['월'].zfill(2)}{x['일'].zfill(2)}", reverse=True)
        latest = trades[0]
        try:
            price = int(latest["거래금액(만원)"])
            area = float(latest["전용면적(㎡)"])
            per_sqm = round(price / area)
            per_pyeong = round(price / (area / 3.3058))
            result.append({
                "아파트": name,
                "전용면적(㎡)": area,
                "거래금액(만원)": price,
                "㎡당(만원)": per_sqm,
                "평당(만원)": per_pyeong,
                "거래건수": len(trades),
                "최근거래일": f"{latest['년']}.{latest['월'].zfill(2)}.{latest['일'].zfill(2)}",
            })
        except:
            pass

    result.sort(key=lambda x: -x["거래건수"])
    return result[:5]

def fetch_apt_info(apt_name):
    url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
    headers = {"Authorization": f"Infuser {API_KEY}"}
    # 공백 제거 버전으로 유사 매칭
    apt_name_nospace = apt_name.replace(" ", "")

    def _search(query):
        params = {
            "page": 1,
            "perPage": 10,
            "cond[HOUSE_NM::LIKE]": query,
            "returnType": "json"
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    # 시도1: 입력명 그대로
    data = _search(apt_name)
    # 시도2: 결과 없으면 공백 제거한 핵심 키워드로 재검색
    if data.get("currentCount", 0) == 0 and len(apt_name_nospace) >= 4:
        # 앞 4글자 이상으로 검색 (예: "한라비발디" 등)
        data = _search(apt_name_nospace[:6])
    if data.get("currentCount", 0) == 0:
        return None

    # 공백 무시 비교로 가장 근접한 항목 반환
    for item in data["data"]:
        nm = item.get("HOUSE_NM", "").replace(" ", "")
        if nm == apt_name_nospace or apt_name_nospace in nm or nm in apt_name_nospace:
            return item
    return data["data"][0]

def fetch_apt_candidates_by_addr(address):
    """주소로 청약홈 단지 후보 검색 (시군구+동 기준, 광역시도 제외)"""
    url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail"
    headers = {"Authorization": f"Infuser {API_KEY}"}

    # 광역시도명 제거 후 시군구+동 추출
    parts = address.replace("특별자치도", "").replace("특별시", "").replace("광역시", "").replace("특별자치시", "").split()
    # parts 예: ["전북", "군산시", "지곡동"] → 시군구부터 사용
    시군구_parts = [p for p in parts if p.endswith(("시","군","구","도")) or p.endswith(("동","읍","면","리"))]
    # 시 or 군 + 동/읍/면 조합으로 검색 (도 이름 제외)
    city = next((p for p in parts if p.endswith(("시","군")) and len(p) >= 3), "")
    dong = next((p for p in parts if p.endswith(("동","읍","면","리"))), "")
    keyword = f"{city} {dong}".strip() if city else dong or " ".join(parts[1:3])

    for kw in [keyword, city, dong]:
        if not kw:
            continue
        params = {
            "page": 1,
            "perPage": 10,
            "cond[HSSPLY_ADRES::LIKE]": kw,
            "returnType": "json"
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("currentCount", 0) > 0:
            return [{"단지명": d.get("HOUSE_NM",""), "주소": d.get("HSSPLY_ADRES",""), "분양일": d.get("RCRIT_PBLANC_DE",""), "_raw": d} for d in data["data"]]
    return []

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
/* 전체 폰트 */
html, body, [class*="css"] {
    font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}

/* 타이틀 */
h1 { color: #1428A0 !important; font-size: 1.8rem !important; font-weight: 800 !important; }

/* 섹션 헤더 */
h2 {
    color: #1a1a2e !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px;
    padding: 10px 0 8px 14px !important;
    margin-top: 8px !important;
    border-left: 4px solid #1428A0;
    border-bottom: none !important;
}

/* 서브헤더 */
h3 {
    color: #444 !important;
    font-size: 0.97rem !important;
    font-weight: 600 !important;
    margin-top: 16px !important;
    padding-bottom: 4px !important;
    border-bottom: 1px solid #e8ecf8 !important;
}

/* 검색 버튼 */
button[kind="primary"] {
    background-color: #1428A0 !important;
    border-color: #1428A0 !important;
    color: white !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
}
button[kind="primary"]:hover {
    background-color: #0e1e7a !important;
    border-color: #0e1e7a !important;
}

/* metric 카드 */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
    border: 1px solid #c0ccee;
    border-radius: 10px;
    padding: 16px !important;
}
[data-testid="metric-container"] label {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #1428A0 !important;
    text-transform: none !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #0d1f7a !important;
}

/* 표 헤더 */
[data-testid="stDataFrame"] th {
    background-color: #1428A0 !important;
    color: white !important;
    font-weight: 700 !important;
}

/* 입력란 */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    border-radius: 8px !important;
    border: 1.5px solid #c0ccee !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {
    border-color: #1428A0 !important;
    box-shadow: 0 0 0 2px rgba(20,40,160,0.15) !important;
}

/* 성공/경고 메시지 */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.95rem !important;
}

/* caption */
[data-testid="stCaptionContainer"] {
    color: #666 !important;
    font-size: 0.82rem !important;
}

/* 구분선 숨김 (카드로 대체) */
hr { border-color: #eef0f8 !important; }
</style>
""", unsafe_allow_html=True)
st.title("미분양 아파트 감정가 적정성 분석")
st.markdown("<p style='color:#666; font-size:0.95rem; margin-top:-12px'>소재지와 아파트명을 입력하면 미분양·시세·할인 근거를 자동 수집합니다.</p>", unsafe_allow_html=True)

# 입력 섹션
st.header("단지 정보 입력")

# 세션스테이트 초기화
for _k, _v in [("kakao_candidates",[]), ("cq_selected_info", None), ("cq_selected_loc", ""), ("cq_apt_name", ""),
               ("last_loc", ""), ("last_apt", "")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

def _extract_loc(addr):
    parts = addr.replace("특별자치도","").replace("특별시","").replace("광역시","").replace("특별자치시","").replace("전라북도","전북").replace("전라남도","전남").replace("경상북도","경북").replace("경상남도","경남").replace("충청북도","충북").replace("충청남도","충남").replace("강원특별자치도","강원").split()
    return " ".join(parts[:3]) if len(parts) >= 3 else addr

def _select_cq(raw, loc):
    """청약홈 후보 선택 콜백 — rerun 전에 실행되므로 조건 블록 안 버튼에서도 안전"""
    st.session_state.cq_selected_info = raw
    st.session_state.cq_selected_loc = loc
    st.session_state.last_loc = loc
    st.session_state.last_apt = raw.get("HOUSE_NM", "")

# ── 기본 입력 (강조 영역) ──
st.markdown(
    "<div style='background:linear-gradient(135deg,#f0f4ff 0%,#e8eeff 100%);border:2px solid #1428A0;"
    "border-radius:12px;padding:6px 16px 2px 16px;margin-bottom:4px'>"
    "<b style='color:#1428A0;font-size:1.02rem'>소재지·아파트명 입력</b></div>",
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
with col1:
    location = st.text_input("소재지", value=st.session_state.last_loc, placeholder="예: 대구 수성구 범어동")
with col2:
    apt_name = st.text_input("아파트명", value=st.session_state.last_apt, placeholder="예: 범어자이")
with col3:
    area_options = ["59㎡", "74㎡", "84㎡", "101㎡", "114㎡", "직접입력"]
    area_select = st.selectbox("전용면적", area_options, index=2)
    if area_select == "직접입력":
        target_area = st.number_input("면적 입력(㎡)", min_value=10.0, max_value=300.0, value=84.0, step=1.0)
    else:
        target_area = float(area_select.replace("㎡", ""))
with col4:
    appraisal = st.number_input("감정가 (만원)", min_value=0, step=100, value=0)
with col5:
    st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
    search_btn = st.button("검색", type="primary", use_container_width=True)

# ── 주소/단지명 검색 (단지가 조회가 안되는 경우) ──
with st.expander("주소 또는 단지명으로 아파트명 검색 (단지가 조회가 안되는 경우)"):
    addr_col1, addr_col2 = st.columns([4, 1])
    with addr_col1:
        address_input = st.text_input("주소 또는 단지명 입력", placeholder="예: 전북 군산시 지곡동 620  또는  대구 수성구 범어자이", label_visibility="collapsed")
    with addr_col2:
        addr_btn = st.button("검색", key="addr_search", use_container_width=True)
    if addr_btn and address_input:
        with st.spinner("카카오 검색 중..."):
            st.session_state.kakao_candidates = fetch_kakao_apt_name(address_input)
    if st.session_state.kakao_candidates:
        st.success(f"검색 결과 {len(st.session_state.kakao_candidates)}건 — 단지를 선택하면 바로 분석합니다.")
        for c in st.session_state.kakao_candidates:
            col_a, col_b = st.columns([4, 1])
            col_a.markdown(f"**{c['아파트명']}** — {c['주소']}")
            if col_b.button("선택", key=f"sel_{c['아파트명']}"):
                # 카카오 선택: 이름+위치만 저장, 청약홈 조회는 검색 시 수행
                st.session_state.cq_apt_name = c['아파트명']
                st.session_state.cq_selected_loc = _extract_loc(c['주소'])
                st.session_state.cq_selected_info = None
                st.session_state.last_loc = st.session_state.cq_selected_loc
                st.session_state.last_apt = c['아파트명']
                st.session_state.kakao_candidates = []
                st.rerun()
    elif addr_btn and address_input:
        st.warning("검색 결과가 없습니다. 다른 주소나 단지명으로 시도해 보세요.")

# 선택된 단지 배너 표시
_banner_name = (st.session_state.cq_selected_info or {}).get("HOUSE_NM", "") or st.session_state.cq_apt_name
if _banner_name:
    st.markdown(
        f"<div style='background:#e8f0fe;border-left:4px solid #1428A0;padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
        f"<b style='color:#1428A0'>선택된 단지:</b> {_banner_name} ({st.session_state.cq_selected_loc})</div>",
        unsafe_allow_html=True
    )

# 선택 데이터가 있으면 자동 분석
cq_run = bool(st.session_state.cq_selected_info or st.session_state.cq_apt_name)

if search_btn or cq_run:
    # 선택 시 location/apt_name 오버라이드
    if cq_run:
        location = st.session_state.cq_selected_loc or location
        if st.session_state.cq_selected_info:
            apt_name = st.session_state.cq_selected_info.get("HOUSE_NM", apt_name)
        elif st.session_state.cq_apt_name:
            apt_name = st.session_state.cq_apt_name

    if not location or not apt_name:
        st.warning("소재지와 아파트명을 입력해주세요.")
    else:
        import re as _re
        location_parts = location.split()
        raw_sido = location_parts[0] if location_parts else ""
        sido = _re.sub(r"(광역시|특별시|특별자치시|특별자치도|시|도)$", "", raw_sido)
        sigungu = location_parts[1] if len(location_parts) > 1 else ""

        with st.spinner("청약홈 데이터 수집 중..."):
            try:
                # 청약홈 후보 목록에서 직접 선택한 경우 API 재조회 불필요
                if st.session_state.cq_selected_info:
                    # 청약홈 목록 직접 선택 → 원본 데이터 그대로 사용
                    apt_info = st.session_state.cq_selected_info
                    st.session_state.cq_selected_info = None
                    st.session_state.cq_selected_loc = ""
                    st.session_state.cq_apt_name = ""
                else:
                    # 카카오 선택 또는 직접 입력 → 청약홈 API 조회
                    st.session_state.cq_apt_name = ""
                    apt_info = fetch_apt_info(apt_name)

                if not apt_info:
                    st.error(f"청약홈에서 '{apt_name}'을 찾을 수 없습니다. 분양 당시 등록명이 다를 수 있습니다.")
                    with st.spinner("소재지 주소로 청약홈 재검색 중..."):
                        cq_candidates = fetch_apt_candidates_by_addr(location)
                    if cq_candidates:
                        st.info("같은 지역 청약홈 등록 단지입니다. 해당 단지를 선택하면 바로 분석합니다.")
                        for cq in cq_candidates:
                            c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
                            c1.markdown(f"**{cq['단지명']}**")
                            c2.markdown(cq['주소'])
                            c3.markdown(cq['분양일'])
                            c4.button("선택", key=f"cq_{cq['단지명']}",
                                      on_click=_select_cq, args=(cq['_raw'], _extract_loc(cq['주소'])))
                    else:
                        st.warning("해당 소재지로도 청약홈 단지를 찾지 못했습니다.")
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

                    st.header("단지 기본 정보")
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**최초 분양일자**<br>{분양일자}", unsafe_allow_html=True)
                    c2.markdown(f"**전체 세대수**<br>{전체세대수:,}세대", unsafe_allow_html=True)
                    st.caption(f"📍 {주소}")

                    if 평형별세대수:
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

                        sido_url = SIDO_LINKS.get(sido, f"https://www.google.com/search?q={sido}+{sigungu}+미분양현황")
                        unsold_link = f"<a href='{sido_url}' target='_blank'>{sido}시청 홈페이지</a>"

                        row4 = st.columns(len(sizes) + 1)
                        row4[0].markdown("현 미분양")
                        row4[1].markdown(
                            f"<span style='color:#888; white-space:nowrap'>확인 필요 → {unsold_link}</span>",
                            unsafe_allow_html=True
                        )
                        for i in range(1, len(sizes)):
                            row4[i+1].markdown("")

                    # 국토부 실거래가 섹션
                    st.header("국토부 실거래가 조회")

                    lawd_cd = LAWD_CD_MAP.get((sido, sigungu))
                    if not lawd_cd:
                        # 경기처럼 시 단위로 찾기
                        for (s, sg), code in LAWD_CD_MAP.items():
                            if s == sido and sigungu in sg:
                                lawd_cd = code
                                break

                    if not lawd_cd:
                        st.warning(f"'{sido} {sigungu}' 법정동코드를 찾을 수 없습니다. 지원되지 않는 지역일 수 있습니다.")
                    else:
                        from datetime import datetime
                        now = datetime.now()
                        years = [str(y) for y in range(now.year, now.year - 3, -1)]
                        months = [str(m).zfill(2) for m in range(1, 13)]

                        rc1, rc2, rc3 = st.columns([1, 1, 2])
                        sel_year  = rc1.selectbox("연도", years, index=0)
                        sel_month = rc2.selectbox("월", months, index=now.month - 2 if now.month > 1 else 0)
                        filter_apt = rc3.checkbox(f"'{apt_info.get('HOUSE_NM', apt_name)}' 단지만 보기", value=True)

                        deal_ymd = f"{sel_year}{sel_month}"
                        apt_filter = apt_info.get("HOUSE_NM", apt_name) if filter_apt else ""

                        with st.spinner("실거래가 조회 중..."):
                            trade_data = fetch_realtrade(lawd_cd, deal_ymd, apt_filter)

                        if trade_data:
                            import pandas as pd
                            df_trade = pd.DataFrame(trade_data)
                            df_trade["거래일"] = df_trade["년"] + "-" + df_trade["월"].str.zfill(2) + "-" + df_trade["일"].str.zfill(2)
                            df_trade["거래금액(만원)"] = pd.to_numeric(df_trade["거래금액(만원)"], errors="coerce")
                            df_trade = df_trade[["거래일","아파트","전용면적(㎡)","층","거래금액(만원)"]].sort_values("거래일", ascending=False)
                            df_trade.index = range(1, len(df_trade) + 1)
                            st.caption(f"총 {len(df_trade)}건 조회 ({sel_year}년 {sel_month}월 · {sido} {sigungu})")
                            st.dataframe(df_trade, use_container_width=True)
                        else:
                            st.info(f"{sel_year}년 {sel_month}월 해당 조건의 실거래 내역이 없습니다.")

                        st.markdown("🔗 [국토부 실거래가 공개시스템](https://rt.molit.go.kr)", unsafe_allow_html=False)

                    # 인근 아파트 시세
                    nearby = []
                    dong = location_parts[2] if len(location_parts) > 2 else ""
                    if lawd_cd and dong:
                        st.header("인근 아파트 시세")
                        st.markdown(f"<span style='color:#1428A0; font-size:0.85rem'>{sido} {sigungu} {dong} · 84㎡ 기준 · 최근 3개월 실거래 · 거래건수 상위 5개</span>", unsafe_allow_html=True)
                        area_low = target_area - 5
                        area_high = target_area + 5
                        with st.spinner("인근 시세 조회 중..."):
                            nearby = fetch_nearby_prices(lawd_cd, dong, months=3, area_low=area_low, area_high=area_high)
                        if nearby:
                            import pandas as pd
                            df_nearby = pd.DataFrame(nearby)
                            df_nearby["거래금액"] = df_nearby.apply(
                                lambda r: f"{r['거래금액(만원)']:,}만원 (㎡당 {r['㎡당(만원)']:,}만원 / 평당 {r['평당(만원)']:,}만원)", axis=1
                            )
                            df_nearby = df_nearby[["아파트","전용면적(㎡)","거래금액","최근거래일","거래건수"]]
                            df_nearby.index = range(1, len(df_nearby) + 1)
                            st.markdown(f"<span style='color:#1428A0; font-size:0.85rem'>{sido} {sigungu} {dong} · {target_area:.0f}㎡ 기준(±5㎡) · 최근 3개월 실거래 · 거래건수 상위 5개</span>", unsafe_allow_html=True)
                            st.dataframe(df_nearby, use_container_width=True)
                        else:
                            st.info(f"{dong} 내 {target_area:.0f}㎡ 근처 최근 실거래 내역이 없습니다.")

                    target_data, sido_summary = fetch_sigungu_unsold(sido, sigungu)

                    if sido_summary:
                        기준월 = sido_summary["기준월"]
                        기준월_str = f"{기준월[:4]}년 {기준월[4:]}월" if 기준월 else ""
                        st.header("지역 미분양 현황")
                        st.markdown(f"<span style='color:#1428A0; font-size:0.85rem'>기준: {기준월_str} · 국토교통부 통계</span>", unsafe_allow_html=True)

                        label_style = "font-size:1.15rem; font-weight:600; margin-bottom:4px"
                        value_style = "font-size:1.15rem; font-weight:700"

                        c1, c2 = st.columns(2)
                        c1.markdown(f"<div style='{label_style}'>{sido} 전체 미분양</div><div style='{value_style}'>{sido_summary['전체세대수']:,}세대</div>", unsafe_allow_html=True)
                        if target_data:
                            c2.markdown(f"<div style='{label_style}'>{sigungu} 미분양</div><div style='{value_style}'>{target_data['미분양세대수']:,}세대</div>", unsafe_allow_html=True)

                        st.markdown(f"<div style='{label_style}; margin-top:16px'>{sido} 구·군별 미분양 현황</div>", unsafe_allow_html=True)
                        import pandas as pd
                        df = pd.DataFrame(sido_summary["구별현황"])
                        df.columns = ["시군구", "미분양세대수"]
                        df["미분양세대수"] = df["미분양세대수"].apply(lambda x: f"{x:,}세대")
                        df.index = range(1, len(df) + 1)
                        st.dataframe(df, use_container_width=True)

                    # 네이버 검색
                    house_nm = apt_info.get('HOUSE_NM', apt_name)
                    query_exact = f"{house_nm} 미분양"
                    query_broad = f"{sido} {sigungu} 미분양 할인"
                    with st.spinner("뉴스·블로그·카페·동영상 검색 중..."):
                        news_all  = fetch_naver_search(query_exact, "news",  10)
                        blog_all  = fetch_naver_search(query_exact, "blog",  10)
                        cafe_all  = fetch_naver_search(query_exact, "cafearticle", 10)
                        vclip_all = fetch_naver_search(query_exact, "vclip", 10)

                    def filter_results(items, keyword, limit=5):
                        exact = [x for x in items if keyword in x["제목"]]
                        return (exact or items)[:limit], bool(exact)

                    news_list,  news_is_exact  = filter_results(news_all,  house_nm)
                    blog_list,  blog_is_exact  = filter_results(blog_all,  house_nm)
                    cafe_list,  cafe_is_exact  = filter_results(cafe_all,  house_nm)
                    vclip_list, vclip_is_exact = filter_results(vclip_all, house_nm)

                    youtube_query = requests.utils.quote(f"{house_nm} 미분양")
                    youtube_url = f"https://www.youtube.com/results?search_query={youtube_query}"

                    st.header("할인 판단 근거")

                    def blue_caption(text):
                        st.markdown(f"<span style='color:#1428A0; font-size:0.85rem'>{text}</span>", unsafe_allow_html=True)

                    def black_caption(text):
                        st.markdown(f"<span style='color:#222222; font-size:0.85rem'>{text}</span>", unsafe_allow_html=True)

                    fallback_msg = lambda label: f"※ '{house_nm}' 직접 관련 {label}가 없어 {sido} {sigungu} 지역 결과를 표시합니다."

                    if news_list:
                        st.subheader("관련 뉴스")
                        if not news_is_exact:
                            black_caption(fallback_msg("기사"))
                        for item in news_list:
                            st.markdown(f"- [{item['제목']}]({item['링크']}) — {item['날짜']}")
                    else:
                        blue_caption("관련 뉴스를 찾지 못했습니다.")

                    if blog_list:
                        st.subheader("관련 블로그")
                        if not blog_is_exact:
                            black_caption(fallback_msg("블로그"))
                        for item in blog_list:
                            label = f"{item['출처']} — " if item['출처'] else ""
                            st.markdown(f"- [{item['제목']}]({item['링크']}) — {label}{item['날짜']}")
                    else:
                        blue_caption("관련 블로그를 찾지 못했습니다.")

                    if cafe_list:
                        st.subheader("관련 카페")
                        if not cafe_is_exact:
                            black_caption(fallback_msg("카페글"))
                        for item in cafe_list:
                            label = f"{item['출처']} — " if item['출처'] else ""
                            st.markdown(f"- [{item['제목']}]({item['링크']}) — {label}{item['날짜']}")
                    else:
                        blue_caption("관련 카페글을 찾지 못했습니다.")

                    st.subheader("유튜브")
                    if vclip_list:
                        if not vclip_is_exact:
                            blue_caption(fallback_msg("동영상"))
                        for item in vclip_list:
                            st.markdown(f"- [{item['제목']}]({item['링크']}) — {item['날짜']}")
                            desc = item.get("설명", "").strip()
                            if desc:
                                lines = [l.strip() for l in desc.splitlines() if l.strip()][:3]
                                st.caption("  \n".join(lines))
                    else:
                        black_caption("※ 네이버 동영상 결과 없음")
                    st.markdown(f"🔗 [유튜브에서 직접 검색하기]({youtube_url})")

                    st.header("종합 의견")
                    총최초미분양 = sum(평형별최초미분양.values())
                    미분양비율 = round(총최초미분양 / 전체세대수 * 100, 1) if 전체세대수 > 0 else 0

                    # 인근 시세 평균/범위
                    avg_price = min_price = max_price = 0
                    if nearby:
                        prices = [x["거래금액(만원)"] for x in nearby]
                        avg_price = round(sum(prices) / len(prices))
                        min_price = min(prices)
                        max_price = max(prices)

                    # ── 리스크 스코어 산출 ──────────────────────────
                    score = 0
                    score_detail = []

                    # ① 가격 갭율 (감정가 입력 시)
                    gap_pct = None
                    if appraisal > 0 and avg_price > 0:
                        gap_pct = round((appraisal - avg_price) / avg_price * 100, 1)
                        if gap_pct > 10:
                            score += 3; score_detail.append(f"가격 갭 +{gap_pct}% (감정가가 시세보다 높음) → 3점")
                        elif gap_pct > 3:
                            score += 2; score_detail.append(f"가격 갭 +{gap_pct}% → 2점")
                        elif gap_pct > -3:
                            score += 1; score_detail.append(f"가격 갭 {gap_pct}% (시세 근접) → 1점")
                        else:
                            score += 0; score_detail.append(f"가격 갭 {gap_pct}% (감정가가 시세보다 낮음) → 0점")

                    # ② 최초 미분양율
                    if 미분양비율 >= 30:
                        score += 3; score_detail.append(f"최초 미분양율 {미분양비율}% (높음) → 3점")
                    elif 미분양비율 >= 10:
                        score += 2; score_detail.append(f"최초 미분양율 {미분양비율}% → 2점")
                    elif 미분양비율 > 0:
                        score += 1; score_detail.append(f"최초 미분양율 {미분양비율}% → 1점")
                    else:
                        score_detail.append("최초 미분양 없음 → 0점")

                    # ③ 경과기간 (분양일로부터 현재까지)
                    from datetime import datetime
                    elapsed_months = 0
                    try:
                        sale_date = datetime.strptime(분양일자, "%Y-%m-%d")
                        elapsed_months = (datetime.now().year - sale_date.year) * 12 + (datetime.now().month - sale_date.month)
                        if elapsed_months >= 36:
                            score += 3; score_detail.append(f"경과기간 {elapsed_months}개월 (3년 이상) → 3점")
                        elif elapsed_months >= 18:
                            score += 2; score_detail.append(f"경과기간 {elapsed_months}개월 → 2점")
                        elif elapsed_months >= 6:
                            score += 1; score_detail.append(f"경과기간 {elapsed_months}개월 → 1점")
                        else:
                            score_detail.append(f"경과기간 {elapsed_months}개월 (단기) → 0점")
                    except:
                        score_detail.append("경과기간 산출 불가")

                    # ④ 정성 시그널 (할인 키워드 매칭)
                    discount_keywords = ["마이너스피", "할인분양", "무순위", "미계약", "잔여세대", "분양가 인하", "특별공급", "할인"]
                    all_titles = " ".join([x["제목"] for x in news_list + blog_list + cafe_list])
                    keyword_hits = sum(1 for kw in discount_keywords if kw in all_titles)
                    if keyword_hits >= 4:
                        score += 3; score_detail.append(f"할인 키워드 {keyword_hits}개 감지 → 3점")
                    elif keyword_hits >= 2:
                        score += 2; score_detail.append(f"할인 키워드 {keyword_hits}개 감지 → 2점")
                    elif keyword_hits == 1:
                        score += 1; score_detail.append(f"할인 키워드 {keyword_hits}개 감지 → 1점")
                    else:
                        score_detail.append("할인 키워드 없음 → 0점")

                    # ── 등급 매핑 ────────────────────────────────────
                    if score <= 2:
                        grade, grade_color, adj_low, adj_high, grade_desc = "A", "#2e7d32", 0, 0, "조정 불필요 — 시세 갭 미미, 미분양 낮음"
                    elif score <= 5:
                        grade, grade_color, adj_low, adj_high, grade_desc = "B", "#1565c0", 3, 5, "경미한 할인 정황"
                    elif score <= 8:
                        grade, grade_color, adj_low, adj_high, grade_desc = "C", "#e65100", 5, 10, "미분양 지속 + 시세 하회"
                    elif score <= 11:
                        grade, grade_color, adj_low, adj_high, grade_desc = "D", "#b71c1c", 10, 15, "다수 할인 시그널 확인됨"
                    else:
                        grade, grade_color, adj_low, adj_high, grade_desc = "E", "#4a148c", 15, 20, "할인 강한 정황 — 재감정 권고"

                    # ── 출력 ─────────────────────────────────────────
                    g1, g2, g3 = st.columns([1, 2, 3])
                    g1.markdown(f"<div style='text-align:center; background:{grade_color}; color:white; border-radius:12px; padding:18px 0; font-size:2.5rem; font-weight:900'>{grade}</div><div style='text-align:center; font-size:1.0rem; font-weight:700; color:#333; margin-top:8px'>리스크 등급 (총점 {score}점)</div>", unsafe_allow_html=True)

                    if avg_price > 0:
                        g2.metric("인근 평균 실거래가", f"{avg_price:,}만원", f"범위 {min_price:,}~{max_price:,}만원")
                    if appraisal > 0 and gap_pct is not None:
                        sign = "+" if gap_pct > 0 else ""
                        g3.metric("감정가 vs 시세 갭", f"{sign}{gap_pct}%", f"감정가 {appraisal:,}만원 / 시세 {avg_price:,}만원", delta_color="off")

                    st.markdown("---")

                    # 의견 문구
                    gap_label = ""
                    if gap_pct is not None:
                        if gap_pct > 3:
                            gap_label = "높음, 조정 필요"
                        elif gap_pct > -3:
                            gap_label = "시세 근접, 정상 범위"
                        else:
                            gap_label = "낮음, 정상 범위"

                    근거_parts = []
                    if 미분양비율 > 0:
                        근거_parts.append(f"최초 미분양율 {미분양비율}%")
                    if keyword_hits > 0:
                        근거_parts.append(f"할인 관련 기사/글 {keyword_hits}건")
                    if elapsed_months > 0:
                        근거_parts.append(f"경과기간 {elapsed_months}개월")
                    근거_str = ", ".join(근거_parts) if 근거_parts else "수집된 정성 시그널 없음"

                    if appraisal > 0 and avg_price > 0:
                        final_low = round(appraisal * (1 - adj_high / 100))
                        final_high = round(appraisal * (1 - adj_low / 100))
                        sign = "+" if gap_pct >= 0 else ""
                        if grade == "A":
                            opinion_text = (
                                f"**[감정가 입력값: {appraisal:,}만원 기준 적정성 판단]**  \n"
                                f"- 인근 실거래 평균 {avg_price:,}만원 → 감정가가 시세 대비 {sign}{gap_pct}% ({gap_label})  \n"
                                f"- 리스크 등급: **{grade}** → 추가 조정 불필요  \n"
                                f"- 근거: {근거_str}"
                            )
                        else:
                            opinion_text = (
                                f"**[감정가 입력값: {appraisal:,}만원 기준 적정성 판단]**  \n"
                                f"- 인근 실거래 평균 {avg_price:,}만원 → 감정가가 시세 대비 {sign}{gap_pct}% ({gap_label})  \n"
                                f"- 리스크 등급: **{grade}** → 추가 조정 권고 -{adj_low}%-{adj_high}%  \n"
                                f"- 최종 권장: 감정가 대비 추가 {adj_low}%-{adj_high}% 하향 검토 (조정 후 약 **{final_low:,}만원-{final_high:,}만원**)  \n"
                                f"- 근거: {근거_str}"
                            )
                    elif avg_price > 0:
                        ref_low = round(avg_price * (1 - adj_high / 100))
                        ref_high = round(avg_price * (1 - adj_low / 100))
                        if grade == "A":
                            opinion_text = (
                                f"**[감정가 미입력 - 참고 시세 제시]**  \n"
                                f"- 인근 {target_area:.0f}㎡ 실거래 평균 **{avg_price:,}만원** (범위: {min_price:,}~{max_price:,}만원)  \n"
                                f"- 미분양/시장 신호 등급: **{grade}** — {grade_desc}  \n"
                                f"- 근거: {근거_str}  \n"
                                f"※ 감정가를 입력하시면 해당 값 대비 적정성을 판단해 드립니다."
                            )
                        else:
                            opinion_text = (
                                f"**[감정가 미입력 - 참고 시세 제시]**  \n"
                                f"- 인근 {target_area:.0f}㎡ 실거래 평균 **{avg_price:,}만원** (범위: {min_price:,}만원-{max_price:,}만원)  \n"
                                f"- 미분양/시장 신호 등급: **{grade}** ({grade_desc})  \n"
                                f"- 권장 감정가 참고 레인지: **{ref_low:,}만원-{ref_high:,}만원** (실거래 평균 대비 {adj_low}%-{adj_high}% 하향 적용, 미분양 리스크 반영)  \n"
                                f"- 근거: {근거_str}  \n"
                                f"※ 감정가를 입력하시면 해당 값 대비 적정성을 판단해 드립니다."
                            )
                    else:
                        opinion_text = (
                            f"- 미분양/시장 신호 등급: **{grade}** ({grade_desc})  \n"
                            f"- 근거: {근거_str}  \n"
                            f"인근 실거래 데이터가 부족하여 시세 비교가 어렵습니다. 감정가와 면적을 입력 후 재검색해 주세요."
                        )

                    st.warning(opinion_text)
                    st.markdown(
                        "<div style='border-left:4px solid #1428A0; background:#f0f4ff; padding:12px 16px; border-radius:6px; margin-top:8px'>"
                        "<span style='color:#1428A0; font-weight:700'>⚠️ 본 결과는 자동 산출된 참고자료이며 최종 판단이 아닙니다.</span><br>"
                        "<span style='color:#1428A0; font-weight:600'>담당자의 정성적 검토 및 최신 미분양 현황(관할 시청 등) 확인 후 최종 결정하시기 바랍니다.</span>"
                        "</div>",
                        unsafe_allow_html=True
                    )

                    with st.expander("점수 산출 근거 보기"):
                        st.markdown("**이번 검색 채점 결과**")
                        for d in score_detail:
                            st.markdown(f"- {d}")

                        st.markdown("---")
                        st.markdown("**채점 기준표**")
                        import pandas as pd
                        df_criteria = pd.DataFrame([
                            ["가격 갭율", "감정가가 시세보다 10% 초과 높음", "3점"],
                            ["가격 갭율", "감정가가 시세보다 3~10% 높음", "2점"],
                            ["가격 갭율", "시세와 ±3% 이내", "1점"],
                            ["가격 갭율", "감정가가 시세보다 낮음", "0점"],
                            ["최초 미분양율", "30% 이상", "3점"],
                            ["최초 미분양율", "10~30%", "2점"],
                            ["최초 미분양율", "0~10%", "1점"],
                            ["최초 미분양율", "없음", "0점"],
                            ["경과기간", "36개월 이상 (3년+)", "3점"],
                            ["경과기간", "18~36개월", "2점"],
                            ["경과기간", "6~18개월", "1점"],
                            ["경과기간", "6개월 미만", "0점"],
                            ["정성 시그널", "할인 키워드 4개 이상 감지", "3점"],
                            ["정성 시그널", "할인 키워드 2~3개 감지", "2점"],
                            ["정성 시그널", "할인 키워드 1개 감지", "1점"],
                            ["정성 시그널", "할인 키워드 없음", "0점"],
                        ], columns=["항목", "기준", "점수"])
                        st.dataframe(df_criteria, use_container_width=True, hide_index=True)

                        st.markdown("**등급별 권장 감액 레인지**")
                        df_grade = pd.DataFrame([
                            ["A", "0~2점", "조정 불필요", "시세 갭 미미, 미분양 낮음"],
                            ["B", "3~5점", "-3~5%", "경미한 할인 정황"],
                            ["C", "6~8점", "-5~10%", "미분양 지속 + 시세 하회"],
                            ["D", "9~11점", "-10~15%", "다수 할인 시그널 확인됨"],
                            ["E", "12점+", "-15~20% / 재감정 권고", "할인 강한 정황"],
                        ], columns=["등급", "총점", "권장 감액", "설명"])
                        st.dataframe(df_grade, use_container_width=True, hide_index=True)
                        st.caption("※ 정성 시그널 키워드: 마이너스피, 할인분양, 무순위, 미계약, 잔여세대, 분양가 인하, 특별공급, 할인")

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
st.header("검색 이력")
history = load_history()
if history:
    for i, record in enumerate(reversed(history[-10:])):
        with st.expander(f"{record['검색일']} — {record['소재지']} {record['단지명']}"):
            st.json(record)
else:
    st.info("아직 검색 이력이 없습니다.")
