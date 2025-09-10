import streamlit as st
import pandas as pd
import openpyxl  # .xlsx 파일 처리를 위해 필요합니다
import xlrd # .xls 파일 처리를 위해 필요합니다
import datetime

st.set_page_config(layout="wide")

st.title("경비예산 시각화 대시보드")
st.write("왼쪽 사이드바에서 경비예산 파일을 업로드하세요.")

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

        # ⚠️ 수정된 부분
        # 데이터프레임 전처리
        # 날짜 변환 오류를 무시하고 NaT로 처리
        df[컬럼_매핑['날짜']] = pd.to_datetime(df[컬럼_매핑['날짜']], errors='coerce')
        
        # 날짜 값이 없는(NaT) 행은 분석에서 제외
        df.dropna(subset=[컬럼_매핑['날짜']], inplace=True)
        # ⚠️ 수정된 부분 끝

        col1, col2 = st.columns([1, 4])
        with col2:
            st.header("데이터 분석")

            st.subheader("기간 선택")
            min_date = df[컬럼_매핑['날짜']].min()
            max_date = df[컬럼_매핑['날짜']].max()
            
            date_range = st.slider(
                "시작월과 종료월을 선택하세요",
                min_value=min_date.date(),
                max_value=max_date.date(),
                value=(min_date.date(), max_date.date()),
                format="YYYY년 MM월"
            )

            st.subheader("필터")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                st.write("**비용센터**")
                unique_비용센터 = sorted(df[컬럼_매핑['비용센터']].unique())
                selected_비용센터 = st.multiselect("비용센터를 선택하세요", unique_비용센터, unique_비용센터)

            with filter_col2:
                st.write("**원가요소**")
                unique_원가요소 = sorted(df[컬럼_매핑['원가요소']].unique())
                selected_원가요소 = st.multiselect("원가요소를 선택하세요", unique_원가요소, unique_원가요소)
            
            filtered_df = df[
                (df[컬럼_매핑['날짜']].dt.date >= date_range[0]) &
                (df[컬럼_매핑['날짜']].dt.date <= date_range[1]) &
                (df[컬럼_매핑['비용센터']].isin(selected_비용센터)) &
                (df[컬럼_매핑['원가요소']].isin(selected_원가요소))
            ]

            if filtered_df.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
            else:
                st.subheader("월별 비용 추이")
                monthly_data = filtered_df.groupby(filtered_df[컬럼_매핑['날짜']].dt.to_period('M'))[컬럼_매핑['비용']].sum()
                monthly_data = monthly_data.reset_index()
                monthly_data[컬럼_매핑['날짜']] = monthly_data[컬럼_매핑['날짜']].astype(str)
                monthly_data.rename(columns={컬럼_매핑['날짜']: '월'}, inplace=True)
                
                st.bar_chart(monthly_data.set_index('월'))

                st.subheader("필터링된 데이터프레임")
                st.write(f"총 데이터 수: {len(filtered_df)}개")
                st.dataframe(filtered_df, use_container_width=True)

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
else:
    st.info("파일을 업로드하면 여기에 데이터 분석 결과가 표시됩니다.")
