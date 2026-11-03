from pathlib import Path
import re
import html
import tempfile

from transliterator import convert

MAX_FILE_BYTES = 19 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".xlsx", ".pptx", ".txt", ".rtf"}

def _convert_paragraph(paragraph, mode):
    original = paragraph.text
    if not original:
        return
    converted = convert(original, mode)
    if converted == original:
        return
    if paragraph.runs:
        paragraph.runs[0].text = converted
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(converted)

def _convert_docx(src, dst, mode):
    from docx import Document
    doc = Document(src)
    for p in doc.paragraphs:
        _convert_paragraph(p, mode)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _convert_paragraph(p, mode)
                for nested in cell.tables:
                    for row2 in nested.rows:
                        for cell2 in row2.cells:
                            for p in cell2.paragraphs:
                                _convert_paragraph(p, mode)
    for section in doc.sections:
        for part in (section.header, section.footer, section.first_page_header, section.first_page_footer):
            for p in part.paragraphs:
                _convert_paragraph(p, mode)
            for table in part.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            _convert_paragraph(p, mode)
    doc.save(dst)
    return {"note": "Matn öğirildi. Paragraf ichidagi turli shrift uslublari ayrim joylarda birinchi matn bo‘lagining uslubiga birlashtirilishi mumkin."}

def _convert_xlsx(src, dst, mode):
    from openpyxl import load_workbook
    wb = load_workbook(src)
    changed = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and not cell.value.startswith("="):
                    new_value = convert(cell.value, mode)
                    if new_value != cell.value:
                        cell.value = new_value
                        changed += 1
    wb.save(dst)
    return {"note": f"{changed} ta katakdagi matn öğirildi. Formulalar özgartirilmadi."}

def _convert_pptx(src, dst, mode):
    from pptx import Presentation
    prs = Presentation(src)
    for slide in prs.slides:
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False):
                for p in shape.text_frame.paragraphs:
                    _convert_paragraph(p, mode)
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    for cell in row.cells:
                        for p in cell.text_frame.paragraphs:
                            _convert_paragraph(p, mode)
    prs.save(dst)
    return {"note": "Slaydlardagi matn öğirildi. Paragraf ichidagi alohida run formatlari soddalashtirilishi mumkin."}

def _read_txt(src):
    data = Path(src).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")

def _convert_txt(src, dst, mode):
    text = convert(_read_txt(src), mode)
    Path(dst).write_text(text, encoding="utf-8")
    return {"note": "TXT fayli UTF-8 kodlashida saqlandi."}

def _rtf_to_text(data):
    try:
        from striprtf.striprtf import rtf_to_text
        return rtf_to_text(data.decode("utf-8", errors="replace"))
    except Exception:
        s = data.decode("latin1", errors="replace")
        s = re.sub(r"\\'[0-9a-fA-F]{2}", " ", s)
        s = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", s)
        s = re.sub(r"[{}]", "", s)
        return s

def _text_to_rtf(text):
    escaped = text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\par " + "\n")
    return r"{\rtf1\ansi\deff0{\fonttbl{\f0 Arial;}}\f0\fs22 " + escaped + "}"

def _convert_rtf(src, dst, mode):
    text = convert(_rtf_to_text(Path(src).read_bytes()), mode)
    Path(dst).write_bytes(_text_to_rtf(text).encode("utf-8"))
    return {"note": "RTF matni öğirildi; murakkab sahifa dizayni va ayrim formatlash elementlari saqlanmasligi mumkin."}

def _convert_pdf(src, dst, mode):
    import fitz
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import mm

    pdf = fitz.open(src)
    pages = []
    total_chars = 0
    for page in pdf:
        text = page.get_text("text")
        pages.append(text)
        total_chars += len(text.strip())
    pdf.close()

    if total_chars < 20:
        raise ValueError("PDF ichidan matn topilmadi. Ehtimol, bu skanerlangan PDF; hozircha OCR qöllab-quvvatlanmaydi.")

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pathlib import Path as _Path
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    font_path = next((p for p in font_candidates if _Path(p).exists()), None)
    if font_path:
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        font_name = "DejaVuSans"
    else:
        font_name = "Helvetica"
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.fontName = font_name
    body.fontSize = 9
    body.leading = 12
    story = []
    for index, page_text in enumerate(pages):
        converted = convert(page_text, mode)
        for line in converted.splitlines():
            if line.strip():
                safe = html.escape(line).replace(" ", "&nbsp;")
                story.append(Paragraph(safe, body))
            else:
                story.append(Spacer(1, 3 * mm))
        if index < len(pages) - 1:
            story.append(PageBreak())

    doc = SimpleDocTemplate(
        str(dst), pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title="Transliteratsiya qilingan hujjat",
    )
    doc.build(story)
    return {"note": "PDF matni yangi PDFga qayta joylandi. Asl sahifa maketi, rasmlar va murakkab jadvallar saqlanmaydi; matnli PDF kerak."}

def convert_file(src, dst, mode="auto"):
    src = Path(src)
    dst = Path(dst)
    if src.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Fayl hajmi 19 MB limitdan katta.")
    ext = src.suffix.lower()
    if ext == ".docx":
        return _convert_docx(src, dst, mode)
    if ext == ".xlsx":
        return _convert_xlsx(src, dst, mode)
    if ext == ".pptx":
        return _convert_pptx(src, dst, mode)
    if ext == ".txt":
        return _convert_txt(src, dst, mode)
    if ext == ".rtf":
        return _convert_rtf(src, dst, mode)
    if ext == ".pdf":
        return _convert_pdf(src, dst, mode)
    raise ValueError("Qo‘llab-quvvatlanmaydigan fayl turi.")
