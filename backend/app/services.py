import logging
import os

from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
from datetime import datetime, timedelta, timezone
import json
from dateutil.parser import parse

from . import models, schemas
from .prediction_engine import PredictionEngine
from .chatbot import Chatbot
from .pdf_parser import PDFParser
from .ml_models.question_analyzer import QuestionAnalyzer
from .ml_models.enhanced_question_analyzer import EnhancedQuestionAnalyzer
from .ml.syllabus_analyzer import SyllabusAnalyzer
from .ml.correlation_analyzer import CorrelationAnalyzer
from .ml_engines.study_planner import StudyPlanner

logger = logging.getLogger(__name__)


class PrepIQService:
    """Main service class to coordinate all PrepIQ functionality"""

    def __init__(self):
        # Each component is wrapped individually so a single failure does not
        # prevent the rest of the service from starting.

        try:
            self.prediction_engine = PredictionEngine()
        except Exception as e:
            logger.warning(f"PredictionEngine failed to initialize: {e}")
            self.prediction_engine = None

        try:
            self.chatbot = Chatbot()
        except Exception as e:
            logger.warning(f"Chatbot failed to initialize: {e}")
            self.chatbot = None

        try:
            self.pdf_parser = PDFParser()
        except Exception as e:
            logger.warning(f"PDFParser failed to initialize: {e}")
            self.pdf_parser = None

        try:
            self.question_analyzer = QuestionAnalyzer()
        except Exception as e:
            logger.warning(f"QuestionAnalyzer failed to initialize: {e}")
            self.question_analyzer = None

        try:
            self.enhanced_question_analyzer = EnhancedQuestionAnalyzer()
        except Exception as e:
            logger.warning(f"EnhancedQuestionAnalyzer failed to initialize: {e}")
            self.enhanced_question_analyzer = None

        try:
            self.syllabus_analyzer = SyllabusAnalyzer()
        except Exception as e:
            logger.warning(f"SyllabusAnalyzer failed to initialize: {e}")
            self.syllabus_analyzer = None

        try:
            self.correlation_analyzer = CorrelationAnalyzer()
        except Exception as e:
            logger.warning(f"CorrelationAnalyzer failed to initialize: {e}")
            self.correlation_analyzer = None

        try:
            self.study_planner = StudyPlanner()
        except Exception as e:
            logger.warning(f"StudyPlanner failed to initialize: {e}")
            self.study_planner = None
    
    def process_uploaded_paper(self, db: Session, paper_id: str) -> Dict[str, Any]:
        """Process an uploaded paper to extract questions and analyze"""
        paper = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.id == paper_id
        ).first()

        if not paper:
            raise ValueError("Paper not found")

        if self.pdf_parser is None:
            raise ValueError("PDF parser service is not available")

        paper.processing_status = "processing"
        db.commit()

        try:
            # ── Download file bytes from Supabase Storage ─────────────────────
            # paper.file_path is a public HTTPS URL — parsers need a local path.
            # Download via the storage service and write to a temp file.
            import tempfile
            from .services.supabase_storage import SupabaseStorageService

            file_bytes = SupabaseStorageService.download_file(
                paper.s3_key, "question-papers"
            )

            # Determine extension from the stored clean filename
            _, raw_ext = os.path.splitext(paper.file_name or "")
            suffix = raw_ext.lower() or ".bin"

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                # ── Extract text ──────────────────────────────────────────────
                text_content = self.pdf_parser.extract_text(tmp_path)

                # ── Extract metadata / images (PDF only) ──────────────────────
                ext = suffix.lstrip(".")
                metadata = (
                    self.pdf_parser.extract_metadata_from_pdf(tmp_path)
                    if ext == "pdf" else {}
                )
                images = (
                    self.pdf_parser.extract_images_from_pdf(tmp_path)
                    if ext == "pdf" else []
                )
            finally:
                # Always remove the temp file
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            # ── OCR placeholder ───────────────────────────────────────────────
            ocr_results = [
                {
                    "image_id": img.get("index"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "processed": False,
                }
                for img in images
            ]

            # ── Parse questions ───────────────────────────────────────────────
            questions_data = self.pdf_parser.parse_questions_from_text(text_content)
            unique_questions = self._remove_duplicate_questions(questions_data)

            # ── Persist ───────────────────────────────────────────────────────
            paper.raw_text = text_content
            paper.metadata_json = json.dumps(metadata)
            paper.processing_status = "completed"
            paper.processed_at = datetime.now(timezone.utc)

            for q_data in unique_questions:
                question = models.Question(
                    paper_id=paper.id,
                    question_text=q_data.get("text", ""),
                    question_number=q_data.get("number", 0),
                    marks=q_data.get("marks", 0),
                    unit_name=q_data.get("unit", "Unknown"),
                    question_type=q_data.get("question_type", "unknown"),
                    difficulty=q_data.get("difficulty", "medium").lower(),
                    text_length=q_data.get("length", 0),
                )
                db.add(question)

            db.commit()

            return {
                "status": "success",
                "message": (
                    f"Successfully processed {len(unique_questions)} unique questions "
                    f"from {len(questions_data)} total"
                ),
                "questions_count": len(unique_questions),
                "metadata": metadata,
                "images_extracted": len(images),
                "ocr_results": ocr_results,
                "duplicate_removed": len(questions_data) - len(unique_questions),
            }

        except Exception as e:
            paper.processing_status = "failed"
            paper.error_message = str(e)
            db.commit()
            raise e
    
    def _remove_duplicate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate questions based on text similarity"""
        if not questions:
            return []
        
        # Normalize and clean question texts for comparison
        seen_questions = set()
        unique_questions = []
        
        for question in questions:
            # Create a normalized version of the question for deduplication
            text = question.get("text", "").strip().lower()
            # Remove extra whitespace and common variations
            normalized = " ".join(text.split())
            
            # Check for similarity using a simple approach
            is_duplicate = False
            for seen_text in seen_questions:
                if self._is_similar_text(normalized, seen_text):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_questions.add(normalized)
                unique_questions.append(question)
        
        return unique_questions
    
    def _is_similar_text(self, text1: str, text2: str, threshold: float = 0.6) -> bool:
        """Check if two texts are similar using token-level Jaccard similarity"""
        if not text1 or not text2:
            return False
        
        # Tokenize by splitting on whitespace and punctuation (word-level, not char-level)
        import re
        tokens1 = set(re.findall(r'\b\w+\b', text1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not tokens1 or not tokens2:
            return False
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        if union == 0:
            return True  # Both empty
        
        similarity = intersection / union
        return similarity >= threshold
    
    # ------------------------------------------------------------------
    # Tier-2 helper: cold-start prediction via Gemini (< 3 papers)
    # ------------------------------------------------------------------
    def _cold_start_prediction(
        self,
        db: Session,
        subject_id: str,
        user_id: str,
        subject: models.Subject,
        paper_count: int,
    ) -> Dict[str, Any]:
        """Generate predictions from Gemini subject-knowledge when < 3 papers exist."""
        subject_name = subject.name if subject else "Unknown Subject"
        syllabus_text = ""
        if subject and subject.syllabus_json:
            syllabus_text = (
                json.dumps(subject.syllabus_json)
                if isinstance(subject.syllabus_json, dict)
                else str(subject.syllabus_json)
            )

        warning_msg = "Generated from subject knowledge, not your past papers"

        # Build the cold-start prompt
        prompt = (
            f"You are an exam prediction engine. The student has not uploaded enough past papers "
            f"yet for this subject: {subject_name}. "
            f"Based on standard {subject_name} exam patterns for engineering students, predict the "
            f"10 most likely exam topics and questions."
            + (f"\n\nSyllabus context:\n{syllabus_text[:2000]}" if syllabus_text else "")
            + '\n\nReturn JSON only:\n'
            '{"predictions": [{"question_text": "...", "topic": "...", "confidence_score": 0.0, "reasoning": "..."}], '
            f'"warning": "{warning_msg}"}}'
        )

        final_predictions: List[Dict[str, Any]] = []
        gemini_ok = False

        if self.prediction_engine and self.prediction_engine.model:
            try:
                import google.generativeai as genai
                response = self.prediction_engine.model.generate_content(prompt)
                raw = response.text.strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                gemini_result = json.loads(raw)
                raw_preds = gemini_result.get("predictions", [])
                for i, p in enumerate(raw_preds):
                    final_predictions.append({
                        "question_number": i + 1,
                        "text": p.get("question_text", p.get("text", "")),
                        "topic": p.get("topic", "General"),
                        "unit": p.get("topic", "General"),
                        "marks": 5,
                        "probability": "moderate",
                        "confidence_score": float(p.get("confidence_score", 0.5)),
                        "reasoning": p.get("reasoning", ""),
                        "source": "syllabus_fallback",
                    })
                gemini_ok = True
                logger.info(
                    f"Cold-start Gemini prediction returned {len(final_predictions)} items "
                    f"for subject {subject_id}"
                )
            except Exception as e:
                logger.warning(f"Cold-start Gemini call failed: {e}")

        if not gemini_ok:
            # Bare-minimum fallback so the endpoint still returns 200
            final_predictions = [
                {
                    "question_number": i + 1,
                    "text": f"Upload more past papers to unlock AI-powered predictions for {subject_name}.",
                    "topic": "General",
                    "unit": "General",
                    "marks": 5,
                    "probability": "low",
                    "confidence_score": 0.1,
                    "reasoning": "Insufficient data; Gemini unavailable.",
                    "source": "syllabus_fallback",
                }
                for i in range(3)
            ]

        # Sort by confidence DESC
        final_predictions.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)

        total_predicted_marks = sum(p.get("marks", 5) for p in final_predictions)
        unit_coverage: Dict[str, int] = {}
        for p in final_predictions:
            u = p.get("unit", "General")
            unit_coverage[u] = unit_coverage.get(u, 0) + 1

        # Persist to DB so get_latest_prediction works normally
        meta = {
            "source": "syllabus_fallback",
            "fallback_used": True,
            "warning": warning_msg,
            "paper_count": paper_count,
        }
        prediction_record = models.Prediction(
            subject_id=subject_id,
            user_id=user_id,
            predicted_questions_json=json.dumps(final_predictions),
            total_questions=len(final_predictions),
            total_predicted_marks=total_predicted_marks,
            unit_coverage_json=unit_coverage,
            ml_analysis_json=json.dumps(meta),
            prediction_accuracy_score=0.0,
        )
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)

        return {
            "id": str(prediction_record.id),
            "subject_id": subject_id,
            "predictions": final_predictions,
            "predicted_questions": final_predictions,  # compat alias
            "total_marks": total_predicted_marks,
            "coverage_percentage": 0,
            "unit_coverage": unit_coverage,
            "generated_at": datetime.now(timezone.utc),
            "analysis_method": "syllabus_fallback",
            "fallback_used": True,
            "warning": warning_msg,
            "source": "syllabus_fallback",
        }

    # ------------------------------------------------------------------
    # Main prediction entry-point (two-tier)
    # ------------------------------------------------------------------
    def generate_predictions(
        self,
        db: Session,
        subject_id: str,
        user_id: str,
        existing_prediction_id: str = None,
    ) -> Dict[str, Any]:
        """Generate predictions for a subject — two-tier system.

        Tier 0 (count == 0): return empty structured response, no Gemini call.
        Tier 2 (1 <= count < 3): Gemini cold-start from subject/syllabus knowledge.
        Tier 1 (count >= 3): full ML → Gemini pipeline with ML fallback.
        """
        # ── Count completed papers ────────────────────────────────────────────
        paper_count = (
            db.query(models.QuestionPaper)
            .filter(
                models.QuestionPaper.subject_id == subject_id,
                models.QuestionPaper.processing_status == "completed",
            )
            .count()
        )

        # ── Tier 0: no papers at all ─────────────────────────────────────────
        if paper_count == 0:
            return {
                "id": None,
                "subject_id": subject_id,
                "predictions": [],
                "predicted_questions": [],
                "total_marks": 0,
                "coverage_percentage": 0,
                "unit_coverage": {},
                "generated_at": datetime.now(timezone.utc),
                "fallback_used": True,
                "fallback_reason": "no_papers",
                "message": (
                    "Upload at least one past paper to get predictions. "
                    "Add 3+ papers for AI-powered predictions."
                ),
                "source": "no_data",
            }

        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()

        # ── Tier 2: cold-start (1 or 2 papers) ───────────────────────────────
        if paper_count < 3:
            logger.info(
                f"Cold-start prediction for subject {subject_id} "
                f"(only {paper_count} paper(s) uploaded)"
            )
            return self._cold_start_prediction(
                db=db,
                subject_id=subject_id,
                user_id=user_id,
                subject=subject,
                paper_count=paper_count,
            )

        # ── Tier 1: full ML + Gemini pipeline (>= 3 papers) ─────────────────
        papers = (
            db.query(models.QuestionPaper)
            .filter(
                models.QuestionPaper.subject_id == subject_id,
                models.QuestionPaper.processing_status == "completed",
            )
            .all()
        )

        # Collect all questions from questions table, filtered by subject
        all_questions: List[Dict[str, Any]] = []
        for paper in papers:
            qs = db.query(models.Question).filter(models.Question.paper_id == paper.id).all()
            for q in qs:
                all_questions.append({
                    "text": q.question_text,
                    "number": q.question_number,
                    "marks": q.marks,
                    "unit": q.unit_name,
                    "type": q.question_type,
                    "difficulty": q.difficulty,
                    "keywords": [],
                    "length": q.text_length,
                })

        if not all_questions:
            raise ValueError("No questions extracted from processed papers")

        # ── ML analysis: topic clusters + importance scores ───────────────────
        enhanced_analysis: Dict[str, Any] = {}
        ml_predictions: List[Dict[str, Any]] = []
        if self.enhanced_question_analyzer:
            try:
                enhanced_analysis = self.enhanced_question_analyzer.analyze_patterns(all_questions)
                ml_predictions = self.enhanced_question_analyzer.predict_exam_questions(
                    historical_questions=all_questions,
                    num_predictions=10,
                )
            except Exception as e:
                logger.warning(f"EnhancedQuestionAnalyzer failed during prediction: {e}")

        # Tag ML predictions with their source
        for p in ml_predictions:
            p.setdefault("source", "ml")

        # ── Syllabus / correlation analysis ───────────────────────────────────
        syllabus_content = ""
        if subject and subject.syllabus_json:
            syllabus_content = (
                json.dumps(subject.syllabus_json)
                if isinstance(subject.syllabus_json, dict)
                else str(subject.syllabus_json)
            )

        correlation_results: Dict[str, Any] = {}
        high_impact_topics: List[Dict[str, Any]] = []
        if self.correlation_analyzer:
            try:
                syllabus_topics: Dict[str, Any] = {}
                if syllabus_content and self.syllabus_analyzer:
                    try:
                        syllabus_topics = self.syllabus_analyzer.calculate_topic_importance(
                            self.syllabus_analyzer.extract_syllabus_structure(syllabus_content)
                        )
                    except Exception as e:
                        logger.warning(f"SyllabusAnalyzer failed: {e}")
                correlation_results = self.correlation_analyzer.comprehensive_correlation_analysis(
                    questions=all_questions,
                    syllabus_topics=syllabus_topics,
                )
                high_impact_topics = self.correlation_analyzer.predict_high_impact_topics(
                    correlation_results
                )
            except Exception as e:
                logger.warning(f"CorrelationAnalyzer failed during prediction: {e}")

        # ── Gemini prediction (Tier 1) ────────────────────────────────────────
        all_text = "\n".join(p.raw_text for p in papers if p.raw_text)

        gemini_predictions: List[Dict[str, Any]] = []
        gemini_failed = False
        try:
            if self.prediction_engine is None:
                raise ValueError("PredictionEngine not initialised")
            ai_result = self.prediction_engine.predict_exam_topics(
                study_material=all_text,
                db=db,
                subject_id=subject_id,
            )
            gemini_predictions = ai_result.get("predictions", [])
            for p in gemini_predictions:
                p.setdefault("source", "gemini")
        except Exception as e:
            logger.warning(f"Gemini prediction failed, using ML fallback: {e}")
            gemini_failed = True

        # ── Combine and rank ──────────────────────────────────────────────────
        if gemini_failed or not gemini_predictions:
            # ML-only fallback
            combined = ml_predictions
            prediction_source = "ml_fallback"
            logger.info(
                f"Using ML fallback for subject {subject_id} "
                f"({len(combined)} ML predictions)"
            )
        else:
            combined = ml_predictions + gemini_predictions
            prediction_source = "gemini"

        combined.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        final_predictions = combined[:10]

        # Ensure every prediction carries its source tag
        for p in final_predictions:
            p.setdefault("source", prediction_source)

        # ── Aggregate metrics ─────────────────────────────────────────────────
        total_predicted_marks = sum(p.get("marks", 5) for p in final_predictions)
        unit_coverage: Dict[str, int] = {}
        for p in final_predictions:
            u = p.get("unit", "General")
            unit_coverage[u] = unit_coverage.get(u, 0) + 1

        ml_analysis_payload = {
            "source": prediction_source,
            "fallback_used": gemini_failed,
            "enhanced_pattern_analysis": enhanced_analysis,
            "correlation_analysis": correlation_results,
            "high_impact_topics": high_impact_topics,
            "confidence_scores": [p.get("confidence_score", 0) for p in final_predictions],
        }

        # ── Persist prediction record ─────────────────────────────────────────
        if existing_prediction_id:
            prediction_record = (
                db.query(models.Prediction)
                .filter(models.Prediction.id == existing_prediction_id)
                .first()
            )
            if prediction_record:
                prediction_record.predicted_questions_json = json.dumps(final_predictions)
                prediction_record.total_questions = len(final_predictions)
                prediction_record.total_predicted_marks = total_predicted_marks
                prediction_record.unit_coverage_json = unit_coverage
                prediction_record.ml_analysis_json = json.dumps(ml_analysis_payload)
                prediction_record.prediction_accuracy_score = self._calculate_prediction_accuracy(
                    ml_predictions
                )
                db.commit()
            else:
                existing_prediction_id = None  # fall through to create

        if not existing_prediction_id:
            prediction_record = models.Prediction(
                subject_id=subject_id,
                user_id=user_id,
                predicted_questions_json=json.dumps(final_predictions),
                total_questions=len(final_predictions),
                total_predicted_marks=total_predicted_marks,
                unit_coverage_json=unit_coverage,
                ml_analysis_json=json.dumps(ml_analysis_payload),
                prediction_accuracy_score=self._calculate_prediction_accuracy(ml_predictions),
            )
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)

        return {
            "id": str(prediction_record.id),
            "subject_id": subject_id,
            "predictions": final_predictions,
            "predicted_questions": final_predictions,  # compat alias for existing router helpers
            "total_marks": total_predicted_marks,
            "coverage_percentage": round(
                len(unit_coverage) / max(len(unit_coverage), 1) * 100
            ),
            "unit_coverage": unit_coverage,
            "generated_at": datetime.now(timezone.utc),
            "analysis_method": "Enhanced ML-NLP prediction with syllabus correlation",
            "accuracy_score": float(prediction_record.prediction_accuracy_score or 0),
            "enhanced_analysis": enhanced_analysis,
            "correlation_analysis": correlation_results,
            "high_impact_topics": high_impact_topics,
            "fallback_used": gemini_failed,
            "source": prediction_source,
        }
    
    def _calculate_prediction_accuracy(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate an estimated accuracy score for predictions (0.0–1.0 float for Numeric DB column)"""
        if not predictions:
            return 0.0

        avg_confidence = sum([pred.get("confidence_score", 0) for pred in predictions]) / len(predictions)
        unique_predictions = len(set(pred.get("text", "")[:50] for pred in predictions))
        consistency = unique_predictions / len(predictions)
        accuracy_score = (avg_confidence * 0.7) + (consistency * 0.3)
        # BUG-M06: return float, not string — column is now Numeric(5,2)
        return round(min(max(accuracy_score, 0.0), 1.0), 2)

    
    def get_trend_analysis(self, db: Session, subject_id: str) -> Dict[str, Any]:
        """Get comprehensive trend analysis for a subject using enhanced ML analysis"""
        from sqlalchemy.orm import joinedload

        # BUG-M11: eager-load paper to avoid N+1 lazy-load queries (one per question)
        questions = db.query(models.Question).options(
            joinedload(models.Question.paper)
        ).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Format questions for analysis — M-11: extract year from the paper, not from Question
        questions_formatted = []
        for q in questions:
            questions_formatted.append({
                "text": q.question_text,
                "marks": q.marks,
                "unit": q.unit_name,
                "difficulty": q.difficulty,
                "year": q.paper.exam_year if q.paper and q.paper.exam_year else datetime.now().year,
            })
        
        # Perform enhanced analysis using ML components
        enhanced_analysis = {}
        if self.enhanced_question_analyzer:
            try:
                enhanced_analysis = self.enhanced_question_analyzer.analyze_patterns(questions_formatted)
            except Exception as e:
                logger.warning(f"EnhancedQuestionAnalyzer failed in trend analysis: {e}")

        # Perform correlation analysis
        correlation_results = {}
        if self.correlation_analyzer:
            try:
                correlation_results = self.correlation_analyzer.comprehensive_correlation_analysis(questions_formatted)
            except Exception as e:
                logger.warning(f"CorrelationAnalyzer failed in trend analysis: {e}")

        # Perform syllabus alignment analysis if available
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        syllabus_alignment = {}
        if subject and subject.syllabus_json and self.syllabus_analyzer:
            try:
                syllabus_content = json.dumps(subject.syllabus_json) if isinstance(subject.syllabus_json, dict) else str(subject.syllabus_json)
                syllabus_alignment = self.syllabus_analyzer.analyze_curriculum_alignment(syllabus_content, questions_formatted)
            except Exception as e:
                logger.warning(f"SyllabusAnalyzer failed in trend analysis: {e}")
        
        # Perform basic analysis for compatibility
        basic_analysis = {
            "topic_frequency": {},
            "unit_frequency": {},
            "unit_weightage": {},
            "mark_distribution": {},
            "total_questions_analyzed": len(questions)
        }
        
        # Calculate topic frequency
        for q in questions:
            if q.unit_name:
                basic_analysis["unit_frequency"][q.unit_name] = basic_analysis["unit_frequency"].get(q.unit_name, 0) + 1
            if q.marks:
                basic_analysis["mark_distribution"][str(q.marks)] = basic_analysis["mark_distribution"].get(str(q.marks), 0) + 1
        
        # Calculate unit weightage based on marks
        unit_marks = {}
        for q in questions:
            if q.unit_name and q.marks:
                unit_marks[q.unit_name] = unit_marks.get(q.unit_name, 0) + q.marks
        
        total_marks = sum(unit_marks.values())
        for unit, marks in unit_marks.items():
            basic_analysis["unit_weightage"][unit] = round((marks / total_marks) * 100, 2) if total_marks > 0 else 0
        
        # Combine all analyses
        return {
            "basic_analysis": basic_analysis,
            "enhanced_analysis": enhanced_analysis,
            "correlation_analysis": correlation_results,
            "syllabus_alignment": syllabus_alignment,
            "total_questions_analyzed": len(questions)
        }
    
    def generate_mock_test(self, db: Session, subject_id: str, user_id: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """Generate a mock test based on predictions and user history"""
        import random
        import json
        
        # Get latest predictions for the subject
        latest_prediction = db.query(models.Prediction).filter(
            models.Prediction.subject_id == subject_id,
            models.Prediction.user_id == user_id
        ).order_by(models.Prediction.created_at.desc()).first()
        
        # Pull real questions from the database
        db_questions = db.query(models.Question).join(
            models.QuestionPaper, models.Question.paper_id == models.QuestionPaper.id
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        if not db_questions:
            # Fallback if no questions are available in DB to prevent breaking
            questions = []
            for i in range(num_questions):
                marks = 2 if i < num_questions//2 else 5 if i < num_questions*4//5 else 10
                questions.append({
                    "id": str(uuid.uuid4()),
                    "number": i+1,
                    "text": f"Please upload question papers to generate targeted mock tests.",
                    "marks": marks,
                    "unit": "General",
                    "type": "descriptive"
                })
        else:
            # Filter by difficulty if not mixed
            filtered = db_questions
            if difficulty and difficulty.lower() != "mixed":
                filtered = [q for q in db_questions if q.difficulty and q.difficulty.lower() == difficulty.lower()]
                if not filtered:
                    filtered = db_questions # fallback if no match
                    
            # Basic random selection weighting could be added here based on latest_prediction
            selected_db_qs = random.sample(filtered, min(num_questions, len(filtered)))
            
            questions = []
            for i, q in enumerate(selected_db_qs):
                questions.append({
                    "id": str(q.id),
                    "number": i+1,
                    "text": q.question_text,
                    "marks": q.marks or 5,
                    "unit": q.unit_name or "General",
                    "type": "mcq" if (q.marks and q.marks <= 2) else "descriptive"
                })
        
        total_marks = sum(q.get("marks", 5) for q in questions)
        
        # Create mock test record
        mock_test = models.MockTest(
            user_id=user_id,
            subject_id=subject_id,
            total_questions=len(questions),
            total_marks=total_marks,
            difficulty_level=difficulty
        )
        db.add(mock_test)
        db.commit()
        
        return {
            "test_id": str(mock_test.id),
            "total_questions": len(questions),
            "total_marks": total_marks,
            "time_limit_minutes": len(questions) * 3,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "questions": questions
        }
    
    def chat_with_bot(self, db: Session, user_id: str, subject_id: str, message: str) -> Dict[str, Any]:
        """Process a chat message with the AI assistant"""
        # Get subject info for context
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")

        # R-02: guard against Chatbot failing to initialise
        if self.chatbot is None:
            return {
                "message_id": "",
                "response": "AI tutor is currently unavailable. Please try again later.",
            }
        
        # Get response from chatbot
        response_text = self.chatbot.get_response(
            user_message=message,
            context=subject.name,
            db=db,
            subject_id=subject_id,
            user_id=user_id
        )
        
        # Create chat history record
        chat_record = models.ChatHistory(
            user_id=user_id,
            subject_id=subject_id,
            user_message=message,
            bot_response=response_text
        )
        db.add(chat_record)
        db.commit()
        
        return {
            "message_id": chat_record.id,
            "response": response_text
        }
    
    def generate_study_plan(self, db: Session, user_id: str, subject_id: str, start_date: str, exam_date: str) -> Dict[str, Any]:
        """Generate a personalized study plan using AI-powered optimization"""
        # R-03: guard against StudyPlanner failing to initialise
        if self.study_planner is None:
            raise ValueError("Study planner is not available")

        # Get user's performance history to personalize the plan
        user_tests = db.query(models.MockTest).filter(
            models.MockTest.user_id == user_id
        ).all()
        
        # Analyze weak areas
        user_performance = {}
        if user_tests:
            weak_topics = []
            strong_topics = []
            understanding_scores = {}
            
            for test in user_tests[-3:]:  # Look at last 3 tests
                if test.weak_topics_json:
                    weak_topics.extend(test.weak_topics_json)
                if test.strong_topics_json:
                    strong_topics.extend(test.strong_topics_json)
                
                # Calculate understanding scores if available
                if hasattr(test, 'performance_metrics'):
                    # Extract performance metrics if available
                    pass
            
            user_performance = {
                'weak_topics': list(set(weak_topics)),
                'strong_topics': list(set(strong_topics)),
                'understanding_scores': understanding_scores
            }
        
        # Use the enhanced study planner
        study_plan_result = self.study_planner.generate_optimized_study_plan(
            subject_id=subject_id,
            user_id=user_id,
            start_date=start_date,
            exam_date=exam_date,
            db=db,
            user_performance=user_performance
        )
        
        # Create study plan record
        from dateutil.parser import parse
        start_dt = parse(start_date)
        exam_dt = parse(exam_date)
        
        study_plan = models.StudyPlan(
            user_id=user_id,
            subject_id=subject_id,
            plan_name=study_plan_result["plan_id"],
            start_date=start_dt,
            exam_date=exam_dt,
            total_days=study_plan_result["total_days"],
            daily_schedule_json=study_plan_result["daily_schedule"]
        )
        
        db.add(study_plan)
        db.commit()
        db.refresh(study_plan)
        
        return {
            "plan_id": study_plan.id,
            "subject_id": study_plan.subject_id,
            "total_days": study_plan.total_days,
            "daily_schedule": study_plan_result["daily_schedule"],
            "optimization_strategy": study_plan_result["optimization_strategy"]
        }
    
    def get_user_study_plan(self, db: Session, user_id: str, subject_id: str = None) -> Dict[str, Any]:
        """Get the current study plan for a user, optionally filtered by subject"""
        # Get the latest active plan for the user
        query = db.query(models.StudyPlan).filter(
            models.StudyPlan.user_id == user_id
        )
        
        if subject_id:
            query = query.filter(models.StudyPlan.subject_id == subject_id)
        
        study_plan = query.order_by(models.StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise ValueError("No study plan found for user")
        
        return {
            "plan_id": str(study_plan.id),
            "subject_id": str(study_plan.subject_id),
            "total_days": study_plan.total_days,
            "daily_schedule": study_plan.daily_schedule_json or [],
            "days_completed": study_plan.days_completed,
            "completion_percentage": float(study_plan.completion_percentage or 0),
            "on_track": study_plan.on_track
        }
    
    def update_study_plan_progress(self, db: Session, plan_id: str, user_id: str, days_completed: int = None, on_track: bool = None) -> Dict[str, Any]:
        """Update the progress of a study plan"""
        # Get the study plan
        study_plan = db.query(models.StudyPlan).filter(
            models.StudyPlan.id == plan_id,
            models.StudyPlan.user_id == user_id
        ).first()
        
        if not study_plan:
            raise ValueError("Study plan not found")
        
        # Update fields if provided
        if days_completed is not None:
            study_plan.days_completed = days_completed
            # BUG-H17 + BUG-M05: guard zero division; store as float not string
            if study_plan.total_days and study_plan.total_days > 0:
                study_plan.completion_percentage = round(
                    (days_completed / study_plan.total_days) * 100, 2
                )
            else:
                study_plan.completion_percentage = 0.0
            study_plan.last_update_date = datetime.now()
        
        if on_track is not None:
            study_plan.on_track = on_track
        
        db.commit()
        db.refresh(study_plan)
        
        return {
            "message": "Study plan updated successfully",
            "plan_id": study_plan.id,
            "days_completed": study_plan.days_completed,
            "completion_percentage": study_plan.completion_percentage,
            "on_track": study_plan.on_track
        }
    
    def get_frequency_analysis(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Get frequency analysis for a subject"""
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")
        
        # Use the existing trend analysis method
        return self.get_trend_analysis(db, subject_id)
    
    def get_weightage_analysis(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Get weightage analysis for a subject"""
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")
        
        # Use the existing trend analysis method
        analysis = self.get_trend_analysis(db, subject_id)
        
        # Keys are nested under "basic_analysis" (BUG-B30 fix)
        basic = analysis.get("basic_analysis", {})
        
        return {
            "unit_weightage": basic.get("unit_weightage", {}),
            "mark_distribution": basic.get("mark_distribution", {})
        }
    
    def get_repetition_analysis(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Get repetition analysis for a subject using real database queries"""
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")
        
        # Get all questions for this subject
        questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id,
            models.QuestionPaper.processing_status == "completed"
        ).all()
        
        if not questions:
            return {
                "exact_repetitions": [],
                "similar_questions": [],
                "repetition_cycle_years": 0,
                "total_questions_analyzed": 0
            }
        
        # Analyze question repetitions
        question_texts = [q.question_text.strip().lower() for q in questions]
        exact_repetitions = []
        similar_questions = []
        
        # Find exact repetitions
        text_counts = {}
        for i, text in enumerate(question_texts):
            if text in text_counts:
                text_counts[text].append(i)
            else:
                text_counts[text] = [i]
        
        for text, indices in text_counts.items():
            if len(indices) > 1:
                # Get actual question numbers and years
                repeated_questions = [questions[i] for i in indices]
                years = []
                for q in repeated_questions:
                    paper = db.query(models.QuestionPaper).filter(
                        models.QuestionPaper.id == q.paper_id
                    ).first()
                    if paper and paper.exam_year:
                        years.append(paper.exam_year)
                
                exact_repetitions.append({
                    "question": repeated_questions[0].question_text,
                    "appeared_years": sorted(list(set(years))),
                    "frequency": len(indices),
                    "question_numbers": [q.question_number for q in repeated_questions]
                })
        
        # Find similar questions using semantic similarity
        if len(questions) > 1:
            # Use enhanced question analyzer for similarity analysis
            questions_data = []
            for q in questions:
                questions_data.append({
                    "text": q.question_text,
                    "number": q.question_number,
                    "marks": q.marks,
                    "unit": q.unit_name
                })

            # BUG-H03: guard against EnhancedQuestionAnalyzer being None
            if self.enhanced_question_analyzer:
                try:
                    patterns = self.enhanced_question_analyzer.analyze_patterns(questions_data)
                    if "similar_questions" in patterns:
                        similar_questions = patterns["similar_questions"][:10]
                except Exception as e:
                    logger.warning(f"EnhancedQuestionAnalyzer failed in repetition analysis: {e}")
        
        # Calculate repetition cycle - OPTIMIZED (PERF-02: Use join instead of O(n) queries)
        # Get exam years in a single query with join
        paper_years = db.query(models.QuestionPaper.exam_year).join(
            models.Question,
            models.Question.paper_id == models.QuestionPaper.id
        ).filter(
            models.QuestionPaper.subject_id == subject_id,
            models.QuestionPaper.processing_status == "completed",
            models.QuestionPaper.exam_year.isnot(None)
        ).distinct().all()
        
        all_years = {py[0] for py in paper_years if py[0]}
        
        repetition_cycle = max(all_years) - min(all_years) + 1 if len(all_years) > 1 else 0
        
        return {
            "exact_repetitions": exact_repetitions,
            "similar_questions": similar_questions,
            "repetition_cycle_years": repetition_cycle,
            "total_questions_analyzed": len(questions)
        }
    
    def get_prediction(self, db: Session, prediction_id: str, user_id: str) -> Dict[str, Any]:
        """Get a specific prediction using real database queries"""
        prediction = db.query(models.Prediction).join(models.Subject).filter(
            models.Prediction.id == prediction_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not prediction:
            raise ValueError("Prediction not found")
        
        # Parse the predicted questions JSON
        try:
            import json
            predicted_questions = json.loads(prediction.predicted_questions_json) if prediction.predicted_questions_json else []
        except:
            predicted_questions = []
        
        # Get unit coverage - JSON column is already deserialized by SQLAlchemy
        unit_coverage = prediction.unit_coverage_json if isinstance(prediction.unit_coverage_json, dict) else {}
        
        # Get ML analysis if available
        try:
            import json
            ml_analysis = json.loads(prediction.ml_analysis_json) if prediction.ml_analysis_json else {}
        except:
            ml_analysis = {}
        
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": predicted_questions,
            "total_marks": prediction.total_predicted_marks,
            "coverage_percentage": prediction.topic_coverage_percentage,
            "unit_coverage": unit_coverage,
            "generated_at": prediction.created_at,
            "accuracy_score": prediction.prediction_accuracy_score,
            "ml_analysis": ml_analysis
        }
    
    def get_latest_prediction(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Get the latest prediction for a subject using real database queries"""
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")
        
        # Get the latest prediction for this subject
        prediction = db.query(models.Prediction).filter(
            models.Prediction.subject_id == subject_id,
            models.Prediction.user_id == user_id
        ).order_by(models.Prediction.created_at.desc()).first()
        
        if not prediction:
            raise ValueError("No predictions found for this subject")
        
        # Parse the predicted questions JSON
        try:
            import json
            predicted_questions = json.loads(prediction.predicted_questions_json) if prediction.predicted_questions_json else []
        except:
            predicted_questions = []
        
        # Get unit coverage - JSON column is already deserialized by SQLAlchemy
        unit_coverage = prediction.unit_coverage_json if isinstance(prediction.unit_coverage_json, dict) else {}
        
        # Get ML analysis if available
        try:
            import json
            ml_analysis = json.loads(prediction.ml_analysis_json) if prediction.ml_analysis_json else {}
        except:
            ml_analysis = {}
        
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": predicted_questions,
            "total_marks": prediction.total_predicted_marks,
            "coverage_percentage": prediction.topic_coverage_percentage,
            "unit_coverage": unit_coverage,
            "generated_at": prediction.created_at,
            "accuracy_score": prediction.prediction_accuracy_score,
            "ml_analysis": ml_analysis
        }