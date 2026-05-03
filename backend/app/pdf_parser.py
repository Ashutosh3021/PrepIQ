import logging
import io
import re
import base64
import io as bio
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# PyMuPDF (fitz) — now in requirements.txt; guard import for graceful degradation
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    logger.warning("PyMuPDF (fitz) not installed — PDF extraction will fall back to PyPDF2")
    fitz = None
    FITZ_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    logger.warning("PyPDF2 not installed — PDF text extraction unavailable")
    PyPDF2 = None
    PYPDF2_AVAILABLE = False

try:
    from PIL import Image
except ImportError:
    logger.warning("Pillow not installed — image extraction from PDFs unavailable")
    Image = None

class PDFParser:
    """PDF parser to extract text and metadata from PDF files"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text content from a PDF file using multiple methods for better accuracy"""
        text = ""
        if FITZ_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                logger.warning(f"PyMuPDF failed, falling back to PyPDF2: {str(e)}")

        if PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                return text
            except Exception as e2:
                logger.error(f"PyPDF2 extraction also failed: {str(e2)}")
                raise e2

        raise RuntimeError("No PDF extraction library available (install PyMuPDF or PyPDF2)")
    
    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
        """Extract text content from PDF bytes using multiple methods for better accuracy"""
        text = ""
        try:
            # Try to save bytes to temp file and process with fitz
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_filename = tmp_file.name
            
            doc = fitz.open(tmp_filename)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
            
            # Clean up temp file
            os.unlink(tmp_filename)
        except Exception as e:
            logger.warning(f"PyMuPDF failed on bytes, falling back to PyPDF2: {str(e)}")
            try:
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            except Exception as e2:
                logger.error(f"Both PDF extraction methods failed on bytes: {str(e2)}")
                raise e2
        return text
    
    @staticmethod
    def parse_questions_from_text(text: str) -> List[Dict[str, Any]]:
        """Parse questions from extracted text with enhanced ML-ready features.

        M-05: The original approach used re.DOTALL with greedy (.*?) across the
        whole document, which causes catastrophic backtracking on large PDFs.
        Fixed by:
          1. Splitting the document into lines first (O(n), no backtracking).
          2. Applying simple per-line patterns that cannot backtrack.
          3. Capping the text length fed to each pattern.
        """
        MAX_TEXT = 200_000  # cap to avoid runaway on huge PDFs
        text = text[:MAX_TEXT]

        questions: List[Dict[str, Any]] = []
        seen_texts: set = set()

        def _add(q_text: str, q_number: int) -> None:
            q_text = q_text.strip()
            if len(q_text) < 10:
                return
            key = hash(q_text.lower())
            if key in seen_texts:
                return
            seen_texts.add(key)
            questions.append({
                "text": q_text,
                "number": q_number,
                "marks": PDFParser._estimate_marks(q_text),
                "unit": PDFParser._estimate_unit(q_text),
                "question_type": PDFParser._classify_question_type(q_text),
                "difficulty": PDFParser._estimate_difficulty(q_text),
                "keywords": PDFParser._extract_keywords(q_text),
                "length": len(q_text),
            })

        # Pattern 1: numbered questions  "Q1." / "1." / "Question 1"
        _numbered = re.compile(
            r'^(?:Q(?:uestion)?\s*\.?\s*)?(\d{1,3})[.)]\s+(.+)$',
            re.IGNORECASE,
        )
        # Pattern 2: lines that contain a marks indicator
        _marks_line = re.compile(
            r'^(.+?)(?:\(\d+\s*marks?\)|\[\d+\s*marks?\]|\d+\s*M\b)',
            re.IGNORECASE,
        )

        q_counter = 0
        for line in text.splitlines():
            line = line.strip()
            if not line or len(line) > 600:
                continue

            m = _numbered.match(line)
            if m:
                q_counter += 1
                _add(m.group(2), int(m.group(1)))
                continue

            m = _marks_line.match(line)
            if m:
                q_counter += 1
                _add(m.group(1), q_counter)

        return questions
    
    @staticmethod
    def _estimate_marks(question_text: str) -> int:
        """Estimate marks for a question based on keywords"""
        # Simple heuristic - in real implementation would be more sophisticated
        if any(keyword in question_text.lower() for keyword in ["10 marks", "ten marks", "10-marks"]):
            return 10
        elif any(keyword in question_text.lower() for keyword in ["5 marks", "five marks", "5-marks"]):
            return 5
        else:
            return 2  # Default to 2 marks
    
    @staticmethod
    def _estimate_unit(question_text: str) -> str:
        """Estimate unit for a question based on keywords"""
        # Simple heuristic - in real implementation would use NLP
        question_lower = question_text.lower()
        
        if any(keyword in question_lower for keyword in ["matrix", "determinant", "linear algebra"]):
            return "Unit 1"
        elif any(keyword in question_lower for keyword in ["algorithm", "sorting", "searching"]):
            return "Unit 2"
        elif any(keyword in question_lower for keyword in ["tree", "graph", "data structure"]):
            return "Unit 3"
        else:
            return "Unknown Unit"
    
    @staticmethod
    def _classify_question_type(question_text: str) -> str:
        """Classify question type based on text characteristics"""
        question_lower = question_text.lower()
        
        if any(keyword in question_lower for keyword in ["prove", "show that", "demonstrate", "derive"]):
            return "Proof/derivation"
        elif any(keyword in question_lower for keyword in ["calculate", "find", "evaluate", "solve"]):
            return "Calculation/problem"
        elif any(keyword in question_lower for keyword in ["explain", "describe", "discuss", "what is"]):
            return "Conceptual/explanation"
        elif any(keyword in question_lower for keyword in ["define", "state"]):
            return "Definition"
        elif any(keyword in question_lower for keyword in ["compare", "contrast", "difference"]):
            return "Comparison"
        else:
            return "Mixed/other"
    
    @staticmethod
    def _estimate_difficulty(question_text: str) -> str:
        """Estimate difficulty level of the question"""
        # Count complex terms or advanced concepts
        complex_indicators = ["advanced", "complex", "challenging", "difficult", "theorem", "proof"]
        easy_indicators = ["basic", "simple", "easy", "introductory"]
        
        question_lower = question_text.lower()
        complex_count = sum(1 for indicator in complex_indicators if indicator in question_lower)
        easy_count = sum(1 for indicator in easy_indicators if indicator in question_lower)
        
        if complex_count > easy_count:
            return "Hard"
        elif easy_count > complex_count:
            return "Easy"
        else:
            return "Medium"
    
    @staticmethod
    def _extract_keywords(question_text: str) -> List[str]:
        """Extract important keywords from the question"""
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            import string
            
            # Download required NLTK data if not present
            for resource, path in [
                ('punkt_tab', 'tokenizers/punkt_tab'),
                ('punkt', 'tokenizers/punkt'),
                ('stopwords', 'corpora/stopwords'),
            ]:
                try:
                    nltk.data.find(path)
                except LookupError:
                    nltk.download(resource, quiet=True)
            
            stop_words = set(stopwords.words('english'))
            word_tokens = word_tokenize(question_text)
            
            # Remove punctuation and stop words
            keywords = []
            for word in word_tokens:
                clean_word = word.translate(str.maketrans('', '', string.punctuation)).lower()
                if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                    keywords.append(clean_word)
            
            # Return top 5 keywords
            return list(set(keywords))[:5]
        except (ImportError, LookupError, Exception):
            # Fallback if NLTK is not available or data is missing
            words = question_text.split()
            keywords = [word.strip('.,!?()[]{}"\'') for word in words if len(word) > 3]
            return list(set(keywords))[:5]
    
    @staticmethod
    def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        if not FITZ_AVAILABLE:
            logger.warning("PyMuPDF not available — returning empty metadata")
            return {}
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            result = {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "pages": len(doc),
                "encrypted": doc.is_encrypted
            }
            doc.close()
            return result
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {str(e)}")
            return {}

    @staticmethod
    def extract_images_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
        """Extract images from PDF file"""
        if not FITZ_AVAILABLE:
            logger.warning("PyMuPDF not available — skipping image extraction")
            return []
        try:
            doc = fitz.open(pdf_path)
            images = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # Skip CMYK images for simplicity
                        img_data = pix.tobytes(output='png')
                        images.append({
                            "page": page_num,
                            "index": img_index,
                            "width": pix.width,
                            "height": pix.height,
                            "image_data": base64.b64encode(img_data).decode('utf-8'),
                            "colorspace": "RGB" if pix.n <= 3 else "RGBA"
                        })
                    pix = None  # Free memory
            doc.close()
            return images
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
            return []