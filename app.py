import streamlit as st
import pandas as pd
import openpyxl  # .xlsx 파일 처리를 위해 필요합니다

st.set_page_config(layout="wide")

st.title("Excel 파일 업로드 및 데이터프레임 표시기")
st.write("왼쪽 사이드바에서 Excel 파일을 업로드하세요.")

# ---
# 사이드바 설정
# ---
st.sidebar.header("파일 업로드")
uploaded_file = st.sidebar.file_uploader(
    "여기에 Excel 파일(.xls, .xlsx)을 끌어다 놓거나 클릭하여 업로드하세요.",
    type=["xls", "xlsx"]
)

# ---
# 메인 화면에 데이터 표시
# ---
if uploaded_file is not None:
    try:
        # 파일 확장자를 확인하여 pandas로 읽기
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        elif uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')
        
        st.subheader("업로드된 파일 미리보기")
        st.write(f"**파일명:** `{uploaded_file.name}`")
        
        # 데이터프레임 표시 (use_container_width=True로 가로 폭에 맞춤)
        st.dataframe(df, use_container_width=True)
        
        # 데이터프레임의 기본 정보 표시
        st.subheader("데이터 정보")
        st.write(f"**행 수:** `{df.shape[0]}`")
        st.write(f"**열 수:** `{df.shape[1]}`")

    except Exception as e:
        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
        st.error("올바른 형식의 Excel 파일인지 확인해주세요.")
else:
    st.info("파일을 업로드하면 여기에 데이터가 표시됩니다.")
