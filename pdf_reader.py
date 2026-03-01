import fitz  # PyMuPDF - لتتمكن من استخدامها، يجب تثبيتها عبر: pip install PyMuPDF

def extract_text_from_pdf(pdf_path):
    """
    قراءة واستخراج النص من ملف PDF.
    """
    try:
        # فتح ملف الـ PDF
        document = fitz.open(pdf_path)
        text = ""
        
        # المرور على كل صفحات الملف واستخراج النص
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
            
        return text
    except Exception as e:
        return f"حدث خطأ أثناء قراءة الملف: {e}"

if __name__ == "__main__":
    # مسار ملف الـ PDF (استبدله بمسار الملف الخاص بك)
    pdf_file_path = "sample.pdf" 
    
    print(f"جاري استخراج النص من {pdf_file_path}...\n")
    extracted_text = extract_text_from_pdf(pdf_file_path)
    
    print("--- النص المستخرج ---")
    print(extracted_text)
