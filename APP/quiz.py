import logging
from .fallback_content import (
    FALLBACK_QUESTIONS,
    fallback_score_answer,
    fallback_generate_analysis,
    fallback_score_explanation
)
import random
# Configure minimal logging - ONLY ERRORS
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Assessment structure
ASSESSMENT_STRUCTURE = {
    "big_five": {
        "traits": ["ouverture", "conscienciosité", "extraversion", "agréabilité", "stabilité émotionnelle"],
        "questions_per_trait": 1,
        "max_score_per_trait": 10,
        "levels": {"faible": (2, 4), "modéré": (5, 7), "élevé": (8, 10)}
    },
    "disc": {
        "styles": ["dominant", "influent", "stable", "conforme"],
        "questions_total": 4,
        "scoring": "choice_based"
    },
    "bien_etre": {
        "questions_total": 1,
        "max_score": 10,
        "levels": {"faible": (2, 4), "modéré": (5, 7), "élevé": (8, 10)}
    },
    "resilience_ie": {
        "questions_total": 1,
        "max_score": 10,
        "levels": {"faible": (2, 4), "modéré": (5, 7), "élevé": (8, 10)}
    }
}

# Big Five traits configuration
TRAITS_CONFIG = {
    "ouverture": {
        "fr": "Ouverture à l'expérience - créativité, curiosité, imagination",
        "en": "Openness to Experience - creativity, curiosity, imagination",
        "ar": "الانفتاح على التجربة - الإبداع والفضول والخيال",
    },
    "conscienciosité": {
        "fr": "Conscienciosité - organisation, discipline, persévérance",
        "en": "Conscientiousness - organization, discipline, perseverance",
        "ar": "الضمير - التنظيم والانضباط والمثابرة",
    },
    "extraversion": {
        "fr": "Extraversion - sociabilité, énergie, affirmation de soi",
        "en": "Extraversion - sociability, energy, assertiveness",
        "ar": "الانبساط - الاجتماعية والطاقة وتأكيد الذات",
    },
    "agréabilité": {
        "fr": "Agréabilité - coopération, confiance, empathie",
        "en": "Agreeableness - cooperation, trust, empathy",
        "ar": "الوداعة - التعاون والثقة والتعاطف",
    },
    "stabilité émotionnelle": {
        "fr": "Stabilité émotionnelle - gestion du stress, équilibre émotionnel",
        "en": "Emotional Stability - stress management, emotional balance",
        "ar": "الاستقرار العاطفي - إدارة التوتر والتوازن العاطفي",
    }
}

# DISC Styles Configuration
DISC_CONFIG = {
    "dominant": {
        "fr": "Dominant (D) - Décideur, orienté résultats, directif",
        "en": "Dominant (D) - Decision-maker, results-oriented, directive",
        "ar": "مهيمن (D) - صانع قرار، موجه للنتائج، توجيهي",
    },
    "influent": {
        "fr": "Influent (I) - Charismatique, communicatif, inspirant",
        "en": "Influent (I) - Charismatic, communicative, inspiring",
        "ar": "مؤثر (I) - جذاب، تواصلي، ملهم",
    },
    "stable": {
        "fr": "Stable (S) - Loyal, calme, patient",
        "en": "Stable (S) - Loyal, calm, patient",
        "ar": "مستقر (S) - مخلص، هادئ، صبور",
    },
    "conforme": {
        "fr": "Conforme (C) - Précis, analytique, rigoureux",
        "en": "Compliant (C) - Precise, analytical, rigorous",
        "ar": "ملتزم (C) - دقيق، تحليلي، صارم",
    }
}


def get_trait_intro(trait, language, assessment_type="big_five"):
    """Get introduction text for a trait based on assessment type"""
    if assessment_type == "big_five":
        intros = {
            "fr": f"Analysons maintenant votre {TRAITS_CONFIG[trait]['fr']}.",
            "en": f"Let's now analyze your {TRAITS_CONFIG[trait]['en']}.",
            "ar": f"دعنا الآن نحلل {TRAITS_CONFIG[trait]['ar']}."
        }
    elif assessment_type == "disc":
        intros = {
            "fr": f"Évaluons votre style {DISC_CONFIG[trait]['fr']}.",
            "en": f"Let's evaluate your {DISC_CONFIG[trait]['en']} style.",
            "ar": f"دعنا نقيم أسلوبك {DISC_CONFIG[trait]['ar']}."
        }
    elif assessment_type == "bien_etre":
        intros = {
            "fr": "Analysons maintenant votre bien-être au travail.",
            "en": "Let's now analyze your workplace well-being.",
            "ar": "دعنا الآن نحلل رفاهيتك في العمل."
        }
    elif assessment_type == "resilience_ie":
        intros = {
            "fr": "Évaluons votre résilience et intelligence émotionnelle.",
            "en": "Let's evaluate your resilience and emotional intelligence.",
            "ar": "دعنا نقيم مرونتك وذكاءك العاطفي."
        }
    else:
        intros = {"fr": "Analysons maintenant ce trait.", "en": "Let's now analyze this trait.", "ar": "دعنا الآن نحلل هذه السمة."}
    
    return intros.get(language, intros["fr"])


