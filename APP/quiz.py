import openai
import os
from openai import OpenAI
import json
import logging
import re
import random

from dotenv import load_dotenv
load_dotenv()

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


try:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
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
                "en": "May lack discipline, with difficulty meeting deadlines or staying organized.",
                "ar": "قد يفتقر للدقة، صعوبة في احترام المواعيد أو التنظيم."
            },
            "modéré": {
                "fr": "Responsable dans les tâches importantes, mais manque parfois de planification.",
                "en": "Responsible with important tasks, but sometimes lacks planning skills.",
                "ar": "مسؤول في المهام المهمة، ولكن يفتقر أحياناً للتخطيط."
            },
            "élevé": {
                "fr": "Très organisé(e), fiable, soucieux(se) de la qualité et de l'efficacité.",
                "en": "Very organized and reliable, with strong focus on quality and efficiency.",
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
                "en": "May appear distant, critical, and uncompromising.",
                "ar": "قد يبدو بعيداً، ناقداً، غير متصالح."
            },
            "modéré": {
                "fr": "Coopératif(ve), mais peut défendre fermement ses opinions.",
                "en": "Cooperative, but may firmly defend their opinions.",
                "ar": "متعاون، ولكن قد يدافع بحزم عن آرائه."
            },
            "élevé": {
                "fr": "Empathique, à l'écoute, privilégie l'harmonie dans les relations.",
                "en": "Empathetic and attentive, prioritizes harmony in relationships.",
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
                "en": "Often stressed, sensitive to criticism, and anxious.",
                "ar": "متوتر، حساس للنقد، قلق."
            },
            "modéré": {
                "fr": "Équilibré(e) mais réagit parfois fortement au stress.",
                "en": "Generally balanced but sometimes reacts strongly to stress.",
                "ar": "متوازن ولكن أحياناً يتفاعل بقوة مع التوتر."
            },
            "élevé": {
                "fr": "Calme, confiant(e), gère bien les émotions et les tensions.",
                "en": "Calm and confident, manages emotions and stress effectively.",
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
            "en": "Decisive, results-oriented, and directive. Enjoys challenges and taking control.",
            "ar": "صانع قرار، موجه للنتائج، توجيهي. يحب التحديات وأخذ السيطرة."
        }
    },
    "influent": {
        "fr": "Influent (I) - Charismatique, communicatif, inspirant",
        "en": "Influent (I) - Charismatic, communicative, inspiring",
        "ar": "مؤثر (I) - جذاب، تواصلي، ملهم",
        "description": {
            "fr": "Charismatique, communicatif, inspirant. Aime convaincre, motiver et être reconnu.",
            "en": "Charismatic, communicative, and inspiring. Enjoys convincing, motivating, and being recognized.",
            "ar": "جذاب، تواصلي، ملهم. يحب الإقناع والتحفيز والحصول على الاعتراف."
        }
    },
    "stable": {
        "fr": "Stable (S) - Loyal, calme, patient",
        "en": "Stable (S) - Loyal, calm, patient",
        "ar": "مستقر (S) - مخلص، هادئ، صبور",
        "description": {
            "fr": "Loyal, calme, patient. Préfère la stabilité, les relations harmonieuses et le travail d'équipe.",
            "en": "Loyal, calm, and patient. Prefers stability, harmonious relationships, and teamwork.",
            "ar": "مخلص، هادئ، صبور. يفضل الاستقرار والعلاقات المتناغمة والعمل الجماعي."
        }
    },
    "conforme": {
        "fr": "Conforme (C) - Précis, analytique, rigoureux",
        "en": "Compliant (C) - Precise, analytical, rigorous",
        "ar": "ملتزم (C) - دقيق، تحليلي، صارم",
        "description": {
            "fr": "Précis, analytique, rigoureux. Valorise les normes, la qualité et la méthode.",
            "en": "Precise, analytical, and rigorous. Values standards, quality, and methodology.",
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
            "en": "Low well-being – risk of demotivation or work overload",
            "ar": "رفاهية منخفضة - خطر فقدان الدافع أو الإفراط في العبء"
        },
        "modéré": {
            "fr": "Bien-être modéré – présence de points à améliorer",
            "en": "Moderate well-being – some areas need improvement",
            "ar": "رفاهية متوسطة - وجود نقاط للتحسين"
        },
        "élevé": {
            "fr": "Bien-être élevé – engagement et satisfaction professionnelle",
            "en": "High well-being – strong engagement and professional satisfaction",
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
            "en": "Moderate – good foundation that needs strengthening for greater fluidity",
            "ar": "متوسط - أسس جيدة، تحتاج للتقوية لمزيد من السلاسة"
        },
        "élevé": {
            "fr": "Élevé – maîtrise émotionnelle et bonne capacité d'adaptation",
            "en": "High – emotional mastery and strong adaptation capacity",
            "ar": "عالي - إتقان عاطفي وقدرة جيدة على التكيف"
        }
    }
}

def get_level_from_score(score, assessment_type, language="fr"):
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
    # Default fallback based on language preference
    if language == "en":
        return "moderate"
    elif language == "ar":
        return "متوسط"
    else:
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
    
    return intros.get(language, intros.get("en", intros.get("fr", "")))

def clean_arabic_text(text):
    """Clean Arabic text from foreign characters"""
    if not text:
        return text
    
    cleaned = ""
    for char in text:
        if ('\u0600' <= char <= '\u06FF' or char in ' .,;:!?()[]{}"\'-\n\r\t' or char.isdigit()):
            cleaned += char
    
    return cleaned.strip()

def extract_question_topics(previous_answers, language):
    """Extract key topics from previous answers to avoid repetition"""
    topics = []
    if not previous_answers:
        return topics
    
    for answer in previous_answers:
        if answer and len(answer) > 20:
            words = answer.lower().split()
            meaningful_words = [w for w in words if len(w) > 4 and w not in ['when', 'that', 'this', 'with', 'have', 'very', 'much', 'more', 'some', 'other']]
            topics.extend(meaningful_words[:5])
    
    return list(set(topics))




