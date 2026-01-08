"""
Evaluation Engine (The "Critic")
Runtime quality control for AI generation.
Verifies that questions are adaptive and scores are consistent.
"""
import logging
import json
from .openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)

class EvaluationEngine:
    """
    Acts as a 'Critic' to evaluate AI outputs before they are shown to the user.
    Uses a fast/free model to check for logical consistency and adaptation.
    """

    def __init__(self):
        self.client = OpenRouterClient()
        # Use a model good at classification/validation
        self.model = 'validation' 

    def evaluate_question_quality(self, generated_question, previous_answer, trait, language):
        """
        Check if a generated question is truly adaptive to the previous answer.
        Returns: (bool is_good, str critique)
        """
        prompt = f"""You are a Quality Control AI. Analyze this follow-up question.

CONTEXT:
- Trait: {trait}
- User's Previous Answer: "{previous_answer}"
- AI Generated Follow-up: "{generated_question}"

CRITERIA FOR PASS:
1. The follow-up MUST reference specific details from the User's Previous Answer (not generic).
2. It must be relevant to the Trait.
3. It must NOT exactly repeat the previous question.

TASK:
- If the question uses generic phrases like "Tell me more" without referencing the user's specific content -> FAIL.
- If the question is specific and tailored -> PASS.

Return JSON:
{{
    "status": "PASS" or "FAIL",
    "critique": "Brief explanation of why it failed (if fail), or 'Good adaptation' (if pass)."
}}"""

        try:
            response = self.client.generate_json(prompt, model=self.model, temperature=0.1)
            is_good = response.get('status') == 'PASS'
            critique = response.get('critique', '')
            
            # Print to console for immediate visibility (User Request)
            status_icon = "✅" if is_good else "❌"
            print(f"\n{status_icon} [EVALUATOR] Question Quality: {response.get('status')}")
            if critique:
                print(f"   Critique: {critique}\n")

            logger.info(f"Question Evaluation: {response.get('status')} - {critique}")
            return is_good, critique

        except Exception as e:
            logger.warning(f"Evaluation failed (defaulting to PASS to avoid blocking): {e}")
            return True, "Evaluation Error"

    def evaluate_score_consistency(self, score, reasoning, answer):
        """
        Check if the score matches the reasoning and the answer content.
        Returns: (bool is_consistent, str critique)
        """
        prompt = f"""You are a Quality Control AI. Verify if this score is consistent with the reasoning.

User Answer: "{answer}"
AI Score: {score}/5
AI Reasoning: "{reasoning}"

TASK:
- Does the reasoning illogical contradiction? (e.g. "User showed no interest" but Score is 5).
- Does the score seem hallucinated based on the text?

Return JSON:
{{
    "status": "CONSISTENT" or "INCONSISTENT",
    "critique": "Brief explanation."
}}"""

        try:
            response = self.client.generate_json(prompt, model=self.model, temperature=0.1)
            is_good = response.get('status') == 'CONSISTENT'
            critique = response.get('critique', '')

            # Print to console for immediate visibility
            status_icon = "✅" if is_good else "⚠️"
            print(f"\n{status_icon} [EVALUATOR] Score Consistency: {response.get('status')}")
            if critique:
                print(f"   Critique: {critique}\n")

            if not is_good:
                logger.warning(f"Score Inconsistency Detected: {critique}")
            
            return is_good, critique

        except Exception as e:
            return True, "Evaluation Error"
