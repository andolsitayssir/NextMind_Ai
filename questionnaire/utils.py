import openai
import os
from openai import OpenAI
import json
import time
import random
from functools import wraps
import logging

# Configure minimal logging - ONLY ERRORS
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger("openai").setLevel(logging.CRITICAL)
logging.getLogger("openai._base_client").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.connection").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.http11").setLevel(logging.CRITICAL)
logging.getLogger("django.request").setLevel(logging.WARNING)
logging.getLogger("django.server").setLevel(logging.WARNING)

# Configure OpenAI client for Groq
try:
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")
    client = None

# Assessment structure
ASSESSMENT_STRUCTURE = {
    "big_five": {
        "traits": ["ouverture", "conscienciosité", "extraversion", "agréabilité", "stabilité émotionnelle"],
        "questions_per_trait": 2,
        "max_score_per_trait": 10,
        "levels": {
            "faible": (2, 4),
            "modéré": (5, 7),
            "élevé": (8, 10)
        }
    },
    "disc": {
        "styles": ["dominant", "influent", "stable", "conforme"],
        "questions_total": 8,
        "scoring": "choice_based"
    },
    "bien_etre": {
        "questions_total": 2,
        "max_score": 10,
        "levels": {
            "faible": (2, 4),
            "modéré": (5, 7),
            "élevé": (8, 10)
        }
    },
    "resilience_ie": {
        "questions_total": 2,
        "max_score": 10,
        "levels": {
            "faible": (2, 4),
            "modéré": (5, 7),
            "élevé": (8, 10)
        }
    }
}

# Big Five traits configuration
TRAITS_CONFIG = {
    "ouverture": {
        "fr": "Ouverture à l'expérience - créativité, curiosité, imagination",
        "en": "Openness to Experience - creativity, curiosity, imagination",
        "ar": "الانفتاح على التجربة - الإبداع والفضول والخيال",
        "descriptions": {
            "faible": {
                "fr": "Préfère les routines, peu d'intérêt pour la nouveauté ou les idées abstraites.",
                "en": "Prefers routines, little interest in novelty or abstract ideas.",
                "ar": "يفضل الروتين، اهتمام قليل بالجديد أو الأفكار المجردة."
            },
            "modéré": {
                "fr": "Ouvert(e) à certaines idées nouvelles mais avec prudence.",
                "en": "Open to some new ideas but with caution.",
                "ar": "منفتح على بعض الأفكار الجديدة ولكن بحذر."
            },
            "élevé": {
                "fr": "Très créatif(ve), curieux(se), attiré(e) par l'innovation et les expériences variées.",
                "en": "Very creative, curious, attracted to innovation and varied experiences.",
                "ar": "مبدع جداً، فضولي، منجذب للابتكار والتجارب المتنوعة."
            }
        }
    },
    "conscienciosité": {
        "fr": "Conscienciosité - organisation, discipline, persévérance",
        "en": "Conscientiousness - organization, discipline, perseverance",
        "ar": "الضمير - التنظيم والانضباط والمثابرة",
        "descriptions": {
            "faible": {
                "fr": "Peut manquer de rigueur, difficulté à respecter les délais ou à s'organiser.",
                "en": "May lack rigor, difficulty meeting deadlines or organizing.",
                "ar": "قد يفتقر للدقة، صعوبة في احترام المواعيد أو التنظيم."
            },
            "modéré": {
                "fr": "Responsable dans les tâches importantes, mais manque parfois de planification.",
                "en": "Responsible in important tasks, but sometimes lacks planning.",
                "ar": "مسؤول في المهام المهمة، ولكن يفتقر أحياناً للتخطيط."
            },
            "élevé": {
                "fr": "Très organisé(e), fiable, soucieux(se) de la qualité et de l'efficacité.",
                "en": "Very organized, reliable, concerned with quality and efficiency.",
                "ar": "منظم جداً، موثوق، مهتم بالجودة والكفاءة."
            }
        }
    },
    "extraversion": {
        "fr": "Extraversion - sociabilité, énergie, affirmation de soi",
        "en": "Extraversion - sociability, energy, assertiveness",
        "ar": "الانبساط - الاجتماعية والطاقة وتأكيد الذات",
        "descriptions": {
            "faible": {
                "fr": "Préfère travailler seul(e), réservé(e), peu énergique socialement.",
                "en": "Prefers working alone, reserved, low social energy.",
                "ar": "يفضل العمل وحيداً، متحفظ، طاقة اجتماعية منخفضة."
            },
            "modéré": {
                "fr": "A l'aise dans certaines interactions, mais aime aussi la solitude.",
                "en": "Comfortable in some interactions, but also enjoys solitude.",
                "ar": "مرتاح في بعض التفاعلات، ولكن يحب أيضاً الوحدة."
            },
            "élevé": {
                "fr": "Sociable, assertif(ve), prend l'initiative dans les groupes.",
                "en": "Sociable, assertive, takes initiative in groups.",
                "ar": "اجتماعي، حازم، يأخذ المبادرة في المجموعات."
            }
        }
    },
    "agréabilité": {
        "fr": "Agréabilité - coopération, confiance, empathie",
        "en": "Agreeableness - cooperation, trust, empathy",
        "ar": "الوداعة - التعاون والثقة والتعاطف",
        "descriptions": {
            "faible": {
                "fr": "Peut sembler distant(e), critique, peu conciliant(e).",
                "en": "May seem distant, critical, uncompromising.",
                "ar": "قد يبدو بعيداً، ناقداً، غير متصالح."
            },
            "modéré": {
                "fr": "Coopératif(ve), mais peut défendre fermement ses opinions.",
                "en": "Cooperative, but may firmly defend opinions.",
                "ar": "متعاون، ولكن قد يدافع بحزم عن آرائه."
            },
            "élevé": {
                "fr": "Empathique, à l'écoute, privilégie l'harmonie dans les relations.",
                "en": "Empathetic, good listener, prioritizes harmony in relationships.",
                "ar": "متعاطف، مستمع جيد، يعطي الأولوية للانسجام في العلاقات."
            }
        }
    },
    "stabilité émotionnelle": {
        "fr": "Stabilité émotionnelle - gestion du stress, équilibre émotionnel",
        "en": "Emotional Stability - stress management, emotional balance",
        "ar": "الاستقرار العاطفي - إدارة التوتر والتوازن العاطفي",
        "descriptions": {
            "faible": {
                "fr": "Stressé(e), sensible aux critiques, anxieux(se).",
                "en": "Stressed, sensitive to criticism, anxious.",
                "ar": "متوتر، حساس للنقد، قلق."
            },
            "modéré": {
                "fr": "Équilibré(e) mais réagit parfois fortement au stress.",
                "en": "Balanced but sometimes reacts strongly to stress.",
                "ar": "متوازن ولكن أحياناً يتفاعل بقوة مع التوتر."
            },
            "élevé": {
                "fr": "Calme, confiant(e), gère bien les émotions et les tensions.",
                "en": "Calm, confident, manages emotions and tensions well.",
                "ar": "هادئ، واثق، يدير المشاعر والتوترات بشكل جيد."
            }
        }
    }
}

