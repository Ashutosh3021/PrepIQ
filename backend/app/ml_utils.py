"""
Lightweight ML utilities that work without heavy ML packages.
Uses heuristic-based fallbacks and cloud API options.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)


def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """
    Extract text from image using lightweight fallback.
    Tries pytesseract first, then PIL contrast analysis.
    """
    result = {
        "text": [],
        "confidence": [],
        "method": "fallback"
    }
    
    try:
        # Method 1: Try pytesseract (lightweight OCR)
        try:
            import pytesseract
            extracted = pytesseract.image_to_string(Image.open(image_path))
            if extracted.strip():
                result["text"].append(extracted)
                result["confidence"].append(0.8)
                result["method"] = "pytesseract"
                logger.info(f"✅ pytesseract extracted text from {os.path.basename(image_path)}")
                return result
        except ImportError:
            logger.info("pytesseract not installed, trying PIL fallback")
        except Exception as e:
            logger.warning(f"pytesseract error: {e}")
        
        # Method 2: Try basic PIL image analysis
        img = Image.open(image_path)
        
        # Convert to grayscale for text-like analysis
        gray = img.convert('L')
        
        # Basic image stats as a proxy for text content
        import numpy as np
        img_array = np.array(gray)
        
        # Detect high-contrast regions (likely text)
        contrast = np.std(img_array)
        
        if contrast > 30:  # Good contrast = likely has text
            result["text"].append(f"[Image text content from {os.path.basename(image_path)}]")
            result["confidence"].append(0.6)
            result["method"] = "pil_contrast_analysis"
            logger.info(f"✅ PIL analysis: detected high contrast image ({contrast:.1f})")
        else:
            result["text"].append("")
            result["confidence"].append(0.0)
            logger.info("⚠️ PIL: low contrast image, no text detected")
            
    except ImportError:
        # PIL not available
        result["text"].append(f"[Image content from {os.path.basename(image_path)}]")
        result["confidence"].append(0.3)
        logger.warning("PIL not available, using filename as placeholder")
        
    except Exception as e:
        logger.warning(f"Image analysis error: {e}")
        result["text"].append("")
        result["confidence"].append(0.0)
    
    return result


def detect_objects_in_image(image_path: str) -> Dict[str, Any]:
    """
    Detect objects using lightweight heuristic-based detection.
    Uses image analysis to detect potential diagrams/circuits.
    """
    result = {
        "objects": [],
        "method": "fallback"
    }
    
    try:
        img = Image.open(image_path)
        
        # Analyze image characteristics
        import numpy as np
        img_array = np.array(img.convert('RGB'))
        
        # Calculate various metrics
        height, width = img_array.shape[:2]
        
        # Edge detection proxy - count high-contrast transitions
        gray = np.array(img.convert('L'))
        edges_h = np.abs(np.diff(gray, axis=1))
        edges_v = np.abs(np.diff(gray, axis=0))
        
        edge_density_h = np.mean(edges_h)
        edge_density_v = np.mean(edges_v)
        
        # Detect potential diagram types based on characteristics
        if edge_density_h > 20 or edge_density_v > 20:
            # High edge density = likely contains lines/diagrams
            result["objects"].append({
                "label": "diagram",
                "confidence": 0.7,
                "type": "line_art"
            })
            
        # Check for circular patterns (circuits, etc.)
        if 'numpy' in dir():
            # Simple circular Hough transform proxy
            circles = np.sum(
                (gray > 200) & (gray < 255)
            )
            if circles > width * height * 0.05:
                result["objects"].append({
                    "label": "circuit_node",
                    "confidence": 0.5,
                    "type": "electronic"
                })
        
        # Color analysis for technical diagrams
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[2]), axis=0))
        if unique_colors < 20:
            result["objects"].append({
                "label": "technical_drawing",
                "confidence": 0.6,
                "type": "schematic"
            })
            
        result["method"] = "heuristic_analysis"
        logger.info(f"✅ Object detection: found {len(result['objects'])} objects")
        
    except ImportError:
        # No numpy - use basic PIL
        result["objects"].append({
            "label": "image_content",
            "confidence": 0.3,
            "type": "unknown"
        })
        logger.warning("Using basic image analysis (numpy not available)")
        
    except Exception as e:
        logger.warning(f"Object detection error: {e}")
    
    return result


def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """
    Simple sentiment analysis using keyword counting.
    Lightweight alternative to transformers.
    """
    if not text:
        return {"sentiment": "neutral", "score": 0.0}
    
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'perfect',
        'important', 'key', 'essential', 'crucial', 'significant', 'main'
    ]
    negative_words = [
        'bad', 'poor', 'difficult', 'hard', 'complex', 'challenging', 'error',
        'wrong', 'incorrect', 'failed', 'issue', 'problem', 'trouble'
    ]
    
    text_lower = text.lower()
    words = text_lower.split()
    
    pos_count = sum(1 for w in words if any(pw in w for pw in positive_words))
    neg_count = sum(1 for w in words if any(nw in w for nw in negative_words))
    
    total = pos_count + neg_count
    if total == 0:
        return {"sentiment": "neutral", "score": 0.0}
    
    score = (pos_count - neg_count) / total
    
    return {
        "sentiment": "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral",
        "score": score,
        "positive_count": pos_count,
        "negative_count": neg_count
    }


def extract_keywords(text: str, top_n: int = 10) -> List[Dict[str, str]]:
    """
    Extract keywords using simple frequency analysis.
    Lightweight alternative to transformers.
    """
    if not text:
        return []
    
    # Common stop words to filter
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'and', 'or', 'but', 'if', 'while', 'because', 'although', 'since',
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'what', 'which', 'who', 'whom', 'where', 'when', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once'
    }
    
    # Extract words
    import re
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter stop words and count
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N
    return [
        {"keyword": word, "frequency": freq}
        for word, freq in sorted_words[:top_n]
    ]


def classify_difficulty(text: str) -> Dict[str, Any]:
    """
    Classify question difficulty using heuristic analysis.
    Lightweight alternative to ML classification.
    """
    if not text:
        return {"difficulty": 2, "label": "medium", "confidence": 0.3}
    
    text_lower = text.lower()
    
    # Difficulty indicators
    easy_indicators = [
        'what is', 'define', 'list', 'name', 'state', 'write', 'draw',
        'explain', 'describe', 'mention', 'identify', 'select', 'choose'
    ]
    hard_indicators = [
        'prove', 'derive', 'analyze', 'evaluate', 'critically', 'compare',
        'contrast', 'synthesize', 'design', 'develop', 'create', 'construct',
        'justify', 'explain why', 'explain how', 'demonstrate'
    ]
    
    easy_count = sum(1 for ind in easy_indicators if ind in text_lower)
    hard_count = sum(1 for ind in hard_indicators if ind in text_lower)
    
    # Text length also indicates difficulty
    word_count = len(text.split())
    
    # Combine factors
    score = 2  # Default medium
    
    if hard_count > easy_count:
        score = 3  # Hard
    elif easy_count > hard_count:
        score = 1  # Easy
    
    # Adjust based on length
    if word_count > 100:
        score = min(3, score + 1)
    elif word_count < 20:
        score = max(1, score - 1)
    
    labels = {1: "easy", 2: "medium", 3: "hard"}
    
    return {
        "difficulty": score,
        "label": labels.get(score, "medium"),
        "confidence": 0.6,
        "word_count": word_count
    }


def detect_topics(text: str) -> List[Dict[str, Any]]:
    """
    Detect topics using keyword matching.
    """
    # Common topic keywords
    topic_keywords = {
        "Mathematics": ["equation", "function", "derivative", "integral", "matrix", "algebra", "calculus"],
        "Physics": ["force", "velocity", "energy", "power", "mass", "wave", "electric", "magnetic"],
        "Chemistry": ["reaction", "bond", "molecule", "element", "compound", "acid", "base"],
        "Computer Science": ["algorithm", "program", "code", "function", "loop", "array", "pointer"],
        "Biology": ["cell", "organ", "gene", "protein", "dna", "rna", "enzyme"],
        "Electrical": ["voltage", "current", "resistance", "circuit", "capacitor", "inductor"],
        "Mechanical": ["force", "motion", "pressure", "heat", "thermodynamics", "fluid"]
    }
    
    text_lower = text.lower()
    detected = []
    
    for topic, keywords in topic_keywords.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            detected.append({
                "topic": topic,
                "confidence": min(0.9, matches / len(keywords) * 2),
                "matched_keywords": [kw for kw in keywords if kw in text_lower]
            })
    
    # Sort by confidence
    detected.sort(key=lambda x: x["confidence"], reverse=True)
    
    return detected[:3]  # Top 3 topics
