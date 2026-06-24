"""PDF text extraction service."""

import pypdf
from services.logger import get_logger

log = get_logger("pdfreader")


def extract_text(file_path):
    log.info("Extracting text from: %s", file_path)
    try:
        reader = pypdf.PdfReader(file_path)
        num_pages = len(reader.pages)
        log.debug("PDF has %d pages", num_pages)

        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            log.debug("Page %d extracted: %d chars", i + 1, len(page_text or ""))

        result = text.strip()
        log.info("Extraction complete: %d chars from %d pages", len(result), num_pages)
        return result
    except Exception as e:
        log.error("Failed to extract text from %s: %s", file_path, e, exc_info=True)
        raise