# DISC Styles Configuration
DISC_CONFIG = {
    "dominant": {
        "fr": "Dominant (D) - Décideur, orienté résultats, directif",
        "en": "Dominant (D) - Decision-maker, results-oriented, directive",
        "ar": "مهيمن (D) - صانع قرار، موجه للنتائج، توجيهي",
        "description": {
            "fr": "Décideur, orienté résultats, directif. Aime les challenges et prendre le contrôle.",
            "en": "Decision-maker, results-oriented, directive. Likes challenges and taking control.",
            "ar": "صانع قرار، موجه للنتائج، توجيهي. يحب التحديات وأخذ السيطرة."
        }
    },
    "influent": {
        "fr": "Influent (I) - Charismatique, communicatif, inspirant",
        "en": "Influent (I) - Charismatic, communicative, inspiring",
        "ar": "مؤثر (I) - جذاب، تواصلي، ملهم",
        "description": {
            "fr": "Charismatique, communicatif, inspirant. Aime convaincre, motiver et être reconnu.",
            "en": "Charismatic, communicative, inspiring. Likes to convince, motivate and be recognized.",
            "ar": "جذاب، تواصلي، ملهم. يحب الإقناع والتحفيز والحصول على الاعتراف."
        }
    },
    "stable": {
        "fr": "Stable (S) - Loyal, calme, patient",
        "en": "Stable (S) - Loyal, calm, patient",
        "ar": "مستقر (S) - مخلص، هادئ، صبور",
        "description": {
            "fr": "Loyal, calme, patient. Préfère la stabilité, les relations harmonieuses et le travail d'équipe.",
            "en": "Loyal, calm, patient. Prefers stability, harmonious relationships and teamwork.",
            "ar": "مخلص، هادئ، صبور. يفضل الاستقرار والعلاقات المتناغمة والعمل الجماعي."
        }
    },
    "conforme": {
        "fr": "Conforme (C) - Précis, analytique, rigoureux",
        "en": "Compliant (C) - Precise, analytical, rigorous",
        "ar": "ملتزم (C) - دقيق، تحليلي، صارم",
        "description": {
            "fr": "Précis, analytique, rigoureux. Valorise les normes, la qualité et la méthode.",
            "en": "Precise, analytical, rigorous. Values standards, quality and method.",
            "ar": "دقيق، تحليلي، صارم. يقدر المعايير والجودة والطريقة."
        }
    }
}

# Well-being and Resilience configurations
WELLBEING_CONFIG = {
    "fr": "Bien-être au Travail - satisfaction, engagement, équilibre",
    "en": "Workplace Well-being - satisfaction, engagement, balance",
    "ar": "الرفاهة في العمل - الرضا والالتزام والتوازن",
    "descriptions": {
        "faible": {
            "fr": "Bien-être faible – risque de démotivation ou de surcharge",
            "en": "Low well-being – risk of demotivation or overload",
            "ar": "رفاهية منخفضة - خطر فقدان الدافع أو الإفراط في العبء"
        },
        "modéré": {
            "fr": "Bien-être modéré – présence de points à améliorer",
            "en": "Moderate well-being – areas for improvement present",
            "ar": "رفاهية متوسطة - وجود نقاط للتحسين"
        },
        "élevé": {
            "fr": "Bien-être élevé – engagement et satisfaction professionnelle",
            "en": "High well-being – engagement and professional satisfaction",
            "ar": "رفاهية عالية - الالتزام والرضا المهني"
        }
    }
}

