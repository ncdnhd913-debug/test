import streamlit as st
import pandas as pd
import openpyxl  # .xlsx 파일 처리를 위해 필요합니다
import xlrd  # .xls 파일 처리를 위해 필요합니다
import datetime
import plotly.express as px

st.set_page_config(layout="wide")

st.title("경비예산 시각화 대시보드")

# ---
# 사이드바: 파일 업로더
# ---
st.sidebar.header("파일 업로드")
uploaded_file = st.sidebar.file_uploader(
    "여기에 Excel 파일(.xls, .xlsx)을 끌어다 놓거나 클릭하세요.",
    type=["xls", "xlsx"]
)

# ---
# 메인 화면
# ---
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')

        컬럼_매핑 = {
            '날짜': '계획연월',
            '비용센터': '비용센터명',
            '원가요소': '원가요소명',
            '비용': '고정금액'
        }
        
        for key, value in 컬럼_매핑.items():
            if value not in df.columns:
                st.error(f"오류: '{value}' 컬럼이 파일에 존재하지 않습니다. 파일을 확인해주세요.")
                st.stop()

        df[컬럼_매핑['날짜']] = pd.to_datetime(df[컬럼_매핑['날짜']], errors='coerce')
        df.dropna(subset=[컬럼_매핑['날짜']], inplace=True)
        
        if df.empty:
            st.warning("업로드된 파일에 유효한 날짜 데이터가 없습니다.")
            st.stop()

        # ⚠️ 전체 콘텐츠를 가운데로 정렬하기 위한 컬럼 설정
        col1, col_main, col3 = st.columns([1, 4, 1])
        
        with col_main:
            st.header("데이터 분석")
            
            # --- 날짜 필터 ---
            st.subheader("기간 선택")
            min_date = df[컬럼_매핑['날짜']].min()
            max_date = df[컬럼_매핑['날짜']].max()
            
            if min_date.date() == max_date.date():
                st.info(f"선택할 수 있는 데이터는 **{min_date.strftime('%Y년 %m월')}** 한 달치입니다.")
                date_range = (min_date.date(), max_date.date())
            else:
                date_range = st.slider(
                    "시작월과 종료월을 선택하세요",
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    value=(min_date.date(), max_date.date()),
                    format="YYYY년 %m월"
                )

            # --- 상위/하위 필터 (Expander 사용) ---
            st.subheader("필터")

            with st.expander("상위 필터: 비용센터"):
                unique_비용센터 = sorted(df[컬럼_매핑['비용센터']].unique())
                selected_비용센터 = st.multiselect(
                    "비용센터를 선택하세요", unique_비용센터, unique_비용센터,
                    key="비용센터_필터"
                )

            with st.expander("하위 필터: 원가요소"):
                unique_원가요소 = sorted(df[컬럼_매핑['원가요소']].unique())
                selected_원가요소 = st.multiselect(
                    "원가요소를 선택하세요", unique_원가요소, unique_원가요소,
                    key="원가요소_필터"
                )

            filtered_df = df[
                (df[컬럼_매핑['날짜']].dt.date >= date_range[0]) &
                (df[컬럼_매핑['날짜']].dt.date <= date_range[1]) &
                (df[컬럼_매핑['비용센터']].isin(selected_비용센터)) &
                (df[컬럼_매핑['원가요소']].isin(selected_원가요소))
            ]

            if filtered_df.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
            else:
                # --- 시각화 (백만원 단위로 변환) ---
                st.subheader("월별 비용
