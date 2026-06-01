from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from utils import (
    ANSWER_PAGE_URL,
    ANSWER_PDF_NAME,
    PAPER_PAGE_URL,
    PAPER_PDF_NAME,
    ensure_dirs,
    ensure_sample_only,
    path_from_root,
)


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=90) as response:
        return response.read()


def find_pdf_url(page_url: str, expected_name: str) -> str:
    html = fetch(page_url).decode("utf-8", errors="replace")
    expected_re = re.escape(expected_name)
    patterns = [
        rf'"src":"([^"]*{expected_re})"',
        rf'\\"src\\":\\"([^"]*{expected_re})\\"',
        rf'src="([^"]*{expected_re})"',
        rf'href="([^"]*{expected_re})"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return urljoin(page_url, unescape(match.group(1)))
    raise RuntimeError(f"Could not locate {expected_name} in {page_url}")


def download_one(page_url: str, expected_name: str) -> str:
    pdf_url = find_pdf_url(page_url, expected_name)
    content = fetch(pdf_url)
    if not content.startswith(b"%PDF"):
        raise RuntimeError(f"Downloaded content is not a PDF: {pdf_url}")
    output = path_from_root("data", "raw_pdfs", expected_name)
    output.write_bytes(content)
    return pdf_url


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    paper_url = download_one(PAPER_PAGE_URL, PAPER_PDF_NAME)
    answer_url = download_one(ANSWER_PAGE_URL, ANSWER_PDF_NAME)
    print(f"paper_pdf_url={paper_url}")
    print(f"answer_pdf_url={answer_url}")


if __name__ == "__main__":
    main()