RESILIENCE_CONFIG = {
    "fr": "Résilience et Intelligence Émotionnelle - adaptation, gestion émotionnelle",
    "en": "Resilience and Emotional Intelligence - adaptation, emotional management",
    "ar": "المرونة والذكاء العاطفي - التكيف وإدارة المشاعر",
    "descriptions": {
        "faible": {
            "fr": "Faible – difficultés à gérer émotions et imprévus",
            "en": "Low – difficulties managing emotions and unexpected events",
            "ar": "منخفض - صعوبات في إدارة المشاعر والأحداث غير المتوقعة"
        },
        "modéré": {
            "fr": "Modéré – bonnes bases, à renforcer pour plus de fluidité",
            "en": "Moderate – good foundation, needs strengthening for more fluidity",
            "ar": "متوسط - أسس جيدة، تحتاج للتقوية لمزيد من السلاسة"
        },
        "élevé": {
            "fr": "Élevé – maîtrise émotionnelle et bonne capacité d'adaptation",
            "en": "High – emotional mastery and good adaptation capacity",
            "ar": "عالي - إتقان عاطفي وقدرة جيدة على التكيف"
        }
    }
}

def get_level_from_score(score, assessment_type):
    """Determine level based on score and assessment type according to specifications"""
    if assessment_type == "big_five":
        levels = ASSESSMENT_STRUCTURE["big_five"]["levels"]
    elif assessment_type == "bien_etre":
        levels = ASSESSMENT_STRUCTURE["bien_etre"]["levels"]
    elif assessment_type == "resilience_ie":
        levels = ASSESSMENT_STRUCTURE["resilience_ie"]["levels"]
    else:
        return "modéré"
    
    for level, (min_score, max_score) in levels.items():
        if min_score <= score <= max_score:
            return level
    return "modéré"

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
        intros = {
            "fr": f"Analysons maintenant ce trait.",
            "en": f"Let's now analyze this trait.",
            "ar": f"دعنا الآن نحلل هذه السمة."
        }
    
    return intros.get(language, intros["fr"])


def get_level_from_score(score, assessment_type):
    """Get level description based on score"""
    if assessment_type in ['big_five', 'bien_etre', 'resilience_ie']:
        if score <= 4:
            return 'faible'
        elif score <= 7:
            return 'modéré'
        else:
            return 'élevé'
    elif assessment_type == 'disc':
        if score <= 3:
            return 'low'
        elif score <= 6:
            return 'medium'
        else:
            return 'high'
    return 'modéré'

def calculate_consistency(scores):
    """Calculate consistency of scores"""
    if len(scores) < 2:
        return 1.0
    
    # Calculate variance
    mean_score = sum(scores) / len(scores)
    variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
    
    # Convert to consistency (lower variance = higher consistency)
    consistency = max(0, 1 - (variance / 2))  # Normalize to 0-1 range
    return round(consistency, 2)

def generate_insights(user_data, language):
    """Generate psychological insights from the assessment"""
    total_responses = len(user_data['responses'])
    avg_response_time = sum(user_data['psychological_profile']['response_times']) / len(user_data['psychological_profile']['response_times']) if user_data['psychological_profile']['response_times'] else 0
    
    insights = {
        'fr': {
            'response_pattern': f'Vous avez maintenu un rythme de réponse de {avg_response_time:.1f}s en moyenne.',
            'behavioral_consistency': 'Vos comportements montrent une cohérence dans vos approches.',
            'development_areas': 'Nous avons identifié des domaines clés pour votre développement.'
        },
        'en': {
            'response_pattern': f'You maintained an average response time of {avg_response_time:.1f}s.',
            'behavioral_consistency': 'Your behaviors show consistency in your approaches.',
            'development_areas': 'We have identified key areas for your development.'
        },
        'ar': {
            'response_pattern': f'حافظت على متوسط وقت إجابة {avg_response_time:.1f}ث.',
            'behavioral_consistency': 'سلوكياتك تُظهر اتساقاً في مناهجك.',
            'development_areas': 'لقد حددنا مجالات رئيسية لتطويرك.'
        }
    }
    
    return insights.get(language, insights['fr'])

def generate_summary(user_data, language):
    """Generate assessment summary"""
    total_responses = len(user_data['responses'])
    avg_response_time = sum(user_data['psychological_profile']['response_times']) / len(user_data['psychological_profile']['response_times']) if user_data['psychological_profile']['response_times'] else 0
    
    summaries = {
        'fr': {
            'total_questions': f"Vous avez répondu à {total_responses} questions",
            'avg_time': f"Temps moyen de réponse: {avg_response_time:.1f} secondes",
            'completion_status': "Évaluation complétée avec succès"
        },
        'en': {
            'total_questions': f"You answered {total_responses} questions",
            'avg_time': f"Average response time: {avg_response_time:.1f} seconds",
            'completion_status': "Assessment completed successfully"
        },
        'ar': {
            'total_questions': f"أجبت على {total_responses} سؤالاً",
            'avg_time': f"متوسط وقت الإجابة: {avg_response_time:.1f} ثانية",
            'completion_status': "تم إكمال التقييم بنجاح"
        }
    }
    
    return summaries.get(language, summaries['fr'])

