import openai
import os
from openai import OpenAI
import json
import logging
import re
import random

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

def get_behavioral_questions(trait, question_number, previous_answers, previous_score, language, assessment_type):
    """Fallback function to generate dynamic behavioral questions based on previous score"""
    topics_to_avoid = extract_question_topics(previous_answers, language)
    
    # Define question templates based on score
    question_templates = {
        "low_score": {  # For scores 1-2
            "fr": [
                "Quels facteurs vous empêchent de {action} dans {context} ?",
                "Pourquoi trouvez-vous difficile de {action} face à {challenge} ?",
                "Quelles contraintes limitent votre capacité à {action} dans {context} ?"
            ],
            "en": [
                "What factors prevent you from {action} in {context}?",
                "Why do you find it difficult to {action} when facing {challenge}?",
                "What constraints limit your ability to {action} in {context}?"
            ],
            "ar": [
                "ما العوامل التي تمنعك من {action} في {context}؟",
                "لماذا تجد صعوبة في {action} عند مواجهة {challenge}؟",
                "ما القيود التي تحد من قدرتك على {action} في {context}؟"
            ]
        },
        "medium_score": {  # For score 3
            "fr": [
                "Dans quelles conditions {action} devient plus facile pour vous ?",
                "Comment votre approche pour {action} varie-t-elle selon {context} ?",
                "Quels facteurs influencent votre capacité à {action} efficacement ?"
            ],
            "en": [
                "Under what conditions does {action} become easier for you?",
                "How does your approach to {action} vary based on {context}?",
                "What factors influence your ability to {action} effectively?"
            ],
            "ar": [
                "في أي ظروف يصبح {action} أسهل بالنسبة لك؟",
                "كيف يتغير نهجك في {action} بناءً على {context}؟",
                "ما العوامل التي تؤثر على قدرتك على {action} بفعالية؟"
            ]
        },
        "high_score": {  # For scores 4-5
            "fr": [
                "Quelles stratégies utilisez-vous pour réussir à {action} dans {context} ?",
                "Comment optimisez-vous votre capacité à {action} face à {challenge} ?",
                "Quels sont vos points forts pour {action} dans {context} ?"
            ],
            "en": [
                "What strategies do you use to succeed in {action} in {context}?",
                "How do you optimize your ability to {action} when facing {challenge}?",
                "What are your strengths in {action} within {context}?"
            ],
            "ar": [
                "ما الاستراتيجيات التي تستخدمها للنجاح في {action} في {context}؟",
                "كيف تعمل على تحسين قدرتك على {action} عند مواجهة {challenge}؟",
                "ما هي نقاط قوتك في {action} ضمن {context}؟"
            ]
        },
        "default": {  # For first question or no previous score
            "fr": [
                "Décrivez votre méthode pour {action} dans un contexte professionnel.",
                "Quelle approche adoptez-vous pour {action} face à {context} ?",
                "Préférez-vous {option1} ou {option2} dans vos {context} ?",
                "Dans quelles situations {action} de manière proactive ?",
                "Comment gérez-vous {challenge} dans un environnement {context} ?"
            ],
            "en": [
                "Describe your method for {action} in a professional context.",
                "What approach do you take to {action} when facing {context}?",
                "Do you prefer {option1} or {option2} in your {context}?",
                "In what situations do you {action} proactively?",
                "How do you manage {challenge} in a {context} environment?"
            ],
            "ar": [
                "صف طريقتك في {action} في سياق مهني.",
                "ما المنهج الذي تتبعه لـ {action} عند مواجهة {context}؟",
                "هل تفضل {option1} أم {option2} في {context}؟",
                "في أي مواقف تقوم بـ {action} بشكل استباقي؟",
                "كيف تدير {challenge} في بيئة {context}؟"
            ]
        }
    }

    trait_contexts = {
        "big_five": {
            "ouverture": {
                "fr": {
                    "actions": ["explorer de nouvelles idées dans un projet complexe impliquant plusieurs départements", "résoudre des problèmes créatifs avec des contraintes budgétaires strictes", "innover face à une résistance organisationnelle"],
                    "contexts": ["un projet de transformation digitale avec des équipes résistantes au changement", "une situation de crise nécessitant des solutions non conventionnelles", "une collaboration avec des partenaires aux cultures très différentes"],
                    "challenges": ["un changement soudain de direction stratégique imposé par la direction", "des contraintes réglementaires qui limitent les options créatives"],
                    "options": [("suivre des méthodes éprouvées pour minimiser les risques", "créer des solutions entièrement nouvelles malgré l'incertitude"), ("prendre des risques calculés pour innover", "préserver la stabilité et les processus existants")]
                },
                "en": {
                    "actions": ["explore innovative solutions in a multi-stakeholder project with conflicting priorities", "solve complex problems when established methods have failed repeatedly", "innovate within a traditional organization resistant to change"],
                    "contexts": ["a digital transformation project involving skeptical senior management and diverse teams", "a crisis situation requiring unconventional approaches with limited resources", "a cross-cultural collaboration with partners who have opposing methodologies"],
                    "challenges": ["a sudden strategic pivot mandated by leadership with tight deadlines", "regulatory constraints that severely limit creative options and require compliance"],
                    "options": [("follow proven methodologies to ensure predictable outcomes", "create entirely new solutions despite inherent uncertainty"), ("take calculated risks to drive innovation forward", "preserve organizational stability and existing proven processes")]
                },
                "ar": {
                    "actions": ["استكشاف حلول مبتكرة في مشروع متعدد أصحاب المصلحة مع أولويات متضاربة", "حل مشاكل معقدة عندما فشلت الطرق التقليدية مراراً", "الابتكار داخل منظمة تقليدية مقاومة للتغيير"],
                    "contexts": ["مشروع تحول رقمي يشمل إدارة عليا متشككة وفرق متنوعة", "حالة أزمة تتطلب مناهج غير تقليدية مع موارد محدودة", "تعاون عبر ثقافي مع شركاء لديهم منهجيات متعارضة"],
                    "challenges": ["تغيير استراتيجي مفاجئ تفرضه القيادة مع مواعيد نهائية ضيقة", "قيود تنظيمية تحد بشدة من الخيارات الإبداعية وتتطلب الامتثال"],
                    "options": [("اتباع منهجيات مجربة لضمان نتائج متوقعة", "إنشاء حلول جديدة تماماً رغم عدم اليقين المتأصل"), ("المخاطرة المحسوبة لدفع الابتكار قدماً", "الحفاظ على استقرار المنظمة والعمليات المجربة")]
                }
            },
            "conscienciosité": {
                "fr": {
                    "actions": ["organiser un projet complexe avec des équipes dispersées géographiquement", "prioriser des tâches contradictoires sous pression temporelle extrême", "assurer la qualité dans un environnement où les standards changent fréquemment"],
                    "contexts": ["un lancement de produit critique avec des dépendances multiples et des risques élevés", "une restructuration organisationnelle nécessitant une coordination méticuleuse", "une équipe internationale avec des fuseaux horaires et cultures de travail différents"],
                    "challenges": ["des priorités conflictuelles imposées par différents directeurs avec des objectifs incompatibles", "des ressources limitées qui obligent à faire des compromis sur la qualité"],
                    "options": [("planifier exhaustivement chaque détail avant de commencer", "s'adapter continuellement aux changements en cours de route"), ("viser la perfection quitte à dépasser les délais", "optimiser l'efficacité même si cela compromet certains détails")]
                },
                "en": {
                    "actions": ["organize a complex project with geographically dispersed teams across time zones", "prioritize conflicting tasks under extreme time pressure with shifting requirements", "ensure quality standards in an environment where criteria change frequently"],
                    "contexts": ["a critical product launch with multiple dependencies and high stakes for company reputation", "an organizational restructuring requiring meticulous coordination and change management", "an international team with different time zones and varying work cultures"],
                    "challenges": ["conflicting priorities imposed by different directors with incompatible objectives and expectations", "severely limited resources forcing difficult compromises on quality standards"],
                    "options": [("plan every detail exhaustively before beginning any execution", "continuously adapt to changes and emerging requirements during implementation"), ("strive for perfection even if it means exceeding deadlines", "optimize efficiency even if it compromises certain quality details")]
                },
                "ar": {
                    "actions": ["تنظيم مشروع معقد مع فرق موزعة جغرافياً عبر مناطق زمنية مختلفة", "ترتيب أولوية مهام متضاربة تحت ضغط زمني شديد مع متطلبات متغيرة", "ضمان معايير الجودة في بيئة تتغير فيها المعايير بشكل متكرر"],
                    "contexts": ["إطلاق منتج حاسم مع تبعيات متعددة ومخاطر عالية لسمعة الشركة", "إعادة هيكلة تنظيمية تتطلب تنسيقاً دقيقاً وإدارة التغيير", "فريق دولي مع مناطق زمنية مختلفة وثقافات عمل متنوعة"],
                    "challenges": ["أولويات متضاربة تفرضها مديرون مختلفون بأهداف وتوقعات غير متوافقة", "موارد محدودة بشدة تجبر على تنازلات صعبة حول معايير الجودة"],
                    "options": [("التخطيط لكل التفاصيل بشمولية قبل البدء بأي تنفيذ", "التكيف المستمر مع التغييرات والمتطلبات الناشئة أثناء التنفيذ"), ("السعي للكمال حتى لو عنى ذلك تجاوز المواعيد النهائية", "تحسين الكفاءة حتى لو أضر ببعض تفاصيل الجودة")]
                }
            },
            "extraversion": {
                "fr": {
                    "actions": ["prendre la parole dans une réunion où règne un conflit ouvert entre départements", "motiver une équipe démoralisée après plusieurs échecs consécutifs", "établir des relations avec des clients difficiles et exigeants"],
                    "contexts": ["une présentation cruciale devant un comité de direction sceptique et critique", "un groupe de collaborateurs résistants au changement et méfiants", "un événement de networking avec des personnalités influentes mais intimidantes"],
                    "challenges": ["un conflit interpersonnel ouvert qui divise l'équipe et paralyse les décisions", "un manque d'engagement généralisé suite à des promesses non tenues par la direction"],
                    "options": [("diriger activement les discussions pour imposer votre vision", "écouter attentivement tous les points de vue avant de proposer une synthèse"), ("convaincre par la force de votre argumentation et votre charisme", "montrer l'exemple par vos actions et laisser les résultats parler")]
                },
                "en": {
                    "actions": ["speak up in a meeting where open conflict exists between departments with entrenched positions", "motivate a demoralized team after several consecutive failures and setbacks", "establish relationships with difficult and demanding clients who have high expectations"],
                    "contexts": ["a crucial presentation to a skeptical and highly critical board of directors", "a group of colleagues resistant to change and distrustful of new initiatives", "a networking event with influential but intimidating industry leaders and decision-makers"],
                    "challenges": ["an open interpersonal conflict that divides the team and paralyzes decision-making processes", "widespread disengagement following broken promises by leadership and failed initiatives"],
                    "options": [("actively lead discussions to impose your vision and drive decisions forward", "listen carefully to all viewpoints before proposing a comprehensive synthesis"), ("convince through the force of your argumentation and personal charisma", "lead by example through your actions and let concrete results speak")]
                },
                "ar": {
                    "actions": ["التحدث في اجتماع يسوده صراع مفتوح بين أقسام ذات مواقف راسخة", "تحفيز فريق محبط بعد عدة إخفاقات ونكسات متتالية", "إقامة علاقات مع عملاء صعبين ومطالبين لديهم توقعات عالية"],
                    "contexts": ["عرض تقديمي حاسم أمام مجلس إدارة متشكك وناقد للغاية", "مجموعة من الزملاء المقاومين للتغيير والمتشككين في المبادرات الجديدة", "حدث تواصل مع قادة صناعة مؤثرين ولكن مخيفين وصناع قرار"],
                    "challenges": ["صراع شخصي مفتوح يقسم الفريق ويشل عمليات اتخاذ القرار", "انفصال واسع النطاق بعد وعود مكسورة من القيادة ومبادرات فاشلة"],
                    "options": [("قيادة النقاشات بنشاط لفرض رؤيتك ودفع القرارات قدماً", "الاستماع بعناية لجميع وجهات النظر قبل اقتراح تركيب شامل"), ("الإقناع من خلال قوة حجتك والكاريزما الشخصية", "القيادة بالمثال من خلال أفعالك ودع النتائج الملموسة تتحدث")]
                }
            },
            "agréabilité": {
                "fr": {
                    "actions": ["résoudre un conflit majeur entre équipes avec des enjeux financiers importants", "collaborer avec des partenaires aux intérêts divergents et aux egos surdimensionnés", "soutenir un collègue en difficulté malgré la pression hiérarchique"],
                    "contexts": ["une négociation tendue où chaque partie défend ses intérêts avec acharnement", "une équipe multiculturelle sous pression avec des malentendus fréquents", "une fusion d'entreprises créant tensions et inquiétudes sur l'emploi"],
                    "challenges": ["une opposition farouche de certains membres influents qui sabotent les initiatives", "des intérêts financiers divergents qui rendent tout compromis apparemment impossible"],
                    "options": [("défendre fermement votre position pour protéger vos intérêts", "rechercher activement un compromis acceptable pour toutes les parties"), ("prioriser les besoins des autres même au détriment de vos objectifs", "maintenir un équilibre entre empathie et atteinte de vos propres buts")]
                },
                "en": {
                    "actions": ["resolve a major conflict between teams with significant financial stakes and competing interests", "collaborate with partners who have divergent goals and oversized egos", "support a struggling colleague despite pressure from hierarchy and politics"],
                    "contexts": ["a tense negotiation where each party fiercely defends their interests with unwillingness to compromise", "a multicultural team under pressure with frequent misunderstandings and cultural clashes", "a company merger creating tensions and employment anxieties among staff"],
                    "challenges": ["fierce opposition from influential members who actively sabotage collaborative initiatives", "divergent financial interests that make any meaningful compromise seemingly impossible"],
                    "options": [("firmly defend your position to protect your core interests and objectives", "actively seek a compromise that remains acceptable to all involved parties"), ("prioritize others' needs even at the expense of your own objectives", "maintain balance between empathy and achieving your own essential goals")]
                },
                "ar": {
                    "actions": ["حل صراع كبير بين فرق ذات مصالح مالية كبيرة ومصالح متنافسة", "التعاون مع شركاء لديهم أهداف متباينة وغرور مفرط", "دعم زميل يواجه صعوبات رغم الضغط من التسلسل الهرمي والسياسات"],
                    "contexts": ["مفاوضة متوترة حيث يدافع كل طرف بشراسة عن مصالحه مع عدم الرغبة في التنازل", "فريق متعدد الثقافات تحت ضغط مع سوء فهم متكرر وصدامات ثقافية", "اندماج شركات يخلق توترات وقلق حول الوظائف بين الموظفين"],
                    "challenges": ["معارضة شرسة من أعضاء مؤثرين يخربون بنشاط المبادرات التعاونية", "مصالح مالية متباينة تجعل أي تنازل ذي معنى يبدو مستحيلاً"],
                    "options": [("الدفاع بحزم عن موقفك لحماية مصالحك وأهدافك الأساسية", "البحث بنشاط عن تنازل يبقى مقبولاً لجميع الأطراف المعنية"), ("إعطاء الأولوية لاحتياجات الآخرين حتى على حساب أهدافك الخاصة", "الحفاظ على التوازن بين التعاطف وتحقيق أهدافك الأساسية")]
                }
            },
            "stabilité émotionnelle": {
                "fr": {
                    "actions": ["gérer une crise majeure qui menace la survie de l'entreprise", "maintenir votre efficacité lors d'une restructuration avec licenciements massifs", "prendre des décisions cruciales sous une pression médiatique intense"],
                    "contexts": ["une situation de crise où votre réputation professionnelle est publiquement remise en question", "une période d'incertitude prolongée sur l'avenir de votre poste", "un environnement toxique avec des critiques constantes et un manque de reconnaissance"],
                    "challenges": ["une pression psychologique intense avec des attaques personnelles répétées", "l'accumulation de plusieurs échecs successifs remettant en cause vos compétences"],
                    "options": [("anticiper et préparer des plans détaillés pour tous les scénarios possibles", "réagir avec agilité aux événements au fur et à mesure qu'ils se présentent"), ("garder vos émotions sous contrôle total en toutes circonstances", "exprimer vos émotions de manière authentique tout en restant professionnel")]
                },
                "en": {
                    "actions": ["manage a major crisis that threatens the company's survival and your career", "maintain effectiveness during restructuring with massive layoffs and uncertainty", "make crucial decisions under intense media pressure and public scrutiny"],
                    "contexts": ["a crisis situation where your professional reputation is publicly questioned and attacked", "a prolonged period of uncertainty about your job security and future prospects", "a toxic environment with constant criticism and complete lack of recognition or support"],
                    "challenges": ["intense psychological pressure with repeated personal attacks on your competence and character", "accumulation of several successive failures that fundamentally question your abilities"],
                    "options": [("anticipate and prepare detailed contingency plans for all possible scenarios", "react with agility to events as they unfold without over-planning"), ("keep your emotions under complete control in all circumstances", "express your emotions authentically while maintaining professional standards")]
                },
                "ar": {
                    "actions": ["إدارة أزمة كبيرة تهدد بقاء الشركة ومسيرتك المهنية", "الحفاظ على الفعالية أثناء إعادة الهيكلة مع تسريحات جماعية وعدم يقين", "اتخاذ قرارات حاسمة تحت ضغط إعلامي شديد ومراقبة عامة"],
                    "contexts": ["حالة أزمة حيث يتم التشكيك في سمعتك المهنية ومهاجمتها علناً", "فترة طويلة من عدم اليقين حول أمان وظيفتك وآفاقك المستقبلية", "بيئة سامة مع انتقادات مستمرة وغياب تام للاعتراف أو الدعم"],
                    "challenges": ["ضغط نفسي شديد مع هجمات شخصية متكررة على كفاءتك وشخصيتك", "تراكم عدة إخفاقات متتالية تشكك جذرياً في قدراتك"],
                    "options": [("توقع وإعداد خطط طوارئ مفصلة لجميع السيناريوهات المحتملة", "التفاعل برشاقة مع الأحداث كما تتكشف دون إفراط في التخطيط"), ("إبقاء مشاعرك تحت السيطرة الكاملة في جميع الظروف", "التعبير عن مشاعرك بصدق مع الحفاظ على المعايير المهنية")]
                }
            }
        },
        "disc": {
            "dominant": {
                "fr": {
                    "actions": ["prendre des décisions stratégiques cruciales dans un contexte d'incertitude totale", "diriger une équipe résistante vers des objectifs ambitieux et controversés", "imposer des changements nécessaires malgré une opposition organisée"],
                    "contexts": ["une situation de crise nécessitant des décisions rapides avec des informations incomplètes", "un projet de transformation majeure avec des résistances à tous les niveaux", "une compétition acharnée où la moindre hésitation peut être fatale"],
                    "challenges": ["une opposition directe et coordonnée de la part d'acteurs influents", "des ressources insuffisantes pour atteindre des objectifs très ambitieux"],
                    "options": [("déléguer la responsabilité tout en gardant le contrôle final", "superviser directement chaque étape pour garantir l'exécution"), ("agir immédiatement sur la base de votre intuition", "analyser en profondeur toutes les options avant de décider")]
                },
                "en": {
                    "actions": ["make crucial strategic decisions in complete uncertainty with high stakes", "lead a resistant team toward ambitious and controversial objectives", "impose necessary changes despite organized opposition from stakeholders"],
                    "contexts": ["a crisis situation requiring rapid decisions with incomplete information and time pressure", "a major transformation project with resistance at all organizational levels", "intense competition where any hesitation could be fatal to success"],
                    "challenges": ["direct and coordinated opposition from influential actors with their own agendas", "insufficient resources to achieve highly ambitious objectives within tight constraints"],
                    "options": [("delegate responsibility while maintaining ultimate control over outcomes", "directly supervise each step to guarantee proper execution"), ("act immediately based on your intuition and experience", "thoroughly analyze all options before making any decisions")]
                },
                "ar": {
                    "actions": ["اتخاذ قرارات استراتيجية حاسمة في عدم يقين كامل مع مخاطر عالية", "قيادة فريق مقاوم نحو أهداف طموحة ومثيرة للجدل", "فرض تغييرات ضرورية رغم معارضة منظمة من أصحاب المصلحة"],
                    "contexts": ["حالة أزمة تتطلب قرارات سريعة بمعلومات ناقصة وضغط زمني", "مشروع تحويل كبير مع مقاومة على جميع المستويات التنظيمية", "منافسة شديدة حيث يمكن أن يكون أي تردد قاتلاً للنجاح"],
                    "challenges": ["معارضة مباشرة ومنسقة من فاعلين مؤثرين لديهم أجنداتهم الخاصة", "موارد غير كافية لتحقيق أهداف طموحة جداً ضمن قيود ضيقة"],
                    "options": [("تفويض المسؤولية مع الحفاظ على السيطرة النهائية على النتائج", "الإشراف المباشر على كل خطوة لضمان التنفيذ السليم"), ("التصرف فوراً بناءً على حدسك وخبرتك", "تحليل جميع الخيارات بدقة قبل اتخاذ أي قرارات")]
                }
            },
            "influent": {
                "fr": {
                    "actions": ["convaincre un groupe sceptique avec des intérêts divergents", "inspirer une équipe démotivée après des échecs répétés", "présenter une idée révolutionnaire à des décideurs conservateurs"],
                    "contexts": ["une audience hostile avec des préjugés établis contre votre proposition", "une réunion de crise où la panique et le pessimisme dominent", "une négociation complexe avec des parties prenantes influentes"],
                    "challenges": ["un manque d'attention généralisé et une distraction constante", "une résistance culturelle profonde au changement organisationnel"],
                    "options": [("utiliser l'émotion et les histoires personnelles pour toucher", "s'appuyer exclusivement sur des données factuelles et des preuves"), ("motiver par l'enthousiasme et la vision inspirante", "structurer méticuleusement l'argumentation logique")]
                },
                "en": {
                    "actions": ["convince a skeptical group with divergent interests and competing priorities", "inspire a demotivated team after repeated failures and setbacks", "present a revolutionary idea to conservative decision-makers with established mindsets"],
                    "contexts": ["a hostile audience with established prejudices against your proposal", "a crisis meeting where panic and pessimism dominate the atmosphere", "a complex negotiation with influential stakeholders and competing agendas"],
                    "challenges": ["widespread lack of attention and constant distractions from competing priorities", "deep cultural resistance to organizational change and new methodologies"],
                    "options": [("use emotion and personal stories to connect and touch hearts", "rely exclusively on factual data and concrete evidence"), ("motivate through enthusiasm and inspiring vision of the future", "meticulously structure logical argumentation and reasoning")]
                },
                "ar": {
                    "actions": ["إقناع مجموعة متشككة ذات مصالح متباينة وأولويات متنافسة", "إلهام فريق محبط بعد إخفاقات ونكسات متكررة", "تقديم فكرة ثورية لصناع قرار محافظين بعقليات راسخة"],
                    "contexts": ["جمهور عدائي مع تحيزات راسخة ضد اقتراحك", "اجتماع أزمة حيث يهيمن الذعر والتشاؤم على الأجواء", "مفاوضة معقدة مع أصحاب مصلحة مؤثرين وأجندات متنافسة"],
                    "challenges": ["نقص واسع في الانتباه وتشتيت مستمر من أولويات متنافسة", "مقاومة ثقافية عميقة للتغيير التنظيمي والمنهجيات الجديدة"],
                    "options": [("استخدام العاطفة والقصص الشخصية للتواصل ولمس القلوب", "الاعتماد حصرياً على البيانات الواقعية والأدلة الملموسة"), ("التحفيز من خلال الحماس والرؤية الملهمة للمستقبل", "هيكلة الحجة المنطقية والتفكير بدقة")]
                }
            },
            "stable": {
                "fr": {
                    "actions": ["maintenir la cohésion dans une équipe fragmentée par des conflits internes", "soutenir des collègues pendant une restructuration majeure avec licenciements", "gérer un changement organisationnel tout en préservant la culture d'entreprise"],
                    "contexts": ["une équipe multiculturelle avec des tensions ethniques et générérationnelles", "une période de transition prolongée avec une incertitude sur l'avenir", "un environnement de travail tendu avec une pression constante sur les résultats"],
                    "challenges": ["un conflit ouvert entre différentes factions avec des loyautés divisées", "une instabilité organisationnelle chronique affectant le moral des équipes"],
                    "options": [("préserver absolument la stabilité existante même si elle freine l'innovation", "adopter progressivement l'innovation tout en maintenant les bases solides"), ("agir systématiquement en médiateur neutre dans tous les conflits", "prendre des positions claires quand les valeurs fondamentales sont en jeu")]
                },
                "en": {
                    "actions": ["maintain cohesion in a team fragmented by internal conflicts and personal disputes", "support colleagues during major restructuring with layoffs and uncertainty", "manage organizational change while preserving essential company culture and values"],
                    "contexts": ["a multicultural team with ethnic and generational tensions affecting collaboration", "a prolonged transition period with persistent uncertainty about the future", "a tense work environment with constant pressure on results and performance"],
                    "challenges": ["open conflict between different factions with divided loyalties and competing interests", "chronic organizational instability severely affecting team morale and productivity"],
                    "options": [("absolutely preserve existing stability even if it hinders innovation and growth", "gradually adopt innovation while maintaining solid foundational structures"), ("systematically act as neutral mediator in all conflicts and disputes", "take clear positions when fundamental values and principles are at stake")]
                },
                "ar": {
                    "actions": ["الحفاظ على التماسك في فريق مجزأ بصراعات داخلية ونزاعات شخصية", "دعم الزملاء أثناء إعادة هيكلة كبيرة مع تسريحات وعدم يقين", "إدارة التغيير التنظيمي مع الحفاظ على ثقافة الشركة الأساسية والقيم"],
                    "contexts": ["فريق متعدد الثقافات مع توترات عرقية وجيلية تؤثر على التعاون", "فترة انتقالية طويلة مع عدم يقين مستمر حول المستقبل", "بيئة عمل متوترة مع ضغط مستمر على النتائج والأداء"],
                    "challenges": ["صراع مفتوح بين فصائل مختلفة مع ولاءات مقسمة ومصالح متنافسة", "عدم استقرار تنظيمي مزمن يؤثر بشدة على معنويات الفريق والإنتاجية"],
                    "options": [("الحفاظ المطلق على الاستقرار الموجود حتى لو أعاق الابتكار والنمو", "تبني الابتكار تدريجياً مع الحفاظ على الهياكل الأساسية الصلبة"), ("العمل بشكل منهجي كوسيط محايد في جميع الصراعات والنزاعات", "اتخاذ مواقف واضحة عندما تكون القيم والمبادئ الأساسية على المحك")]
                }
            },
            "conforme": {
                "fr": {
                    "actions": ["analyser une situation complexe avec des données contradictoires et incomplètes", "assurer la conformité réglementaire dans un environnement en évolution constante", "optimiser un processus critique avec des contraintes de qualité strictes"],
                    "contexts": ["une décision stratégique majeure avec des implications légales importantes", "un cadre réglementé avec des audits fréquents et des sanctions potentielles", "un projet détaillé nécessitant une précision absolue et zéro défaut"],
                    "challenges": ["une ambiguïté persistante dans les règles et réglementations", "une pression constante pour accélérer au détriment de la rigueur"],
                    "options": [("suivre rigoureusement les normes établies même si elles ralentissent", "prendre des initiatives calculées pour améliorer l'efficacité"), ("prioriser systématiquement la précision absolue dans tous les détails", "favoriser la flexibilité opérationnelle selon les contraintes du moment")]
                },
                "en": {
                    "actions": ["analyze a complex situation with contradictory and incomplete data requiring thorough investigation", "ensure regulatory compliance in a constantly evolving environment with changing standards", "optimize a critical process with strict quality constraints and zero-tolerance for errors"],
                    "contexts": ["a major strategic decision with significant legal implications and compliance requirements", "a highly regulated framework with frequent audits and potential severe sanctions", "a detailed project requiring absolute precision and zero defects in execution"],
                    "challenges": ["persistent ambiguity in rules and regulations creating uncertainty in decision-making", "constant pressure to accelerate processes at the expense of thoroughness and rigor"],
                    "options": [("rigorously follow established standards even if they significantly slow progress", "take calculated initiatives to improve efficiency while maintaining compliance"), ("systematically prioritize absolute precision in every detail and aspect", "favor operational flexibility according to situational constraints and demands")]
                },
                "ar": {
                    "actions": ["تحليل موقف معقد مع بيانات متناقضة وناقصة تتطلب تحقيقاً شاملاً", "ضمان الامتثال التنظيمي في بيئة متطورة باستمرار مع معايير متغيرة", "تحسين عملية حرجة مع قيود جودة صارمة وعدم تسامح مع الأخطاء"],
                    "contexts": ["قرار استراتيجي كبير مع آثار قانونية مهمة ومتطلبات امتثال", "إطار شديد التنظيم مع تدقيقات متكررة وعقوبات محتملة شديدة", "مشروع مفصل يتطلب دقة مطلقة وصفر عيوب في التنفيذ"],
                    "challenges": ["غموض مستمر في القوانين واللوائح يخلق عدم يقين في اتخاذ القرار", "ضغط مستمر لتسريع العمليات على حساب الشمولية والصرامة"],
                    "options": [("اتباع المعايير المعتمدة بصرامة حتى لو أبطأت التقدم بشكل كبير", "اتخاذ مبادرات محسوبة لتحسين الكفاءة مع الحفاظ على الامتثال"), ("إعطاء الأولوية بشكل منهجي للدقة المطلقة في كل تفصيل وجانب", "تفضيل المرونة التشغيلية وفقاً للقيود والمطالب الظرفية")]
                }
            }
        },
        "bien_etre": {
            "fr": {
                "actions": ["équilibrer travail et vie personnelle lors d'une période de surcharge professionnelle", "maintenir votre motivation malgré un manque de reconnaissance persistant", "gérer votre énergie pendant des projets marathons avec des délais impossibles"],
                "contexts": ["une période de forte charge avec des heures supplémentaires obligatoires", "une équipe sous pression constante avec un management dysfonctionnel", "un projet long et stressant sans perspectives d'amélioration à court terme"],
                "challenges": ["un épuisement professionnel imminent avec des signes de burnout", "un manque total de reconnaissance malgré des efforts exceptionnels"],
                "options": [("prioriser absolument le repos même si cela affecte les résultats", "maintenir la productivité malgré la fatigue croissante"), ("exprimer clairement vos besoins et limites à la hiérarchie", "vous adapter silencieusement aux attentes sans protester")]
            },
            "en": {
                "actions": ["balance work and personal life during a period of professional overload and excessive demands", "maintain motivation despite persistent lack of recognition and appreciation from management", "manage your energy during marathon projects with impossible deadlines and unrealistic expectations"],
                "contexts": ["a period of heavy workload with mandatory overtime and weekend work", "a team under constant pressure with dysfunctional management and toxic leadership", "a long and stressful project with no prospects for improvement in the near future"],
                "challenges": ["imminent professional burnout with clear warning signs and symptoms", "complete lack of recognition despite exceptional efforts and outstanding contributions"],
                "options": [("absolutely prioritize rest even if it negatively affects results and performance", "maintain productivity despite growing fatigue and declining mental health"), ("clearly express your needs and limits to hierarchy and management", "silently adapt to expectations without protest or resistance")]
            },
            "ar": {
                "actions": ["توازن العمل والحياة الشخصية خلال فترة حمولة مهنية زائدة ومطالب مفرطة", "الحفاظ على الدافعية رغم النقص المستمر في الاعتراف والتقدير من الإدارة", "إدارة طاقتك خلال مشاريع ماراثونية مع مواعيد نهائية مستحيلة وتوقعات غير واقعية"],
                "contexts": ["فترة عبء عمل ثقيل مع ساعات إضافية إجبارية وعمل نهاية الأسبوع", "فريق تحت ضغط مستمر مع إدارة مختلة وقيادة سامة", "مشروع طويل ومجهد دون آفاق للتحسن في المستقبل القريب"],
                "challenges": ["إرهاق مهني وشيك مع علامات تحذيرية وأعراض واضحة", "غياب كامل للاعتراف رغم الجهود الاستثنائية والمساهمات المتميزة"],
                "options": [("إعطاء الأولوية المطلقة للراحة حتى لو أثر سلباً على النتائج والأداء", "الحفاظ على الإنتاجية رغم التعب المتزايد وتدهور الصحة النفسية"), ("التعبير بوضوح عن احتياجاتك وحدودك للتسلسل الهرمي والإدارة", "التكيف بصمت مع التوقعات دون احتجاج أو مقاومة")]
            }
        },
        "resilience_ie": {
            "fr": {
                "actions": ["gérer une situation de stress extrême qui dépasse vos capacités habituelles", "adapter votre approche lors d'échecs répétés dans des domaines critiques", "comprendre et gérer les émotions complexes de votre équipe en crise"],
                "contexts": ["une crise personnelle et professionnelle simultanée affectant tous les aspects de votre vie", "un conflit interpersonnel majeur avec des conséquences sur votre carrière", "une décision cruciale avec des implications émotionnelles lourdes pour votre entourage"],
                "challenges": ["une surcharge émotionnelle massive dépassant vos mécanismes de défense", "une incertitude prolongée sur l'avenir créant anxiété et stress chronique"],
                "options": [("contrôler rigoureusement vos émotions en toutes circonstances", "les exprimer authentiquement tout en restant constructif"), ("anticiper méthodiquement tous les obstacles potentiels", "réagir spontanément aux défis au moment où ils surviennent")]
            },
            "en": {
                "actions": ["manage an extreme stress situation that exceeds your usual coping capacities", "adapt your approach following repeated failures in critical areas of responsibility", "understand and manage complex emotions of your team during organizational crisis"],
                "contexts": ["a simultaneous personal and professional crisis affecting all aspects of your life", "a major interpersonal conflict with significant consequences for your career trajectory", "a crucial decision with heavy emotional implications for your family and colleagues"],
                "challenges": ["massive emotional overload exceeding your normal defense mechanisms and coping strategies", "prolonged uncertainty about the future creating chronic anxiety and persistent stress"],
                "options": [("rigorously control your emotions in all circumstances and situations", "authentically express them while remaining constructive and solution-focused"), ("methodically anticipate all potential obstacles and prepare contingencies", "spontaneously react to challenges as they arise in real-time")]
            },
            "ar": {
                "actions": ["إدارة موقف ضغط شديد يتجاوز قدراتك المعتادة على التأقلم", "تكييف نهجك بعد إخفاقات متكررة في مجالات مسؤولية حرجة", "فهم وإدارة المشاعر المعقدة لفريقك أثناء أزمة تنظيمية"],
                "contexts": ["أزمة شخصية ومهنية متزامنة تؤثر على جميع جوانب حياتك", "صراع شخصي كبير مع عواقب مهمة على مسار مسيرتك المهنية", "قرار حاسم مع آثار عاطفية ثقيلة على عائلتك وزملائك"],
                "challenges": ["حمولة عاطفية هائلة تتجاوز آليات دفاعك العادية واستراتيجيات التأقلم", "عدم يقين طويل حول المستقبل يخلق قلقاً مزمناً وضغطاً مستمراً"],
                "options": [("السيطرة بصرامة على مشاعرك في جميع الظروف والمواقف", "التعبير عنها بصدق مع البقاء بناءً ومركزاً على الحلول"), ("توقع منهجي لجميع العقبات المحتملة وإعداد خطط طوارئ", "التفاعل بعفوية مع التحديات كما تنشأ في الوقت الفعلي")]
            }
        }
    }
   
    # Select template based on previous score
    score_category = "default"
    if previous_score is not None:
        if previous_score <= 2:
            score_category = "low_score"
        elif previous_score == 3:
            score_category = "medium_score"
        elif previous_score >= 4:
            score_category = "high_score"

    templates = question_templates.get(score_category, question_templates["default"]).get(language, question_templates["default"].get(language, question_templates["default"]["fr"]))
    
    # Get language-specific contexts
    trait_data = trait_contexts.get(assessment_type, {}).get(trait, {})
    if isinstance(trait_data, dict) and language in trait_data:
        contexts = trait_data[language]
    else:
        # Fallback to appropriate language defaults instead of French
        if language == "en":
            contexts = {
                "actions": ["managing situations", "handling challenges", "making decisions"],
                "contexts": ["a professional context", "your workplace", "team environment"],
                "challenges": ["an unexpected challenge", "time pressure", "conflicting priorities"],
                "options": [("act quickly", "think thoroughly"), ("take initiative", "wait for guidance")]
            }
        elif language == "ar":
            contexts = {
                "actions": ["إدارة موقف", "التعامل مع التحديات", "اتخاذ قرارات"],
                "contexts": ["سياق مهني", "مكان عملك", "بيئة الفريق"],
                "challenges": ["تحدي غير متوقع", "ضغط الوقت", "أولويات متضاربة"],
                "options": [("التصرف بسرعة", "التفكير بعمق"), ("أخذ المبادرة", "انتظار التوجيه")]
            }
        else:
            contexts = trait_data.get("fr", {
                "actions": ["gérer une situation", "relever des défis", "prendre des décisions"],
                "contexts": ["un contexte professionnel", "votre lieu de travail", "environnement d'équipe"],
                "challenges": ["un défi inattendu", "pression temporelle", "priorités conflictuelles"],
                "options": [("agir rapidement", "réfléchir en profondeur"), ("prendre l'initiative", "attendre des directives")]
            })
    
    template = random.choice(templates)
    action = random.choice(contexts.get("actions", ["managing situations" if language == "en" else "إدارة موقف" if language == "ar" else "gérer une situation"]))
    context = random.choice(contexts.get("contexts", ["a professional context" if language == "en" else "سياق مهني" if language == "ar" else "un contexte professionnel"]))
    challenge = random.choice(contexts.get("challenges", ["an unexpected challenge" if language == "en" else "تحدي غير متوقع" if language == "ar" else "un défi inattendu"]))
    option1, option2 = random.choice(contexts.get("options", [("act quickly", "think thoroughly") if language == "en" else ("التصرف بسرعة", "التفكير بعمق") if language == "ar" else ("agir rapidement", "réfléchir en profondeur")]))
    
    question = template.format(action=action, context=context, challenge=challenge, option1=option1, option2=option2)
    
    question_lower = question.lower()
    for topic in topics_to_avoid:
        if topic in question_lower:
            return get_behavioral_questions(trait, question_number, previous_answers, previous_score, language, assessment_type)
    
    return question

