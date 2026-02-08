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

class PrepIQService:
    """Main service class to coordinate all PrepIQ functionality"""
    
    def __init__(self):
        self.prediction_engine = PredictionEngine()
        self.chatbot = Chatbot()
        self.pdf_parser = PDFParser()
        self.question_analyzer = QuestionAnalyzer()
        self.enhanced_question_analyzer = EnhancedQuestionAnalyzer()
        self.syllabus_analyzer = SyllabusAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.study_planner = StudyPlanner()
    
    def process_uploaded_paper(self, db: Session, paper_id: str) -> Dict[str, Any]:
        """Process an uploaded paper to extract questions and analyze"""
        # Get the paper record
        paper = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.id == paper_id
        ).first()
        
        if not paper:
            raise ValueError("Paper not found")
        
        # Update status to processing
        paper.processing_status = "processing"
        db.commit()
        
        try:
            # Extract text from PDF using enhanced parser
            text_content = self.pdf_parser.extract_text_from_pdf(paper.file_path)
            
            # Extract metadata from PDF
            metadata = self.pdf_parser.extract_metadata_from_pdf(paper.file_path)
            
            # Extract images from PDF (for potential visual analysis)
            images = self.pdf_parser.extract_images_from_pdf(paper.file_path)
            
            # Process images with OCR if available
            ocr_results = []
            for img in images:
                # Placeholder for OCR processing - in real implementation, would use pytesseract
                # For now, just store image info
                ocr_results.append({
                    "image_id": img.get("index"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "processed": False
                })
            
            # Parse questions from text with enhanced features
            questions_data = self.pdf_parser.parse_questions_from_text(text_content)
            
            # Remove duplicate questions
            unique_questions = self._remove_duplicate_questions(questions_data)
            
            # Update paper with extracted information
            paper.raw_text = text_content
            paper.metadata_json = json.dumps(metadata)  # Store metadata
            paper.processing_status = "completed"
            paper.processed_at = datetime.now(timezone.utc)
            
            # Create question records with enhanced attributes
            for q_data in unique_questions:
                question = models.Question(
                    paper_id=paper.id,
                    question_text=q_data.get("text", ""),
                    question_number=q_data.get("number", 0),
                    marks=q_data.get("marks", 0),
                    unit_name=q_data.get("unit", "Unknown"),
                    question_type=q_data.get("question_type", "unknown"),
                    difficulty_level=q_data.get("difficulty", "medium"),
                    keywords_json=json.dumps(q_data.get("keywords", [])),
                    text_length=q_data.get("length", 0)
                )
                db.add(question)
            
            db.commit()
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(unique_questions)} unique questions from {len(questions_data)} total",
                "questions_count": len(unique_questions),
                "metadata": metadata,
                "images_extracted": len(images),
                "ocr_results": ocr_results,
                "duplicate_removed": len(questions_data) - len(unique_questions)
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
    
    def _is_similar_text(self, text1: str, text2: str, threshold: float = 0.9) -> bool:
        """Check if two texts are similar based on character overlap"""
        if not text1 or not text2:
            return False
        
        # Simple similarity check using character overlap
        set1 = set(text1)
        set2 = set(text2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return True  # Both empty
        
        similarity = intersection / union
        return similarity >= threshold
    
    def generate_predictions(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Generate predictions for a subject using enhanced ML and NLP analysis"""
        # Get all processed papers for the subject
        papers = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.subject_id == subject_id,
            models.QuestionPaper.processing_status == "completed"
        ).all()
        
        if not papers:
            raise ValueError("No processed papers found for this subject")
        
        # Get subject information for syllabus analysis
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        
        # Extract all questions from papers for ML analysis
        all_questions = []
        for paper in papers:
            questions = db.query(models.Question).filter(
                models.Question.paper_id == paper.id
            ).all()
            for q in questions:
                all_questions.append({
                    "text": q.question_text,
                    "number": q.question_number,
                    "marks": q.marks,
                    "unit": q.unit_name,
                    "type": q.question_type,
                    "difficulty": q.difficulty_level,
                    "keywords": json.loads(q.keywords_json) if q.keywords_json else [],
                    "length": q.text_length
                })
        
        if not all_questions:
            raise ValueError("No questions extracted from processed papers")
        
        # Use enhanced ML model to analyze patterns and generate predictions
        enhanced_analysis = self.enhanced_question_analyzer.analyze_patterns(all_questions)
        ml_predictions = self.enhanced_question_analyzer.predict_exam_questions(
            historical_questions=all_questions,
            num_predictions=10  # Generate 10 predictions
        )
        
        # Perform syllabus-to-question correlation analysis
        syllabus_content = ""
        if subject and subject.syllabus_json:
            syllabus_content = json.dumps(subject.syllabus_json) if isinstance(subject.syllabus_json, dict) else str(subject.syllabus_json)
        
        # Perform correlation analysis
        correlation_results = self.correlation_analyzer.comprehensive_correlation_analysis(
            questions=all_questions,
            syllabus_topics=self.syllabus_analyzer.calculate_topic_importance(
                self.syllabus_analyzer.extract_syllabus_structure(syllabus_content)
            ) if syllabus_content else {}
        )
        
        # Get high-impact topics from correlation analysis
        high_impact_topics = self.correlation_analyzer.predict_high_impact_topics(correlation_results)
        
        # Generate traditional AI predictions with enhanced context
        all_text = ""
        for paper in papers:
            if paper.raw_text:
                all_text += paper.raw_text + "\n"
        
        ai_predictions = self.prediction_engine.predict_exam_topics(
            study_material=all_text,
            db=db,
            subject_id=subject_id
        )
        
        # Combine enhanced ML and AI predictions
        combined_predictions = ml_predictions + ai_predictions.get("predictions", [])
        
        # Sort by confidence score (if available) and limit to top 10
        combined_predictions.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        final_predictions = combined_predictions[:10]
        
        # Calculate total predicted marks
        total_predicted_marks = sum([pred.get("marks", 5) for pred in final_predictions])
        
        # Calculate unit coverage
        unit_coverage = {}
        for pred in final_predictions:
            unit = pred.get("unit", "General")
            unit_coverage[unit] = unit_coverage.get(unit, 0) + 1
        
        # Create prediction record
        prediction_record = models.Prediction(
            subject_id=subject_id,
            user_id=user_id,
            predicted_questions_json=json.dumps(final_predictions),
            total_questions=len(final_predictions),
            total_predicted_marks=total_predicted_marks,
            unit_coverage_json=unit_coverage,
            ml_analysis_json=json.dumps({
                "enhanced_pattern_analysis": enhanced_analysis,
                "correlation_analysis": correlation_results,
                "high_impact_topics": high_impact_topics,
                "confidence_scores": [pred.get("confidence_score", 0) for pred in final_predictions]
            }),
            prediction_accuracy_score=self._calculate_prediction_accuracy(ml_predictions)
        )
        db.add(prediction_record)
        db.commit()
        
        return {
            "predictions": final_predictions,
            "total_marks": total_predicted_marks,
            "coverage_percentage": len(set(unit_coverage.keys())) / max(len(unit_coverage.keys()), 1) * 100,
            "unit_coverage": unit_coverage,
            "generated_at": datetime.now(timezone.utc),
            "analysis_method": "Enhanced ML-NLP prediction with syllabus correlation and impact analysis",
            "accuracy_score": prediction_record.prediction_accuracy_score,
            "enhanced_analysis": enhanced_analysis,
            "correlation_analysis": correlation_results,
            "high_impact_topics": high_impact_topics
        }
    
    def _calculate_prediction_accuracy(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate an estimated accuracy score for predictions"""
        if not predictions:
            return 0.0
        
        # Calculate average confidence score
        avg_confidence = sum([pred.get("confidence_score", 0) for pred in predictions]) / len(predictions)
        
        # Calculate consistency score based on similar predictions
        unique_predictions = len(set(pred.get("text", "")[:50] for pred in predictions))
        consistency = unique_predictions / len(predictions)
        
        # Weighted combination of confidence and consistency
        accuracy_score = (avg_confidence * 0.7) + (consistency * 0.3)
        
        # Ensure score is between 0 and 1
        return min(max(accuracy_score, 0.0), 1.0)

    
    def get_trend_analysis(self, db: Session, subject_id: str) -> Dict[str, Any]:
        """Get comprehensive trend analysis for a subject using enhanced ML analysis"""
        # Get all questions for the subject
        questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Format questions for analysis
        questions_formatted = []
        for q in questions:
            questions_formatted.append({
                "text": q.question_text,
                "marks": q.marks,
                "unit": q.unit_name,
                "difficulty": q.difficulty_level,
                "year": getattr(q, 'year', datetime.now().year)  # Assuming year attribute exists
            })
        
        # Perform enhanced analysis using ML components
        enhanced_analysis = self.enhanced_question_analyzer.analyze_patterns(questions_formatted)
        
        # Perform correlation analysis
        correlation_results = self.correlation_analyzer.comprehensive_correlation_analysis(questions_formatted)
        
        # Perform syllabus alignment analysis if available
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        syllabus_alignment = {}
        if subject and subject.syllabus_json:
            syllabus_content = json.dumps(subject.syllabus_json) if isinstance(subject.syllabus_json, dict) else str(subject.syllabus_json)
            syllabus_alignment = self.syllabus_analyzer.analyze_curriculum_alignment(syllabus_content, questions_formatted)
        
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
        # Get latest predictions for the subject
        latest_prediction = db.query(models.Prediction).filter(
            models.Prediction.subject_id == subject_id
        ).order_by(models.Prediction.created_at.desc()).first()
        
        # Get user's performance history
        user_tests = db.query(models.MockTest).filter(
            models.MockTest.user_id == user_id
        ).all()
        
        # Generate test based on predictions and user history
        # This is a simplified implementation
        questions = []
        for i in range(num_questions):
            marks = 2 if i < num_questions//2 else 5 if i < num_questions*4//5 else 10
            questions.append({
                "id": str(uuid.uuid4()),
                "number": i+1,
                "text": f"Sample question {i+1} for mock test",
                "marks": marks,
                "unit": f"Unit {((i % 3) + 1)}",
                "type": "mcq" if marks == 2 else "descriptive"
            })
        
        # Create mock test record
        mock_test = models.MockTest(
            user_id=user_id,
            subject_id=subject_id,
            total_questions=num_questions,
            total_marks=100,
            difficulty_level=difficulty
        )
        db.add(mock_test)
        db.commit()
        
        return {
            "test_id": mock_test.id,
            "total_questions": num_questions,
            "total_marks": 100,
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
    
    def get_user_study_plan(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get the current study plan for a user"""
        # Get the latest active plan for the user
        study_plan = db.query(models.StudyPlan).filter(
            models.StudyPlan.user_id == user_id
        ).order_by(models.StudyPlan.created_at.desc()).first()
        
        if not study_plan:
            raise ValueError("No study plan found for user")
        
        return {
            "plan_id": study_plan.id,
            "subject_id": study_plan.subject_id,
            "total_days": study_plan.total_days,
            "daily_schedule": study_plan.daily_schedule_json,
            "days_completed": study_plan.days_completed,
            "completion_percentage": study_plan.completion_percentage,
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
            study_plan.completion_percentage = str((days_completed / study_plan.total_days) * 100)
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
        
        return {
            "unit_weightage": analysis.get("unit_weightage", {}),
            "mark_distribution": analysis.get("mark_distribution", {})
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
            
            # Analyze patterns to find similar questions
            patterns = self.enhanced_question_analyzer.analyze_patterns(questions_data)
            
            # Extract similar questions from pattern analysis
            if "similar_questions" in patterns:
                similar_questions = patterns["similar_questions"][:10]  # Limit to top 10
        
        # Calculate repetition cycle
        all_years = set()
        for q in questions:
            paper = db.query(models.QuestionPaper).filter(
                models.QuestionPaper.id == q.paper_id
            ).first()
            if paper and paper.exam_year:
                all_years.add(paper.exam_year)
        
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
        
        # Get unit coverage if available
        try:
            unit_coverage = json.loads(prediction.unit_coverage_json) if prediction.unit_coverage_json else {}
        except:
            unit_coverage = {}
        
        # Get ML analysis if available
        try:
            ml_analysis = json.loads(prediction.ml_analysis_json) if prediction.ml_analysis_json else {}
        except:
            ml_analysis = {}
        
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": predicted_questions,
            "total_marks": prediction.total_predicted_marks,
            "coverage_percentage": prediction.coverage_percentage,
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
        
        # Get unit coverage if available
        try:
            unit_coverage = json.loads(prediction.unit_coverage_json) if prediction.unit_coverage_json else {}
        except:
            unit_coverage = {}
        
        # Get ML analysis if available
        try:
            ml_analysis = json.loads(prediction.ml_analysis_json) if prediction.ml_analysis_json else {}
        except:
            ml_analysis = {}
        
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": predicted_questions,
            "total_marks": prediction.total_predicted_marks,
            "coverage_percentage": prediction.coverage_percentage,
            "unit_coverage": unit_coverage,
            "generated_at": prediction.created_at,
            "accuracy_score": prediction.prediction_accuracy_score,
            "ml_analysis": ml_analysis
        }