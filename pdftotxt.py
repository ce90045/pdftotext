import streamlit as st
import os
import tempfile
import re
from collections import Counter
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path

st.set_page_config(page_title="PDF → TXT 변환기 (스마트 정렬)", page_icon="📄", layout="centered")
st.title("📄 PDF → TXT 변환기 (스마트 정렬)")
st.markdown("""
- ✅ **줄바꿈 단절 해결**: 화면 라인 단위가 아닌 문장/문단 단위로 재구성
- ✅ **머릿글/꼬리글 제거**: 페이지 번호, 반복 제목 자동 탐지 및 삭제
- ✅ **OCR 지원**: 체크 시 스캔형/이미지 PDF도 변환 가능
""")

OUTPUT_DIR = "./converted_txt"
os.makedirs(OUTPUT_DIR, exist_ok=True)

uploaded_file = st.file_uploader("PDF 파일을 선택하세요", type="pdf")
use_ocr = st.checkbox("🔍 OCR 활성화 (스캔형/이미지 PDF)", value=False)
clean_option = st.checkbox("🧹 문장 단위 정리 및 머릿글/꼬리글 제거", value=True)

def clean_and_structure_text(pages_text, remove_hf=True):
    if not pages_text:
        return ""

    # 1. 헤더/푸터 자동 제거
    if remove_hf:
        hf_counter = Counter()
        normalize = lambda s: re.sub(r'[\d\s.,;:!?\'"()\[\]{}\-]', '', s).strip()

        for page in pages_text:
            lines = [l.strip() for l in page.split('\n') if l.strip()]
            if len(lines) < 6:
                continue
            top = lines[:3]
            bottom = lines[-3:]
            for line in top + bottom:
                norm = normalize(line)
                if len(norm) >= 2:
                    hf_counter[norm] += 1

        threshold = max(2, len(pages_text) * 0.4)
        remove_norms = {n for n, c in hf_counter.items() if c >= threshold}

        cleaned_pages = []
        for page in pages_text:
            lines = page.split('\n')
            filtered = [l for l in lines if normalize(l.strip()) not in remove_norms]
            cleaned_pages.append('\n'.join(filtered))
    else:
        cleaned_pages = pages_text

    # 2. 전체 텍스트 합치기 및 문장 재구성
    full_text = "\n\n".join(cleaned_pages)
    full_text = re.sub(r'-\s*\n\s*', '', full_text)
    full_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', full_text)
    full_text = re.sub(r'[ \t]{2,}', ' ', full_text)
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)

    paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
    return '\n\n'.join(paragraphs)

if uploaded_file is not None:
    original_name = uploaded_file.name
    txt_filename = os.path.splitext(original_name)[0] + ".txt"
    save_path = os.path.join(OUTPUT_DIR, txt_filename)

    if st.button("🔄 변환 및 정리 시작", type="primary"):
        pages_text = []
        temp_pdf = None
        try:
            if use_ocr:
                st.info("⏳ OCR 변환 중... (페이지 수에 따라 수 분 소요)")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=OUTPUT_DIR) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    temp_pdf = tmp.name

                images = convert_from_path(temp_pdf, dpi=200)
                for i, img in enumerate(images):
                    txt = pytesseract.image_to_string(img, lang="kor+eng")
                    pages_text.append(txt)
                    st.progress((i + 1) / len(images), text="페이지 {}/{} 처리 중...".format(i+1, len(images)))
            else:
                st.info("⏳ 텍스트 레이어 추출 중...")
                pdf_reader = PdfReader(uploaded_file)
                for i, page in enumerate(pdf_reader.pages):
                    pages_text.append(page.extract_text() or "")

            final_text = clean_and_structure_text(pages_text, remove_hf=clean_option)

            if not final_text.strip():
                st.warning("❌ 추출된 텍스트가 없습니다.\n"
                           "• 일반 PDF라면 문서가 이미지로만 구성되었을 수 있습니다.\n"
                           "• OCR 사용 중이라면 Tesseract 한글 언어팩(`kor.traineddata`)이 필요합니다.")
            else:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(final_text)
                st.success("✅ 변환 완료: " + save_path)

                preview = final_text[:2000] + ("..." if len(final_text) > 2000 else "")
                st.text_area("미리보기", preview, height=250)
                st.download_button(
                    label="📥 TXT 파일 다운로드",
                    data=final_text.encode("utf-8"),
                    file_name=txt_filename,
                    mime="text/plain"
                )

        except Exception as e:
            err = str(e).lower()
            if "tesseract" in err:
                st.error("❌ Tesseract OCR이 설치되지 않았습니다.")
            elif "poppler" in err:
                st.error("❌ Poppler가 설치되지 않았습니다.")
            else:
                st.error("❌ 오류 발생: " + str(e))
        finally:
            if temp_pdf and os.path.exists(temp_pdf):
                os.remove(temp_pdf)