def generate_question(trait, question_number, previous_answers, previous_score, language, assessment_type="big_five"):
    """Generate dynamic behavioral questions based on previous score and answers"""
    if not client:
        logger.error("No API client available")
        return None
    
    context = ""
    if previous_answers:
        latest_answer = previous_answers[-1] if previous_answers else ""
        context = f"Previous answer summary: \"{latest_answer[:80]}...\"\n\n"
        if len(previous_answers) >= 1:
            context += f"PREVIOUS TOPICS COVERED: {len(previous_answers)} previous answers about {trait}\n"
            context += f"CRITICAL: Generate a COMPLETELY DIFFERENT question focusing on a NEW ASPECT of {trait}\n"
            context += f"AVOID REPETITION: Do NOT ask about the same situations, scenarios, or approaches already covered\n\n"
    
    score_context = ""
    if previous_score is not None:
        if previous_score <= 2:
            score_context = f"Previous score: {previous_score} (Low). Generate a NEW question to explore different factors limiting {trait}."
        elif previous_score == 3:
            score_context = f"Previous score: {previous_score} (Moderate). Generate a NEW question to explore DIFFERENT situational factors."
        elif previous_score >= 4:
            score_context = f"Previous score: {previous_score} (High). Generate a NEW question to identify DIFFERENT strengths or strategies."

    prompts = {
        "fr": f"""Tu es psychologue expert. Génère UNE question comportementale UNIQUE pour analyser "{trait}" (question {question_number}).

{context}{score_context}

IMPÉRATIF - ÉVITER LA RÉPÉTITION:
- Si des réponses précédentes existent, crée une question sur un ASPECT COMPLÈTEMENT DIFFÉRENT
- Change TOTALEMENT le contexte, la situation, l'angle d'approche, le début de la question
- Le début de la question doit être VARIÉ et CRÉATIF
- Utilise des débuts de question VARIÉS et créatifs

STYLE REQUIS:
- Question situationnelle et comportementale (10-15 mots)
- Explore ACTIONS, DÉCISIONS, PRÉFÉRENCES, STRATÉGIES dans des contextes VARIÉS
- Débuts créatifs: "Comment...", "Comment abordez-vous...", "Comment réagissez-vous quand...","Que faites-vous quand...","Préférez-vous...",ect...
- Contextes variés: travail, social, créatif, organisationnel, professionel, relationnel
- ÉVITE: répétition, questions similaires, même contexte que précédemment, mêmes mots dans la même question

QUALITÉ:
- Focus sur comportements concrets et choix réels
- Adapte selon le score: explore raisons (faible), contexte (modéré), ou forces (élevé)
- Question unique qui apporte une perspective nouvelle sur le trait

Réponds UNIQUEMENT avec la question comportementale en français.""",

        "en": f"""You are an expert psychologist. Generate ONE UNIQUE behavioral question to analyze "{trait}" (question {question_number}).

{context}{score_context}

IMPERATIVE - AVOID REPETITION:
- If previous answers exist, create a question about a COMPLETELY DIFFERENT aspect 
- TOTALLY change the context, situation, approach angle , question beginning
-Question beginning must be VARIED and CREATIVE
- Use VARIED and creative question beginnings

REQUIRED STYLE:
- Situational and behavioral question (10-15 words)
- Explore ACTIONS, DECISIONS, PREFERENCES, STRATEGIES in VARIED contexts
- Creative beginnings: "how do you...","what do you do when ...","Do you prefer...", "How do you react when...",ect...
- Varied contexts: work, social, creative, organizational, professional, relational
- AVOID: repetition, similar questions, same context as previously , same words in the same question

QUALITY:
- Focus on concrete behaviors and real choices
- Adapt based on score: explore reasons (low), context (moderate), or strengths (high)
- Unique question that brings a new perspective on the trait

Respond ONLY with the behavioral question in English.""",

        "ar": f"""أنت خبير نفسي. أنشئ سؤالاً سلوكياً واحداً فريداً لتحليل "{trait}" (السؤال {question_number}).

{context}{score_context}

إلزامي - تجنب التكرار:
- إذا كانت هناك إجابات سابقة، أنشئ سؤالاً حول جانب مختلف تماماً من السمة
- غيّر السياق والموقف ومنظور النهج تماماً
- يجب أن يكون بداية الاسئلة متنوعاً وإبداعياً
- استخدم بدايات أسئلة متنوعة وإبداعية

النمط المطلوب:
- سؤال موقفي وسلوكي (10-15 كلمة)
- استكشف الأفعال والقرارات والتفضيلات والاستراتيجيات في سياقات متنوعة
- "...بدايات إبداعية: "كيف تتصرف ...", "كيف تتعامل عندما...","هل تفضل...عندما","هل...","كيف  
-ياقات متنوعة: العمل،  الاجتماعي، الإبداعي، التنظيمي، العملي،  العلائقي
-   تجنب: التكرار، الأسئلة المماثلة، نفس السياق كما في السابق، نفس الكلمات في نفس السؤال  ، نفس بدايات الاسئلة
الجودة:
- التركيز على السلوكيات الملموسة والخيارات الحقيقية
- التكيف حسب النتيجة: استكشف الأسباب (منخفض)، السياق (متوسط)، أو نقاط القوة (عالي)
- سؤال فريد يجلب منظوراً جديداً للسمة

أجب فقط بالسؤال السلوكي بالعربية."""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7,
        )
        
        question = response.choices[0].message.content.strip()
        question = re.sub(r'^\d+[\.\)]\s*', '', question)
        question = re.sub(r'^Question\s*\d*\s*[:\-]?\s*', '', question, flags=re.IGNORECASE)
        question = question.strip('"\'`')
        
        if not question.endswith('?'):
            question += ' ?'
        
        # Validate the question
        validated_question = validate_question_quality(question, trait, language)
        return validated_question
        
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return None


def validate_question_quality(question, trait, language):
    """Validate question focuses on behavior and decision-making"""
    if not question:
        logger.error("Empty question received")
        return None
    
    question = question.strip()
    question_lower = question.lower()
    
    # Block emotional/story questions
    forbidden_patterns = [
        'comment vous sentez', 'comment réagissez',
        'how do you feel', 'how do you react',
        'كيف تشعر', 'كيف تتفاعل',
        'tell me about', 'parlez-moi de', 'حدثني عن',
        'share your experience', 'describe a time when', 'racontez une fois'
    ]
    
    for pattern in forbidden_patterns:
        if pattern in question_lower:
            logger.warning(f"BLOCKED EMOTIONAL/STORY QUESTION: {question}")
            return None
    
    
    behavioral_patterns = {
        "fr": ["quelle est votre", "préférez-vous",   "comment réagissez-vous quand", "pourquoi trouvez-vous", "quelles stratégies"],
        "en": ["what is your", "do you prefer", "what do you do when ","how do you manage", "how do you find", "what strategies", "why do you find"],
        "ar": ["ما هو", "هل تفضل", "كيف تدير", "كيف تتصرف عندما","ماذا تفعل عندما", "كيف تجد", "ما الاستراتيجيات"],
        "fr": [
            "quelle est votre", "préférez-vous", "comment gérez-vous", 
            "comment réagissez-vous quand", "pourquoi trouvez-vous", "quelles stratégies",
            "comment abordez", "que faites-vous", "comment conciliez", "comment équilibrez"
        ],
        "en": [
            "what is your", "do you prefer", "what do you do when", "how do you manage", 
            "how do you find", "what strategies", "why do you find", "how do you approach",
            "how do you balance", "when collaborating", "how do you handle", "when tasked",
            "how do you allocate", "when planning", "how do you prioritize"
        ],
        "ar": [
            "ما هو", "هل تفضل", "كيف تدير", "كيف تتصرف عندما", 
            "ماذا تفعل عندما", "كيف تجد", "ما الاستراتيجيات", 
            "كيف تُجري", "كيف تتعامل", "كيف توازن", "كيف تخصص",
            "عندما يكون", "عند التخطيط", "كيف تقسم"
        ]
    }
    
    patterns = behavioral_patterns.get(language, behavioral_patterns["fr"])
    is_behavioral = any(pattern in question_lower for pattern in patterns)
    
    # Additional check for question structure
    if language == "ar":
        arabic_behavioral_indicators = ["كيف", "ماذا", "متى", "هل"]
        has_arabic_structure = any(indicator in question_lower for indicator in arabic_behavioral_indicators)
        is_behavioral = is_behavioral or has_arabic_structure
    elif language == "en":
        english_behavioral_indicators = ["how", "what", "when", "do you", "would you", "where", "which"]
        has_english_structure = any(indicator in question_lower for indicator in english_behavioral_indicators)
        is_behavioral = is_behavioral or has_english_structure
    elif language == "fr":
        french_behavioral_indicators = ["comment", "que", "quand", "préférez-vous", "où", "quel"]
        has_french_structure = any(indicator in question_lower for indicator in french_behavioral_indicators)
        is_behavioral = is_behavioral or has_french_structure
    
    if not is_behavioral:
        logger.warning(f"NON-BEHAVIORAL QUESTION REJECTED: {question}")
        return None
    
    return question
