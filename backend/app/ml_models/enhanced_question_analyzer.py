import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from typing import List, Dict, Any, Tuple, Optional
import json
from datetime import datetime
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
from sklearn.metrics.pairwise import cosine_similarity

# Lazy imports to prevent DLL errors
_spacy = None
_sentence_transformers = None

def _lazy_import_spacy():
    """Lazy import spacy to prevent DLL errors on startup"""
    global _spacy
    if _spacy is None:
        try:
            import spacy
            _spacy = spacy
            return spacy
        except Exception as e:
            logger.warning(f"Failed to import spacy: {e}")
            return None
    return _spacy

def _lazy_import_sentence_transformers():
    """Lazy import sentence_transformers"""
    global _sentence_transformers
    if _sentence_transformers is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformers = SentenceTransformer
            return SentenceTransformer
        except Exception as e:
            logger.warning(f"Failed to import sentence_transformers: {e}")
            return None
    return _sentence_transformers

# Try to import external_api, but don't fail if it doesn't work
try:
    from ..ml.external_api_wrapper import get_external_api
    external_api = get_external_api()
except Exception as e:
    logger.warning(f"Failed to import external_api: {e}")
    external_api = None

logger = logging.getLogger(__name__)

# BERTopic for advanced topic modeling
try:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    BERTopic = None
    UMAP = None
    HDBSCAN = None

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
except:
    pass  # Handle cases where downloads fail

logger = logging.getLogger(__name__)

