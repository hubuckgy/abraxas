import streamlit as st
import requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="K-Tour AI Plus", layout="wide")

# -----------------------------
# Session State
# -----------------------------
if "school_search_results" not in st.session_state:
    st.session_state.school_search_results = []
if "selected_school_name" not in st.session_state:
    st.session_state.selected_school_name = ""
if "selected_school_details" not in st.session_state:
    st.session_state.selected_school_details = None
if "generated_items" not in st.session_state:
    st.session_state.generated_items = []
if "trip_plan_text" not in st.session_state:
    st.session_state.trip_plan_text = ""

# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1A1A2E;
        color: #FFFFFF;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
    }

    .stTextInput > label, .stSelectbox > label, .stRadio > label, .stTextArea > label {
        color: #FFFFFF;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #2E2E4A !important;
        color: #FFFFFF !important;
        border: 1px solid #444466 !important;
        border-radius: 8px !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #2E2E4A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }

    .stButton button {
        background-image: linear-gradient(to right, #6C45F6, #8A2BE2);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        font-weight: bold;
    }

    .stButton button:hover {
        transform: translateY(-1px);
    }

    .stRadio div[data-baseweb="radio"] label {
        background-color: #2E2E4A;
        border: 1px solid #444466;
        border-radius: 20px;
        padding: 6px 14px;
        color: #FFFFFF;
    }

    .stAlert {
        background-color: #2E2E4A !important;
        color: #FFFFFF !important;
        border-radius: 12px;
    }

    .block-container {
        padding-top: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 지역 코드 (한국관광공사 areaCode2 기준)
# -----------------------------
# 각 시/도의 areaCode 와, 그 안의 모든 시/군/구(sigunguCode) 매핑
REGIONS = {
    "서울특별시": {"code": "1", "sigungu": {
        "1": "강남구", "2": "강동구", "3": "강북구", "4": "강서구", "5": "관악구",
        "6": "광진구", "7": "구로구", "8": "금천구", "9": "노원구", "10": "도봉구",
        "11": "동대문구", "12": "동작구", "13": "마포구", "14": "서대문구", "15": "서초구",
        "16": "성동구", "17": "성북구", "18": "송파구", "19": "양천구", "20": "영등포구",
        "21": "용산구", "22": "은평구", "23": "종로구", "24": "중구", "25": "중랑구",
    }},
    "인천광역시": {"code": "2", "sigungu": {
        "1": "강화군", "2": "계양구", "3": "미추홀구", "4": "남동구", "5": "동구",
        "6": "부평구", "7": "서구", "8": "연수구", "9": "옹진군", "10": "중구",
    }},
    "대전광역시": {"code": "3", "sigungu": {
        "1": "대덕구", "2": "동구", "3": "서구", "4": "유성구", "5": "중구",
    }},
    "대구광역시": {"code": "4", "sigungu": {
        "1": "남구", "2": "달서구", "3": "달성군", "4": "동구", "5": "북구",
        "6": "서구", "7": "수성구", "8": "중구", "9": "군위군",
    }},
    "광주광역시": {"code": "5", "sigungu": {
        "1": "광산구", "2": "남구", "3": "동구", "4": "북구", "5": "서구",
    }},
    "부산광역시": {"code": "6", "sigungu": {
        "1": "강서구", "2": "금정구", "3": "기장군", "4": "남구", "5": "동구",
        "6": "동래구", "7": "부산진구", "8": "북구", "9": "사상구", "10": "사하구",
        "11": "서구", "12": "수영구", "13": "연제구", "14": "영도구", "15": "중구",
        "16": "해운대구",
    }},
    "울산광역시": {"code": "7", "sigungu": {
        "1": "중구", "2": "남구", "3": "동구", "4": "북구", "5": "울주군",
    }},
    "세종특별자치시": {"code": "8", "sigungu": {
        "1": "세종시",
    }},
    "경기도": {"code": "31", "sigungu": {
        "1": "가평군", "2": "고양시", "3": "과천시", "4": "광명시", "5": "광주시",
        "6": "구리시", "7": "군포시", "8": "김포시", "9": "남양주시", "10": "동두천시",
        "11": "부천시", "12": "성남시", "13": "수원시", "14": "시흥시", "15": "안산시",
        "16": "안성시", "17": "안양시", "18": "양주시", "19": "양평군", "20": "여주시",
        "21": "연천군", "22": "오산시", "23": "용인시", "24": "의왕시", "25": "의정부시",
        "26": "이천시", "27": "파주시", "28": "평택시", "29": "포천시", "31": "하남시",
        "32": "화성시",
    }},
    "강원특별자치도": {"code": "32", "sigungu": {
        "1": "강릉시", "2": "고성군", "3": "동해시", "4": "삼척시", "5": "속초시",
        "6": "양구군", "7": "양양군", "8": "영월군", "9": "원주시", "10": "인제군",
        "11": "정선군", "12": "철원군", "13": "춘천시", "14": "태백시", "15": "평창군",
        "16": "홍천군", "17": "화천군", "18": "횡성군",
    }},
    "충청북도": {"code": "33", "sigungu": {
        "1": "괴산군", "2": "단양군", "3": "보은군", "4": "영동군", "5": "옥천군",
        "6": "음성군", "7": "제천시", "8": "진천군", "9": "청주시", "10": "충주시",
        "11": "증평군",
    }},
    "충청남도": {"code": "34", "sigungu": {
        "1": "공주시", "2": "금산군", "3": "논산시", "4": "당진시", "5": "보령시",
        "6": "부여군", "7": "서산시", "8": "서천군", "9": "아산시", "11": "예산군",
        "12": "천안시", "13": "청양군", "14": "태안군", "15": "홍성군", "16": "계룡시",
    }},
    "경상북도": {"code": "35", "sigungu": {
        "1": "경산시", "2": "경주시", "3": "고령군", "4": "구미시", "5": "김천시",
        "6": "문경시", "7": "봉화군", "8": "상주시", "9": "성주군", "10": "안동시",
        "11": "영덕군", "12": "영양군", "13": "영주시", "14": "영천시", "15": "예천군",
        "16": "울릉군", "17": "울진군", "18": "의성군", "19": "청도군", "20": "청송군",
        "21": "칠곡군", "22": "포항시",
    }},
    "경상남도": {"code": "36", "sigungu": {
        "1": "거제시", "2": "거창군", "3": "고성군", "4": "김해시", "5": "남해군",
        "6": "밀양시", "7": "사천시", "8": "산청군", "9": "양산시", "11": "의령군",
        "12": "진주시", "13": "창녕군", "14": "창원시", "15": "통영시", "16": "하동군",
        "17": "함안군", "18": "함양군", "19": "합천군",
    }},
    "전북특별자치도": {"code": "37", "sigungu": {
        "1": "고창군", "2": "군산시", "3": "김제시", "4": "남원시", "5": "무주군",
        "6": "부안군", "7": "순창군", "8": "완주군", "9": "익산시", "10": "임실군",
        "11": "장수군", "12": "전주시", "13": "정읍시", "14": "진안군",
    }},
    "전라남도": {"code": "38", "sigungu": {
        "1": "강진군", "2": "고흥군", "3": "곡성군", "4": "광양시", "5": "구례군",
        "6": "나주시", "7": "담양군", "8": "목포시", "9": "무안군", "10": "보성군",
        "11": "순천시", "12": "신안군", "13": "여수시", "14": "영광군", "15": "영암군",
        "16": "완도군", "17": "장성군", "18": "장흥군", "19": "진도군", "20": "함평군",
        "21": "해남군", "22": "화순군",
    }},
    "제주특별자치도": {"code": "39", "sigungu": {
        "1": "제주시", "2": "서귀포시",
    }},
}

# NEIS 시도교육청 코드
SIDO_TO_NEIS_CODE = {
    "서울특별시": "B10", "부산광역시": "C10", "대구광역시": "D10", "인천광역시": "E10",
    "광주광역시": "F10", "대전광역시": "G10", "울산광역시": "H10", "세종특별자치시": "I10",
    "경기도": "J10", "강원특별자치도": "K10", "충청북도": "M10", "충청남도": "N10",
    "전북특별자치도": "P10", "전라남도": "Q10", "경상북도": "R10", "경상남도": "S10",
    "제주특별자치도": "T10",
}

# 테마 → contentTypeId
CONTENT_MAP = {
    "관광지": "12",
    "문화시설": "14",
    "축제/공연/행사": "15",
    "여행코스": "25",
    "레포츠/액티비티": "28",
    "숙박": "32",
    "쇼핑": "38",
    "맛집": "39",
}


# -----------------------------
# Helpers
# -----------------------------
def safe_text(value, default=""):
    return value if value not in (None, "") else default


def fetch_tour_data(area_code, sigungu_code, content_type_id, service_key, num_rows=20):
    api_url = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"
    params = {
        "serviceKey": service_key.strip(),
        "numOfRows": num_rows,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "K-TourAI",
        "_type": "json",
        "arrange": "A",
        "areaCode": area_code,
        "contentTypeId": content_type_id,
    }
    # 시/군/구가 "전체"가 아닐 때만 sigunguCode 추가
    if sigungu_code:
        params["sigunguCode"] = sigungu_code

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") not in ("0000", None):
            st.error(f"관광공사 API: {header.get('resultMsg', '알 수 없는 오류')}")
            return []

        items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
        )
        # 결과가 없으면 items 가 빈 문자열로 옴
        if items in (None, ""):
            return []
        items = items.get("item", [])

        if isinstance(items, list):
            return items
        if isinstance(items, dict):
            return [items]
        return []

    except Exception as e:
        st.error(f"관광공사 API 오류: {e}")
        return []


def search_school_neis(school_name, neis_key, atpt_ofcdc_sc_code=None, school_kind=None):
    base_url = "https://open.neis.go.kr/hub/schoolInfo"
    params = {
        "KEY": neis_key.strip(),
        "Type": "xml",
        "pIndex": 1,
        "pSize": 100,
        "SCHUL_NM": school_name.strip(),
    }

    if atpt_ofcdc_sc_code:
        params["ATPT_OFCDC_SC_CODE"] = atpt_ofcdc_sc_code

    school_kind_map = {
        "초등": "초등학교",
        "중등": "중학교",
        "고등": "고등학교",
    }
    if school_kind in school_kind_map:
        params["SCHUL_KND_SC_NM"] = school_kind_map[school_kind]

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        rows = []

        for row in root.findall(".//row"):
            item = {}
            for child in row:
                item[child.tag] = safe_text(child.text, "")
            rows.append(item)

        return rows

    except requests.exceptions.Timeout:
        st.error("NEIS API 요청 시간이 초과되었습니다.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"NEIS API 통신 오류: {e}")
        return []
    except ET.ParseError:
        st.error("NEIS 응답 파싱 실패: API 키 또는 응답 형식을 확인해주세요.")
        return []
    except Exception as e:
        st.error(f"NEIS 처리 중 예기치 않은 오류: {e}")
        return []


def generate_simple_plan(selected_school_name, selected_school_details, area_name, sigungu_name, content_name, extra_request):
    school_addr = ""
    if isinstance(selected_school_details, dict):
        school_addr = selected_school_details.get("ORG_RDNMA", "") or selected_school_details.get("ORG_RDNDA", "")

    dest = f"{area_name} {sigungu_name}".strip()

    plan_lines = [
        f"학교: {selected_school_name}",
        f"학교 주소: {school_addr if school_addr else '정보 없음'}",
        f"목적지: {dest}",
        f"테마: {content_name}",
        "",
        "추천 일정 흐름:",
        "1. 학교 출발",
        "2. 이동 및 점심",
        f"3. {dest} 내 주요 관광지 방문",
        "4. 체험/산책/사진 촬영",
        "5. 귀가",
    ]

    if extra_request.strip():
        plan_lines.extend(["", "추가 요청 반영:", extra_request.strip()])

    return "\n".join(plan_lines)


def card_html(item):
    title = item.get("title", "제목 미제공")
    addr = item.get("addr1", "주소 미제공")
    tel = item.get("tel", "연락처 미제공")
    image = item.get("firstimage", "")
    contentid = item.get("contentid", "")
    link = f"https://korean.visitkorea.or.kr/detail/ms_detail.do?cotid={contentid}" if contentid else "#"

    img_html = (
        f'<img src="{image}" style="width:100%;height:180px;object-fit:cover;border-radius:12px;">'
        if image
        else '<div style="width:100%;height:180px;background:#2E2E4A;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#9CA3AF;">이미지 없음</div>'
    )

    return f"""
    <div style="
        border:1px solid #444466;
        border-radius:16px;
        padding:14px;
        margin-bottom:16px;
        background:#2E2E4A;
        box-shadow:0 2px 8px rgba(0,0,0,0.2);
    ">
        {img_html}
        <h4 style="margin:12px 0 8px 0; color:#FFFFFF;">{title}</h4>
        <p style="margin:0;color:#CBD5E1;font-size:14px;">📍 {addr}</p>
        <p style="margin:6px 0 0 0;color:#CBD5E1;font-size:14px;">☎ {tel}</p>
        <p style="margin:10px 0 0 0;"><a href="{link}" target="_blank" style="color:#6C45F6;">상세보기</a></p>
    </div>
    """


# -----------------------------
# UI
# -----------------------------
st.title("📍 AI 대한민국 여행 가이드")
st.caption("한국관광공사 API와 NEIS API를 이용해 여행지와 학교를 연결합니다.")

left, right = st.columns([1, 2.2], gap="large")

with left:
    st.subheader("설정")

    st.markdown("#### 한국관광공사 API 키")
    service_key = st.text_input(
        "관광공사 서비스키(Decoding)",
        type="password",
        key="kto_service_key_input",
    )

    st.markdown("#### NEIS API 키")
    neis_service_key = st.text_input(
        "NEIS API 키",
        type="password",
        key="neis_service_key_input",
    )

    st.markdown("---")

    st.markdown("#### 1. 대상 학교")
    school_grade = st.radio("학교급", ["초등", "중등", "고등"], horizontal=True, key="school_grade_radio")

    # 학교 검색용 시/도 (NEIS 교육청 기준)
    school_sido = st.selectbox("학교 소재 시/도", list(SIDO_TO_NEIS_CODE.keys()), key="school_sido_select")
    current_neis_code = SIDO_TO_NEIS_CODE.get(school_sido)

    school_name_query = st.text_input(
        "학교명 검색",
        placeholder="예: 서울대학교사범대학부설고등학교",
        key="school_name_query_input",
    )

    if st.button("학교 검색", use_container_width=True):
        if not neis_service_key:
            st.warning("NEIS API 키를 입력해주세요.")
        elif not school_name_query.strip():
            st.warning("학교명을 입력해주세요.")
        elif not current_neis_code:
            st.warning("선택한 시/도에 대한 교육청 코드를 찾지 못했습니다.")
        else:
            with st.spinner("학교를 검색 중입니다..."):
                results = search_school_neis(
                    school_name=school_name_query,
                    neis_key=neis_service_key,
                    atpt_ofcdc_sc_code=current_neis_code,
                    school_kind=school_grade,
                )
                st.session_state.school_search_results = results
                st.session_state.selected_school_name = ""
                st.session_state.selected_school_details = None

            if not st.session_state.school_search_results:
                st.info("검색 결과가 없습니다. 학교명, 학교급, 시/도를 다시 확인해주세요.")

    if st.session_state.school_search_results:
        school_options_display = []
        for s in st.session_state.school_search_results:
            name = s.get("SCHUL_NM", "학교명 없음")
            addr = s.get("ORG_RDNMA", s.get("ORG_RDNDA", "주소 없음"))
            school_options_display.append(f"{name} ({addr})")

        selected_school_option = st.selectbox(
            "검색된 학교 선택",
            options=["--- 학교 선택 ---"] + school_options_display,
            key="selected_school_dropdown",
        )

        if selected_school_option != "--- 학교 선택 ---":
            idx = school_options_display.index(selected_school_option)
            school = st.session_state.school_search_results[idx]
            st.session_state.selected_school_details = school
            st.session_state.selected_school_name = school.get("SCHUL_NM", "")
            st.success(f"선택된 학교: {st.session_state.selected_school_name}")

            with st.expander("선택한 학교 상세정보", expanded=False):
                st.write(f"학교명: {school.get('SCHUL_NM', '')}")
                st.write(f"주소: {school.get('ORG_RDNMA', school.get('ORG_RDNDA', ''))}")
                st.write(f"설립형태: {school.get('FOND_SC_NM', '')}")
                st.write(f"학교구분: {school.get('SCHUL_KND_SC_NM', '')}")

    st.markdown("---")

    # =========================================================
    # 목적지 — 시/도 + 시/군/구 전체 선택 가능 (핵심 수정 부분)
    # =========================================================
    st.markdown("#### 목적지")

    dest_sido = st.selectbox(
        "목적지 시/도",
        options=list(REGIONS.keys()),
        key="dest_sido_select",
    )
    area_code = REGIONS[dest_sido]["code"]

    # 선택한 시/도의 모든 시/군/구 + "전체" 옵션
    sigungu_dict = REGIONS[dest_sido]["sigungu"]
    # "" (빈 문자열) = 전체
    sigungu_options = [""] + list(sigungu_dict.keys())

    def fmt_sigungu(code):
        return "전체 (시/도 전역)" if code == "" else sigungu_dict.get(code, code)

    sigungu_code = st.selectbox(
        "목적지 시/군/구",
        options=sigungu_options,
        format_func=fmt_sigungu,
        key="dest_sigungu_select",
    )
    sigungu_name = fmt_sigungu(sigungu_code)

    st.markdown("---")

    st.markdown("#### 테마 태그")
    selected_content_name = st.radio(
        "테마 선택",
        list(CONTENT_MAP.keys()),
        horizontal=True,
        key="theme_tags_radio",
    )
    content_type_id = CONTENT_MAP[selected_content_name]

    st.markdown("---")

    st.markdown("#### AI에게 특별히 부탁할 점")
    ai_request_text = st.text_area("추가 요청", height=100, key="ai_request_textarea")

    st.markdown("---")

    btn_generate_all = st.button("🚀 일정 생성 시작", use_container_width=True)

with right:
    st.subheader("결과")

    if btn_generate_all:
        if not service_key:
            st.warning("한국관광공사 API 키를 입력해주세요.")
        else:
            with st.spinner("여행 일정을 생성 중입니다..."):
                tour_items = fetch_tour_data(area_code, sigungu_code, content_type_id, service_key)
                plan_text = generate_simple_plan(
                    st.session_state.selected_school_name or "(학교 미선택)",
                    st.session_state.selected_school_details,
                    dest_sido,
                    sigungu_name,
                    selected_content_name,
                    ai_request_text,
                )

                st.session_state.generated_items = tour_items
                st.session_state.trip_plan_text = plan_text

            st.success("일정 생성 완료!")
            st.markdown("### 🧭 생성된 일정")
            st.text_area("일정 텍스트", value=st.session_state.trip_plan_text, height=220)

            st.markdown(f"### 📍 {dest_sido} {sigungu_name} · {selected_content_name}")
            if st.session_state.generated_items:
                cols = st.columns(2)
                for idx, item in enumerate(st.session_state.generated_items):
                    with cols[idx % 2]:
                        st.markdown(card_html(item), unsafe_allow_html=True)
            else:
                st.info("해당 지역/테마의 데이터가 없습니다. 다른 시/군/구나 테마를 선택해보세요.")

    if not btn_generate_all:
        st.markdown("### 안내")
        st.write("왼쪽에서 **목적지 시/도와 시/군/구**를 선택하고 테마를 고른 뒤 [일정 생성 시작]을 누르세요.")
        st.write("시/군/구에서 **'전체'**를 선택하면 해당 시/도 전역의 관광지를 검색합니다.")
        st.write("관광지 결과는 한국관광공사 API에서, 학교 정보는 NEIS API에서 불러옵니다.")