def analyze_answer(answer_text, trait, all_answers_for_trait, language, assessment_type="big_five"):
    """Analyze answers focusing on behavioral patterns and decision-making"""
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

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.3,
        )
        score = int(response.choices[0].message.content.strip())
        return max(1, min(5, score))
    except Exception as e:
        logger.error(f"Error scoring answer: {e}")
        if not answer_text.strip():
            return 1
        elif len(answer_text.split()) < 10:
            return 2
        elif len(answer_text.split()) < 25:
            return 3
        elif len(answer_text.split()) < 50:
            return 4
        else:
            return 5

def generate_detailed_analysis(trait, all_answers, total_score, language, assessment_type="big_five"):
    """Generate detailed analysis according to specifications"""
    level = get_level_from_score(total_score, assessment_type)
    
    context = f"All answers for '{trait}' (Assessment: {assessment_type}):\n"
    for i, answer in enumerate(all_answers, 1):
        context += f"Answer {i}: {answer}\n"
    
    if assessment_type == "big_five":
        trait_description = TRAITS_CONFIG[trait]["descriptions"][level][language]
    elif assessment_type == "bien_etre":
        trait_description = WELLBEING_CONFIG["descriptions"][level][language]
    elif assessment_type == "resilience_ie":
        trait_description = RESILIENCE_CONFIG["descriptions"][level][language]
    else:
        trait_description = f"Score de {total_score} pour {trait}"
    
    prompts = {
        "fr": f"""Tu es un psychologue expert certifié. Génère une analyse psychologique COMPLÈTE et DÉTAILLÉE pour le trait "{trait}" basée sur ces réponses comportementales:

{context}

Score total: {total_score}/10 (Niveau: {level})
Description officielle: {trait_description}

STRUCTURE D'ANALYSE REQUISE - Format JSON:

1. **"observations"**: Analyse comportementale approfondie (150-200 mots)
   - Patterns comportementaux spécifiques identifiés
   - Cohérence/incohérence dans les réponses
   - Indicateurs psychologiques révélés
   - Style de réponse et auto-perception

2. **"score_explanation"**: Explication DÉTAILLÉE du score (100-150 mots)
   - Pourquoi ce score exact (pas plus haut/bas)
   - Éléments des réponses qui justifient chaque point
   - Comparaison avec les seuils de niveau
   - Facteurs déterminants du score final

3. **"behavioral_indicators"**: Indicateurs comportementaux concrets (80-100 mots)
   - Actions/décisions révélatrices
   - Stratégies utilisées
   - Réactions face aux défis
   - Préférences comportementales

4. **"strengths"**: Forces identifiées avec exemples (100-120 mots)
   - Capacités démontrées
   - Compétences naturelles
   - Avantages dans différents contextes
   - Exemples tirés des réponses

5. **"development_areas"**: Zones de développement avec justification (100-120 mots)
   - Aspects à améliorer avec preuves
   - Limitations identifiées
   - Défis potentiels
   - Écarts par rapport au niveau optimal

6. **"practical_recommendations"**: Conseils actionnables (120-150 mots)
   - 3-4 actions concrètes et spécifiques
   - Stratégies adaptées au profil
   - Exercices pratiques
   - Objectifs mesurables

7. **"professional_impact"**: Impact professionnel (80-100 mots)
   - Influence sur performance au travail
   - Interactions avec collègues
   - Leadership et collaboration
   - Adaptation organisationnelle

EXIGENCES QUALITÉ:
- Utilise des termes psychologiques précis
- Base CHAQUE affirmation sur les réponses données
- Sois spécifique, évite les généralités
- Ton professionnel et bienveillant
- JSON parfaitement formaté

Réponds UNIQUEMENT avec le JSON complet.""",

        "en": f"""You are a certified expert psychologist. Generate a COMPLETE and DETAILED psychological analysis for trait "{trait}" based on these behavioral responses:

{context}

Total score: {total_score}/10 (Level: {level})
Official description: {trait_description}

REQUIRED ANALYSIS STRUCTURE - JSON Format:

1. **"observations"**: In-depth behavioral analysis (150-200 words)
   - Specific behavioral patterns identified
   - Consistency/inconsistency in responses
   - Psychological indicators revealed
   - Response style and self-perception

2. **"score_explanation"**: DETAILED score explanation (100-150 words)
   - Why this exact score (not higher/lower)
   - Response elements justifying each point
   - Comparison with level thresholds
   - Key factors determining final score

3. **"behavioral_indicators"**: Concrete behavioral indicators (80-100 words)
   - Revealing actions/decisions
   - Strategies employed
   - Reactions to challenges
   - Behavioral preferences

4. **"strengths"**: Identified strengths with examples (100-120 words)
   - Demonstrated capabilities
   - Natural competencies
   - Advantages in different contexts
   - Examples from responses

5. **"development_areas"**: Development areas with justification (100-120 words)
   - Areas for improvement with evidence
   - Identified limitations
   - Potential challenges
   - Gaps from optimal level

6. **"practical_recommendations"**: Actionable advice (120-150 words)
   - 3-4 concrete and specific actions
   - Strategies tailored to profile
   - Practical exercises
   - Measurable objectives

7. **"professional_impact"**: Professional impact (80-100 words)
   - Influence on work performance
   - Interactions with colleagues
   - Leadership and collaboration
   - Organizational adaptation

QUALITY REQUIREMENTS:
- Use precise psychological terms
- Base EVERY statement on given responses
- Be specific, avoid generalities
- Professional and supportive tone
- Perfectly formatted JSON

Respond ONLY with the complete JSON.""",

        "ar": f"""أنت خبير نفسي معتمد. أنشئ تحليلاً نفسياً شاملاً ومفصلاً للسمة "{trait}" بناءً على هذه الإجابات السلوكية:

{context}

النتيجة الإجمالية: {total_score}/10 (المستوى: {level})
الوصف الرسمي: {trait_description}

هيكل التحليل المطلوب - تنسيق JSON:

1. **"observations"**: تحليل سلوكي معمق (150-200 كلمة)
   - الأنماط السلوكية المحددة المحددة
   - الاتساق/عدم الاتساق في الإجابات
   - المؤشرات النفسية المكشوفة
   - أسلوب الإجابة والإدراك الذاتي

2. **"score_explanation"**: شرح مفصل للنتيجة (100-150 كلمة)
   - لماذا هذه النتيجة بالضبط (وليس أعلى/أقل)
   - عناصر الإجابة التي تبرر كل نقطة
   - مقارنة مع عتبات المستوى
   - العوامل المحددة للنتيجة النهائية

3. **"behavioral_indicators"**: مؤشرات سلوكية ملموسة (80-100 كلمة)
   - الأفعال/القرارات الكاشفة
   - الاستراتيجيات المستخدمة
   - ردود الفعل تجاه التحديات
   - التفضيلات السلوكية

4. **"strengths"**: نقاط القوة المحددة مع أمثلة (100-120 كلمة)
   - القدرات المُظهرة
   - الكفاءات الطبيعية
   - المزايا في سياقات مختلفة
   - أمثلة من الإجابات

5. **"development_areas"**: مناطق التطوير مع التبرير (100-120 كلمة)
   - المجالات التي تحتاج تحسين مع أدلة
   - القيود المحددة
   - التحديات المحتملة
   - الفجوات من المستوى الأمثل

6. **"practical_recommendations"**: نصائح قابلة للتطبيق (120-150 كلمة)
   - 3-4 إجراءات ملموسة ومحددة
   - استراتيجيات مصممة للملف الشخصي
   - تمارين عملية
   - أهداف قابلة للقياس

7. **"professional_impact"**: التأثير المهني (80-100 كلمة)
   - التأثير على الأداء في العمل
   - التفاعلات مع الزملاء
   - القيادة والتعاون
   - التكيف التنظيمي

متطلبات الجودة:
- استخدم مصطلحات نفسية دقيقة
- اربط كل تأكيد بالإجابات المعطاة
- كن محدداً، تجنب العموميات
- نبرة مهنية وداعمة
- JSON منسق بشكل مثالي

أجب فقط بـ JSON الكامل."""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.7,
        )
        
        analysis_text = response.choices[0].message.content.strip()
        try:
            analysis = json.loads(analysis_text)
            return analysis
        except json.JSONDecodeError:
            return {
                "observations": f"Detailed behavioral analysis based on {len(all_answers)} comprehensive responses for {trait}. Response patterns indicate specific behavioral tendencies and decision-making preferences that provide insight into personality expression in various contexts.",
                "score_explanation": f"Score of {total_score}/10 places this trait in the {level} category according to official psychological assessment standards. This score reflects the consistency and strength of behavioral indicators demonstrated across multiple situational contexts.",
                "behavioral_indicators": f"Key behavioral patterns identified include specific approaches to challenges, decision-making strategies, and interpersonal interactions that characterize this trait level.",
                "strengths": f"Positive behavioral indicators and natural competencies identified through response analysis, demonstrating areas of psychological strength and adaptive capacity.",
                "development_areas": f"Areas identified for potential growth and development, based on behavioral patterns that could benefit from focused attention and practice.",
                "practical_recommendations": f"Specific, actionable strategies tailored to enhance trait expression and address development opportunities. Recommendations include concrete steps for improvement and skill building.",
                "professional_impact": f"This trait level influences workplace performance, team dynamics, leadership capacity, and overall organizational effectiveness in measurable ways."
            }
    except Exception as e:
        logger.error(f"Error generating detailed analysis: {e}")
        return {
            "observations": f"Comprehensive behavioral analysis for {trait} reveals specific patterns and psychological indicators based on detailed response evaluation. Multiple behavioral contexts were assessed to provide thorough personality insight.",
            "score_explanation": f"Score of {total_score}/10 reflects {level} level expression of this trait according to established psychological assessment criteria. This scoring accounts for behavioral consistency and strength of trait manifestation.",
            "behavioral_indicators": f"Analysis identifies key behavioral patterns, decision-making approaches, and situational responses that characterize this trait level and provide insight into personality expression.",
            "strengths": f"Individual demonstrates specific psychological strengths and adaptive behaviors associated with this trait, showing natural competencies and positive behavioral patterns.",
            "development_areas": f"Growth opportunities identified through behavioral analysis, highlighting areas where focused development could enhance trait expression and overall psychological functioning.",
            "practical_recommendations": f"Tailored development strategies including specific actions, skill-building exercises, and behavioral modifications designed to optimize trait expression and personal growth.",
            "professional_impact": f"This trait level significantly influences workplace effectiveness, interpersonal relationships, leadership capacity, and overall professional success in measurable ways."
        }

