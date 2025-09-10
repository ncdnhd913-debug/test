import streamlit as st
import pandas as pd
import openpyxl  # .xlsx 파일 처리를 위해 필요합니다
import xlrd  # .xls 파일 처리를 위해 필요합니다
import datetime
import plotly.express as px

# 페이지 설정: 와이드 레이아웃과 제목, 아이콘 설정
st.set_page_config(layout="wide", page_title="경비예산 대시보드", page_icon="📊")

# 제목을 가운데로 정렬하는 CSS 추가
st.markdown("""
    <style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .st-emotion-cache-121p55r {
        text-align: center;
    }
    .st-emotion-cache-c3qg0s {
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 경비예산 시각화 대시보드")
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

        df[컬럼_매핑['날짜']] = pd.to_datetime(df[컬럼_매핑['날짜']], errors='coerce')
        df.dropna(subset=[컬럼_매핑['날짜']], inplace=True)
        
        if df.empty:
            st.warning("업로드된 파일에 유효한 날짜 데이터가 없습니다.")
            st.stop()
        
        # 전체 콘텐츠를 왼쪽으로 정렬하기 위해 컬럼 제거
        st.header("데이터 분석")
        
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
                format="YYYY년 MM월"
            )

        # 필터와 차트를 가로로 나란히 배치
        filter_col1, filter_col2, chart_col = st.columns([1, 1, 3])

        with filter_col1:
            with st.expander("비용센터"):
                unique_비용센터 = sorted(df[컬럼_매핑['비용센터']].unique())
                selected_비용센터 = st.multiselect(
                    "비용센터를 선택하세요", unique_비용센터, unique_비용센터,
                    key="비용센터_필터"
                )

        with filter_col2:
            with st.expander("원가요소"):
                # 비용센터 필터에 따라 원가요소 목록을 동적으로 변경
                if selected_비용센터:
                    # 선택된 비용센터에 해당하는 원가요소만 추출
                    filtered_원가요소_df = df[df[컬럼_매핑['비용센터']].isin(selected_비용센터)]
                    unique_원가요소 = sorted(filtered_원가요소_df[컬럼_매핑['원가요소']].unique())
                else:
                    # 비용센터가 선택되지 않았을 경우 모든 원가요소 표시
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

        with chart_col:
            if filtered_df.empty:
                st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
            else:
                st.subheader("월별 비용 추이")
                monthly_data = filtered_df.groupby(filtered_df[컬럼_매핑['날짜']].dt.to_period('M'))[컬럼_매핑['비용']].sum()
                monthly_data = monthly_data.reset_index()
                
                # 비용을 백만원 단위로 변환
                monthly_data[컬럼_매핑['비용']] = monthly_data[컬럼_매핑['비용']] / 1_000_000
                monthly_data.rename(columns={컬럼_매핑['비용']: '비용 (백만원)'}, inplace=True)

                # 날짜 형식을 "YYYY년 MM월"로 변환
                monthly_data['월'] = pd.to_datetime(monthly_data[컬럼_매핑['날짜']].astype(str)).dt.strftime('%Y년 %m월')
                
                fig = px.bar(
                    monthly_data, 
                    x='월',  # '월' 컬럼 사용
                    y='비용 (백만원)',
                    labels={'월': '날짜', '비용 (백만원)': '비용 (백만원)'},
                    title="월별 비용 추이 (단위: 백만원)"
                )
                st.plotly_chart(fig, use_container_width=True)

        # 데이터프레임을 왼쪽으로 밀착시켜 표시
        st.subheader("필터링된 데이터프레임")
        st.write(f"총 데이터 수: {len(filtered_df)}개")
        st.dataframe(filtered_df, use_container_width=True)

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
        st.error("파일 형식을 확인하거나 컬럼명을 다시 확인해주세요.")
else:
    st.info("파일을 업로드하면 여기에 데이터 분석 결과가 표시됩니다.")
