"""
NLP Scorer for NextMind
Scores answers using NLP analysis + LLM with cahier de charge alignment
"""
import json
import logging
import re
from .openrouter_client import OpenRouterClient
from .trait_guidelines import get_scoring_guide, get_trait_keywords

logger = logging.getLogger(__name__)


class NLPScorer:
    """Scores psychological assessment answers using NLP + LLM"""
    
    def __init__(self):
        self.client = OpenRouterClient()
    
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
        
        # Get trait-specific keywords
        keywords = get_trait_keywords(trait, assessment_type, language)
        
        # Find matching keywords
        answer_lower = answer.lower()
        keywords_high_found = [kw for kw in keywords['high'] if kw.lower() in answer_lower]
        keywords_low_found = [kw for kw in keywords['low'] if kw.lower() in answer_lower]
        
        # Calculate depth score (based on length and specificity)
        depth_score = min(1.0, word_count / 50.0)  # 50+ words = max depth
        
        # Language-specific specificity indicators
        specificity_patterns = self._get_specificity_patterns(language)
        specificity_count = sum(1 for pattern in specificity_patterns if re.search(pattern, answer_lower))
        specificity_score = min(1.0, specificity_count / 3.0)
        
        return {
            'word_count': word_count,
            'depth_score': round(depth_score, 2),
            'specificity_score': round(specificity_score, 2),
            'keywords_high_found': keywords_high_found,
            'keywords_low_found': keywords_low_found,
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

NLP ANALYSIS:
- Answer length: {nlp_features['word_count']} words
- Depth score: {nlp_features['depth_score']} (0-1 scale)
- Specificity score: {nlp_features['specificity_score']} (0-1 scale)
- High trait keywords found: {', '.join(nlp_features['keywords_high_found']) if nlp_features['keywords_high_found'] else 'none'}
- Low trait keywords found: {', '.join(nlp_features['keywords_low_found']) if nlp_features['keywords_low_found'] else 'none'}
- Contains specific examples: {'yes' if nlp_features['has_examples'] else 'no'}

SCORING RULES:
1. Score from 1 to 5 (integers only)
2. Base score on the CONTENT and MEANING of the answer, not just keywords
3. Consider the psychological theory behind the trait
4. A score of 1-2 indicates LOW trait expression
5. A score of 3 indicates MODERATE/NEUTRAL trait expression
6. A score of 4-5 indicates HIGH trait expression
7. Provide clear, concise reasoning (max 150 characters)
8. Estimate your confidence (0.0 to 1.0)

IMPORTANT:
- If the answer is vague or too short (< 10 words), score conservatively (2-3)
- If the answer shows clear trait alignment, score accordingly (1-2 or 4-5)
- If the answer is ambiguous, score 3
- DO NOT give high scores without clear evidence in the answer

Return your response in this EXACT JSON format:
{{
    "score": <integer 1-5>,
    "reasoning": "<brief explanation in {language}>",
    "confidence": <float 0.0-1.0>
}}"""

        return prompt
    
    def _fallback_nlp_score(self, answer, trait, assessment_type, language, nlp_features):
        """Fallback scoring using only NLP features (no LLM)"""
        
        # Simple heuristic scoring
        high_keywords = len(nlp_features['keywords_high_found'])
        low_keywords = len(nlp_features['keywords_low_found'])
        
        if high_keywords > low_keywords:
            base_score = 4
        elif low_keywords > high_keywords:
            base_score = 2
        else:
            base_score = 3
        
        # Adjust for depth
        if nlp_features['depth_score'] < 0.3:
            base_score = max(2, base_score - 1)  # Penalize very short answers
        
        return {
            'score': base_score,
            'reasoning': f"Score basé sur l'analyse NLP (fallback)",
            'confidence': 0.6,
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