def should_recommend_coaching(all_assessment_scores, language):
    """Determine if coaching should be recommended based on complete profile according to specifications"""
    coaching_indicators = []
    
    if "big_five" in all_assessment_scores:
        big_five_scores = all_assessment_scores["big_five"]
        low_scores = [trait for trait, data in big_five_scores.items() if data['total_score'] <= 4]
        if len(low_scores) >= 2:
            coaching_indicators.append("multiple_big_five_challenges")
        if 'stabilité émotionnelle' in big_five_scores and big_five_scores['stabilité émotionnelle']['total_score'] <= 4:
            coaching_indicators.append("emotional_stability_low")
    
    if "bien_etre" in all_assessment_scores:
        wellbeing_score = all_assessment_scores["bien_etre"]["total_score"]
        if wellbeing_score <= 4:
            coaching_indicators.append("low_wellbeing")
    
    if "resilience_ie" in all_assessment_scores:
        resilience_score = all_assessment_scores["resilience_ie"]["total_score"]
        if resilience_score <= 4:
            coaching_indicators.append("low_resilience")
    
    recommendations = {
        "fr": {
            "should_recommend": len(coaching_indicators) > 0,
            "reasons": [],
            "message": "Nous recommandons une session avec un coach NextMind pour vous accompagner dans votre développement.",
            "priority": "normal"
        },
        "en": {
            "should_recommend": len(coaching_indicators) > 0,
            "reasons": [],
            "message": "We recommend a coaching session with a NextMind coach to support your development.",
            "priority": "normal"
        },
        "ar": {
            "should_recommend": len(coaching_indicators) > 0,
            "reasons": [],
            "message": "نوصي بجلسة مع مدرب NextMind لدعمك في تطويرك.",
            "priority": "normal"
        }
    }
    
    if len(coaching_indicators) >= 3:
        recommendations["fr"]["priority"] = "high"
        recommendations["en"]["priority"] = "high"
        recommendations["ar"]["priority"] = "high"
    elif len(coaching_indicators) >= 2:
        recommendations["fr"]["priority"] = "medium"
        recommendations["en"]["priority"] = "medium"
        recommendations["ar"]["priority"] = "medium"
    
    reason_mappings = {
        "emotional_stability_low": {
            "fr": "Gestion du stress et équilibre émotionnel",
            "en": "Stress management and emotional balance",
            "ar": "إدارة التوتر والتوازن العاطفي"
        },
        "multiple_big_five_challenges": {
            "fr": "Développement personnel sur plusieurs dimensions",
            "en": "Personal development across multiple dimensions",
            "ar": "التطوير الشخصي عبر عدة أبعاد"
        },
        "low_wellbeing": {
            "fr": "Amélioration du bien-être et de l'engagement",
            "en": "Well-being and engagement improvement",
            "ar": "تحسين الرفاهة والالتزام"
        },
        "low_resilience": {
            "fr": "Renforcement de la résilience et intelligence émotionnelle",
            "en": "Strengthening resilience and emotional intelligence",
            "ar": "تعزيز المرونة والذكاء العاطفي"
        }
    }
    
    for indicator in coaching_indicators:
        if indicator in reason_mappings:
            for lang in ["fr", "en", "ar"]:
                recommendations[lang]["reasons"].append(reason_mappings[indicator][lang])
    
    return recommendations.get(language, recommendations["fr"])

