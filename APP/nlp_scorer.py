"""
NLP Scorer for NextMind
Scores answers using NLP analysis + LLM with cahier de charge alignment
"""
import json
import logging
import re
from .openrouter_client import OpenRouterClient
from .trait_guidelines import get_scoring_guide, get_trait_keywords, get_trait_guidelines
from .vector_engine import VectorEngine
from .evaluation_engine import EvaluationEngine

logger = logging.getLogger(__name__)


class NLPScorer:
    """Scores psychological assessment answers using NLP + LLM"""
    
    def __init__(self):
        self.client = OpenRouterClient()
        self.vector_engine = VectorEngine()
        try:
            self.evaluation_engine = EvaluationEngine()
        except Exception:
            self.evaluation_engine = None
    
    def score_answer(self, question, answer, trait, assessment_type, language):
        """
        Score answer 1-5 using NLP + LLM
        
        Args:
            question: The question that was asked
            answer: User's answer text
            trait: Trait being assessed
            assessment_type: 'big_five' or 'disc'
            language: 'fr', 'en', or 'ar'
            
        Returns:
            dict with score, reasoning, confidence, nlp_features
        """
        # Step 1: Extract NLP features
        nlp_features = self._extract_nlp_features(answer, trait, assessment_type, language)
        
        # Step 2: Build scoring prompt with cahier de charge
        scoring_prompt = self._build_scoring_prompt(
            question=question,
            answer=answer,
            trait=trait,
            assessment_type=assessment_type,
            nlp_features=nlp_features,
            language=language
        )
        
        # Step 3: Get structured score from LLM
        try:
            response = self.client.generate_json(
                prompt=scoring_prompt,
                model='reasoning',
                temperature=0.2  # Very low for consistency and speed
            )
            
            # Validate score
            score = int(response.get('score', 3))
            if score < 1 or score > 5:
                logger.warning(f"Invalid score {score}, defaulting to 3")
                score = 3
            
            result = {
                'score': score,
                'reasoning': response.get('reasoning', ''),
                'confidence': float(response.get('confidence', 0.7)),
                'nlp_features': nlp_features
            }
            
            # --- CONSISTENCY CHECK (Evaluation Engine) ---
            if self.evaluation_engine:
                 is_consistent, critique = self.evaluation_engine.evaluate_score_consistency(
                     score=score,
                     reasoning=result['reasoning'],
                     answer=answer
                 )
                 
                 if not is_consistent:
                     logger.warning(f"Score Inconsistency Detected: {critique}")
                     # Penalize confidence significantly if logic doesn't hold
                     result['confidence'] = max(0.1, result['confidence'] - 0.4)
                     result['reasoning'] += f" [Note: Potential inconsistency detected: {critique}]"
            # ---------------------------------------------
            
            logger.info(f"Scored answer for {trait}: {score}/5 (confidence: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error scoring answer: {e}")
            # Fallback to NLP-only scoring
            return self._fallback_nlp_score(answer, trait, assessment_type, language, nlp_features)

    def _extract_nlp_features(self, answer, trait, assessment_type, language):
        """Extract NLP features from answer"""
        words = answer.split()
        word_count = len(words)
        
        # Get trait-specific keywords (Legacy/Fallback)
        keywords = get_trait_keywords(trait, assessment_type, language)
        
        # Vector Semantic Analysis
        semantic_score = 0
        if self.vector_engine.is_ready():
            guidelines = get_trait_guidelines(trait, assessment_type, language)
            # Use description as the "concept" to match against
            description = guidelines.get('description', trait)
            semantic_score = self.vector_engine.get_semantic_score_for_trait(answer, description)
        
        # Calculate depth score
        depth_score = min(1.0, word_count / 50.0)
        
        # Language-specific specificity indicators
        specificity_patterns = self._get_specificity_patterns(language)
        specificity_count = sum(1 for pattern in specificity_patterns if re.search(pattern, answer.lower()))
        specificity_score = min(1.0, specificity_count / 3.0)
        
        return {
            'word_count': word_count,
            'depth_score': round(depth_score, 2),
            'specificity_score': round(specificity_score, 2),
            'semantic_match_score': semantic_score, # 0-100
            'has_examples': specificity_count > 0
        }
    
    def _get_specificity_patterns(self, language):
        """Get language-specific patterns for detecting concrete examples"""
        patterns = {
            'fr': [
                r'\bpar exemple\b', r'\bexemple\b', r"\bj'ai\b", r'\bje\b',
                r'\b\d+\b', r'\b20\d{2}\b',  # numbers and years
                r'\bquand\b', r'\blorsque\b', r'\bun jour\b',
                r'\bune fois\b', r'\brécemment\b', r'\bdernièrement\b'
            ],
            'en': [
                r'\bfor example\b', r'\bexample\b', r'\bi\b', r"\bi've\b", r'\bi have\b',
                r'\b\d+\b', r'\b20\d{2}\b',  # numbers and years
                r'\bwhen\b', r'\bonce\b', r'\brecently\b',
                r'\blast\b', r'\bspecifically\b', r'\binstance\b'
            ],
            'ar': [
                r'\bمثال\b', r'\bمثلا\b', r'\bعلى سبيل المثال\b',
                r'\bأنا\b', r'\bكنت\b', r'\bقمت\b',
                r'\b\d+\b', r'\b20\d{2}\b',  # numbers and years
                r'\bعندما\b', r'\bحين\b', r'\bمؤخرا\b',
                r'\bفي مرة\b', r'\bتحديدا\b'
            ]
        }
        
        return patterns.get(language, patterns['fr'])
    
    def _build_scoring_prompt(self, question, answer, trait, assessment_type, nlp_features, language):
        """Build structured scoring prompt with cahier de charge"""
        
        scoring_guide = get_scoring_guide(trait, assessment_type, language)
        
        prompt = f"""You are a professional psychological assessor. Score this answer on a scale of 1-5 based on psychological theory and the guidelines provided.

TRAIT BEING ASSESSED: {trait}
ASSESSMENT TYPE: {assessment_type}

QUESTION ASKED:
{question}

USER'S ANSWER:
{answer}

SCORING GUIDELINES (from cahier de charge):
{scoring_guide}

CONTEXT ANALYSIS:
- Answer length: {nlp_features['word_count']} words
- Semantic Match (Vector): {nlp_features['semantic_match_score']}% (Alignment with trait concept)
- Vague answer risk: {'High' if nlp_features['word_count'] < 10 else 'Low'}

SCORING INSTRUCTIONS:
1. SEMANTIC ALIGNMENT: Does the answer's *meaning* align with the High or Low description? Do not look for exact keywords, but analyze the sentiment and intent.
2. CONCRETENESS: Did the user provide specific details or context? (The answer is short, so look for density of meaning).
3. SCORE ESTIMATION:
    - 1-2: Clearly matches the "Low" description or expresses inability/dislike.
    - 3: Ambiguous, neutral, or "it depends".
    - 4-5: Clearly matches the "High" description with conviction.
4. CONFIDENCE: Rate your confidence (0.0-1.0). If the answer is too short (e.g. "yes", "no", "idk"), confidence should be low.

Return your response in this EXACT JSON format:
{{
    "score": <integer 1-5>,
    "reasoning": "<brief explanation in {language} focusing on WHY the answer fits the level>",
    "confidence": <float 0.0-1.0>
}}"""

        return prompt
    
    def _fallback_nlp_score(self, answer, trait, assessment_type, language, nlp_features):
        """Fallback scoring using only NLP features (no LLM)"""
        
        # Simple heuristic scoring
        # If words are very few (< 5), likely low quality
        if nlp_features['word_count'] < 5:
            base_score = 2
        elif nlp_features['word_count'] > 30:
            # Long answers usually imply effort -> slightly higher fallback
            base_score = 4
        else:
            # Neutral default
            base_score = 3
        
        # Slight adjustment if strong Semantic Match calculated
        if nlp_features.get('semantic_match_score', 0) > 60:
             base_score = min(5, base_score + 1)
        elif nlp_features.get('semantic_match_score', 0) < 20 and nlp_features['word_count'] > 10:
             # Long but irrelevant answer -> penalize
             base_score = max(1, base_score - 1)
        
        return {
            'score': base_score,
            'reasoning': f"Score basé sur la longueur et la densité (fallback)",
            'confidence': 0.4,  # Lower confidence for fallback
            'nlp_features': nlp_features
        }
    
    def analyze_answer_semantics(self, answer, language):
        """
        Analyze semantic properties of answer for adaptive question generation
        
        Returns:
            dict with depth_score, specificity_score, etc.
        """
        words = answer.split()
        word_count = len(words)
        
        depth_score = min(1.0, word_count / 50.0)
        
        # Use language-specific patterns
        specificity_patterns = self._get_specificity_patterns(language)
        specificity_count = sum(1 for pattern in specificity_patterns if re.search(pattern, answer.lower()))
        specificity_score = min(1.0, specificity_count / 3.0)
        
        return {
            'word_count': word_count,
            'depth_score': round(depth_score, 2),
            'specificity_score': round(specificity_score, 2),
            'is_vague': depth_score < 0.3 or specificity_score < 0.2
        }