def generate_question(trait, question_number, previous_answers, previous_score, language, assessment_type="big_five"):
    """Generate dynamic behavioral questions based on previous score and answers"""
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
- Si des réponses précédentes existent, crée une question sur un ASPECT COMPLÈTEMENT DIFFÉRENT du trait
- Change TOTALEMENT le contexte, la situation, l'angle d'approche
- Utilise des débuts de question VARIÉS et créatifs

STYLE REQUIS:
- Question situationnelle et comportementale (10-15 mots)
- Explore ACTIONS, DÉCISIONS, PRÉFÉRENCES, STRATÉGIES dans des contextes VARIÉS
- Débuts créatifs: "Décrivez votre méthode pour...", "Comment abordez-vous...", "Quelle stratégie utilisez-vous...", "Dans quels cas préférez-vous...", "Comment adaptez-vous..."
- Contextes variés: travail, personnel, social, créatif, organisationnel, relationnel
- ÉVITE: répétition, questions similaires, même contexte que précédemment

QUALITÉ:
- Focus sur comportements concrets et choix réels
- Adapte selon le score: explore raisons (faible), contexte (modéré), ou forces (élevé)
- Question unique qui apporte une perspective nouvelle sur le trait

Réponds UNIQUEMENT avec la question comportementale en français.""",
        "en": f"""You are an expert psychologist. Generate ONE UNIQUE behavioral question to analyze "{trait}" (question {question_number}).