def analyze_behavioral_tone(answer_text, response_time):
    """Analyze behavioral patterns in answers"""
    text_lower = answer_text.lower()
    
    # Decision-making indicators
    decision_words = ['décide', 'choisis', 'planifie', 'organise', 'stratégie', 'méthode']
    if any(word in text_lower for word in decision_words):
        return 'decisive'
    
    # Collaborative indicators
    collaborative_words = ['équipe', 'ensemble', 'coopère', 'discute', 'collabore', 'partage']
    if any(word in text_lower for word in collaborative_words):
        return 'collaborative'
    
    # Analytical indicators
    analytical_words = ['analyse', 'évalue', 'examine', 'compare', 'considère', 'réfléchis']
    if any(word in text_lower for word in analytical_words):
        return 'analytical'
    
    # Innovation indicators
    innovation_words = ['innove', 'crée', 'développe', 'imagine', 'nouveau', 'différent']
    if any(word in text_lower for word in innovation_words):
        return 'innovative'
    
    # Response time patterns
    if response_time < 15:
        return 'quick_decision'
    elif response_time > 45:
        return 'thoughtful'
    
    return 'balanced'

def analyze_response_quality(answer_text, response_time):
    """Analyze response quality based on behavioral depth"""
    answer_length = len(answer_text)
    
    # High quality: detailed behavioral descriptions
    if answer_length > 120 and response_time > 20:
        return 'high_quality'
    # Medium quality: good behavioral content
    elif answer_length > 60 and response_time > 10:
        return 'medium_quality'
    # Basic quality: minimal but present
    elif answer_length > 20:
        return 'basic_quality'
    else:
        return 'low_quality'

def get_next_step(user_data):
    """Determine the next step in the assessment process"""
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait')
    current_question = user_data['current_question_number']
    
    # Assessment configuration
    ASSESSMENTS = {
        'big_five': {
            'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
            'questions_per_trait': 2,
        },
        'disc': {
            'traits': ['dominant', 'influent', 'stable', 'conforme'],
            'questions_per_trait': 2,
        },
        'bien_etre': {
            'questions_total': 2,
        },
        'resilience_ie': {
            'questions_total': 2,
        }
    }
    
    # Default return value
    result = {'completed': False}
    
    try:
        if current_assessment == 'big_five':
            if current_question >= ASSESSMENTS['big_five']['questions_per_trait']:
                # Move to next trait
                progress = user_data['assessment_progress']['big_five']
                progress['completed_traits'].append(current_trait)
                progress['current_trait_index'] += 1
                
                if progress['current_trait_index'] < len(ASSESSMENTS['big_five']['traits']):
                    # Next Big Five trait
                    next_trait = ASSESSMENTS['big_five']['traits'][progress['current_trait_index']]
                    result.update({
                        'current_assessment': 'big_five',
                        'current_trait': next_trait,
                        'current_question_number': 1
                    })
                else:
                    # Move to DISC
                    result.update({
                        'current_assessment': 'disc',
                        'current_trait': ASSESSMENTS['disc']['traits'][0],
                        'current_question_number': 1
                    })
            else:
                # Next question for same trait
                result.update({
                    'current_question_number': current_question + 1
                })
        
        elif current_assessment == 'disc':
            if current_question >= ASSESSMENTS['disc']['questions_per_trait']:
                progress = user_data['assessment_progress']['disc']
                progress['completed_traits'].append(current_trait)
                progress['current_trait_index'] += 1
                
                if progress['current_trait_index'] < len(ASSESSMENTS['disc']['traits']):
                    # Next DISC style
                    next_trait = ASSESSMENTS['disc']['traits'][progress['current_trait_index']]
                    result.update({
                        'current_assessment': 'disc',
                        'current_trait': next_trait,
                        'current_question_number': 1
                    })
                else:
                    # Move to Well-being
                    result.update({
                        'current_assessment': 'bien_etre',
                        'current_trait': 'bien_etre',
                        'current_question_number': 1
                    })
            else:
                result.update({
                    'current_question_number': current_question + 1
                })
        
        elif current_assessment == 'bien_etre':
            if current_question >= ASSESSMENTS['bien_etre']['questions_total']:
                # Move to Resilience
                result.update({
                    'current_assessment': 'resilience_ie',
                    'current_trait': 'resilience_ie',
                    'current_question_number': 1
                })
            else:
                result.update({
                    'current_question_number': current_question + 1
                })
        
        elif current_assessment == 'resilience_ie':
            if current_question >= ASSESSMENTS['resilience_ie']['questions_total']:
                # All assessments completed
                result.update({'completed': True})
            else:
                result.update({
                    'current_question_number': current_question + 1
                })
        
        else:
            # Unknown assessment, mark as completed
            result.update({'completed': True})
    
    except Exception as e:
        logger.error(f"Error in get_next_step: {e}")
        result.update({'completed': True})
    
    return result

