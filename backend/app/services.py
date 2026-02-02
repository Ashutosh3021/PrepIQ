from sqlalchemy.orm import Session
from typing import Dict, Any, List
import uuid
from datetime import datetime, timedelta
import json
from dateutil.parser import parse

from . import models, schemas
from .prediction_engine import PredictionEngine
from .chatbot import Chatbot
from .pdf_parser import PDFParser
from .ml_models.question_analyzer import QuestionAnalyzer

class PrepIQService:
    """Main service class to coordinate all PrepIQ functionality"""
    
    def __init__(self):
        self.prediction_engine = PredictionEngine()
        self.chatbot = Chatbot()
        self.pdf_parser = PDFParser()
        self.question_analyzer = QuestionAnalyzer()
    
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
            paper.processed_at = datetime.utcnow()
            
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
        """Generate predictions for a subject using ML-enhanced analysis"""
        # Get all processed papers for the subject
        papers = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.subject_id == subject_id,
            models.QuestionPaper.processing_status == "completed"
        ).all()
        
        if not papers:
            raise ValueError("No processed papers found for this subject")
        
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
        
        # Use ML model to analyze patterns and generate predictions
        ml_predictions = self.question_analyzer.predict_exam_questions(
            historical_questions=all_questions,
            num_predictions=10  # Generate 10 predictions
        )
        
        # Also generate traditional AI predictions for comparison
        all_text = ""
        for paper in papers:
            if paper.raw_text:
                all_text += paper.raw_text + "\n"
        
        ai_predictions = self.prediction_engine.predict_exam_topics(
            study_material=all_text,
            db=db,
            subject_id=subject_id
        )
        
        # Combine ML and AI predictions
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
                "pattern_analysis": self.question_analyzer.analyze_patterns(all_questions),
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
            "generated_at": datetime.utcnow(),
            "analysis_method": "ML-enhanced prediction with pattern analysis",
            "accuracy_score": prediction_record.prediction_accuracy_score
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
        """Get trend analysis for a subject"""
        # Get all questions for the subject
        questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Perform analysis
        analysis = {
            "topic_frequency": {},
            "unit_frequency": {},
            "unit_weightage": {},
            "mark_distribution": {},
            "total_questions_analyzed": len(questions)
        }
        
        # Calculate topic frequency
        for q in questions:
            if q.unit_name:
                analysis["unit_frequency"][q.unit_name] = analysis["unit_frequency"].get(q.unit_name, 0) + 1
            if q.marks:
                analysis["mark_distribution"][str(q.marks)] = analysis["mark_distribution"].get(str(q.marks), 0) + 1
        
        # Calculate unit weightage based on marks
        unit_marks = {}
        for q in questions:
            if q.unit_name and q.marks:
                unit_marks[q.unit_name] = unit_marks.get(q.unit_name, 0) + q.marks
        
        total_marks = sum(unit_marks.values())
        for unit, marks in unit_marks.items():
            analysis["unit_weightage"][unit] = round((marks / total_marks) * 100, 2) if total_marks > 0 else 0
        
        return analysis
    
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
        """Generate a personalized study plan"""
        from datetime import datetime, timedelta
        from dateutil.parser import parse
        
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found or doesn't belong to user")
        
        # Parse dates
        start_dt = parse(start_date)
        exam_dt = parse(exam_date)
        
        # Calculate total days
        total_days = (exam_dt - start_dt).days + 1
        
        # Get subject syllabus info if available
        syllabus = subject.syllabus_json or {"units": [{"name": f"Unit {i}", "topics": [f"Topic {i}-{j}" for j in range(1, 3)]} for i in range(1, 5)]}
        
        # Generate daily schedule
        daily_schedule = []
        current_date = start_dt
        
        # Flatten all topics from all units
        all_topics = []
        for unit in syllabus.get("units", []):
            for topic in unit.get("topics", []):
                all_topics.append({"unit": unit["name"], "topic": topic})
        
        # Distribute topics across days
        topic_idx = 0
        for day in range(1, total_days + 1):
            day_topics = []
            
            # Assign 2-3 topics per day
            for _ in range(min(3, len(all_topics) - topic_idx)):
                if topic_idx < len(all_topics):
                    day_topics.append(f"{all_topics[topic_idx]['unit']}: {all_topics[topic_idx]['topic']}")
                    topic_idx += 1
            
            daily_schedule.append({
                "day": day,
                "date": current_date.strftime("%Y-%m-%d"),
                "topics": day_topics,
                "recommended_hours": 2.0,
                "priority_topics": day_topics[:1]  # First topic as priority
            })
            current_date += timedelta(days=1)
        
        # Create study plan record
        study_plan = models.StudyPlan(
            user_id=user_id,
            subject_id=subject_id,
            plan_name=f"Study Plan for {subject.name}",
            start_date=start_dt,
            exam_date=exam_dt,
            total_days=total_days,
            daily_schedule_json=daily_schedule
        )
        
        db.add(study_plan)
        db.commit()
        db.refresh(study_plan)
        
        return {
            "plan_id": study_plan.id,
            "subject_id": study_plan.subject_id,
            "total_days": study_plan.total_days,
            "daily_schedule": daily_schedule
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
        """Get repetition analysis for a subject"""
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not subject:
            raise ValueError("Subject not found")
        
        # This would be implemented with actual repetition analysis logic
        # For now, return mock data
        return {
            "exact_repetitions": [
                {
                    "question": "Sample repeated question",
                    "appeared_years": [2022, 2023, 2024],
                    "frequency": 3
                }
            ],
            "similar_questions": [
                {
                    "question": "Sample similar question",
                    "similarity_score": 0.85,
                    "variants": ["variant 1", "variant 2"]
                }
            ],
            "repetition_cycle_years": 2
        }
    
    def get_prediction(self, db: Session, prediction_id: str, user_id: str) -> Dict[str, Any]:
        """Get a specific prediction"""
        """Get a specific prediction"""
        prediction = db.query(models.Prediction).join(models.Subject).filter(
            models.Prediction.id == prediction_id,
            models.Subject.user_id == user_id
        ).first()
        
        if not prediction:
            raise ValueError("Prediction not found")
        
        # In a real implementation, we would parse the predicted questions JSON
        # For now, we'll return mock data
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": [
                {
                    "question_number": 1,
                    "text": "Sample predicted question based on pattern analysis",
                    "marks": 5,
                    "unit": "Unit 1",
                    "probability": "very_high",
                    "reasoning": "Appeared in 4 out of 5 previous papers"
                }
            ],
            "total_marks": 100,
            "coverage_percentage": 95,
            "unit_coverage": {
                "Unit 1": 45,
                "Unit 2": 30,
                "Unit 3": 25
            },
            "generated_at": prediction.created_at
        }
    
    def get_latest_prediction(self, db: Session, subject_id: str, user_id: str) -> Dict[str, Any]:
        """Get the latest prediction for a subject"""
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
        
        # Return mock data for now
        return {
            "id": prediction.id,
            "subject_id": prediction.subject_id,
            "predicted_questions": [
                {
                    "question_number": 1,
                    "text": "Sample predicted question based on pattern analysis",
                    "marks": 5,
                    "unit": "Unit 1",
                    "probability": "very_high",
                    "reasoning": "Appeared in 4 out of 5 previous papers"
                }
            ],
            "total_marks": 100,
            "coverage_percentage": 95,
            "unit_coverage": {
                "Unit 1": 45,
                "Unit 2": 30,
                "Unit 3": 25
            },
            "generated_at": prediction.created_at
        }