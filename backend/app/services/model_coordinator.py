"""
Model Coordinator Service
Manages all 11 ML models and coordinates their interactions
"""
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for each model"""
    name: str
    provider: str
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    enabled: bool = True

class ModelCoordinator:
    """
    Coordinates all 11 models in the PrepIQ workflow:
    
    Image Processing Pipeline:
    1. EasyOCR - Text extraction
    2. YOLOv8 - Object detection
    3. GroundingDINO - Circuit diagram detection
    
    Bytez Models:
    4. roberta-base-squad2 - Q&A
    5. sentence-transformers/all-MiniLM-L6-v2 - Similarity
    6. distilbert-base-uncased - Classification
    
    Gemini Models:
    7. Gemini 2.5 Flash - Chat
    8. Gemini 2.5 Flash - AI Tutor
    9. Gemini 2.5 Flash - Summarization
    10. Gemini 2.5 Flash - Generation
    11. Gemini 2.5 Flash - Translation
    """
    
    def __init__(self):
        self.models = {}
        self.initialized = False
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all model configurations"""
        # Image Processing Models
        self.models['easyocr'] = ModelConfig(
            name='EasyOCR',
            provider='local',
            enabled=True
        )
        
        self.models['yolo'] = ModelConfig(
            name='YOLOv8',
            provider='local',
            model_id='yolov8n.pt',
            enabled=True
        )
        
        self.models['groundingdino'] = ModelConfig(
            name='GroundingDINO',
            provider='transformers',
            model_id='google/owlvit-base-patch32',
            enabled=True
        )
        
        # Bytez Models
        bytez_key = os.getenv('BYTEZ_API_KEY', 'd02578a68c2621c9fdac702219d0722e')
        
        self.models['qa'] = ModelConfig(
            name='RoBERTa QA',
            provider='bytez',
            api_key=bytez_key,
            model_id='deepset/roberta-base-squad2',
            enabled=True
        )
        
        self.models['similarity'] = ModelConfig(
            name='Sentence Similarity',
            provider='bytez',
            api_key=bytez_key,
            model_id='sentence-transformers/all-MiniLM-L6-v2',
            enabled=True
        )
        
        self.models['classification'] = ModelConfig(
            name='Text Classification',
            provider='bytez',
            api_key=bytez_key,
            model_id='distilbert/distilbert-base-uncased-finetuned-sst-2-english',
            enabled=True
        )
        
        # Gemini Models
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        self.models['gemini_chat'] = ModelConfig(
            name='Gemini Chat',
            provider='google',
            api_key=gemini_key,
            model_id='gemini-2.5-flash',
            enabled=gemini_key is not None
        )
        
        self.models['gemini_tutor'] = ModelConfig(
            name='Gemini AI Tutor',
            provider='google',
            api_key=gemini_key,
            model_id='gemini-2.5-flash',
            enabled=gemini_key is not None
        )
        
        self.models['gemini_summarize'] = ModelConfig(
            name='Gemini Summarization',
            provider='google',
            api_key=gemini_key,
            model_id='gemini-2.5-flash',
            enabled=gemini_key is not None
        )
        
        self.models['gemini_generate'] = ModelConfig(
            name='Gemini Text Generation',
            provider='google',
            api_key=gemini_key,
            model_id='gemini-2.5-flash',
            enabled=gemini_key is not None
        )
        
        self.models['gemini_translate'] = ModelConfig(
            name='Gemini Translation',
            provider='google',
            api_key=gemini_key,
            model_id='gemini-2.5-flash',
            enabled=gemini_key is not None
        )
        
        self.initialized = True
        logger.info("Model Coordinator initialized with 11 models")
        self._log_model_status()
    
    def _log_model_status(self):
        """Log the status of all models"""
        enabled = sum(1 for m in self.models.values() if m.enabled)
        logger.info(f"Models enabled: {enabled}/{len(self.models)}")
        for name, config in self.models.items():
            status = "✅" if config.enabled else "❌"
            logger.info(f"  {status} {name}: {config.provider}")
    
    # ==================== IMAGE PROCESSING PIPELINE ====================
    
    async def process_image_pipeline(self, image_path: str) -> Dict[str, Any]:
        """
        Execute image processing pipeline:
        EasyOCR → YOLOv8 → GroundingDINO
        """
        result = {
            "text": [],
            "objects": [],
            "circuits": [],
            "pipeline_status": []
        }
        
        # Step 1: EasyOCR
        if self.models['easyocr'].enabled:
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                ocr_results = reader.readtext(image_path)
                
                if ocr_results:
                    extracted_text = ' '.join([text for (_, text, _) in ocr_results])
                    result["text"].append(extracted_text)
                    result["pipeline_status"].append("✅ EasyOCR: Text extracted")
                    logger.info(f"EasyOCR extracted {len(ocr_results)} regions")
                else:
                    result["pipeline_status"].append("⚠️ EasyOCR: No text found")
            except Exception as e:
                result["pipeline_status"].append(f"❌ EasyOCR: {str(e)}")
                logger.error(f"EasyOCR error: {e}")
        
        # Step 2: YOLOv8 (always run for object detection)
        if self.models['yolo'].enabled:
            try:
                from ultralytics import YOLO
                model = YOLO(self.models['yolo'].model_id)
                yolo_results = model(image_path, verbose=False)
                
                for r in yolo_results:
                    for box in r.boxes:
                        result["objects"].append({
                            "label": model.names[int(box.cls[0])],
                            "confidence": float(box.conf[0])
                        })
                
                result["pipeline_status"].append(f"✅ YOLOv8: {len(result['objects'])} objects")
                logger.info(f"YOLOv8 detected {len(result['objects'])} objects")
            except Exception as e:
                result["pipeline_status"].append(f"❌ YOLOv8: {str(e)}")
                logger.error(f"YOLOv8 error: {e}")
        
        # Step 3: GroundingDINO (run if low text detected)
        text_length = len(result["text"][0]) if result["text"] else 0
        if text_length < 100 and self.models['groundingdino'].enabled:
            try:
                from transformers import pipeline
                from PIL import Image
                
                detector = pipeline(
                    "zero-shot-object-detection",
                    model=self.models['groundingdino'].model_id
                )
                
                image = Image.open(image_path)
                circuit_results = detector(
                    image,
                    candidate_labels=["circuit diagram", "electronic schematic", "wiring diagram"],
                    threshold=0.1
                )
                
                result["circuits"] = circuit_results
                result["pipeline_status"].append(f"✅ GroundingDINO: {len(circuit_results)} circuits")
                logger.info(f"GroundingDINO found {len(circuit_results)} circuits")
            except Exception as e:
                result["pipeline_status"].append(f"❌ GroundingDINO: {str(e)}")
                logger.error(f"GroundingDINO error: {e}")
        
        return result
    
    # ==================== BYTEZ MODELS ====================
    
    def _get_bytez_sdk(self):
        """Get Bytez SDK instance"""
        try:
            from bytez import Bytez
            return Bytez(self.models['qa'].api_key)
        except ImportError:
            logger.error("Bytez SDK not installed")
            return None
    
    async def answer_question(self, context: str, question: str) -> Dict[str, Any]:
        """
        Model 4: RoBERTa QA - Answer questions from context
        """
        if not self.models['qa'].enabled:
            return {"error": "QA model not enabled", "answer": None}
        
        try:
            sdk = self._get_bytez_sdk()
            if not sdk:
                return {"error": "Bytez SDK not available", "answer": None}
            
            model = sdk.model(self.models['qa'].model_id)
            results = model.run({
                "context": context,
                "question": question
            })
            
            if results.error:
                return {"error": results.error, "answer": None}
            
            return {
                "answer": results.output,
                "model": "roberta-base-squad2",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"QA model error: {e}")
            return {"error": str(e), "answer": None}
    
    async def calculate_similarity(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Model 5: Sentence Similarity - Calculate semantic similarity
        """
        if not self.models['similarity'].enabled:
            return {"error": "Similarity model not enabled", "score": 0}
        
        try:
            sdk = self._get_bytez_sdk()
            if not sdk:
                return {"error": "Bytez SDK not available", "score": 0}
            
            model = sdk.model(self.models['similarity'].model_id)
            
            # Get embeddings for both texts
            results1 = model.run(text1)
            results2 = model.run(text2)
            
            if results1.error or results2.error:
                return {"error": "Failed to get embeddings", "score": 0}
            
            # Calculate cosine similarity
            vec1 = np.array(results1.output)
            vec2 = np.array(results2.output)
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return {
                "score": float(similarity),
                "model": "all-MiniLM-L6-v2",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Similarity model error: {e}")
            return {"error": str(e), "score": 0}
    
    async def classify_text(self, text: str) -> Dict[str, Any]:
        """
        Model 6: Text Classification - Classify sentiment/topic
        """
        if not self.models['classification'].enabled:
            return {"error": "Classification model not enabled", "classification": None}
        
        try:
            sdk = self._get_bytez_sdk()
            if not sdk:
                return {"error": "Bytez SDK not available", "classification": None}
            
            model = sdk.model(self.models['classification'].model_id)
            results = model.run(text)
            
            if results.error:
                return {"error": results.error, "classification": None}
            
            return {
                "classification": results.output,
                "model": "distilbert-base-uncased",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Classification model error: {e}")
            return {"error": str(e), "classification": None}
    
    # ==================== GEMINI MODELS ====================
    
    def _get_gemini_model(self):
        """Get Gemini model instance"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.models['gemini_chat'].api_key)
            return genai.GenerativeModel(self.models['gemini_chat'].model_id)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    async def chat(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Model 7: Gemini Chat - General conversation
        """
        if not self.models['gemini_chat'].enabled:
            return {"error": "Chat model not enabled", "response": None}
        
        try:
            model = self._get_gemini_model()
            if not model:
                return {"error": "Gemini not initialized", "response": None}
            
            # Build context from history
            context = ""
            if history:
                for msg in history[-5:]:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    context += f"{role}: {msg.get('content', '')}\n"
            
            prompt = f"{context}\nUser: {message}\nAssistant:"
            response = model.generate_content(prompt)
            
            return {
                "response": response.text,
                "model": "gemini-2.5-flash",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Chat model error: {e}")
            return {"error": str(e), "response": None}
    
    async def tutor_chat(self, message: str, history: List[Dict] = None, context: str = None) -> Dict[str, Any]:
        """
        Model 8: Gemini AI Tutor - Socratic teaching
        """
        if not self.models['gemini_tutor'].enabled:
            return {"error": "Tutor model not enabled", "response": None}
        
        try:
            model = self._get_gemini_model()
            if not model:
                return {"error": "Gemini not initialized", "response": None}
            
            # AI Tutor System Prompt
            TUTOR_PROMPT = """Act as a highly intelligent, slightly sarcastic but supportive teacher. Your role is to guide the student through concepts using active questioning and structured reasoning.

Rules:
- Always ask at least one diagnostic question before giving any explanation
- Do not reveal the full answer immediately
- Teach through step-by-step reasoning
- Make the student think. Ask guiding questions after each step
- Only provide the complete answer if the student explicitly says: "Tell me the full answer"
- Use light, clever sarcasm (subtle, not rude) to keep the tone engaging
- Break complex ideas into connected stages
- If the student gives a wrong answer, do not immediately correct it. Instead, ask a question that exposes the flaw and leads them to self-correct
- Keep explanations clear, precise, and structured. No fluff.

You are not a solution machine. You are a thinking trainer."""
            
            # Build conversation history
            conv_context = ""
            if history:
                for msg in history[-5:]:
                    role = "Student" if msg.get("role") == "user" else "Tutor"
                    conv_context += f"{role}: {msg.get('content', '')}\n"
            
            full_prompt = f"""{TUTOR_PROMPT}

{context if context else ''}

Previous conversation:
{conv_context}

Student's current question: {message}

Respond as the AI Tutor:"""
            
            response = model.generate_content(full_prompt)
            
            return {
                "response": response.text,
                "model": "gemini-2.5-flash",
                "mode": "tutor",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Tutor model error: {e}")
            return {"error": str(e), "response": None}
    
    async def summarize(self, text: str, max_sentences: int = 3) -> Dict[str, Any]:
        """
        Model 9: Gemini Summarization - Summarize text
        """
        if not self.models['gemini_summarize'].enabled:
            return {"error": "Summarization model not enabled", "summary": None}
        
        try:
            model = self._get_gemini_model()
            if not model:
                return {"error": "Gemini not initialized", "summary": None}
            
            prompt = f"Summarize the following text in {max_sentences} sentences:\n\n{text}"
            response = model.generate_content(prompt)
            
            return {
                "summary": response.text,
                "model": "gemini-2.5-flash",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {"error": str(e), "summary": None}
    
    async def generate_text(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Model 10: Gemini Text Generation - Generate creative text
        """
        if not self.models['gemini_generate'].enabled:
            return {"error": "Generation model not enabled", "text": None}
        
        try:
            model = self._get_gemini_model()
            if not model:
                return {"error": "Gemini not initialized", "text": None}
            
            response = model.generate_content(prompt)
            
            return {
                "text": response.text,
                "model": "gemini-2.5-flash",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return {"error": str(e), "text": None}
    
    async def translate(self, text: str, target_language: str = "Spanish") -> Dict[str, Any]:
        """
        Model 11: Gemini Translation - Translate text
        """
        if not self.models['gemini_translate'].enabled:
            return {"error": "Translation model not enabled", "translation": None}
        
        try:
            model = self._get_gemini_model()
            if not model:
                return {"error": "Gemini not initialized", "translation": None}
            
            prompt = f"Translate the following text to {target_language}:\n\n{text}"
            response = model.generate_content(prompt)
            
            return {
                "translation": response.text,
                "target_language": target_language,
                "model": "gemini-2.5-flash",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {"error": str(e), "translation": None}
    
    # ==================== WORKFLOW COORDINATION ====================
    
    async def analyze_uploaded_material(self, image_path: str, text_content: str = None) -> Dict[str, Any]:
        """
        Complete workflow for analyzing uploaded material:
        1. Image Processing (EasyOCR + YOLOv8 + GroundingDINO)
        2. Question Extraction
        3. Classification
        4. Similarity Analysis
        5. Generate predictions
        """
        logger.info("Starting material analysis workflow...")
        
        result = {
            "image_analysis": None,
            "extracted_text": text_content or "",
            "questions": [],
            "classifications": [],
            "similarity_groups": [],
            "predictions": []
        }
        
        # Step 1: Image Processing
        if image_path:
            result["image_analysis"] = await self.process_image_pipeline(image_path)
            if result["image_analysis"]["text"]:
                result["extracted_text"] += " " + " ".join(result["image_analysis"]["text"])
        
        # Step 2: Extract and classify questions
        if result["extracted_text"]:
            # This would use the extract_questions function from upload router
            # For now, placeholder
            questions = self._extract_questions_from_text(result["extracted_text"])
            result["questions"] = questions
            
            # Step 3: Classify each question
            for question in questions:
                classification = await self.classify_text(question["text"])
                if classification.get("status") == "success":
                    result["classifications"].append({
                        "question": question["text"][:50] + "...",
                        "classification": classification["classification"]
                    })
        
        # Step 4: Calculate similarities between questions
        if len(result["questions"]) > 1:
            similarity_groups = await self._group_similar_questions(result["questions"])
            result["similarity_groups"] = similarity_groups
        
        # Step 5: Generate predictions based on patterns
        result["predictions"] = self._generate_predictions_from_analysis(result)
        
        logger.info("Material analysis workflow completed")
        return result
    
    def _extract_questions_from_text(self, text: str) -> List[Dict]:
        """Extract questions from text (simplified)"""
        import re
        
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.endswith('?') or any(m in line.lower() for m in ['explain', 'describe', 'calculate', 'q.', 'marks:']):
                if len(line) > 20:
                    # Detect type
                    q_type = "theory"
                    if any(w in line.lower() for w in ['calculate', 'compute', 'solve']):
                        q_type = "numerical"
                    elif any(w in line.lower() for w in ['diagram', 'draw']):
                        q_type = "diagram"
                    
                    # Extract marks
                    marks = 0
                    match = re.search(r'\((\d+)\)|\[(\d+)\]|(\d+)\s*marks', line.lower())
                    if match:
                        marks = int(match.group(1) or match.group(2) or match.group(3))
                    
                    questions.append({
                        "text": line,
                        "type": q_type,
                        "marks": marks
                    })
        
        return questions
    
    async def _group_similar_questions(self, questions: List[Dict]) -> List[Dict]:
        """Group similar questions using similarity model"""
        groups = []
        
        for i, q1 in enumerate(questions):
            for q2 in questions[i+1:]:
                similarity = await self.calculate_similarity(q1["text"], q2["text"])
                if similarity.get("score", 0) > 0.7:  # Threshold for similarity
                    groups.append({
                        "questions": [q1["text"][:50], q2["text"][:50]],
                        "similarity": similarity["score"]
                    })
        
        return groups
    
    def _generate_predictions_from_analysis(self, analysis: Dict) -> List[Dict]:
        """Generate predictions based on analysis"""
        predictions = []
        questions = analysis.get("questions", [])
        
        # Group by type and calculate frequency
        type_counts = {}
        for q in questions:
            q_type = q.get("type", "unknown")
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        # Simple prediction logic
        for q in questions:
            confidence = 50
            if type_counts.get(q["type"], 0) > 2:
                confidence = 75
            if q.get("marks", 0) >= 10:
                confidence += 10
            
            predictions.append({
                "question": q["text"][:100] + "..." if len(q["text"]) > 100 else q["text"],
                "confidence": min(confidence, 95),
                "type": q["type"],
                "marks": q.get("marks", 0)
            })
        
        return predictions
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            "total_models": len(self.models),
            "enabled": sum(1 for m in self.models.values() if m.enabled),
            "models": {
                name: {
                    "enabled": config.enabled,
                    "provider": config.provider,
                    "model_id": config.model_id
                }
                for name, config in self.models.items()
            }
        }

# Global instance
model_coordinator = ModelCoordinator()