def calculate_total_questions():
    """Calculate total number of questions across all assessments"""
    total = 0
    total += 5 * 2  # 5 Big Five traits × 2 questions
    total += 4 * 2  # 4 DISC styles × 2 questions  
    total += 2      # 2 well-being questions
    total += 2      # 2 resilience questions
    return total    # Total: 18 questions

def get_assessment_name(assessment_type, language):
    """Get localized assessment name"""
    names = {
        'big_five': {
            'fr': 'Big Five',
            'en': 'Big Five', 
            'ar': 'العوامل الخمسة'
        },
        'disc': {
            'fr': 'DISC',
            'en': 'DISC',
            'ar': 'DISC'
        },
        'bien_etre': {
            'fr': 'Bien-être',
            'en': 'Well-being',
            'ar': 'الرفاهة'
        },
        'resilience_ie': {
            'fr': 'Résilience & IE',
            'en': 'Resilience & EI',
            'ar': 'المرونة والذكاء العاطفي'
        }
    }
    return names.get(assessment_type, {}).get(language, assessment_type)

# Add retry decorator with exponential backoff
def retry_with_backoff(max_retries=2, backoff_factor=1):
    """Decorator to retry API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "503" in str(e) or "Service unavailable" in str(e):
                        if attempt == max_retries - 1:
                            logger.error(f"All retries failed for {func.__name__}: {e}")
                            raise e
                        
                        wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time:.2f}s: {e}")
                        time.sleep(wait_time)
                    else:
                        raise e
            return None
        return wrapper
    return decorator

# Main generate_question function - API only
@retry_with_backoff(max_retries=2, backoff_factor=1)
def generate_question(trait, question_number, previous_answers, previous_score, language, assessment_type="big_five"):
    """Generate dynamic behavioral questions using AI"""
    if not client:
        raise Exception("No Groq client available")
    
    context = ""
    if previous_answers:
        latest_answer = previous_answers[-1] if previous_answers else ""
        context = f"Last answer: \"{latest_answer[:100]}...\"\n\n"
        if len(previous_answers) >= 1:
            context += f"PREVIOUS TOPICS COVERED: {len(previous_answers)} previous answers\n"
            context += f"AVOID REPETITION with previous themes\n\n"
    
    score_context = ""
    if previous_score is not None:
        if previous_score <= 2:
            score_context = f"Previous score: {previous_score} (Low). Generate a question to explore reasons or factors limiting {trait}."
        elif previous_score == 3:
            score_context = f"Previous score: {previous_score} (Moderate). Generate a question to clarify situational factors affecting {trait}."
        elif previous_score >= 4:
            score_context = f"Previous score: {previous_score} (High). Generate a question to identify strategies or strengths for {trait}."

    prompts = {
        "fr": f"""Tu es un psychologue expert. Génère UNE question comportementale pour analyser "{trait}" (question {question_number}/2).

{context}{score_context}

STYLE REQUIS:
- Question situationnelle et comportementale (10-15 mots)
- Explore les ACTIONS, DÉCISIONS, PRÉFÉRENCES, STRATÉGIES
- VARIE les débuts: "Décrivez votre...", "Quelle est votre approche...", "Préférez-vous...", "Dans quelles situations...", "Comment gérez-vous..."
- Focus sur comportements concrets et choix réels pour aider un coach psychologique
- ÉVITE: "Comment vous sentez-vous", "Que faites-vous quand", questions émotionnelles
- ANALYSE: situations professionnelles, prises de décision, méthodes de travail
- ADAPTE: selon le score précédent, explore raisons (faible), contexte (modéré), ou forces (élevé)

Réponds UNIQUEMENT avec la question comportementale.""",
        "en": f"""You are an expert psychologist. Generate ONE behavioral question to analyze "{trait}" (question {question_number}/2).

{context}{score_context}

REQUIRED STYLE:
- Situational and behavioral question (10-15 words)
- Explore ACTIONS, DECISIONS, PREFERENCES, STRATEGIES
- VARY beginnings: "Describe your...", "What's your approach...", "Do you prefer...", "In what situations...", "How do you manage..."
- Focus on concrete behaviors and real choices to aid a psychological coach
- AVOID: "How do you feel", "What do you do when", emotional questions
- ANALYZE: professional situations, decision-making, work methods
- ADAPT: based on previous score, explore reasons (low), context (moderate), or strengths (high)

Respond ONLY with the behavioral question.""",
        "ar": f"""أنت خبير نفسي. أنشئ سؤالاً سلوكياً واحداً لتحليل "{trait}" (السؤال {question_number}/2).

{context}{score_context}

النمط المطلوب:
- سؤال موقفي وسلوكي (10-15 كلمة)
- استكشف الأفعال والقرارات والتفضيلات والاستراتيجيات
- نوع البدايات: "صف طريقتك...", "ما منهجك...", "هل تفضل...", "في أي مواقف...", "كيف تدير..."
- التركيز على السلوكيات الملموسة والخيارات الحقيقية لمساعدة مدرب نفسي
- تجنب: "كيف تشعر", "ماذا تفعل عندما", الأسئلة العاطفية
- التحليل: المواقف المهنية، اتخاذ القرارات، طرق العمل
- التكيف: بناءً على النتيجة السابقة، استكشف الأسباب (منخفض)، السياق (متوسط)، أو نقاط القوة (عالي)

