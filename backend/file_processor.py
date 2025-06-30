import os
import io
import uuid
import fitz  # PyMuPDF
import docx  # python-docx
import pandas as pd
import zipfile
from fastapi import UploadFile

# (No changes needed in config.py, we just use its settings)
# from .config import settings 

# --- Private Helper Functions for Text Extraction ---

def _extract_text_from_pdf(content: bytes) -> str:
    """
    Extracts text from a PDF, with special handling for tables.
    It finds tables on each page, formats them as Markdown, 
    and extracts regular text, avoiding duplication.
    """
    text = ""
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page_num, page in enumerate(doc):
            text += f"\n--- Page {page_num + 1} ---\n"
            
            # Find and extract tables first
            tables = page.find_tables()
            for i, table in enumerate(tables):
                # Mark the area of the table to exclude it from normal text extraction
                page.add_redact_annot(table.bbox, text="") 
                
                # Extract table data and format as Markdown
                table_data = table.extract()
                if table_data:
                    text += f"\n**Table {i+1} on Page {page_num + 1}**\n"
                    # Create header
                    header = "| " + " | ".join(map(str, table_data[0])) + " |"
                    separator = "| " + " | ".join(["---"] * len(table_data[0])) + " |"
                    # Create rows
                    rows = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in table_data[1:]])
                    text += header + "\n" + separator + "\n" + rows + "\n\n"

            # Apply redactions to remove table text before extracting the rest
            page.apply_redactions()
            text += page.get_text()
            
    return text

def _extract_text_from_docx(content: bytes) -> str:
    """Extracts text from a DOCX file's content."""
    doc = docx.Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs)

def _extract_text_from_txt(content: bytes) -> str:
    """Extracts text from a TXT file's content."""
    return content.decode("utf-8", errors='ignore')

def _extract_text_from_csv(content: bytes) -> str:
    """Extracts text from a CSV file by converting it to a string."""
    try:
        df = pd.read_csv(io.BytesIO(content))
        return df.to_string()
    except Exception as e:
        return f"Error processing CSV: {e}"

def _extract_text_from_xlsx(content: bytes) -> str:
    """Extracts text from an XLSX file by converting all sheets to strings."""
    try:
        xls = pd.ExcelFile(io.BytesIO(content))
        full_text = ""
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            full_text += f"--- Sheet: {sheet_name} ---\n"
            full_text += df.to_string() + "\n\n"
        return full_text
    except Exception as e:
        return f"Error processing XLSX: {e}"

def get_text_from_file(file: UploadFile) -> str:
    """
    Main dispatcher function to extract text from an uploaded file.
    It now handles ZIP archives by recursively processing their contents.
    """
    filename = file.filename.lower()
    content = file.file.read()

    # If the file is a ZIP archive, process its contents
    if filename.endswith(".zip"):
        all_text = ""
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Read file content from the zip
                inner_file_content = zf.read(info.filename)
                # Recursively call the dispatcher for each file inside the zip
                all_text += f"\n--- From ZIP: {info.filename} ---\n"
                all_text += _dispatch_text_extraction(info.filename, inner_file_content) + "\n"
        return all_text
    else:
        # Otherwise, process the single file
        return _dispatch_text_extraction(filename, content)


def _dispatch_text_extraction(filename: str, content: bytes) -> str:
    """Internal dispatcher based on file extension."""
    filename = filename.lower()
    
    if filename.endswith(".pdf"):
        return _extract_text_from_pdf(content)
    elif filename.endswith(".docx"):
        return _extract_text_from_docx(content)
    elif filename.endswith(".txt"):
        return _extract_text_from_txt(content)
    elif filename.endswith(".csv"):
        return _extract_text_from_csv(content)
    elif filename.endswith(".xlsx"):
        return _extract_text_from_xlsx(content)
    else:
        # Silently ignore unsupported files within ZIPs or raise an error for direct uploads
        # This prevents one bad file in a ZIP from failing the whole batch.
        unsupported_ext = os.path.splitext(filename)[1]
        print(f"Skipping unsupported file type: {unsupported_ext}")
        return "" # Return empty string for unsupported types