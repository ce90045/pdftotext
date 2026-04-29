import streamlit as st
import os
from pypdf import PdfReader

st.set_page_config(page_title="PDF → TXT 변환기", page_icon="📄", layout="centered")
st.title("📄 PDF → TXT 변환기")
st.markdown("PDF 파일을 선택하면 **동일한 파일명**으로 `.txt` 파일을 생성합니다.")

# 파일 업로더
uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type="pdf")

if uploaded_file is not None:
    # 원본 파일명에서 확장자만 .txt로 변경
    original_name = uploaded_file.name
    txt_filename = os.path.splitext(original_name)[0] + ".txt"

    try:
        # PDF 읽기 및 텍스트 추출
        pdf_reader = PdfReader(uploaded_file)
        extracted_text = ""
        
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"
            else:
                st.info(f"⚠️ {i+1}페이지는 텍스트를 추출할 수 없습니다. (이미지/스캔본일 가능성)")

        # 추출된 텍스트가 없을 경우 처리
        if not extracted_text.strip():
            st.warning("❌ PDF에서 텍스트를 추출하지 못했습니다.\n"
                       "스캔된 이미지 기반 PDF인 경우 OCR 도구(예: `pytesseract`)가 필요합니다.")
        else:
            st.success(f"✅ 텍스트 추출 완료: `{txt_filename}`")
            st.text_area("미리보기", extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""), height=200)

            # TXT 파일 다운로드 버튼
            st.download_button(
                label="📥 TXT 파일 다운로드",
                data=extracted_text.encode("utf-8"),
                file_name=txt_filename,
                mime="text/plain"
            )

    except Exception as e:
        st.error(f"❌ 처리 중 오류가 발생했습니다:\n{e}")