def generate_score_explanations(all_assessment_scores, language="fr"):
    """Generate one-line explanations for each score based on actual results"""
    explanations = {}
    
    # Big Five explanations
    if "big_five" in all_assessment_scores:
        big_five_scores = all_assessment_scores["big_five"]
        
        trait_explanations = {
            "fr": {
                "ouverture": {
                    "low": "Préférence pour les approches familières, résistance aux nouvelles expériences et au changement",
                    "medium": "Équilibre entre tradition et innovation, ouverture situationnelle aux nouveautés",
                    "high": "Forte curiosité intellectuelle, recherche active de nouvelles expériences et d'innovation"
                },
                "conscienciosité": {
                    "low": "Difficultés d'organisation et de planification, approche flexible mais parfois désordonnée",
                    "medium": "Organisation modérée avec quelques lacunes dans la planification systématique",
                    "high": "Excellent sens de l'organisation, planification rigoureuse et suivi méticuleux des objectifs"
                },
                "extraversion": {
                    "low": "Forte préférence pour l'introspection, évitement des interactions sociales intenses",
                    "medium": "Équilibre entre solitude et sociabilité selon les contextes et l'humeur",
                    "high": "Énergie tirée des interactions sociales, leadership naturel et communication aisée"
                },
                "agréabilité": {
                    "low": "Priorité aux intérêts personnels, approche directe parfois au détriment de l'harmonie",
                    "medium": "Équilibre entre coopération et affirmation de soi selon les situations",
                    "high": "Forte empathie, priorité à l'harmonie et au bien-être collectif"
                },
                "stabilité émotionnelle": {
                    "low": "Sensibilité importante au stress, fluctuations émotionnelles et réactivité élevée",
                    "medium": "Gestion émotionnelle variable, vulnérabilité au stress dans certaines situations",
                    "high": "Excellente régulation émotionnelle, calme et sérénité face aux défis"
                }
            },
            "en": {
                "ouverture": {
                    "low": "Preference for familiar approaches, resistance to new experiences and change",
                    "medium": "Balance between tradition and innovation, situational openness to novelty",
                    "high": "Strong intellectual curiosity, active pursuit of new experiences and innovation"
                },
                "conscienciosité": {
                    "low": "Organizational and planning difficulties, flexible but sometimes disorderly approach", 
                    "medium": "Moderate organization with some gaps in systematic planning",
                    "high": "Excellent organizational skills, rigorous planning and meticulous goal tracking"
                },
                "extraversion": {
                    "low": "Strong preference for introspection, avoidance of intense social interactions",
                    "medium": "Balance between solitude and sociability depending on context and mood",
                    "high": "Energy drawn from social interactions, natural leadership and easy communication"
                },
                "agréabilité": {
                    "low": "Priority on personal interests, direct approach sometimes at expense of harmony",
                    "medium": "Balance between cooperation and self-assertion depending on situations",
                    "high": "Strong empathy, priority on harmony and collective well-being"
                },
                "stabilité émotionnelle": {
                    "low": "High sensitivity to stress, emotional fluctuations and elevated reactivity",
                    "medium": "Variable emotional management, vulnerability to stress in certain situations", 
                    "high": "Excellent emotional regulation, calm and serenity when facing challenges"
                }
            },
            "ar": {
                "ouverture": {
                    "low": "تفضيل للطرق المألوفة، مقاومة للتجارب الجديدة والتغيير",
                    "medium": "توازن بين التقليد والابتكار، انفتاح ظرفي على الجديد",
                    "high": "فضول فكري قوي، سعي نشط للتجارب الجديدة والابتكار"
                },
                "conscienciosité": {
                    "low": "صعوبات في التنظيم والتخطيط، نهج مرن لكن أحياناً فوضوي",
                    "medium": "تنظيم متوسط مع بعض الثغرات في التخطيط المنهجي",
                    "high": "مهارات تنظيمية ممتازة، تخطيط صارم ومتابعة دقيقة للأهداف"
                },
                "extraversion": {
                    "low": "تفضيل قوي للاستبطان، تجنب التفاعلات الاجتماعية المكثفة",
                    "medium": "توازن بين العزلة والاجتماعية حسب السياق والمزاج",
                    "high": "طاقة مستمدة من التفاعلات الاجتماعية، قيادة طبيعية وتواصل سهل"
                },
                "agréabilité": {
                    "low": "أولوية للمصالح الشخصية، نهج مباشر أحياناً على حساب الانسجام",
                    "medium": "توازن بين التعاون وتأكيد الذات حسب المواقف",
                    "high": "تعاطف قوي، أولوية للانسجام والرفاهة الجماعية"
                },
                "stabilité émotionnelle": {
                    "low": "حساسية عالية للتوتر، تقلبات عاطفية وردود فعل مرتفعة",
                    "medium": "إدارة عاطفية متغيرة، عرضة للتوتر في مواقف معينة",
                    "high": "تنظيم عاطفي ممتاز، هدوء وطمأنينة عند مواجهة التحديات"
                }
            }
        }
        
        for trait, data in big_five_scores.items():
            score = data.get('total_score', 0)
            if score <= 4:
                level = "low"
            elif score <= 7:
                level = "medium"
            else:
                level = "high"
            
            trait_key = trait.lower().replace(' ', '_')
            if trait_key in trait_explanations[language]:
                explanations[f"big_five_{trait}"] = trait_explanations[language][trait_key][level]
    
    # DISC explanations
    if "disc" in all_assessment_scores:
        disc_scores = all_assessment_scores["disc"]
        
        disc_explanations = {
            "fr": {
                "dominant": {
                    "low": "Approche collaborative, évite le contrôle direct, préfère la consultation",
                    "medium": "Leadership situationnel, assertivité modérée selon les contextes",
                    "high": "Leadership fort, prise de décision rapide, orientation résultats"
                },
                "influent": {
                    "low": "Réticence à convaincre, préfère observer plutôt qu'influencer activement",
                    "medium": "Influence modérée, persuasion situationnelle selon l'aisance",
                    "high": "Grande capacité de persuasion, charisme naturel, motivation d'équipe"
                },
                "stable": {
                    "low": "Préférence pour la variété, difficultés avec les routines établies",
                    "medium": "Adaptabilité équilibrée entre stabilité et changement",
                    "high": "Recherche de stabilité, excellent dans les environnements prévisibles"
                },
                "conforme": {
                    "low": "Approche flexible des règles, moins d'emphasis sur la précision systématique",
                    "medium": "Respect modéré des procédures avec adaptation contextuelle",
                    "high": "Respect strict des normes, attention méticuleuse aux détails et procédures"
                }
            },
            "en": {
                "dominant": {
                    "low": "Collaborative approach, avoids direct control, prefers consultation",
                    "medium": "Situational leadership, moderate assertiveness depending on context",
                    "high": "Strong leadership, quick decision-making, results-oriented"
                },
                "influent": {
                    "low": "Reluctant to convince, prefers observing rather than actively influencing",
                    "medium": "Moderate influence, situational persuasion depending on comfort",
                    "high": "Great persuasion ability, natural charisma, team motivation"
                },
                "stable": {
                    "low": "Preference for variety, difficulties with established routines",
                    "medium": "Balanced adaptability between stability and change",
                    "high": "Seeks stability, excellent in predictable environments"
                },
                "conforme": {
                    "low": "Flexible approach to rules, less emphasis on systematic precision",
                    "medium": "Moderate respect for procedures with contextual adaptation",
                    "high": "Strict adherence to standards, meticulous attention to details and procedures"
                }
            },
            "ar": {
                "dominant": {
                    "low": "نهج تعاوني، يتجنب السيطرة المباشرة، يفضل الاستشارة",
                    "medium": "قيادة ظرفية، حزم متوسط حسب السياق",
                    "high": "قيادة قوية، اتخاذ قرار سريع، توجه للنتائج"
                },
                "influent": {
                    "low": "تردد في الإقناع، يفضل المراقبة على التأثير النشط",
                    "medium": "تأثير متوسط، إقناع ظرفي حسب الراحة",
                    "high": "قدرة إقناع عظيمة، كاريزما طبيعية، تحفيز الفريق"
                },
                "stable": {
                    "low": "تفضيل للتنوع، صعوبات مع الروتين الثابت",
                    "medium": "قابلية تكيف متوازنة بين الاستقرار والتغيير",
                    "high": "يسعى للاستقرار، ممتاز في البيئات المتوقعة"
                },
                "conforme": {
                    "low": "نهج مرن للقواعد، تركيز أقل على الدقة المنهجية",
                    "medium": "احترام متوسط للإجراءات مع تكيف سياقي",
                    "high": "التزام صارم بالمعايير، انتباه دقيق للتفاصيل والإجراءات"
                }
            }
        }
        
        for style, data in disc_scores.items():
            score = data.get('score', 0)  # DISC uses 'score' not 'total_score'
            if score <= 2:
                level = "low"
            elif score <= 3.5:
                level = "medium"
            else:
                level = "high"
            
            if style in disc_explanations[language]:
                explanations[f"disc_{style}"] = disc_explanations[language][style][level]
    
    # Well-being explanation
    if "bien_etre" in all_assessment_scores:
        wellbeing_score = all_assessment_scores["bien_etre"].get('score', 0)  # Use 'score' not 'total_score'
        wellbeing_explanations = {
            "fr": {
                "low": "Déséquilibre professionnel significatif, manque de satisfaction et d'engagement au travail",
                "medium": "Bien-être modéré avec des aspects à améliorer pour un équilibre optimal",
                "high": "Excellent équilibre travail-vie personnelle, forte satisfaction et engagement professionnel"
            },
            "en": {
                "low": "Significant professional imbalance, lack of satisfaction and work engagement",
                "medium": "Moderate well-being with aspects to improve for optimal balance",
                "high": "Excellent work-life balance, strong satisfaction and professional engagement"
            },
            "ar": {
                "low": "عدم توازن مهني كبير، نقص في الرضا والالتزام في العمل",
                "medium": "رفاهة متوسطة مع جوانب للتحسين لتوازن أمثل",
                "high": "توازن ممتاز بين العمل والحياة، رضا قوي والتزام مهني"
            }
        }
        
        if wellbeing_score <= 4:
            level = "low"
        elif wellbeing_score <= 7:
            level = "medium"
        else:
            level = "high"
        
        explanations["bien_etre"] = wellbeing_explanations[language][level]
    
    # Resilience explanation
    if "resilience_ie" in all_assessment_scores:
        resilience_score = all_assessment_scores["resilience_ie"].get('score', 0)  # Use 'score' not 'total_score'
        resilience_explanations = {
            "fr": {
                "low": "Difficultés importantes de gestion émotionnelle et d'adaptation aux défis",
                "medium": "Résilience modérée avec capacité d'adaptation variable selon les situations",
                "high": "Excellente résilience et intelligence émotionnelle, adaptation efficace aux changements"
            },
            "en": {
                "low": "Significant difficulties in emotional management and adapting to challenges",
                "medium": "Moderate resilience with variable adaptation capacity depending on situations",
                "high": "Excellent resilience and emotional intelligence, effective adaptation to changes"
            },
            "ar": {
                "low": "صعوبات كبيرة في الإدارة العاطفية والتكيف مع التحديات",
                "medium": "مرونة متوسطة مع قدرة تكيف متغيرة حسب المواقف",
                "high": "مرونة وذكاء عاطفي ممتاز، تكيف فعال مع التغييرات"
            }
        }
        
        if resilience_score <= 4:
            level = "low"
        elif resilience_score <= 7:
            level = "medium"
        else:
            level = "high"
        
        explanations["resilience_ie"] = resilience_explanations[language][level]
    
    return explanations

