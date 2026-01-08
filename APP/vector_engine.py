"""
Vector Engine for NextMind
Handles semantic similarity calculations using local Transformer models.
"""
import logging
import os
try:
    from sentence_transformers import SentenceTransformer, util
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorEngine:
    """Singleton class for Vector Semantic Analysis"""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorEngine, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance
    
    def _initialize_model(self):
        """Load the model (downloading if necessary)"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not installed. Vector Engine disabled.")
            return

        try:
            logger.info("Loading Vector Model (all-MiniLM-L6-v2)...")
            # This will download (~80MB) on first run to standard cache
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Vector Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vector Model: {e}")
            self._model = None
            
    def is_ready(self):
        return self._model is not None

    def get_semantic_similarity(self, text1, text2):
        """
        Calculate cosine similarity between two texts.
        Returns float between 0.0 and 1.0
        """
        if not self._model or not text1 or not text2:
            return 0.0

        try:
            # Encode sentences to get their embeddings
            # sentence-transformers outputs tensors by default suitable for cos_sim
            embedding1 = self._model.encode(text1, convert_to_tensor=True)
            embedding2 = self._model.encode(text2, convert_to_tensor=True)

            # Compute cosine similarities
            cosine_scores = util.cos_sim(embedding1, embedding2)
            
            # Extract scalar value
            return float(cosine_scores[0][0])
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def get_semantic_score_for_trait(self, user_answer, trait_definition):
        """
        Convenience method to get a semantic alignment score (0-100)
        """
        similarity = self.get_semantic_similarity(user_answer, trait_definition)
        # Normalize: Cosine similarity is -1 to 1, but for text usually 0 to 1
        # We allow it to be 0 if negative
        score = max(0.0, similarity)
        return int(score * 100)
