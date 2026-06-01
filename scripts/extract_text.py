from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader

from utils import (
    ANSWER_PDF_NAME,
    PAPER_PDF_NAME,
    append_error,
    ensure_dirs,
    ensure_sample_only,
    path_from_root,
    write_text,
)


WINDOWS_OCR_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.FileAccessMode, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.IsGenericMethod })[0]
function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(-1) | Out-Null
  $netTask.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
  throw 'Windows OCR engine is unavailable for the current user profile languages.'
}
foreach ($path in $args) {
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  [PSCustomObject]@{
    path = $path
    language = $engine.RecognizerLanguage.LanguageTag
    text = $result.Text
  } | ConvertTo-Json -Compress
}
"""


def page_image_paths(reader: PdfReader, temp_dir: Path) -> dict[int, Path]:
    paths: dict[int, Path] = {}
    for page_index, page in enumerate(reader.pages, start=1):
        images = list(page.images)
        if not images:
            continue
        image = images[0]
        suffix = Path(image.name).suffix or ".jpg"
        image_path = temp_dir / f"page_{page_index:02d}{suffix}"
        image_path.write_bytes(image.data)
        paths[page_index] = image_path
    return paths


def windows_ocr(image_paths: dict[int, Path]) -> tuple[dict[int, str], str | None]:
    if not image_paths or shutil.which("powershell") is None:
        return {}, None
    with tempfile.TemporaryDirectory(prefix="cet6_ocr_ps_") as temp:
        script_path = Path(temp) / "ocr.ps1"
        script_path.write_text(WINDOWS_OCR_SCRIPT, encoding="utf-8")
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), *[str(path) for path in image_paths.values()]],
            check=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    path_to_page = {str(path): page for page, path in image_paths.items()}
    texts: dict[int, str] = {}
    language: str | None = None
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        page = path_to_page.get(payload["path"])
        if page is not None:
            texts[page] = payload.get("text") or ""
            language = payload.get("language") or language
    return texts, language


def extract_pdf(pdf_path: Path, *, prefer_ocr: bool = False, ocr_fallback: bool = False) -> str:
    reader = PdfReader(str(pdf_path))
    text_pages: dict[int, str] = {}
    for index, page in enumerate(reader.pages, start=1):
        try:
            text_pages[index] = page.extract_text() or ""
        except Exception as exc:
            append_error("extract_text", pdf_path.name, type(exc).__name__, f"page {index}: {exc}")
            text_pages[index] = ""

    ocr_pages: dict[int, str] = {}
    ocr_language: str | None = None
    needs_ocr = prefer_ocr or (ocr_fallback and any(not text.strip() for text in text_pages.values()))
    if needs_ocr:
        with tempfile.TemporaryDirectory(prefix="cet6_answer_ocr_") as temp:
            try:
                ocr_pages, ocr_language = windows_ocr(page_image_paths(reader, Path(temp)))
            except Exception as exc:
                append_error("extract_text_ocr", pdf_path.name, type(exc).__name__, str(exc))
                ocr_pages = {}
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        source = "text-layer"
        text = ""
        if prefer_ocr and ocr_pages.get(index):
            text = ocr_pages[index]
            source = f"ocr:{ocr_language or 'Windows.Media.Ocr'}"
        elif not text_pages[index].strip() and ocr_pages.get(index):
            text = ocr_pages[index]
            source = f"ocr:{ocr_language or 'Windows.Media.Ocr'}"
        else:
            text = text_pages[index]
        pages.append(f"\n\n===== PAGE {index} [{source}] =====\n{text.strip()}\n")
    return "".join(pages).strip() + "\n"


def main() -> None:
    ensure_sample_only()
    ensure_dirs()
    pdf_path = path_from_root("data", "raw_pdfs", ANSWER_PDF_NAME)
    text_path = path_from_root("data", "extracted_text", "2025_06_set1_answer.txt")
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    write_text(text_path, extract_pdf(pdf_path, ocr_fallback=True))
    print(f"extracted={text_path}")


if __name__ == "__main__":
    main()
