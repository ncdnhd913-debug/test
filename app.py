import streamlit as st
import pandas as pd
import openpyxl  # .xlsx 파일 처리를 위해 필요합니다
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
        # 파일 확장자에 따라 다른 엔진 사용
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')

        # ---
        # ⚠️ 컬럼 이름 매핑: 파일의 실제 컬럼명에 맞게 수정하세요.
        # ---
        컬럼_매핑 = {
            '날짜': '날짜',
            '비용센터': '비용센터명',
            '원가요소': '원가요소',
            '비용': '비용'
        }
        
        # 컬럼 이름이 존재하지 않으면 에러 메시지 출력
        for key, value in 컬럼_매핑.items():
            if value not in df.columns:
                st.error(f"오류: '{value}' 컬럼이 파일에 존재하지 않습니다. `컬럼_매핑`을 수정해주세요.")
                st.stop()

        # 데이터프레임 전처리
        df[컬럼_매핑['날짜']] = pd.to_datetime(df[컬럼_매핑['날짜']])

        # ---
        # 필터링 UI (컬럼으로 분할)
        # ---
        col1, col2 = st.columns([1, 4])
        with col2:
            st.header("데이터 분석")

            # --- 날짜 필터 ---
            st.subheader("기간 선택")
            min_date = df[컬럼_매핑['날짜']].min()
            max_date = df[컬럼_매핑['날짜']].max()
            
            # 날짜 선택기 (드래그 형식)
            date_range = st.slider(
                "시작월과 종료월을 선택하세요",
                min_value=min_date.date(),
                max_value=max_date.date(),
                value=(min_date.date(), max_date.date()),
                format="YYYY년 MM월"
            )

            # --- 비용센터 및 원가요소 필터 ---
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
            
            # 필터 적용
            filtered_df = df[
                (df[컬럼_매핑['날짜']].dt.date >= date_range[0]) &
                (df[컬럼_매핑['날짜']].dt.date <= date_range[1]) &
                (df[컬럼_매핑['비용센터']].isin(selected_비용센터)) &
                (df[컬럼_매핑['원가요소']].isin(selected_원가요소))
            ]

            if filtered_df.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
            else:
                # --- 시각화 ---
                st.subheader("월별 비용 추이")
                # 월별로 데이터 집계
                monthly_data = filtered_df.groupby(filtered_df[컬럼_매핑['날짜']].dt.to_period('M'))[컬럼_매핑['비용']].sum()
                monthly_data = monthly_data.reset_index()
                monthly_data[컬럼_매핑['날짜']] = monthly_data[컬럼_매핑['날짜']].astype(str)
                monthly_data.rename(columns={컬럼_매핑['날짜']: '월'}, inplace=True)
                
                st.bar_chart(monthly_data.set_index('월'))

                # --- 데이터프레임 표시 ---
                st.subheader("필터링된 데이터프레임")
                st.write(f"총 데이터 수: {len(filtered_df)}개")
                st.dataframe(filtered_df, use_container_width=True)

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
        st.error("파일 형식이 올바른지 확인하거나, `컬럼_매핑`을 다시 확인해주세요.")

else:
    st.info("파일을 업로드하면 여기에 데이터 분석 결과가 표시됩니다.")