أجب فقط بالسؤال السلوكي."""
    }

    prompt = prompts.get(language, prompts["fr"])

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.7,
    )
    
    if response.choices and response.choices[0].message:
        question = response.choices[0].message.content.strip()
        
        # Clean up the question
        question = question.replace('"', '').replace("'", "'")
        if not question.endswith('?'):
            question += '?'
        
        return question
    else:
        raise Exception("No response content from Groq API")

# Analyze answer function - API only
@retry_with_backoff(max_retries=2, backoff_factor=1)
def analyze_answer(answer_text, trait, all_answers_for_trait, language, assessment_type="big_five"):
    """Analyze answers using AI"""
    if not client:
        raise Exception("No Groq client available")
    
    context = ""
    if all_answers_for_trait:
        context = f"All previous answers for trait '{trait}':\n"
        for i, ans in enumerate(all_answers_for_trait, 1):
            context += f"Answer {i}: {ans}\n"
        context += "\n"
    
    prompts = {
        "fr": f"""Tu es un psychologue expert en analyse comportementale. Analyse cette réponse pour le trait "{trait}":

{context}Nouvelle réponse: "{answer_text}"

ANALYSE COMPORTEMENTALE:
- Évalue les stratégies, décisions et approches décrites
- Identifie les patterns comportementaux révélés
- Analyse la cohérence des actions avec le trait {trait}

Score de 1 à 5:
1 = Comportements opposés au trait
2 = Faible manifestation comportementale
3 = Manifestation modérée
4 = Forte manifestation comportementale 
5 = Très forte manifestation avec stratégies claires

Réponds uniquement par un chiffre de 1 à 5.""",
        "en": f"""You are an expert psychologist in behavioral analysis. Analyze this answer for trait "{trait}":

{context}New answer: "{answer_text}"

BEHAVIORAL ANALYSIS:
- Evaluate described strategies, decisions and approaches
- Identify revealed behavioral patterns
- Analyze consistency of actions with trait {trait}

Score 1 to 5:
1 = Behaviors opposite to trait
2 = Low behavioral manifestation
3 = Moderate manifestation
4 = Strong behavioral manifestation
5 = Very strong manifestation with clear strategies

Respond only with a number from 1 to 5.""",
        "ar": f"""أنت خبير نفسي في التحليل السلوكي. حلل هذه الإجابة للسمة "{trait}":

{context}إجابة جديدة: "{answer_text}"

التحليل السلوكي:
- قيّم الاستراتيجيات والقرارات والمناهج الموصوفة
- حدد الأنماط السلوكية المكشوفة
- حلل اتساق الأفعال مع السمة {trait}

نتيجة من 1 إلى 5:
1 = سلوكيات معاكسة للسمة
2 = مظهر سلوكي ضعيف
3 = مظهر متوسط
4 = مظهر سلوكي قوي
5 = مظهر قوي جداً مع استراتيجيات واضحة

أجب برقم فقط من 1 إلى 5."""
    }
    
    prompt = prompts.get(language, prompts["fr"])

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.3,
    )
    score = int(response.choices[0].message.content.strip())
    return max(1, min(5, score))

# Generate detailed analysis - API only
@retry_with_backoff(max_retries=2, backoff_factor=1)
def generate_detailed_analysis(trait, all_answers, total_score, language, assessment_type="big_five"):
    """Generate detailed analysis using AI"""
    if not client:
        raise Exception("No Groq client available")
    
    level = get_level_from_score(total_score, assessment_type)
    
    context = f"All answers for '{trait}' (Assessment: {assessment_type}):\n"
    for i, answer in enumerate(all_answers, 1):
        context += f"Answer {i}: {answer}\n"
    
    # Check if coaching is needed
    needs_coaching = total_score <= 4  # Low scores need coaching
    
    prompts = {
        "fr": f"""Tu es un psychologue expert. Analyse "{trait}" basé sur ces réponses avec un ton direct et personnel:

{context}

Score total: {total_score} (Niveau: {level})

Génère une analyse DIRECTE et PERSONNELLE avec "vous" qui inclut:

1. **Ce que nous observons** (2-3 phrases courtes commençant par "Vous" ou "Vos réponses"):
   - "Vous démontrez..." ou "Vous tendez à..." ou "Vos réponses révèlent..."

2. **Points forts** (2-3 points courts avec tirets):
   - "Vous maîtrisez bien..."
   - "Vous savez..."
   - "Vous êtes capable de..."

3. **Points à améliorer** (2-3 points courts avec tirets):
   - "Vous pourriez développer..."
   - "Vous bénéficieriez de..."
   - "Vous gagnerriez à..."

4. **Conseils pratiques** (2-3 suggestions courtes):
   - "Nous vous recommandons de..."
   - "Essayez de..."
   - "Concentrez-vous sur..."

{f"5. **Coaching recommandé** : Si score faible, dire 'Nous recommandons de discuter ce point avec un coach NextMind pour développer vos compétences.'" if needs_coaching else ""}

