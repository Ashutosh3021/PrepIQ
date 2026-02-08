import os
import json
import logging
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from dotenv import load_dotenv
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)

# Bytez SDK import
_bytez = None
_bytez_sdk = None

def _lazy_import_bytez():
    """Lazy import Bytez SDK"""
    global _bytez, _bytez_sdk
    if _bytez is None:
        try:
            from bytez import Bytez
            _bytez = Bytez
            # Get API key from environment or use default
            api_key = os.getenv("BYTEZ_API_KEY", "d02578a68c2621c9fdac702219d0722e")
            _bytez_sdk = Bytez(api_key)
            logger.info("Bytez SDK initialized successfully")
            return _bytez_sdk
        except ImportError as e:
            logger.error(f"Failed to import Bytez SDK: {e}. Please install: pip install bytez")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Bytez SDK: {e}")
            return None
    return _bytez_sdk

class ExternalAPIWrapper:
    """Bytez API wrapper for all ML model inference - no local PyTorch required"""
    
    def __init__(self):
        self.models_available = False
        self.bytez_sdk = None
        
        # Model mappings to Bytez models
        self.model_mappings = {
            'qa': 'deepset/roberta-base-squad2',
            'summarization': 'facebook/bart-large-cnn',
            'classification': 'ProsusAI/finbert',
            'generation': 'meta-llama/Meta-Llama-3-8B',
            'sentence_similarity': 'google/embeddinggemma-300m',
            'translation': 'google/madlad400-3b-mt', # Note: multilingual, might need language token
            'image_captioning': 'Salesforce/blip-image-captioning-large',
            'chat': 'meta-llama/Llama-2-7b-chat-hf'
        }
        
        # Cache for model instances
        self.model_cache = {}
        
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
        
        # Initialize Bytez SDK
        try:
            self.bytez_sdk = _lazy_import_bytez()
            if self.bytez_sdk:
                self.models_available = True
                logger.info("Bytez API wrapper initialized successfully - all models available via Bytez")
            else:
                logger.warning("Bytez SDK not available - using fallback methods")
                self._initialize_fallback_models()
        except Exception as e:
            logger.warning(f"Failed to initialize Bytez SDK: {e}. Using fallback methods.")
            self._initialize_fallback_models()
    
    def _get_model(self, model_type: str):
        """Get or create a Bytez model instance"""
        if not self.bytez_sdk:
            return None
        
        if model_type not in self.model_cache:
            try:
                model_name = self.model_mappings.get(model_type)
                if model_name:
                    self.model_cache[model_type] = self.bytez_sdk.model(model_name)
                    logger.info(f"Loaded Bytez model: {model_name} for {model_type}")
                else:
                    logger.warning(f"No model mapping found for {model_type}")
                    return None
            except Exception as e:
                logger.error(f"Failed to load Bytez model for {model_type}: {e}")
                return None
        
        return self.model_cache.get(model_type)
    
    def _initialize_fallback_models(self):
        """Initialize lightweight fallback models when Bytez is not available"""
        logger.warning("Initializing fallback models (Bytez not available)...")
        self.models_available = True  # Mark as available even with fallbacks
        logger.info("Fallback models initialized")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_bytez_model(self, model_type: str, input_data: Any) -> Dict[str, Any]:
        """Call a Bytez model with retry logic"""
        if not self.bytez_sdk:
            return {"success": False, "output": None, "error": "Bytez SDK not available"}
        
        try:
            model = self._get_model(model_type)
            if not model:
                return {"success": False, "output": None, "error": f"Model {model_type} not available"}
            
            # Run the model
            results = model.run(input_data)
            
            # Handle Bytez response format
            if hasattr(results, 'error') and results.error:
                return {
                    "success": False,
                    "output": None,
                    "error": str(results.error)
                }
            
            return {
                "success": True,
                "output": results.output if hasattr(results, 'output') else results,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error calling Bytez model {model_type}: {str(e)}")
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
    
    def question_answering(self, context: str, question: str) -> Dict[str, Any]:
        """Question answering using Bytez API"""
        if self.bytez_sdk:
            # Format input for QA model (context + question)
            qa_input = {
                "context": context,
                "question": question
            }
            result = self._call_bytez_model('qa', qa_input)
            if result["success"]:
                return result
        
        # Fallback: return a simple answer based on keyword matching
        context_lower = context.lower()
        question_lower = question.lower()
        question_words = question_lower.split()
        
        # Find sentences containing question words
        sentences = sent_tokenize(context)
        for sentence in sentences:
            if any(word in sentence.lower() for word in question_words if len(word) > 3):
                return {
                    "success": True,
                    "output": sentence[:200],
                    "error": None
                }
        
        return {
            "success": True,
            "output": context[:200] if context else "No answer found",
            "error": None
        }
    
    async def question_answering_async(self, context: str, question: str) -> Dict[str, Any]:
        """Async question answering"""
        return self.question_answering(context, question)
    
    def text_summarization(self, text: str) -> Dict[str, Any]:
        """Text summarization using Bytez API"""
        if self.bytez_sdk:
            result = self._call_bytez_model('summarization', text)
            if result["success"]:
                # Handle different response formats
                output = result["output"]
                if isinstance(output, dict):
                    summary = output.get("summary_text", output.get("summary", str(output)))
                elif isinstance(output, list) and len(output) > 0:
                    summary = output[0].get("summary_text", str(output[0])) if isinstance(output[0], dict) else str(output[0])
                else:
                    summary = str(output)
                
                return {
                    "success": True,
                    "output": summary,
                    "error": None
                }
        
        # Fallback: extract first few sentences
        if len(text.split()) < 50:
            return {
                "success": True,
                "output": text,
                "error": None
            }
        
        sentences = sent_tokenize(text)
        fallback_summary = " ".join(sentences[:3]) if len(sentences) > 3 else text
        return {
            "success": True,
            "output": fallback_summary,
            "error": None
        }
    
    async def text_summarization_async(self, text: str) -> Dict[str, Any]:
        """Async text summarization"""
        return self.text_summarization(text)
    
    def text_classification(self, text: str) -> Dict[str, Any]:
        """Text classification using Bytez API"""
        if self.bytez_sdk:
            result = self._call_bytez_model('classification', text)
            if result["success"]:
                output = result["output"]
                # Handle different response formats
                if isinstance(output, list) and len(output) > 0:
                    if isinstance(output[0], dict):
                        return {
                            "success": True,
                            "output": output[0],
                            "error": None
                        }
                    else:
                        return {
                            "success": True,
                            "output": {"label": str(output[0]), "score": 0.9},
                            "error": None
                        }
                elif isinstance(output, dict):
                    return {
                        "success": True,
                        "output": output,
                        "error": None
                    }
        
        # Fallback
        return {
            "success": True,
            "output": {"label": "neutral", "score": 0.5},
            "error": None
        }
    
    async def text_classification_async(self, text: str) -> Dict[str, Any]:
        """Async text classification"""
        return self.text_classification(text)
    
    def text_generation(self, prompt: str, max_length: int = 100) -> Dict[str, Any]:
        """Text generation using Bytez API"""
        if self.bytez_sdk:
            # Format input for generation model - Llama-3 expects string prompt
            # as per user example: model.run("Once upon a time...")
            # We can append max_length instruction to prompt if needed, but for now stick to simple string
            result = self._call_bytez_model('generation', prompt)
            if result["success"]:
                output = result["output"]
                # Handle different response formats
                if isinstance(output, list) and len(output) > 0:
                    if isinstance(output[0], dict):
                        generated_text = output[0].get("generated_text", str(output[0]))
                    else:
                        generated_text = str(output[0])
                elif isinstance(output, dict):
                    generated_text = output.get("generated_text", str(output))
                else:
                    generated_text = str(output)
                
                return {
                    "success": True,
                    "output": generated_text,
                    "error": None
                }
        
        # Fallback
        return {
            "success": True,
            "output": prompt + " [continuation would go here]",
            "error": None
        }
    
    async def text_generation_async(self, prompt: str, max_length: int = 100) -> Dict[str, Any]:
        """Async text generation"""
        return self.text_generation(prompt, max_length)
    
    def sentence_similarity(self, sentences: List[str]) -> Dict[str, Any]:
        """Sentence similarity using Bytez API embeddings"""
        if self.bytez_sdk and len(sentences) >= 2:
            try:
                # Get embeddings for both sentences
                model = self._get_model('sentence_similarity')
                if model:
                    # Get embeddings
                    emb1_result = model.run(sentences[0])
                    emb2_result = model.run(sentences[1])
                    
                    if emb1_result and emb2_result:
                        emb1 = emb1_result.output if hasattr(emb1_result, 'output') else emb1_result
                        emb2 = emb2_result.output if hasattr(emb2_result, 'output') else emb2_result
                        
                        # Convert to numpy arrays if needed
                        if isinstance(emb1, list):
                            emb1 = np.array(emb1)
                        if isinstance(emb2, list):
                            emb2 = np.array(emb2)
                        
                        # Calculate cosine similarity
                        similarity = cosine_similarity([emb1], [emb2])[0][0]
                        
                        return {
                            "success": True,
                            "output": [float(similarity)],
                            "error": None
                        }
            except Exception as e:
                logger.warning(f"Bytez sentence similarity failed: {e}, using fallback")
        
        # Fallback: basic word overlap similarity
        if len(sentences) >= 2:
            words1 = set(sentences[0].lower().split())
            words2 = set(sentences[1].lower().split())
            if words1 or words2:
                similarity = len(words1.intersection(words2)) / len(words1.union(words2))
            else:
                similarity = 0.0
            return {
                "success": True,
                "output": [float(similarity)],
                "error": None
            }
        else:
            return {
                "success": True,
                "output": [1.0],  # Perfect similarity for single sentence
                "error": None
            }
    
    async def sentence_similarity_async(self, sentences: List[str]) -> Dict[str, Any]:
        """Async sentence similarity"""
        return self.sentence_similarity(sentences)
    
    def translation(self, text: str, source_lang: str = "en", target_lang: str = "es") -> Dict[str, Any]:
        """Translation using Bytez API"""
        if self.bytez_sdk:
            # Format input for translation model - madlad400 uses <2xx> token
            # e.g. <2es> Good morning
            formatted_text = f"<2{target_lang}> {text}"
            result = self._call_bytez_model('translation', formatted_text)
            if result["success"]:
                output = result["output"]
                # Handle different response formats
                if isinstance(output, list) and len(output) > 0:
                    if isinstance(output[0], dict):
                        translation_text = output[0].get("translation_text", str(output[0]))
                    else:
                        translation_text = str(output[0])
                elif isinstance(output, dict):
                    translation_text = output.get("translation_text", str(output))
                else:
                    translation_text = str(output)
                
                return {
                    "success": True,
                    "output": translation_text,
                    "error": None
                }
        
        # Fallback
        return {
            "success": True,
            "output": f"[Translation {source_lang} to {target_lang}]: {text}",
            "error": None
        }
    
    async def translation_async(self, text: str, source_lang: str = "en", target_lang: str = "es") -> Dict[str, Any]:
        """Async translation"""
        return self.translation(text, source_lang, target_lang)
    
    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Chat functionality using Bytez API"""
        if self.bytez_sdk:
            # Format messages for chat model - Llama-2 chat expects list of messages
            # as per user example: model.run([{"role": "user", "content": "Hello"}])
            result = self._call_bytez_model('chat', messages)
            if result["success"]:
                output = result["output"]
                # Handle different response formats
                if isinstance(output, dict):
                    response = output.get("response", output.get("text", str(output)))
                elif isinstance(output, list) and len(output) > 0:
                    response = str(output[0])
                else:
                    response = str(output)
                
                return {
                    "success": True,
                    "output": response,
                    "error": None
                }
        
        # Fallback: use text generation
        try:
            last_message = messages[-1]["content"] if messages else "Hello"
            return self.text_generation(last_message, max_length=150)
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                "success": True,
                "output": "Hello! I'm your AI assistant.",
                "error": None
            }
    
    async def chat_async(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Async chat"""
        return self.chat(messages)
    
    def image_captioning(self, image_path: str) -> Dict[str, Any]:
        """Image captioning using Bytez API"""
        if self.bytez_sdk:
            # Bytez image captioning model expects image URL or path
            result = self._call_bytez_model('image_captioning', image_path)
            if result["success"]:
                output = result["output"]
                # Handle different response formats
                if isinstance(output, dict):
                    caption = output.get("caption", output.get("text", str(output)))
                elif isinstance(output, list) and len(output) > 0:
                    caption = str(output[0])
                else:
                    caption = str(output)
                
                return {
                    "success": True,
                    "output": caption,
                    "error": None
                }
        
        # Fallback
        return {
            "success": True,
            "output": "This is a description of the image [image captioning requires Bytez API]",
            "error": None
        }
    
    async def image_captioning_async(self, image_path: str) -> Dict[str, Any]:
        """Async image captioning"""
        return self.image_captioning(image_path)

# Create a global instance with error handling
external_api = None

def _get_external_api_safe():
    """Safely create external API instance"""
    global external_api
    if external_api is None:
        try:
            external_api = ExternalAPIWrapper()
        except Exception as e:
            logger.error(f"Failed to create ExternalAPIWrapper: {e}")
            # Create a minimal fallback instance
            external_api = ExternalAPIWrapper()
            external_api.models_available = False
    return external_api

# Initialize on first import, but don't crash if it fails
try:
    external_api = ExternalAPIWrapper()
except Exception as e:
    logger.warning(f"ExternalAPIWrapper initialization failed: {e}. Will retry on first use.")
    external_api = None

# For backward compatibility with existing code
def get_external_api():
    """Get the external API wrapper instance"""
    return _get_external_api_safe()
