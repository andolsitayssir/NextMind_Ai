"""
Adaptive Question Generator for NextMind
Generates AI-powered questions that adapt based on previous answers
"""
import logging
from .openrouter_client import OpenRouterClient
from .trait_guidelines import get_trait_guidelines, get_scoring_guide
from .evaluation_engine import EvaluationEngine

logger = logging.getLogger(__name__)


class AdaptiveQuestionGenerator:
    """Generates adaptive psychological assessment questions"""
    
    def __init__(self):
        self.client = OpenRouterClient()
        try:
            self.evaluation_engine = EvaluationEngine()
        except Exception:
            self.evaluation_engine = None
    
    def generate_first_question(self, trait, assessment_type, language):
        """
        Generate broad exploratory first question for a trait
        
        Args:
            trait: Trait name (e.g., 'ouverture', 'dominant')
            assessment_type: 'big_five' or 'disc'
            language: 'fr', 'en', or 'ar'
            
        Returns:
            Question text
        """
        guidelines = get_trait_guidelines(trait, assessment_type, language)
        
        prompt = f"""You are a professional psychological assessor creating questions for a {assessment_type} assessment.

Generate ONE open-ended question in {language} to assess: {trait}

Context:
{guidelines.get('description', '')}

Requirements:
1. The question should be BROAD and EXPLORATORY
2. It should encourage the person to describe their behavior, preferences, or experiences
3. It should be open-ended (not yes/no)
4. It should feel natural and conversational
5. It should be in {language} language
6. DO NOT ask multiple questions - only ONE question
7. DO NOT include explanations or context - ONLY the question

Examples of good questions:
- "how do you typically approach new experiences?"
- "would you prefer working in a team or alone, and why?"
- "do you enjoy taking charge in group settings? can you give an example?"
- "do you prefer planned activities or spontaneous ones? why?"

Generate the question now (ONLY the question text, nothing else):"""

        try:
            question = self.client.generate(
                prompt=prompt,
                model='reasoning',
                temperature=0.7  # Creative for variety
            )
            
            # Clean up the response
            question = question.strip().strip('"').strip("'")
            
            logger.info(f"Generated Q1 for {trait}: {question[:50]}...")
            return question
            
        except Exception as e:
            logger.error(f"Error generating first question: {e}")
            # Emergency fallback
            return self._get_fallback_question(trait, assessment_type, language, question_number=1)
    
    def generate_adaptive_second_question(self, trait, assessment_type, q1_answer, q1_score, language, nlp_analysis=None):
        """
        Generate adaptive follow-up question based on first answer
        
        Args:
            trait: Trait name
            assessment_type: 'big_five' or 'disc'
            q1_answer: User's answer to first question
            q1_score: Score from first question (1-5)
            language: 'fr', 'en', or 'ar'
            nlp_analysis: Optional NLP analysis of Q1 answer
            
        Returns:
            Adaptive question text
        """
        guidelines = get_trait_guidelines(trait, assessment_type, language)
        scoring_guide = get_scoring_guide(trait, assessment_type, language)
        
        # Determine adaptation strategy
        if q1_score >= 4:
            strategy = "HIGH_SCORE_VALIDATION"
            instruction = "The person scored HIGH on the first question. Ask for a SPECIFIC CONCRETE EXAMPLE to validate this high score. The question should probe deeper to confirm they truly exhibit this trait."
        elif q1_score <= 2:
            strategy = "LOW_SCORE_CLARIFICATION"
            instruction = "The person scored LOW on the first question. Ask a CLARIFYING question to better understand their perspective. The question should explore why they might score low on this trait."
        else:
            strategy = "NEUTRAL_DEEPENING"
            instruction = "The person scored NEUTRAL on the first question. Ask a DEEPER question to get a clearer signal. The question should help distinguish whether they lean high or low on this trait."
        
        # Check for vague answers
        if nlp_analysis and nlp_analysis.get('depth_score', 1.0) < 0.4:
            instruction += "\n\nIMPORTANT: The first answer was VAGUE or TOO SHORT. Ask for a CONCRETE, DETAILED EXAMPLE."
        
        prompt = f"""You are a professional psychological assessor conducting an adaptive assessment.

TRAIT BEING ASSESSED: {trait}
ASSESSMENT TYPE: {assessment_type}

TRAIT DESCRIPTION:
{guidelines.get('description', '')}

SCORING GUIDE:
{scoring_guide}

FIRST QUESTION ANSWER: "{q1_answer}"
FIRST QUESTION SCORE: {q1_score}/5

ADAPTATION STRATEGY: {strategy}
{instruction}

Generate ONE adaptive follow-up question in {language} that:
1. Builds on the first answer
2. Seeks clarification or validation
3. Is specific and targeted
4. Helps confirm the trait level
5. Is in {language} language
6. Is open-ended and encourages detailed response

DO NOT:
- Ask multiple questions
- Include explanations
- Repeat the first question
- Ask yes/no questions

Generate the question now (ONLY the question text, nothing else):"""

        try:
            question = self.client.generate(
                prompt=prompt,
                model='reasoning',
                temperature=0.4  # Lower for faster, more focused questions
            )
            
            # Clean up the response
            question = question.strip().strip('"').strip("'")
            
            # --- VALIDATION LOOP (New) ---
            if self.evaluation_engine:
                 is_good, critique = self.evaluation_engine.evaluate_question_quality(
                     generated_question=question, 
                     previous_answer=q1_answer, 
                     trait=trait, 
                     language=language
                 )
                 
                 if not is_good:
                     logger.warning(f"Validation failed for Q2 ({critique}). Retrying...")
                     
                     # Retry with critique
                     retry_prompt = prompt + f"\n\nCRITIQUE FROM PREVIOUS ATTEMPT: {critique}\nFix the question to address this critique."
                     
                     question = self.client.generate(
                        prompt=retry_prompt,
                        model='reasoning',
                        temperature=0.4
                     )
                     question = question.strip().strip('"').strip("'")
                     logger.info(f"Retried Q2: {question[:50]}")
            # -----------------------------
            
            logger.info(f"Generated adaptive Q2 for {trait} (score={q1_score}): {question[:50]}...")
            return question
            
        except Exception as e:
            logger.error(f"Error generating adaptive question: {e}")
            # Emergency fallback
            return self._get_fallback_question(trait, assessment_type, language, question_number=2)
    
    def _get_fallback_question(self, trait, assessment_type, language, question_number):
        """Emergency fallback questions if AI generation fails"""
        fallbacks = {
            'fr': {
                1: f"Décrivez votre approche concernant {trait}.",
                2: f"Pouvez-vous donner un exemple concret concernant {trait}?"
            },
            'en': {
                1: f"Describe your approach regarding {trait}.",
                2: f"Can you give a concrete example regarding {trait}?"
            }
        }
        
        return fallbacks.get(language, fallbacks['fr']).get(question_number, "Décrivez votre expérience.")