def generate_question(trait, question_number, previous_answers, previous_score, language, assessment_type="big_five"):
    """Generate question using FALLBACK ONLY"""
    try:
        questions = FALLBACK_QUESTIONS.get(language, FALLBACK_QUESTIONS['fr'])
        
        if assessment_type in ['bien_etre', 'resilience_ie']:
            q_list = questions.get(assessment_type, [])
        else:
            q_list = questions.get(assessment_type, {}).get(trait, [])
        
        if not q_list:
            return "Décrivez votre expérience dans ce domaine."
        
        # Cycle through questions
        idx = (question_number - 1) % len(q_list)
        return q_list[idx]
    except Exception as e:
        logger.error(f"Fallback question error: {e}")
        return "Décrivez votre expérience dans ce domaine."


def analyze_answer(answer_text, trait, all_answers_for_trait, language, assessment_type="big_five"):
    """Analyze answer using FALLBACK scoring only"""
    try:
        score = fallback_score_answer(answer_text, trait, assessment_type, language)
        return score
    except Exception as e:
        logger.error(f"Error scoring answer: {e}")
        # Emergency fallback based on length
        word_count = len(answer_text.split())
        if word_count < 10:
            return 2
        elif word_count < 30:
            return 3
        elif word_count < 60:
            return 4
        else:
            return 5


def generate_enhanced_detailed_analysis(trait, all_answers, total_score, language, assessment_type="big_five"):
    """Generate detailed analysis using FALLBACK only"""
    try:
        return fallback_generate_analysis(trait, total_score, assessment_type, language)
    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        return {
            "observations": f"Analyse basée sur vos réponses pour {trait}. Score: {total_score}/10.",
            "points_forts": [f"Expression du trait {trait}", "Cohérence des réponses"],
            "zones_developpement": ["Opportunités d'amélioration", "Développement continu"]
        }


def generate_score_explanations(all_assessment_scores, language="fr"):
    """Generate score explanations using FALLBACK"""
    explanations = {}
    
    try:
        # Big Five
        if "big_five" in all_assessment_scores:
            for trait, data in all_assessment_scores["big_five"].items():
                score = data.get('score', 0)
                key = f"big_five_{trait}"
                explanations[key] = fallback_score_explanation(score, trait, 'big_five', language)
        
        # DISC
        if "disc" in all_assessment_scores:
            for style, data in all_assessment_scores["disc"].items():
                score = data.get('score', 0)
                key = f"disc_{style}"
                explanations[key] = fallback_score_explanation(score, style, 'disc', language)
        
        # Bien-être
        if "bien_etre" in all_assessment_scores:
            score = all_assessment_scores["bien_etre"].get('score', 0)
            explanations["bien_etre"] = fallback_score_explanation(score, 'bien_etre', 'bien_etre', language)
        
        # Resilience
        if "resilience_ie" in all_assessment_scores:
            score = all_assessment_scores["resilience_ie"].get('score', 0)
            explanations["resilience_ie"] = fallback_score_explanation(score, 'resilience_ie', 'resilience_ie', language)
    
    except Exception as e:
        logger.error(f"Error generating explanations: {e}")
    
    return explanations


def should_recommend_coaching(all_assessment_scores, language):
    """Determine if coaching should be recommended"""
    coaching_indicators = []
    
    try:
        if "big_five" in all_assessment_scores:
            big_five_scores = all_assessment_scores["big_five"]
            low_scores = [trait for trait, data in big_five_scores.items() if data.get('score', 5) <= 4]
            if len(low_scores) >= 2:
                coaching_indicators.append("multiple_big_five_challenges")
        
        if "bien_etre" in all_assessment_scores:
            if all_assessment_scores["bien_etre"].get('score', 5) <= 4:
                coaching_indicators.append("low_wellbeing")
        
        if "resilience_ie" in all_assessment_scores:
            if all_assessment_scores["resilience_ie"].get('score', 5) <= 4:
                coaching_indicators.append("low_resilience")
    except Exception as e:
        logger.error(f"Error in coaching recommendation: {e}")
    
    messages = {
        "fr": "Nous recommandons une session avec un coach NextMind pour vous accompagner.",
        "en": "We recommend a coaching session with a NextMind coach to support you.",
        "ar": "نوصي بجلسة مع مدرب NextMind لدعمك."
    }
    
    return {
        "should_recommend": len(coaching_indicators) > 0,
        "reasons": coaching_indicators,
        "message": messages.get(language, messages["fr"]),
        "priority": "high" if len(coaching_indicators) >= 3 else "medium" if len(coaching_indicators) >= 2 else "normal"
    }