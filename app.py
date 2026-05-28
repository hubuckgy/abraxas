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
# Helpers
# -----------------------------
def safe_text(value, default=""):
    return value if value not in (None, "") else default


def fetch_tour_data(area_code, sigungu_code, content_type_id, service_key):
    api_url = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"
    params = {
        "serviceKey": service_key.strip(),
        "numOfRows": 12,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "K-TourAI",
        "_type": "json",
        "areaCode": area_code,
        "sigunguCode": sigungu_code,
        "contentTypeId": content_type_id,
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )

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


def generate_simple_plan(selected_school_name, selected_school_details, area_name, content_name, extra_request):
    school_addr = ""
    if isinstance(selected_school_details, dict):
        school_addr = selected_school_details.get("ORG_RDNMA", "") or selected_school_details.get("ORG_RDNDA", "")

    plan_lines = [        f"학교: {selected_school_name}",
        f"학교 주소: {school_addr if school_addr else '정보 없음'}",
        f"목적지 지역: {area_name}",
        f"테마: {content_name}",
        "",
        "추천 일정 흐름:",
        "1. 학교 출발",
        "2. 이동 및 점심",
        f"3. {area_name} 내 주요 관광지 방문",
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
# 지역 데이터
# -----------------------------
sido_to_neis_code = {
    "서울특별시": "B10", "부산광역시": "C10", "대구광역시": "D10", "인천광역시": "E10",
    "광주광역시": "F10", "대전광역시": "G10", "울산광역시": "H10", "세종특별자치시": "I10",
    "경기도": "J10", "강원특별자치도": "K10", "충청북도": "M10", "충청남도": "N10",
    "전라북도": "P10", "전라남도": "Q10", "경상북도": "R10", "경상남도": "S10",
    "제주특별자치도": "T10",
}

sido_to_tour_area_code = {
    "서울특별시": "1", "부산광역시": "6", "대구광역시": "4", "인천광역시": "2",
    "광주광역시": "5", "대전광역시": "3", "울산광역시": "7", "세종특별자치시": "8",
    "경기도": "31", "강원특별자치도": "32", "충청북도": "33", "충청남도": "34",
    "전라북도": "35", "전라남도": "36", "경상북도": "37", "경상남도": "38",
    "제주특별자치도": "39",
}

sigungu_map = {
    "서울특별시": {"23": "종로구", "24": "중구", "25": "용산구", "26": "성동구", "27": "광진구", "28": "동대문구", "29": "중랑구", "30": "성북구", "31": "강북구", "32": "도봉구", "33": "노원구", "34": "은평구", "35": "서대문구", "36": "마포구", "37": "양천구", "38": "강서구", "39": "구로구", "40": "금천구", "41": "영등포구", "42": "동작구", "43": "관악구", "44": "서초구", "45": "강남구", "46": "송파구", "47": "강동구"},
    "부산광역시": {"1": "중구", "2": "서구", "3": "동구", "4": "영도구", "5": "부산진구", "6": "동래구", "7": "남구", "8": "북구", "9": "해운대구", "10": "사하구", "11": "금정구", "12": "강서구", "13": "연제구", "14": "수영구", "15": "사상구", "16": "기장군"},
    "대구광역시": {"1": "중구", "2": "동구", "3": "서구", "4": "남구", "5": "북구", "6": "수성구", "7": "달서구", "8": "달성군"},
    "인천광역시": {"1": "중구", "2": "동구", "3": "미추홀구", "4": "연수구", "5": "남동구", "6": "부평구", "7": "계양구", "8": "서구", "9": "강화군", "10": "옹진군"},
    "광주광역시": {"1": "동구", "2": "서구", "3": "남구", "4": "북구", "5": "광산구"},
    "대전광역시": {"1": "동구", "2": "중구", "3": "서구", "4": "유성구", "5": "대덕구"},
    "울산광역시": {"1": "중구", "2": "남구", "3": "동구", "4": "북구", "5": "울주군"},
    "세종특별자치시": {"1": "세종시"},
    "경기도": {"1": "수원시", "2": "성남시", "3": "의정부시", "4": "안양시", "5": "부천시", "6": "광명시", "7": "평택시", "8": "동두천시", "9": "안산시", "10": "고양시", "11": "과천시", "12": "구리시", "13": "남양주시", "14": "오산시", "15": "시흥시", "16": "군포시", "17": "의왕시", "18": "하남시", "19": "용인시", "20": "파주시", "21": "이천시", "22": "안성시", "23": "김포시", "24": "화성시"},
    "강원특별자치도": {"1": "춘천시", "2": "원주시", "3": "강릉시", "4": "동해시", "5": "태백시", "6": "속초시", "7": "삼척시"},
    "충청북도": {"1": "청주시", "2": "충주시", "3": "제천시", "4": "보은군", "5": "옥천군", "6": "영동군"},
    "충청남도": {"1": "천안시", "2": "공주시", "3": "보령시", "4": "아산시", "5": "서산시", "6": "논산시"},
    "전라북도": {"1": "전주시", "2": "군산시", "3": "익산시", "4": "정읍시", "5": "남원시"},
    "전라남도": {"1": "목포시", "2": "여수시", "3": "순천시", "4": "나주시", "5": "광양시"},
    "경상북도": {"1": "포항시", "2": "경주시", "3": "김천시", "4": "안동시", "5": "구미시"},
    "경상남도": {"1": "창원시", "2": "진주시", "3": "통영시", "4": "사천시", "5": "김해시"},
    "제주특별자치도": {"1": "제주시", "2": "서귀포시"},
}

# -----------------------------
# UI
# -----------------------------
st.title("📍 AI 대한민국 여행 가이드")
st.caption("한국관광공사 API와 NEIS API를 이용해 여행지와 학교를 연결합니다.")

left, right = st.columns([1, 2.2], gap="large")

with left:
    st.subheader("설정")

    st.markdown("#### 한국관광공사 API 키")
    service_key = st.text_input("관광공사 서비스키(Decoding)", type="password", key="kto_service_key_input")

    st.markdown("#### NEIS API 키")
    neis_service_key = st.text_input("NEIS API 키", type="password", key="neis_service_key_input")

    st.markdown("---")

    st.markdown("#### 1. 대상 학교")
    school_grade = st.radio("학교급", ["초등", "중등", "고등"], horizontal=True, key="school_grade_radio")

    sido_options = list(sido_to_neis_code.keys())
    school_sido = st.selectbox("학교 시/도", sido_options, key="school_sido_select")
    current_neis_code = sido_to_neis_code.get(school_sido)

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
                st.session_state.school_search_results =
 if dest_sigungu_keys:
        dest_sigungu_code = st.selectbox(
            "목적지 시/군/구",
            options=dest_sigungu_keys,
            format_func=lambda x: dest_sigungu_map.get(x, x),
            key="dest_sigungu_select",
        )
        dest_sigungu_name = dest_sigungu_map.get(dest_sigungu_code, "")
    else:
        dest_sigungu_code = ""
        dest_sigungu_name = ""

    st.markdown("---")
    st.markdown("#### 4. 관광 테마")
    content_map = {
        "역사유적": "12",
        "자연생태": "28",
        "액티비티": "38",
        "맛집투어": "39",
        "문화예술": "14",
        "축제/공연/행사": "15",
    }

    selected_content_name = st.radio(
        "테마 선택",
        list(content_map.keys()),
        horizontal=True,
        key="theme_tags_radio",
    )
    content_type_id = content_map[selected_content_name]

    st.markdown("---")
    st.markdown("#### 5. 추가 요청")
    extra_request = st.text_area(
        "원하는 조건을 적어주세요",
        placeholder="예: 점심식사 포함, 실내 위주, 도보 이동 최소화",
        height=100,
        key="extra_request_input",
    )

    st.markdown("---")
    search_button = st.button("여행지 검색", use_container_width=True)

with right:
    st.subheader("결과")

    if search_button:
        if not service_key:
            st.warning("관광공사 서비스키를 입력해주세요.")
        elif not st.session_state.selected_school_name:
            st.warning("먼저 학교를 선택해주세요.")
        elif not dest_sigungu_code:
            st.warning("목적지 시/군/구를 선택해주세요.")
        else:
            with st.spinner("관광지를 검색 중입니다..."):
                tour_items = fetch_tour_data(
                    area_code=current_area_code,
                    sigungu_code=dest_sigungu_code,
                    content_type_id=content_type_id,
                    service_key=service_key,
                )
                st.session_state.generated_items = tour_items

                school_details = st.session_state.selected_school_details
                plan_title_area = f"{dest_sido} {dest_sigungu_name}".strip()
                st.session_state.trip_plan_text = generate_simple_plan(
                    selected_school_name=st.session_state.selected_school_name,
                    selected_school_details=school_details,
                    area_name=plan_title_area,
                    content_name=selected_content_name,
                    extra_request=extra_request,
                )

    if st.session_state.trip_plan_text:
        st.markdown("### 📌 여행 계획")
        st.text_area("계획서", value=st.session_state.trip_plan_text, height=260, key="plan_output_textarea")

    if st.session_state.generated_items:
        st.markdown("### 🏞️ 추천 관광지")
        for item in st.session_state.generated_items:
            st.markdown(card_html(item), unsafe_allow_html=True)
    else:
        st.info("조건을 선택한 뒤 ‘여행지 검색’을 누르면 관광지가 표시됩니다.")