{context}{score_context}

IMPERATIVE - AVOID REPETITION:
- If previous answers exist, create a question about a COMPLETELY DIFFERENT aspect of the trait
- TOTALLY change the context, situation, approach angle
- Use VARIED and creative question beginnings

REQUIRED STYLE:
- Situational and behavioral question (10-15 words)
- Explore ACTIONS, DECISIONS, PREFERENCES, STRATEGIES in VARIED contexts
- Creative beginnings: "Describe your method for...", "How do you approach...", "What strategy do you use...", "In what cases do you prefer...", "How do you adapt..."
- Varied contexts: work, personal, social, creative, organizational, relational
- AVOID: repetition, similar questions, same context as previously

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
- استخدم بدايات أسئلة متنوعة وإبداعية

النمط المطلوب:
- سؤال موقفي وسلوكي (10-15 كلمة)
- استكشف الأفعال والقرارات والتفضيلات والاستراتيجيات في سياقات متنوعة
- بدايات إبداعية: "صف طريقتك في...", "كيف تتعامل مع...", "ما الاستراتيجية التي تستخدمها...", "في أي حالات تفضل...", "كيف تتكيف..."
- سياقات متنوعة: العمل، الشخصي، الاجتماعي، الإبداعي، التنظيمي، العلائقي
- تجنب: التكرار، الأسئلة المشابهة، نفس السياق السابق