Si les réponses sont vagues ou peu claires, mentionner: "Vos réponses manquent de clarté, nous aurions besoin de plus de détails."

Format ta réponse en JSON avec les clés : "observations", "points_forts", "points_faibles", "conseils"{', "coaching_recommande": true' if needs_coaching else ', "coaching_recommande": false'}

Réponds uniquement avec le JSON.""",
        
        "en": f"""You are an expert psychologist. Analyze "{trait}" based on these answers with a direct and personal tone:

{context}

Total score: {total_score} (Level: {level})

Generate a DIRECT and PERSONAL analysis using "you" that includes:

1. **What we observe** (2-3 short sentences starting with "You" or "Your responses"):
   - "You demonstrate..." or "You tend to..." or "Your responses reveal..."

2. **Strengths** (2-3 short bullet points):
   - "You master well..."
   - "You know how to..."
   - "You are capable of..."

3. **Areas for improvement** (2-3 short bullet points):
   - "You could develop..."
   - "You would benefit from..."
   - "You would gain from..."

4. **Practical advice** (2-3 short suggestions):
   - "We recommend you..."
   - "Try to..."
   - "Focus on..."

{f"5. **Coaching recommended** : If low score, say 'We recommend discussing this point with a NextMind coach to develop your skills.'" if needs_coaching else ""}

If answers are vague or unclear, mention: "Your answers lack clarity, we would need more details."

Format your response as JSON with keys: "observations", "points_forts", "points_faibles", "conseils"{', "coaching_recommande": true' if needs_coaching else ', "coaching_recommande": false'}

Respond only with JSON.""",
        
        "ar": f"""أنت خبير نفسي. حلل "{trait}" بناءً على هذه الإجابات بنبرة مباشرة وشخصية:

{context}

النتيجة الإجمالية: {total_score} (المستوى: {level})

أنشئ تحليلاً مباشراً وشخصياً باستخدام "أنت" يتضمن:

1. **ما نلاحظه** (2-3 جمل قصيرة تبدأ بـ "أنت" أو "إجاباتك"):
   - "أنت تُظهر..." أو "أنت تميل إلى..." أو "إجاباتك تكشف..."

2. **نقاط القوة** (2-3 نقاط قصيرة):
   - "أنت تتقن..."
   - "أنت تعرف كيف..."
   - "أنت قادر على..."

3. **نقاط للتحسين** (2-3 نقاط قصيرة):
   - "يمكنك تطوير..."
   - "ستستفيد من..."
   - "ستكسب من..."

4. **نصائح عملية** (2-3 اقتراحات قصيرة):
   - "نوصيك بـ..."
   - "حاول أن..."
   - "ركز على..."

{f"5. **التدريب موصى به** : إذا كانت النتيجة منخفضة، قل 'نوصي بمناقشة هذه النقطة مع مدرب NextMind لتطوير مهاراتك.'" if needs_coaching else ""}

إذا كانت الإجابات غامضة أو غير واضحة، اذكر: "إجاباتك تفتقر للوضوح، نحتاج لمزيد من التفاصيل."

نسق إجابتك كـ JSON مع المفاتيح: "observations", "points_forts", "points_faibles", "conseils"{', "coaching_recommande": true' if needs_coaching else ', "coaching_recommande": false'}