class EnhancedQuestionAnalyzer:
    """
    Enhanced Machine Learning model for analyzing question patterns and predicting likely exam questions
    with advanced NLP capabilities including spaCy preprocessing, semantic similarity analysis,
    and BERTopic modeling.
    """
    
    def __init__(self):
        # Load spaCy model for advanced NLP preprocessing (lazy loading)
        self.nlp = None
        try:
            spacy_module = _lazy_import_spacy()
            if spacy_module:
                try:
                    self.nlp = spacy_module.load("en_core_web_sm")
                    logger.info("spaCy model loaded successfully")
                except OSError:
                    logger.warning("spaCy 'en_core_web_sm' model not found. Please install it with: python -m spacy download en_core_web_sm")
                    self.nlp = None
                except Exception as e:
                    logger.warning(f"Failed to load spaCy model: {e}")
                    self.nlp = None
        except Exception as e:
            logger.warning(f"spaCy not available: {e}. Using fallback preprocessing.")
            self.nlp = None
        
        # Load sentence transformer model for semantic similarity (lazy loading)
        self.sentence_model = None
        try:
            SentenceTransformer = _lazy_import_sentence_transformers()
            if SentenceTransformer:
                try:
                    self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Sentence transformer model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load sentence transformer model: {e}")
                    self.sentence_model = None
        except Exception as e:
            logger.warning(f"Sentence transformers not available: {e}. Using fallback similarity.")
            self.sentence_model = None
            
        # Initialize NLTK components
        try:
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
        except LookupError:
            logger.warning("NLTK data not found. Please install NLTK data.")
            self.stop_words = set()
            self.lemmatizer = None
        
        # TF-IDF vectorizer with enhanced parameters
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3),  # Include trigrams for better context
            lowercase=True,
            min_df=1,  # Minimum document frequency
            max_df=0.8  # Maximum document frequency to filter common terms
        )
        
        # LDA model for topic modeling
        self.lda_model = LatentDirichletAllocation(
            n_components=10,  # Number of topics to extract
            random_state=42,
            max_iter=100,  # Increased iterations for better convergence
            learning_method='online',  # Better for larger datasets
            learning_offset=50.,
            doc_topic_prior=0.1,  # Symmetric Dirichlet prior
            topic_word_prior=0.01  # Symmetric Dirichlet prior
        )
        
        # K-means clustering for question types
        self.kmeans_model = KMeans(
            n_clusters=5,
            random_state=42,
            n_init=10
        )
        
        # Initialize BERTopic if available
        self.bertopic_model = None
        if BERTOPIC_AVAILABLE:
            try:
                # Initialize BERTopic with UMAP and HDBSCAN for better clustering
                self.umap_model = UMAP(n_neighbors=15, 
                                       n_components=5, 
                                       min_dist=0.0, 
                                       metric='cosine',
                                       random_state=42)
                
                self.cluster_model = HDBSCAN(min_cluster_size=5,
                                            metric='euclidean',
                                            cluster_selection_method='eom',
                                            prediction_data=True)
                
                self.bertopic_model = BERTopic(
                    embedding_model=self.sentence_model,
                    umap_model=self.umap_model,
                    hdbscan_model=self.cluster_model,
                    vectorizer_model=self.vectorizer,
                    nr_topics=10,  # Target number of topics
                    min_topic_size=5,
                    low_memory=True,
                    calculate_probabilities=True,
                    seed=42
                )
            except Exception as e:
                logger.error(f"Failed to initialize BERTopic model: {e}")
                self.bertopic_model = None
        else:
            logger.warning("BERTopic not available. Install it with: pip install bertopic")
        
        # Semantic similarity threshold
        self.similarity_threshold = 0.7
    
    def preprocess_text_spacy(self, text: str) -> str:
        """Advanced text preprocessing using spaCy"""
        if not self.nlp:
            return self.preprocess_text_basic(text)
        
        try:
            doc = self.nlp(text)
            
            # Process tokens: remove stop words, punctuation, lemmatize
            processed_tokens = []
            for token in doc:
                if (not token.is_stop and 
                    not token.is_punct and 
                    not token.is_space and 
                    token.text.lower() not in string.punctuation and
                    len(token.text.strip()) > 1):
                    
                    # Lemmatize the token
                    lemma = token.lemma_.lower()
                    if len(lemma) > 2 and lemma not in self.stop_words:
                        processed_tokens.append(lemma)
            
            return ' '.join(processed_tokens)
        except Exception as e:
            logger.error(f"Error in spaCy preprocessing: {e}")
            return self.preprocess_text_basic(text)
    
    def preprocess_text_nltk(self, text: str) -> str:
        """Text preprocessing using NLTK"""
        try:
            # Tokenize
            tokens = word_tokenize(text.lower())
            
            # Remove stop words and punctuation, lemmatize
            processed_tokens = []
            for token in tokens:
                if (token not in self.stop_words and 
                    token not in string.punctuation and 
                    len(token) > 2):
                    
                    if self.lemmatizer:
                        lemma = self.lemmatizer.lemmatize(token)
                        processed_tokens.append(lemma)
                    else:
                        processed_tokens.append(token)
            
            return ' '.join(processed_tokens)
        except Exception as e:
            logger.error(f"Error in NLTK preprocessing: {e}")
            return self.preprocess_text_basic(text)
    
    def preprocess_text_basic(self, text: str) -> str:
        """Basic text preprocessing as fallback"""
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.strip().lower()
        return text
    
    def preprocess_text(self, text: str) -> str:
        """Main preprocessing function that tries spaCy first, then NLTK, then basic"""
        if self.nlp:
            return self.preprocess_text_spacy(text)
        elif self.lemmatizer:
            return self.preprocess_text_nltk(text)
        else:
            return self.preprocess_text_basic(text)
    
    def extract_questions_features(self, questions: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str], List[Dict[str, Any]]]:
        """Extract features from questions for ML analysis with enhanced preprocessing"""
        texts = []
        processed_texts = []
        processed_questions = []
        
        for question in questions:
            original_text = question.get('text', '')
            processed_text = self.preprocess_text(original_text)
            
            if len(processed_text) > 10:  # Only process substantial questions
                texts.append(original_text)  # Keep original for some analyses
                processed_texts.append(processed_text)
                processed_questions.append(question)
        
        if not processed_texts:
            return np.array([]), [], []
        
        # Vectorize the processed texts
        try:
            vectors = self.vectorizer.fit_transform(processed_texts).toarray()
        except ValueError as e:
            logger.error(f"Error in vectorization: {e}")
            # If no features found, return empty arrays
            return np.array([]), processed_texts, processed_questions
        
        return vectors, processed_texts, processed_questions
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using external API or sentence transformers"""
        # Try external API first (if available)
        if external_api:
            try:
                response = external_api.sentence_similarity([text1, text2])
                if response.get("success") and response.get("output"):
                    # Use API result if available
                    api_similarity = response["output"]
                    if isinstance(api_similarity, list) and len(api_similarity) > 0:
                        return float(api_similarity[0])
            except Exception as e:
                logger.warning(f"External API similarity failed, using local method: {e}")
        
        # Fallback to sentence transformers
        if not self.sentence_model:
            # Fallback to basic similarity if sentence transformer is not available
            return self.calculate_basic_similarity(text1, text2)
        
        try:
            embeddings = self.sentence_model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return self.calculate_basic_similarity(text1, text2)
    
    def calculate_basic_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic similarity as fallback"""
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union != 0 else 0.0
    
    def find_similar_questions(self, questions: List[Dict[str, Any]], threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find semantically similar questions"""
        similar_pairs = []
        
        for i in range(len(questions)):
            for j in range(i + 1, len(questions)):
                text1 = questions[i].get('text', '')
                text2 = questions[j].get('text', '')
                
                similarity = self.calculate_semantic_similarity(text1, text2)
                
                if similarity >= threshold:
                    similar_pairs.append({
                        'question1': questions[i],
                        'question2': questions[j],
                        'similarity_score': similarity
                    })
        
        return similar_pairs
    
    def analyze_patterns(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in questions to identify topics and trends with enhanced capabilities"""
        if not questions:
            return {
                "topics": [],
                "frequencies": {},
                "patterns": [],
                "trends": [],
                "predicted_questions": [],
                "similar_questions": [],
                "semantic_analysis": {},
                "bertopic_analysis": {}
            }
        
        # Extract features
        vectors, processed_texts, processed_questions = self.extract_questions_features(questions)
        
        if vectors.size == 0:
            return {
                "topics": [],
                "frequencies": {},
                "patterns": [],
                "trends": [],
                "predicted_questions": [],
                "similar_questions": [],
                "semantic_analysis": {},
                "bertopic_analysis": {}
            }
        
        # Perform topic modeling using LDA
        try:
            topics = self.lda_model.fit_transform(vectors)
        except Exception as e:
            logger.error(f"Error in LDA topic modeling: {str(e)}")
            topics = np.zeros((len(processed_questions), 10))
        
        # Perform clustering to identify question types
        try:
            clusters = self.kmeans_model.fit_predict(vectors)
        except Exception as e:
            logger.error(f"Error in KMeans clustering: {str(e)}")
            clusters = np.zeros(len(processed_questions))
        
        # Perform BERTopic analysis if available
        bertopic_analysis = {}
        if self.bertopic_model and processed_texts:
            try:
                # Fit BERTopic model
                bertopic_topics, bertopic_probs = self.bertopic_model.fit_transform(processed_texts)
                
                # Get topic info
                topic_info = self.bertopic_model.get_topic_info()
                
                # Get keywords for each topic
                topic_keywords = {}
                for topic_id in topic_info['Topic'].values:
                    if topic_id != -1:  # Skip outlier topic
                        topic_keywords[topic_id] = self.bertopic_model.get_topic(topic_id)
                
                bertopic_analysis = {
                    "topics": len(np.unique(bertopic_topics)),
                    "topic_info": topic_info.to_dict('records'),
                    "topic_keywords": topic_keywords,
                    "probabilities": bertopic_probs.tolist() if bertopic_probs is not None else [],
                    "model_available": True
                }
            except Exception as e:
                logger.error(f"Error in BERTopic analysis: {str(e)}")
                bertopic_analysis = {"model_available": False, "error": str(e)}
        else:
            bertopic_analysis = {"model_available": False, "message": "BERTopic model not available"}
        
        # Analyze frequencies of topics
        topic_frequencies = {}
        for i, topic_dist in enumerate(topics):
            dominant_topic = np.argmax(topic_dist)
            topic_frequencies[dominant_topic] = topic_frequencies.get(dominant_topic, 0) + 1
        
        # Identify question patterns based on clustering
        cluster_analysis = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id not in cluster_analysis:
                cluster_analysis[cluster_id] = {
                    "count": 0,
                    "questions": [],
                    "avg_length": 0,
                    "avg_difficulty": 0,
                    "marks_range": []
                }
            cluster_analysis[cluster_id]["count"] += 1
            cluster_analysis[cluster_id]["questions"].append(processed_questions[i])
            cluster_analysis[cluster_id]["avg_length"] += len(processed_questions[i].get("text", ""))
            
            # Add difficulty and marks if available
            marks = processed_questions[i].get("marks", 0)
            difficulty = processed_questions[i].get("difficulty", "medium")
            cluster_analysis[cluster_id]["marks_range"].append(marks)
            
            # Map difficulty to numeric value for averaging
            diff_map = {"easy": 1, "medium": 2, "hard": 3}
            cluster_analysis[cluster_id]["avg_difficulty"] += diff_map.get(difficulty, 2)
        
        # Calculate averages
        for cluster_id in cluster_analysis:
            count = cluster_analysis[cluster_id]["count"]
            if count > 0:
                cluster_analysis[cluster_id]["avg_length"] /= count
                cluster_analysis[cluster_id]["avg_difficulty"] /= count
        
        # Find similar questions using semantic analysis
        similar_questions = self.find_similar_questions(processed_questions)
        
        # Generate predictions based on analysis
        predictions = self._generate_predictions(processed_questions, topic_frequencies, cluster_analysis)
        
        # Perform semantic analysis
        semantic_analysis = self._perform_semantic_analysis(processed_questions)
        
        return {
            "topics": [
                {
                    "topic_id": topic_id,
                    "frequency": freq,
                    "percentage": round((freq / len(processed_questions)) * 100, 2) if processed_questions else 0
                }
                for topic_id, freq in topic_frequencies.items()
            ],
            "frequencies": topic_frequencies,
            "patterns": [
                {
                    "cluster_id": cluster_id,
                    "count": analysis["count"],
                    "avg_length": analysis["avg_length"],
                    "avg_difficulty": analysis["avg_difficulty"],
                    "marks_range": analysis["marks_range"],
                    "sample_questions": [q.get("text", "")[:100] for q in analysis["questions"][:3]]
                }
                for cluster_id, analysis in cluster_analysis.items()
            ],
            "trends": self._analyze_trends(processed_questions),
            "predicted_questions": predictions,
            "similar_questions": similar_questions,
            "semantic_analysis": semantic_analysis,
            "bertopic_analysis": bertopic_analysis
        }
    
    def _perform_semantic_analysis(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform semantic analysis on questions"""
        if not questions:
            return {}
        
        # Extract key terms and concepts
        all_terms = []
        for q in questions:
            text = q.get("text", "")
            if self.nlp:
                doc = self.nlp(text)
                # Extract named entities and key terms
                entities = [ent.text for ent in doc.ents]
                nouns = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]
                all_terms.extend(entities + nouns)
            else:
                # Fallback: extract capitalized words and common nouns
                words = text.split()
                terms = [word for word in words if word[0].isupper() or len(word) > 4]
                all_terms.extend(terms)
        
        # Count term frequencies
        term_freq = {}
        for term in all_terms:
            term_freq[term] = term_freq.get(term, 0) + 1
        
        # Get most common terms
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "key_concepts": sorted_terms[:20],  # Top 20 concepts
            "total_concepts": len(term_freq),
            "average_concept_frequency": sum(term_freq.values()) / len(term_freq) if term_freq else 0
        }
    
    def _analyze_trends(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze temporal and frequency trends in questions"""
        trends = []
        
        if not questions:
            return trends
        
        # Analyze by marks distribution
        marks_dist = {}
        for q in questions:
            marks = q.get('marks', 0)
            marks_dist[marks] = marks_dist.get(marks, 0) + 1
        
        # Analyze by unit distribution
        unit_dist = {}
        for q in questions:
            unit = q.get('unit', 'Unknown')
            unit_dist[unit] = unit_dist.get(unit, 0) + 1
        
        # Analyze by difficulty distribution
        difficulty_dist = {}
        for q in questions:
            difficulty = q.get('difficulty', 'Unknown')
            difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1
        
        trends.append({
            "type": "marks_distribution",
            "data": marks_dist
        })
        
        trends.append({
            "type": "unit_distribution", 
            "data": unit_dist
        })
        
        trends.append({
            "type": "difficulty_distribution",
            "data": difficulty_dist
        })
        
        # Identify most frequent units
        if unit_dist:
            most_frequent_unit = max(unit_dist, key=unit_dist.get)
            trends.append({
                "type": "most_frequent_unit",
                "unit": most_frequent_unit,
                "frequency": unit_dist[most_frequent_unit]
            })
        
        # Identify most difficult topics
        if difficulty_dist and 'hard' in difficulty_dist:
            trends.append({
                "type": "most_challenging_topics",
                "count": difficulty_dist.get('hard', 0)
            })
        
        return trends
    
    def _generate_predictions(self, questions: List[Dict[str, Any]], topic_frequencies: Dict[int, int], cluster_analysis: Dict[int, Any]) -> List[Dict[str, Any]]:
        """Generate predicted questions based on analysis"""
        predictions = []
        
        if not questions:
            return predictions
        
        # Identify the most frequent topics and clusters
        if topic_frequencies:
            most_frequent_topic = max(topic_frequencies, key=topic_frequencies.get)
            topic_percentage = (topic_frequencies[most_frequent_topic] / len(questions)) * 100
            
            # Generate a prediction based on the most frequent topic
            predictions.append({
                "question_number": 1,
                "text": f"Predicted question based on Topic {most_frequent_topic} pattern analysis",
                "marks": self._estimate_common_marks(questions),
                "unit": self._estimate_common_unit(questions),
                "probability": "high" if topic_percentage > 30 else "moderate",
                "reasoning": f"Based on Topic {most_frequent_topic} being the most frequent ({topic_percentage:.1f}%)",
                "confidence_score": min(topic_percentage / 100, 1.0)
            })
        
        # Add more predictions based on cluster analysis
        if cluster_analysis:
            for cluster_id, analysis in list(cluster_analysis.items())[:2]:  # Take top 2 clusters
                if analysis["count"] > 1:  # Only consider clusters with multiple questions
                    predictions.append({
                        "question_number": len(predictions) + 1,
                        "text": f"Predicted question based on Cluster {cluster_id} pattern analysis",
                        "marks": self._estimate_common_marks(questions),
                        "unit": self._estimate_common_unit(questions),
                        "probability": "moderate" if analysis["count"] > 2 else "low",
                        "reasoning": f"Based on Cluster {cluster_id} pattern with {analysis['count']} similar questions",
                        "confidence_score": min(analysis["count"] / len(questions), 1.0)
                    })
        
        # Add predictions based on high-frequency units
        unit_dist = {}
        for q in questions:
            unit = q.get('unit', 'Unknown')
            unit_dist[unit] = unit_dist.get(unit, 0) + 1
        
        if unit_dist:
            # Add predictions for top units
            sorted_units = sorted(unit_dist.items(), key=lambda x: x[1], reverse=True)
            for i, (unit, count) in enumerate(sorted_units[:3]):
                if count > 1:
                    predictions.append({
                        "question_number": len(predictions) + 1,
                        "text": f"Predicted question for {unit} based on historical pattern",
                        "marks": self._estimate_common_marks(questions),
                        "unit": unit,
                        "probability": "high" if count > len(questions) * 0.3 else "moderate",
                        "reasoning": f"Based on {unit} appearing {count} times in historical data",
                        "confidence_score": min(count / len(questions), 1.0)
                    })
        
        return predictions
    
    def _estimate_common_marks(self, questions: List[Dict[str, Any]]) -> int:
        """Estimate the most common marks value"""
        marks_list = [q.get('marks', 2) for q in questions if q.get('marks')]
        if marks_list:
            # Return the most common marks value
            from collections import Counter
            counter = Counter(marks_list)
            return counter.most_common(1)[0][0]
        return 5  # Default
    
    def _estimate_common_unit(self, questions: List[Dict[str, Any]]) -> str:
        """Estimate the most common unit"""
        unit_list = [q.get('unit', 'Unknown') for q in questions if q.get('unit') and q.get('unit') != 'Unknown']
        if unit_list:
            # Return the most common unit
            from collections import Counter
            counter = Counter(unit_list)
            return counter.most_common(1)[0][0]
        return "General"
    
    def predict_exam_questions(self, historical_questions: List[Dict[str, Any]], num_predictions: int = 5) -> List[Dict[str, Any]]:
        """Main method to predict exam questions based on historical data"""
        try:
            analysis = self.analyze_patterns(historical_questions)
            predictions = analysis.get("predicted_questions", [])
            
            # Ensure we have enough predictions
            while len(predictions) < num_predictions:
                # Generate additional predictions if needed
                additional_pred = {
                    "question_number": len(predictions) + 1,
                    "text": f"Additional predicted question based on pattern analysis",
                    "marks": self._estimate_common_marks(historical_questions),
                    "unit": self._estimate_common_unit(historical_questions),
                    "probability": "low",
                    "reasoning": "Generated based on overall pattern analysis",
                    "confidence_score": 0.5
                }
                predictions.append(additional_pred)
            
            # Limit to requested number
            return predictions[:num_predictions]
        
        except Exception as e:
            logger.error(f"Error in predicting exam questions: {str(e)}")
            # Return fallback predictions
            return [
                {
                    "question_number": i+1,
                    "text": f"Fallback predicted question {i+1}",
                    "marks": 5,
                    "unit": "General",
                    "probability": "low",
                    "reasoning": "Fallback prediction due to analysis error",
                    "confidence_score": 0.1
                }
                for i in range(num_predictions)
            ]
    
    def get_topic_keywords(self) -> List[Dict[str, Any]]:
        """Get keywords for each topic from the LDA model"""
        if hasattr(self, 'vectorizer') and hasattr(self, 'lda_model'):
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(self.lda_model.components_):
                top_keywords_idx = topic.argsort()[-10:][::-1]  # Top 10 keywords
                top_keywords = [feature_names[i] for i in top_keywords_idx]
                topics.append({
                    "topic_id": topic_idx,
                    "keywords": top_keywords,
                    "weights": topic[top_keywords_idx].tolist()
                })
            
            return topics
        return []
    
    def map_syllabus_to_questions(self, syllabus_content: str, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map syllabus content to relevant questions based on semantic similarity"""
        if not self.sentence_model:
            return []
        
        try:
            # Get embedding for syllabus content
            syllabus_embedding = self.sentence_model.encode([syllabus_content])[0]
            
            mapped_questions = []
            for question in questions:
                question_text = question.get('text', '')
                question_embedding = self.sentence_model.encode([question_text])[0]
                
                # Calculate similarity
                similarity = cosine_similarity([syllabus_embedding], [question_embedding])[0][0]
                
                if similarity > self.similarity_threshold:
                    mapped_questions.append({
                        "question": question,
                        "relevance_score": float(similarity),
                        "mapped_to_syllabus": True
                    })
            
            # Sort by relevance score
            mapped_questions.sort(key=lambda x: x['relevance_score'], reverse=True)
            return mapped_questions
            
        except Exception as e:
            logger.error(f"Error in syllabus-to-question mapping: {e}")
            return []