def analyze_and_score_answer_enhanced(answer_text, trait, previous_answers, language, assessment_type="big_five", psychological_context=None):
    """Enhanced scoring with psychological analysis including tone, timing, and user state"""
    if psychological_context is None:
        psychological_context = {}
    
    response_time = psychological_context.get('response_time', 0)
    answer_length = psychological_context.get('answer_length', len(answer_text))
    question_number = psychological_context.get('question_number', 1)
    user_patterns = psychological_context.get('user_patterns', {})
    
    context = f"""
CONTEXTE PSYCHOLOGIQUE COMPLET:
- Temps de réponse: {response_time:.1f} secondes
- Longueur de réponse: {answer_length} caractères  
- Question numéro: {question_number}
- Patterns utilisateur: {len(user_patterns.get('response_times', []))} réponses précédentes
"""
    
    if previous_answers:
        context += "Réponses précédentes pour ce trait:\n"
        for i, answer in enumerate(previous_answers, 1):
            context += f"R{i}: {answer}\n"
    
    prompts = {
        "fr": f"""Tu es un psychologue expert en évaluation psychométrique avancée. Analyse cette réponse pour "{trait}" avec une approche psychologique complète:

{context}

NOUVELLE RÉPONSE: "{answer_text}"

ANALYSE PSYCHOLOGIQUE REQUISE:
1. **Analyse du contenu**: Que révèle le contenu sur le trait {trait}?
2. **Analyse temporelle**: Le temps de réponse ({response_time:.1f}s) indique-t-il réflexion, impulsivité, hésitation?
3. **Analyse de l'engagement**: La longueur ({answer_length} chars) montre-t-elle implication ou détachement?
4. **Détection d'état émotionnel**: Quel est l'état psychologique apparent (calme, stressé, confiant, défensif)?
5. **Analyse de cohérence**: Cette réponse est-elle cohérente avec les précédentes?
6. **Patterns comportementaux**: Quels patterns psychologiques émergent?

SCORING PSYCHOLOGIQUE (1-5):
- Contenu: qualité et pertinence de la réponse
- Authenticité: sincérité vs réponses socialement désirables  
- Profondeur: niveau d'introspection et de réflexion
- Cohérence: consistance avec le profil émergent

Réponds en JSON avec:
{{
  "score": [1-5],
  "emotional_tone": "[calm/stressed/confident/defensive/engaged/detached]",
  "engagement_level": "[high/medium/low]",
  "authenticity": "[high/medium/low]", 
  "analysis": {{
    "content_analysis": "...",
    "temporal_analysis": "...",
    "psychological_state": "...",
    "coherence_assessment": "...",
    "behavioral_patterns": "..."
  }}
}}""",
        "en": f"""You are an expert psychologist in advanced psychometric assessment. Analyze this response for "{trait}" with a comprehensive psychological approach:

{context}

NEW RESPONSE: "{answer_text}"

REQUIRED PSYCHOLOGICAL ANALYSIS:
1. **Content analysis**: What does the content reveal about trait {trait}?
2. **Temporal analysis**: Does response time ({response_time:.1f}s) indicate reflection, impulsivity, hesitation?
3. **Engagement analysis**: Does length ({answer_length} chars) show involvement or detachment?
4. **Emotional state detection**: What is the apparent psychological state (calm, stressed, confident, defensive)?
5. **Coherence analysis**: Is this response coherent with previous ones?
6. **Behavioral patterns**: What psychological patterns emerge?

PSYCHOLOGICAL SCORING (1-5):
- Content: quality and relevance of response
- Authenticity: sincerity vs socially desirable responses
- Depth: level of introspection and reflection
- Coherence: consistency with emerging profile

Respond in JSON with:
{{
  "score": [1-5],
  "emotional_tone": "[calm/stressed/confident/defensive/engaged/detached]",
  "engagement_level": "[high/medium/low]",
  "authenticity": "[high/medium/low]",
  "analysis": {{
    "content_analysis": "...",
    "temporal_analysis": "...", 
    "psychological_state": "...",
    "coherence_assessment": "...",
    "behavioral_patterns": "..."
  }}
}}""",
        "ar": f"""أنت خبير نفسي في التقييم النفسي المتقدم. حلل هذه الإجابة لـ "{trait}" بنهج نفسي شامل:

{context}

الإجابة الجديدة: "{answer_text}"

التحليل النفسي المطلوب:
1. **تحليل المحتوى**: ماذا يكشف المحتوى عن السمة {trait}؟
2. **التحليل الزمني**: هل وقت الاستجابة ({response_time:.1f}ث) يشير للتأمل أم الاندفاع أم التردد؟
3. **تحليل المشاركة**: هل الطول ({answer_length} حرف) يظهر مشاركة أم انفصال؟
4. **كشف الحالة العاطفية**: ما الحالة النفسية الظاهرة (هادئ، متوتر، واثق، دفاعي)؟
5. **تحليل التماسك**: هل هذه الإجابة متماسكة مع السابقة؟
6. **الأنماط السلوكية**: ما الأنماط النفسية الناشئة؟

التقييم النفسي (1-5):
- المحتوى: جودة وصلة الاستجابة
- الأصالة: الصدق مقابل الاستجابات المرغوبة اجتماعياً
- العمق: مستوى الاستبطان والتأمل
- التماسك: الاتساق مع الملف الناشئ

أجب بـ JSON مع:
{{
  "score": [1-5],
  "emotional_tone": "[calm/stressed/confident/defensive/engaged/detached]",
  "engagement_level": "[high/medium/low]",
  "authenticity": "[high/medium/low]",
  "analysis": {{
    "content_analysis": "...",
    "temporal_analysis": "...",
    "psychological_state": "...",
    "coherence_assessment": "...",
    "behavioral_patterns": "..."
  }}
}}"""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        try:
            result = json.loads(result_text)
            score = max(1, min(5, result.get('score', 3)))
            return {
                'score': score,
                'emotional_tone': result.get('emotional_tone', 'neutral'),
                'engagement_level': result.get('engagement_level', 'medium'),
                'authenticity': result.get('authenticity', 'medium'),
                'analysis': result.get('analysis', {})
            }
        except json.JSONDecodeError:
            return fallback_enhanced_scoring(answer_text, response_time, answer_length)
    except Exception as e:
        logger.error(f"Error in enhanced scoring: {e}")
        return fallback_enhanced_scoring(answer_text, response_time, answer_length)

def fallback_enhanced_scoring(answer_text, response_time, answer_length):
    """Fallback scoring based on quantitative metrics"""
    score = 3
    if answer_length < 20:
        score = max(1, score - 1)
    elif answer_length > 100:
        score = min(5, score + 1)
    
    if response_time < 5:
        score = max(1, score - 1)
    elif response_time > 60:
        if answer_length > 50:
            score = min(5, score + 1)
        else:
            score = max(1, score - 1)
    
    emotional_tone = 'neutral'
    if any(word in answer_text.lower() for word in ['stress', 'anxieux', 'difficile', 'problème']):
        emotional_tone = 'stressed'
    elif any(word in answer_text.lower() for word in ['confiant', 'sûr', 'capable', 'facile']):
        emotional_tone = 'confident'
    elif any(word in answer_text.lower() for word in ['passionate', 'motivé', 'enthousiaste']):
        emotional_tone = 'engaged'
    
    return {
        'score': score,
        'emotional_tone': emotional_tone,
        'engagement_level': 'medium',
        'authenticity': 'medium',
        'analysis': {
            'content_analysis': 'Basic response analysis based on length and keywords.',
            'temporal_analysis': f'Response time of {response_time:.1f}s suggests moderate engagement.',
            'psychological_state': f'Inferred {emotional_tone} state based on content.',
            'coherence_assessment': 'Limited prior answers for coherence check.',
            'behavioral_patterns': 'Basic behavioral patterns detected.'
        }
    }



def generate_enhanced_detailed_analysis(trait, all_answers, total_score, language, assessment_type="big_five"):
    """Generate simplified detailed analysis with only 3 essential sections"""
    if not client:
        return generate_fallback_detailed_analysis(trait, all_answers, total_score, language, assessment_type)
    
    context = f"Trait: {trait} | Assessment: {assessment_type} | Score: {total_score}/10\n"
    for i, answer in enumerate(all_answers, 1):
        context += f"Answer {i}: {answer}\n"
    
    prompts = {
        "fr": f"""Analyse personnalisée pour "{trait}" basée sur cette réponse:

{context}

Ton amical et personnel requis. Commence par "Vous" ou "Nous avons remarqué" ou "Votre réponse révèle que".
Sois concis et bienveillant.

Format JSON:
{{
  "observations": "Analyse comportementale amicale (80-100 mots, commence par 'Vous' ou 'Nous avons remarqué')",
  "points_forts": ["Force 1", "Force 2", "Force 3"],
  "zones_developpement": ["Zone 1", "Zone 2"]
}}

JSON seulement.""",
        
        "en": f"""Personal analysis for "{trait}" based on this response:

{context}

Friendly and personal tone required. Start with "You" or "We noticed" or "Your answer reveals that".
Be concise and kind.

JSON format:
{{
  "observations": "Friendly behavioral analysis (80-100 words, start with 'You' or 'We noticed')",
  "points_forts": ["Strength 1", "Strength 2", "Strength 3"],
  "zones_developpement": ["Area 1", "Area 2"]
}}

JSON only.""",
        
        "ar": f"""تحليل شخصي لـ "{trait}" بناءً على هذه الإجابة:

{context}

مطلوب نبرة ودودة وشخصية. ابدأ بـ "أنت" أو "لاحظنا" أو "إجابتك تكشف أن".
كن موجزاً ولطيفاً.

تنسيق JSON:
{{
  "observations": "تحليل سلوكي ودود (80-100 كلمة، ابدأ بـ 'أنت' أو 'لاحظنا')",
  "points_forts": ["قوة 1", "قوة 2", "قوة 3"],
  "zones_developpement": ["منطقة 1", "منطقة 2"]
}}

JSON فقط."""
    }
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompts.get(language, prompts["fr"])}],
            max_tokens=400,
            temperature=0.7,
        )
        
        analysis_text = response.choices[0].message.content.strip()
        return json.loads(analysis_text)
        
    except Exception as e:
        logger.error(f"Error generating enhanced analysis: {e}")
        return generate_fallback_detailed_analysis(trait, all_answers, total_score, language, assessment_type)