الجودة:
- التركيز على السلوكيات الملموسة والخيارات الحقيقية
- التكيف حسب النتيجة: استكشف الأسباب (منخفض)، السياق (متوسط)، أو نقاط القوة (عالي)
- سؤال فريد يجلب منظوراً جديداً للسمة

أجب فقط بالسؤال السلوكي بالعربية."""
    }

    prompt = prompts.get(language, prompts["fr"])

    if not client:
        return validate_question_quality(
            get_behavioral_questions(trait, question_number, previous_answers, previous_score, language, assessment_type),
            trait, language
        )

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
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
        
        return validate_question_quality(question, trait, language)
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return validate_question_quality(
            get_behavioral_questions(trait, question_number, previous_answers, previous_score, language, assessment_type),
            trait, language
        )

def validate_question_quality(question, trait, language):
    """Validate question focuses on behavior and decision-making"""
    if not question:
        return get_behavioral_questions(trait, 1, [], None, language, "big_five")
    
    question = question.strip()
    question_lower = question.lower()
    
    forbidden_patterns = [
        'comment vous sentez', 'que faites-vous quand', 'comment réagissez',
        'how do you feel', 'what do you do when', 'how do you react',
        'كيف تشعر', 'ماذا تفعل عندما', 'كيف تتفاعل',
        'tell me about', 'parlez-moi de', 'حدثني عن',
        'share your experience', 'describe a time when', 'racontez une fois'
    ]
    
    for pattern in forbidden_patterns:
        if pattern in question_lower:
            logger.warning(f"BLOCKED EMOTIONAL/STORY QUESTION: {question}")
            return get_behavioral_questions(trait, 1, [], None, language, "big_five")
    
    behavioral_patterns = {
        "fr": ["décrivez votre", "quelle est votre", "préférez-vous", "dans quelles situations", "comment gérez-vous", "quelle approche", "quels facteurs", "pourquoi trouvez-vous", "quelles stratégies"],
        "en": ["describe your", "what is your", "do you prefer", "in what situations", "how do you manage", "what approach", "what factors", "why do you find", "what strategies"],
        "ar": ["صف", "ما هو", "هل تفضل", "في أي مواقف", "كيف تدير", "ما منهج", "ما العوامل", "لماذا تجد", "ما الاستراتيجيات"]
    }
    
    patterns = behavioral_patterns.get(language, behavioral_patterns["fr"])
    is_behavioral = any(pattern in question_lower for pattern in patterns)
    
    if not is_behavioral:
        logger.info(f"Converting to behavioral style: {question}")
        return get_behavioral_questions(trait, 1, [], None, language, "big_five")
    
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
            model="llama3-70b-8192",
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
            model="llama3-70b-8192",
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
            model="llama3-70b-8192",
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
            model="llama3-70b-8192",
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