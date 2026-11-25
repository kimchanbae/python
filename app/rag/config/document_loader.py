import csv
import hashlib

from pathlib import Path

from pypdf import PdfReader
from docx import Document as WordDocument
from openpyxl import load_workbook
from pptx import Presentation
from bs4 import BeautifulSoup

from langchain_core.documents import Document


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".md",
    ".csv", ".xlsx", ".pptx", ".html", ".htm"
}


def file_hash(file_path):
    """파일 내용의 SHA256 해시"""

    sha = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)

    return sha.hexdigest()


def load_pdf(path):
    reader = PdfReader(path)
    docs = []

    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""

        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "file_type": "pdf",
                        "page": page_num
                    }
                )
            )

    return docs


def load_docx(path):
    doc = WordDocument(path)

    parts = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text)

    for table in doc.tables:
        for row in table.rows:
            parts.append(
                " | ".join(cell.text for cell in row.cells)
            )

    return [
        Document(
            page_content="\n".join(parts),
            metadata={
                "source": str(path),
                "file_type": "docx"
            }
        )
    ]


def load_text(path):
    text = Path(path).read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    return [
        Document(
            page_content=text,
            metadata={
                "source": str(path),
                "file_type": Path(path).suffix[1:]
            }
        )
    ]


def load_csv(path):
    docs = []

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, 1):

            content = "\n".join(
                f"{key}: {value}"
                for key, value in row.items()
            )

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": str(path),
                        "file_type": "csv",
                        "row": row_num
                    }
                )
            )

    return docs


def load_excel(path):
    workbook = load_workbook(
        path,
        read_only=True,
        data_only=True
    )

    docs = []

    try:
        for sheet in workbook.worksheets:

            rows = []

            for row in sheet.iter_rows(values_only=True):
                values = [
                    str(value) if value is not None else ""
                    for value in row
                ]

                if any(values):
                    rows.append(" | ".join(values))

            if rows:
                docs.append(
                    Document(
                        page_content="\n".join(rows),
                        metadata={
                            "source": str(path),
                            "file_type": "xlsx",
                            "sheet": sheet.title
                        }
                    )
                )
    finally:
        workbook.close()

    return docs


def load_pptx(path):
    presentation = Presentation(path)
    docs = []

    for slide_num, slide in enumerate(
        presentation.slides, 1
    ):

        texts = []

        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                texts.append(shape.text)

            if shape.has_table:
                for row in shape.table.rows:
                    texts.append(
                        " | ".join(
                            cell.text for cell in row.cells
                        )
                    )

        if texts:
            docs.append(
                Document(
                    page_content="\n".join(texts),
                    metadata={
                        "source": str(path),
                        "file_type": "pptx",
                        "slide": slide_num
                    }
                )
            )

    return docs


def load_html(path):
    html = Path(path).read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    text = soup.get_text(
        separator="\n",
        strip=True
    )

    return [
        Document(
            page_content=text,
            metadata={
                "source": str(path),
                "file_type": "html"
            }
        )
    ]


def load_document(path):

    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return load_pdf(path)

    elif ext == ".docx":
        return load_docx(path)

    elif ext in [".txt", ".md"]:
        return load_text(path)

    elif ext == ".csv":
        return load_csv(path)

    elif ext == ".xlsx":
        return load_excel(path)

    elif ext == ".pptx":
        return load_pptx(path)

    elif ext in [".html", ".htm"]:
        return load_html(path)

    return []