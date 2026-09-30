"""
OCR fallback + LLM phraser tests — no network, no real DB (mostly).

Run from backend/:
  python -m pytest tests/test_ocr_phraser.py -v

The two Tesseract round-trip tests run only when a binary is resolvable;
they validate the Windows tesseract_cmd fix and the --psm 4 / grayscale
OCR settings live.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.pdf_parser import PDFParser, PIL_AVAILABLE, TESSERACT_AVAILABLE  # noqa: E402
from app.services import question_extraction as qe  # noqa: E402

MARKER = "[Page 1] (no text layer; pass ocr=True to extract)"
CLEAN_TEXT = (
    "[Page 1]\n"
    "1. Explain deadlock prevention techniques in operating systems with suitable examples. (5 marks)\n"
    "2. Compare paging and segmentation in memory management, giving suitable diagrams. (5 marks)\n"
    "3. Describe the producerconsumer problem and explain how semaphores solve it in practice. (5 marks)\n"
)


# ── Tesseract resolution + real OCR round-trips ──────────────────────────────

@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="pytesseract not installed")
def test_tesseract_binary_resolves():
    import pytesseract

    version = str(pytesseract.get_tesseract_version())
    assert version


@pytest.mark.skipif(
    not (TESSERACT_AVAILABLE and PIL_AVAILABLE),
    reason="pytesseract/Pillow not installed",
)
def test_real_ocr_reads_rendered_text(tmp_path):
    from PIL import Image, ImageDraw, ImageFont

    font_path = r"C:\Windows\Fonts\arial.ttf"
    font = (
        ImageFont.truetype(font_path, 40)
        if Path(font_path).exists()
        else ImageFont.load_default()
    )
    img = Image.new("L", (1000, 120), 255)
    draw = ImageDraw.Draw(img)
    draw.text((30, 35), "Explain Newtons laws of motion", fill=0, font=font)
    path = tmp_path / "q.png"
    img.save(path)

    text = PDFParser.extract_text_from_image(str(path))
    assert "Newton" in text
    assert "Explain" in text


# ── extract_text_with_ocr_fallback ───────────────────────────────────────────

def test_ocr_fallback_retries_when_no_text_layer(monkeypatch):
    calls = []

    def fake_extract(path, ocr=False):
        calls.append(ocr)
        return MARKER if not ocr else "[Page 1 — OCR]\n1. Define_OS. (5 marks)"

    monkeypatch.setattr(PDFParser, "extract_text", fake_extract)
    out = PDFParser.extract_text_with_ocr_fallback("paper.pdf")
    assert calls == [False, True]
    assert "OCR" in out and "Define_OS" in out


def test_ocr_fallback_skips_retry_for_clean_text(monkeypatch):
    calls = []

    def fake_extract(path, ocr=False):
        calls.append(ocr)
        return CLEAN_TEXT

    monkeypatch.setattr(PDFParser, "extract_text", fake_extract)
    out = PDFParser.extract_text_with_ocr_fallback("paper.pdf")
    assert calls == [False]
    assert out == CLEAN_TEXT


def test_ocr_fallback_retries_on_thin_text(monkeypatch):
    calls = []

    def fake_extract(path, ocr=False):
        calls.append(ocr)
        if ocr:
            return "[Page 1 — OCR]\n" + CLEAN_TEXT
        return "[Page 1]\nHi"

    monkeypatch.setattr(PDFParser, "extract_text", fake_extract)
    out = PDFParser.extract_text_with_ocr_fallback("paper.pdf")
    assert calls == [False, True]
    assert "OCR" in out


# ── question_extraction: regex fallback (no LLM key) ─────────────────────────

def test_regex_fallback_without_llm(monkeypatch):
    monkeypatch.setattr(
        qe, "get_llm_client", lambda cap: type("C", (), {"is_available": False})()
    )
    out = qe.extract_questions("1. Explain deadlock prevention techniques. (5 marks)")
    assert out, "regex parser must return questions without an LLM"
    assert "deadlock" in out[0]["text"].lower()


def test_empty_text_returns_empty(monkeypatch):
    assert qe.extract_questions("") == []
    assert qe.extract_questions("   ") == []


# ── question_extraction: LLM path (cached, normalized, deduped) ─────────────

class _FakeClient:
    is_available = True

    def __init__(self, payload=None, error=None):
        self.prompts = []
        self._payload = payload
        self._error = error

    def generate_text(self, prompt):
        self.prompts.append(prompt)
        if self._error is not None:
            raise self._error
        return self._payload


def _memo_cache(store, fn_calls):
    def fake_cached(capability, namespace, prompt, fn):
        key = (capability, namespace, prompt)
        if key not in store:
            fn_calls.append(key)
            store[key] = fn()
        return store[key]

    return fake_cached


def test_llm_path_normalizes_and_caches(monkeypatch):
    payload = json.dumps([
        {"text": "Explain Newtons laws of motion", "marks": "5",
         "question_type": "Conceptual/explanation", "difficulty": "Easy",
         "unit": "Mechanics"},
        {"text": "Explain Newtons laws of motion", "marks": 5},   # duplicate
        {"text": "", "marks": 0},                                 # dropped
        {"text": "Derive the workenergy theorem", "marks": "bad"},  # marks → 0
    ])
    client = _FakeClient(payload=payload)
    monkeypatch.setattr(qe, "get_llm_client", lambda cap: client)

    store, fn_calls = {}, []
    monkeypatch.setattr(qe.llm_cache, "cached_json", _memo_cache(store, fn_calls))

    text = "[Page 1]\n1. Explain Newtons laws of motion. (5 marks)\n2. Derive the workenergy theorem."
    first = qe.extract_questions(text)

    assert len(first) == 2, "duplicates and empty items must be dropped"
    assert first[0]["marks"] == 5
    assert first[0]["number"] in (1, 2)
    assert first[0]["keywords"] == []
    assert first[1]["marks"] == 0
    assert len(client.prompts) == 1
    assert len(fn_calls) == 1
    assert "OCR" in client.prompts[0] and "JSON array" in client.prompts[0]

    # second upload of the same paper → zero new LLM calls
    second = qe.extract_questions(text)
    assert len(second) == 2
    assert len(client.prompts) == 1, "identical chunk must be served from cache"


def test_llm_failure_falls_back_to_regex(monkeypatch):
    client = _FakeClient(error=RuntimeError("quota exhausted"))
    monkeypatch.setattr(qe, "get_llm_client", lambda cap: client)
    monkeypatch.setattr(
        qe.llm_cache, "cached_json",
        lambda cap, ns, prompt, fn: fn(),  # pass-through, nothing cached
    )

    out = qe.extract_questions("1. Explain deadlock prevention techniques. (5 marks)")
    assert out, "regex fallback must kick in when the LLM raises"
    assert "deadlock" in out[0]["text"].lower()


def test_llm_non_json_falls_back_to_regex(monkeypatch):
    client = _FakeClient(payload="sorry, I cannot do that")
    monkeypatch.setattr(qe, "get_llm_client", lambda cap: client)
    monkeypatch.setattr(
        qe.llm_cache, "cached_json",
        lambda cap, ns, prompt, fn: fn(),
    )

    out = qe.extract_questions("1. Define virtual memory. (4 marks)")
    assert out and "virtual memory" in out[0]["text"].lower()


def test_study_material_uses_concept_prompt(monkeypatch):
    client = _FakeClient(payload=json.dumps([{"text": "Newton second law", "marks": 0}]))
    monkeypatch.setattr(qe, "get_llm_client", lambda cap: client)
    monkeypatch.setattr(
        qe.llm_cache, "cached_json",
        lambda cap, ns, prompt, fn: fn(),
    )

    qe.extract_questions("Newton second law: F = ma.", "study_material")
    assert "study-material analyst" in client.prompts[0]


# ── chunking ────────────────────────────────────────────────────────────────

def test_chunks_split_on_page_markers_and_bound_limit():
    limit = 500
    page = "[Page {i}]\n" + ("x" * 240) + "\n"
    text = "".join(page.format(i=i) for i in range(1, 10))

    chunks = qe._chunks(text, limit=limit)
    assert len(chunks) > 1
    assert all(len(c) <= limit for c in chunks)
    assert "".join(chunks) == text


def test_chunks_keeps_short_text_whole():
    assert qe._chunks("short text", limit=500) == ["short text"]


def test_prompt_promises_repair_and_no_invention():
    assert "OCR" in qe.QUESTION_PROMPT
    assert "JSON array" in qe.QUESTION_PROMPT
    assert "Never invent" in qe.QUESTION_PROMPT
    assert "Q141" in qe.QUESTION_PROMPT  # chip-delimited exports


# ── chip-delimited ("2025 · Q141 · MCQ") exports ────────────────────────────

TAG_PAPER = """\
[Page 1]
All papers
The current passing through the battery in the given circuit, is:
Includes diagram
2025 · Q141 · MCQ
A wire of resistance
is cut into 8 equal pieces. From these pieces two equivalent resistances
are made. Then these two sets are added in series…
2025 · Q169 · MCQ
R
A
B
CD
The terminal voltage of the battery, whose emf is
and internal resistance , when connected through an external resistance is:
Includes diagram
2024 · Q154 · MCQ
Quick practice · Current Electricity
[Page 2]
The reciprocal of resistance is :
2022 · Q140 · MCQ
"""


def test_tag_delimited_export_finds_every_question():
    qs = PDFParser.parse_questions_from_text(TAG_PAPER)
    assert len(qs) == 4, [q["text"][:60] for q in qs]
    texts = [q["text"].lower() for q in qs]
    assert "current passing through the battery" in texts[0]
    assert "wire of resistance" in texts[1]
    assert "terminal voltage" in texts[2]
    assert "reciprocal of resistance" in texts[3]
    # chips, chrome and option fragments never leak into question text
    assert not any("MCQ" in t or "includes diagram" in t for t in texts)
    assert [q["number"] for q in qs] == [1, 2, 3, 4]


def test_tag_delimited_requires_three_chips():
    classic = "1. Explain deadlock prevention techniques. (5 marks)\n2. Define paging."
    assert len(PDFParser.parse_questions_from_text(classic)) == 2


def test_edge_junk_rules():
    from app.pdf_parser import _edge_junk

    assert _edge_junk("10 V")
    assert _edge_junk("AB")
    assert _edge_junk("(22000 ± 5%)Ω")
    assert not _edge_junk("Two heaters")          # real stem start
    assert not _edge_junk("Find current in the circuit?")
    assert not _edge_junk("A cell of emf 4 V and internal resistance")  # len >= 20