أجب بـ JSON فقط."""
    }

    prompt = prompts.get(language, prompts["fr"])

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.6,
    )
    
    analysis_text = response.choices[0].message.content.strip()
    try:
        analysis = json.loads(analysis_text)
        return analysis
    except json.JSONDecodeError:
        raise Exception(f"Failed to parse JSON response: {analysis_text}")

def generate_detailed_results(user_data):
    """Generate comprehensive results with detailed psychological analysis"""
    results = {}
    responses = user_data['responses']
    
    # Big Five results with enhanced analysis
    big_five_results = {}
    for trait in ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle']:
        trait_responses = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if trait_responses:
            scores = [r['score'] for r in trait_responses]
            avg_score = sum(scores) / len(scores)
            total_score = avg_score * 2  # Scale to 10
            
            # Generate enhanced detailed analysis using AI
            detailed_analysis = generate_detailed_analysis(
                trait=trait,
                all_answers=[r['text'] for r in trait_responses],
                total_score=total_score,
                language=user_data['language'],
                assessment_type='big_five'
            )
            
            big_five_results[trait] = {
                'score': round(total_score, 1),
                'total_score': round(total_score, 1),
                'level': get_level_from_score(total_score, 'big_five'),
                'responses': trait_responses,
                'detailed_analysis': detailed_analysis,
                'individual_scores': scores,
                'consistency': calculate_consistency(scores),
                'description': detailed_analysis.get('observations', f'Analysis for {trait}'),
                'coaching_needed': detailed_analysis.get('coaching_recommande', False)
            }
    
    results['big_five'] = big_five_results
    
    # DISC results with enhanced analysis
    disc_results = {}
    for style in ['dominant', 'influent', 'stable', 'conforme']:
        style_responses = [r for r in responses if r['trait'] == style and r['assessment'] == 'disc']
        if style_responses:
            scores = [r['score'] for r in style_responses]
            avg_score = sum(scores) / len(scores)
            total_score = avg_score * 2  # Scale to 10
            
            detailed_analysis = generate_detailed_analysis(
                trait=style,
                all_answers=[r['text'] for r in style_responses],
                total_score=total_score,
                language=user_data['language'],
                assessment_type='disc'
            )
            
            disc_results[style] = {
                'score': round(total_score, 1),
                'total_score': round(total_score, 1),
                'preference_strength': 'high' if total_score >= 7 else 'medium' if total_score >= 4 else 'low',
                'responses': style_responses,
                'detailed_analysis': detailed_analysis,
                'individual_scores': scores,
                'consistency': calculate_consistency(scores),
                'description': detailed_analysis.get('observations', f'Analysis for {style}'),
                'coaching_needed': detailed_analysis.get('coaching_recommande', False)
            }
    
    results['disc'] = disc_results
    
    # Well-being results with enhanced analysis
    wellbeing_responses = [r for r in responses if r['assessment'] == 'bien_etre']
    if wellbeing_responses:
        scores = [r['score'] for r in wellbeing_responses]
        total_score = sum(scores) * 2.5  # Scale to 10
        
        detailed_analysis = generate_detailed_analysis(
            trait='bien_etre',
            all_answers=[r['text'] for r in wellbeing_responses],
            total_score=total_score,
            language=user_data['language'],
            assessment_type='bien_etre'
        )
        
        results['bien_etre'] = {
            'score': round(total_score, 1),
            'total_score': round(total_score, 1),
            'level': get_level_from_score(total_score, 'bien_etre'),
            'responses': wellbeing_responses,
            'detailed_analysis': detailed_analysis,
            'individual_scores': scores,
            'consistency': calculate_consistency(scores),
            'description': detailed_analysis.get('observations', f'Analysis for bien-être'),
            'coaching_needed': detailed_analysis.get('coaching_recommande', False)
        }
    
    # Resilience results with enhanced analysis
    resilience_responses = [r for r in responses if r['assessment'] == 'resilience_ie']
    if resilience_responses:
        scores = [r['score'] for r in resilience_responses]
        total_score = sum(scores) * 2.5  # Scale to 10
        
        detailed_analysis = generate_detailed_analysis(
            trait='resilience_ie',
            all_answers=[r['text'] for r in resilience_responses],
            total_score=total_score,
            language=user_data['language'],
            assessment_type='resilience_ie'
        )
        
        results['resilience_ie'] = {
            'score': round(total_score, 1),
            'total_score': round(total_score, 1),
            'level': get_level_from_score(total_score, 'resilience_ie'),
            'responses': resilience_responses,
            'detailed_analysis': detailed_analysis,
            'individual_scores': scores,
            'consistency': calculate_consistency(scores),
            'description': detailed_analysis.get('observations', f'Analysis for resilience'),
            'coaching_needed': detailed_analysis.get('coaching_recommande', False)
        }
    
    return results


def should_recommend_coaching(results, language):
    """Determine if coaching should be recommended"""
    low_scores = []
    total_low_scores = 0
    
    # Check all assessment results for low scores
    for assessment_name, assessment_data in results.items():
        if isinstance(assessment_data, dict):
            if assessment_name in ['big_five', 'disc']:
                for trait_name, trait_data in assessment_data.items():
                    if isinstance(trait_data, dict) and 'total_score' in trait_data:
                        if trait_data['total_score'] <= 4:
                            low_scores.append(f"{assessment_name}.{trait_name}")
                            total_low_scores += 1
            else:
                if 'total_score' in assessment_data and assessment_data['total_score'] <= 4:
                    low_scores.append(assessment_name)
                    total_low_scores += 1
    
    should_recommend = total_low_scores >= 2 or any(score <= 3 for assessment_data in results.values() 
                                                   if isinstance(assessment_data, dict) 
                                                   for trait_data in (assessment_data.values() if 'total_score' not in assessment_data else [assessment_data])
                                                   if isinstance(trait_data, dict) and trait_data.get('total_score', 5) <= 3)
    
    messages = {
        'fr': {
            'high': "Nous recommandons fortement un accompagnement personnalisé pour développer vos compétences.",
            'medium': "Un coaching pourrait vous aider à optimiser certains aspects de votre profil.",
            'low': "Votre profil montre de bonnes bases, un coaching peut consolider vos acquis."
        },
        'en': {
            'high': "We strongly recommend personalized coaching to develop your skills.",
            'medium': "Coaching could help you optimize certain aspects of your profile.",
            'low': "Your profile shows good foundations, coaching can consolidate your achievements."
        },
        'ar': {
            'high': "نوصي بشدة بالتدريب الشخصي لتطوير مهاراتك.",
            'medium': "يمكن أن يساعدك التدريب في تحسين جوانب معينة من ملفك الشخصي.",
            'low': "يُظهر ملفك الشخصي أسساً جيدة، يمكن للتدريب ترسيخ إنجازاتك."
        }
    }
    
    priority = 'high' if total_low_scores >= 3 else 'medium' if total_low_scores >= 2 else 'low'
    
    return {
        'should_recommend': should_recommend,
        'message': messages.get(language, messages['fr']).get(priority),
        'priority': priority,
        'reasons': low_scores
    }

