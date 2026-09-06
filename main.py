import streamlit as st
import requests
import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="당곡고등학교 급식 조회",
    page_icon="🍚",
    layout="centered"
)

# 학교 고정 정보 (당곡고등학교)
ATPT_OFCDC_SC_CODE = "B10"   # 시도교육청코드 (서울)
SD_SCHUL_CODE = "7010073"    # 당곡고등학교 행정표준코드

# 나이스 오픈 API 인증키 (본인의 키로 교체하세요)
# https://open.neis.go.kr 에서 발급받을 수 있습니다.
NEIS_API_KEY = st.secrets.get("NEIS_API_KEY", "sample")  # secrets.toml에 저장 권장

# 식사코드 매핑
MEAL_CODE_DICT = {
    "조식": "1",
    "중식": "2",
    "석식": "3"
}

def get_meal_info(meal_date: str, meal_code: str):
    """
    나이스 급식식단정보 API 호출 함수
    meal_date: YYYYMMDD 형식의 문자열
    meal_code: 식사코드 (1:조식, 2:중식, 3:석식)
    """
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": meal_code,
        "MLSV_FROM_YMD": meal_date,
        "MLSV_TO_YMD": meal_date,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None
    except ValueError:
        st.error("응답을 JSON으로 파싱하는 데 실패했습니다.")
        return None


def parse_meal_data(data):
    """
    API 응답 데이터를 파싱하여 급식 정보 리스트 반환
    """
    if data is None:
        return None, "API 응답이 없습니다."

    # 에러 응답 처리 (RESULT 코드가 있는 경우)
    if "RESULT" in data:
        code = data["RESULT"].get("CODE", "")
        message = data["RESULT"].get("MESSAGE", "알 수 없는 오류")
        return None, f"[{code}] {message}"

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
        return rows, None
    except (KeyError, IndexError):
        return None, "해당 날짜의 급식 정보를 찾을 수 없습니다."


def main():
    st.title("🍚 당곡고등학교 급식 조회")
    st.caption("나이스(NEIS) 교육정보 개방 포털 Open API 활용")

    st.divider()

    # 사용자 입력: 날짜 선택
    col1, col2 = st.columns(2)

    with col1:
        selected_date = st.date_input(
            "조회할 날짜를 선택하세요",
            value=datetime.date.today()
        )

    with col2:
        selected_meal = st.selectbox(
            "식사 종류를 선택하세요",
            options=list(MEAL_CODE_DICT.keys()),
            index=1  # 기본값: 중식
        )

    meal_code = MEAL_CODE_DICT[selected_meal]
    meal_date_str = selected_date.strftime("%Y%m%d")

    st.divider()

    if st.button("🔍 급식 정보 조회", use_container_width=True):
        with st.spinner("급식 정보를 불러오는 중입니다..."):
            data = get_meal_info(meal_date_str, meal_code)
            rows, error_msg = parse_meal_data(data)

        if error_msg:
            st.warning(f"⚠️ {error_msg}")
        else:
            for row in rows:
                meal_date = row.get("MLSV_YMD", "")
                meal_type = row.get("MMEAL_SC_NM", "")
                dish_name = row.get("DDISH_NM", "")
                calorie = row.get("CAL_INFO", "")
                nutrition = row.get("NTR_INFO", "")
                origin = row.get("ORPLC_INFO", "")

                # 날짜 포맷 변환 (YYYYMMDD -> YYYY년 MM월 DD일)
                formatted_date = f"{meal_date[:4]}년 {meal_date[4:6]}월 {meal_date[6:]}일"

                st.subheader(f"📅 {formatted_date} - {meal_type}")

                # 메뉴는 <br/> 태그로 구분되어 있으므로 줄바꿈 처리
                menu_list = dish_name.replace("<br/>", "\n").split("\n")
                # 메뉴명에 포함된 숫자(알레르기 표시) 제거하지 않고 그대로 표시
                menu_text = "\n".join([f"- {item}" for item in menu_list if item.strip()])
                st.markdown("**🍽️ 메뉴**")
                st.markdown(menu_text)

                if calorie:
                    st.markdown(f"**🔥 칼로리:** {calorie}")

                if nutrition:
                    with st.expander("📊 영양 정보 보기"):
                        nutrition_list = nutrition.replace("<br/>", "\n").split("\n")
                        for item in nutrition_list:
                            if item.strip():
                                st.write(f"- {item}")

                if origin:
                    with st.expander("🌍 원산지 정보 보기"):
                        origin_list = origin.replace("<br/>", "\n").split("\n")
                        for item in origin_list:
                            if item.strip():
                                st.write(f"- {item}")

                st.divider()

    st.caption("데이터 출처: 교육부 및 한국교육학술정보원 나이스 대국민서비스(NEIS Open API)")


if __name__ == "__main__":
    main()