def generate_fallback_detailed_analysis(trait, all_answers, total_score, language, assessment_type):
    """Simplified fallback analysis with only 3 sections"""
    fallback_content = {
        "fr": {
            "observations": f"Vous montrez des caractéristiques intéressantes dans le trait {trait}. Nous avons remarqué que vos réponses révèlent une approche personnelle distinctive. Votre score de {total_score}/10 indique un niveau spécifique d'expression de cette dimension de personnalité.",
            "points_forts": [
                f"Expression claire du trait {trait}",
                "Cohérence dans vos réponses",
                "Authenticité dans vos descriptions"
            ],
            "zones_developpement": [
                "Opportunités d'enrichissement identifiées",
                "Aspects à approfondir"
            ]
        },
        "en": {
            "observations": f"You show interesting characteristics in the {trait} trait. We noticed that your answers reveal a distinctive personal approach. Your score of {total_score}/10 indicates a specific level of expression of this personality dimension.",
            "points_forts": [
                f"Clear expression of {trait} trait",
                "Consistency in your responses",
                "Authenticity in your descriptions"
            ],
            "zones_developpement": [
                "Enrichment opportunities identified",
                "Aspects to deepen"
            ]
        },
        "ar": {
            "observations": f"أنت تُظهر خصائص مثيرة للاهتمام في سمة {trait}. لاحظنا أن إجاباتك تكشف عن نهج شخصي مميز. نتيجتك {total_score}/10 تشير إلى مستوى محدد من التعبير عن هذا البعد الشخصي.",
            "points_forts": [
                f"تعبير واضح عن سمة {trait}",
                "تناسق في إجاباتك",
                "أصالة في أوصافك"
            ],
            "zones_developpement": [
                "فرص إثراء محددة",
                "جوانب للتعمق"
            ]
        }
    }
    
    return fallback_content.get(language, fallback_content["fr"])
def generate_fallback_detailed_analysis(trait, all_answers, total_score, language, assessment_type):
    """Fallback detailed analysis when API fails"""
    fallback_content = {
        "fr": {
            "observations": f"Vous montrez des caractéristiques intéressantes dans le trait {trait}. Nous avons remarqué que vos réponses révèlent une approche personnelle distinctive. Votre score de {total_score}/10 indique un niveau spécifique d'expression de cette dimension de personnalité.",
            "points_forts": [
                f"Expression claire du trait {trait}",
                "Cohérence dans vos réponses",
                "Authenticité dans vos descriptions"
            ],
            "zones_developpement": [
                "Opportunités d'enrichissement identifiées",
                "Aspects à approfondir"
            ],
            "conseils_pratiques": [
                "Continuez à développer cette dimension",
                "Observez et apprenez des autres"
            ],
            "impact_professionnel": f"Votre niveau dans {trait} influence positivement votre environnement de travail. Cette caractéristique peut être un atout précieux dans vos interactions professionnelles et votre efficacité.",
            "analyse_psychologique": f"Vous présentez des patterns comportementaux cohérents avec le trait {trait}. Ces tendances reflètent votre façon unique d'aborder les situations et de prendre des décisions."
        },
        "en": {
            "observations": f"You show interesting characteristics in the {trait} trait. We noticed that your answers reveal a distinctive personal approach. Your score of {total_score}/10 indicates a specific level of expression of this personality dimension.",
            "points_forts": [
                f"Clear expression of {trait} trait",
                "Consistency in your responses",
                "Authenticity in your descriptions"
            ],
            "zones_developpement": [
                "Enrichment opportunities identified",
                "Aspects to deepen"
            ],
            "conseils_pratiques": [
                "Continue developing this dimension",
                "Observe and learn from others"
            ],
            "impact_professionnel": f"Your level in {trait} positively influences your work environment. This characteristic can be a valuable asset in your professional interactions and effectiveness.",
            "analyse_psychologique": f"You present behavioral patterns consistent with the {trait} trait. These tendencies reflect your unique way of approaching situations and making decisions."
        },
        "ar": {
            "observations": f"أنت تُظهر خصائص مثيرة للاهتمام في سمة {trait}. لاحظنا أن إجاباتك تكشف عن نهج شخصي مميز. نتيجتك {total_score}/10 تشير إلى مستوى محدد من التعبير عن هذا البعد الشخصي.",
            "points_forts": [
                f"تعبير واضح عن سمة {trait}",
                "تناسق في إجاباتك",
                "أصالة في أوصافك"
            ],
            "zones_developpement": [
                "فرص إثراء محددة",
                "جوانب للتعمق"
            ],
            "conseils_pratiques": [
                "واصل تطوير هذا البعد",
                "راقب وتعلم من الآخرين"
            ],
            "impact_professionnel": f"مستواك في {trait} يؤثر إيجابياً على بيئة عملك. هذه الخاصية يمكن أن تكون أصلاً قيماً في تفاعلاتك المهنية وفعاليتك.",
            "analyse_psychologique": f"أنت تقدم أنماط سلوكية متسقة مع سمة {trait}. هذه الميول تعكس طريقتك الفريدة في التعامل مع المواقف واتخاذ القرارات."
        }
    }
    
    return fallback_content.get(language, fallback_content["fr"])
def generate_fallback_detailed_analysis(trait, all_answers, total_score, language, assessment_type):
    """Fallback detailed analysis when API fails"""
    fallback_content = {
        "fr": {
            "observations": f"Analyse comportementale basée sur {len(all_answers)} réponse(s) pour {trait}. Les patterns identifiés révèlent des tendances spécifiques dans l'expression de ce trait, avec un score de {total_score}/10 indiquant un niveau particulier de manifestation comportementale.",
            "points_forts": [
                f"Manifestation claire du trait {trait} dans les réponses",
                "Cohérence dans l'expression comportementale",
                "Capacités naturelles identifiées"
            ],
            "zones_developpement": [
                "Opportunités d'amélioration identifiées",
                "Aspects du trait à renforcer",
                "Développement de nouvelles stratégies"
            ],
            "conseils_pratiques": [
                "Pratiquer régulièrement les comportements liés au trait",
                "Chercher des situations pour développer ces capacités",
                "Observer et apprendre des modèles positifs"
            ],
            "impact_professionnel": f"Ce niveau de {trait} influence directement la performance professionnelle, les interactions d'équipe et l'efficacité organisationnelle. L'impact varie selon les contextes et peut être optimisé par un développement ciblé.",
            "analyse_psychologique": f"L'analyse révèle des patterns psychologiques spécifiques liés à {trait}. Ces tendances influencent les processus de décision, les réactions émotionnelles et les stratégies d'adaptation dans diverses situations personnelles et professionnelles."
        },
        "en": {
            "observations": f"Behavioral analysis based on {len(all_answers)} response(s) for {trait}. Identified patterns reveal specific tendencies in trait expression, with a score of {total_score}/10 indicating a particular level of behavioral manifestation.",
            "points_forts": [
                f"Clear manifestation of {trait} trait in responses",
                "Consistency in behavioral expression",
                "Natural abilities identified"
            ],
            "zones_developpement": [
                "Improvement opportunities identified",
                "Trait aspects to strengthen",
                "Development of new strategies"
            ],
            "conseils_pratiques": [
                "Regularly practice trait-related behaviors",
                "Seek situations to develop these capacities",
                "Observe and learn from positive models"
            ],
            "impact_professionnel": f"This level of {trait} directly influences professional performance, team interactions, and organizational effectiveness. Impact varies by context and can be optimized through targeted development.",
            "analyse_psychologique": f"Analysis reveals specific psychological patterns related to {trait}. These tendencies influence decision-making processes, emotional reactions, and adaptation strategies in various personal and professional situations."
        },
        "ar": {
            "observations": f"تحليل سلوكي بناءً على {len(all_answers)} إجابة لـ {trait}. الأنماط المحددة تكشف عن ميول خاصة في التعبير عن السمة، مع نتيجة {total_score}/10 تشير إلى مستوى معين من المظهر السلوكي.",
            "points_forts": [
                f"مظهر واضح لسمة {trait} في الإجابات",
                "اتساق في التعبير السلوكي",
                "قدرات طبيعية محددة"
            ],
            "zones_developpement": [
                "فرص تحسين محددة",
                "جوانب السمة للتقوية",
                "تطوير استراتيجيات جديدة"
            ],
            "conseils_pratiques": [
                "ممارسة السلوكيات المرتبطة بالسمة بانتظام",
                "البحث عن مواقف لتطوير هذه القدرات",
                "مراقبة والتعلم من النماذج الإيجابية"
            ],
            "impact_professionnel": f"هذا المستوى من {trait} يؤثر مباشرة على الأداء المهني وتفاعلات الفريق والفعالية التنظيمية. التأثير يختلف حسب السياق ويمكن تحسينه من خلال التطوير المستهدف.",
            "analyse_psychologique": f"التحليل يكشف عن أنماط نفسية خاصة مرتبطة بـ {trait}. هذه الميول تؤثر على عمليات اتخاذ القرار والردود العاطفية واستراتيجيات التكيف في مواقف شخصية ومهنية مختلفة."
        }
    }
    
    return fallback_content.get(language, fallback_content["fr"])
