import openai
import os
from openai import OpenAI
import json
import logging

# Configure minimal logging - ONLY ERRORS
logging.basicConfig(
    level=logging.ERROR,  # Changed from DEBUG to ERROR
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


logging.getLogger("openai").setLevel(logging.CRITICAL)
logging.getLogger("openai._base_client").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.connection").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.http11").setLevel(logging.CRITICAL)

# Also disable Django's default logging for development
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

# Complete assessment structure according to specifications
ASSESSMENT_STRUCTURE = {
    "big_five": {
        "traits": ["ouverture", "conscienciosité", "extraversion", "agréabilité", "stabilité émotionnelle"],
        "questions_per_trait": 5,
        "max_score_per_trait": 25,
        "levels": {
            "faible": (5, 11),
            "modéré": (12, 18), 
            "élevé": (19, 25)
        }
    },
    "disc": {
        "styles": ["dominant", "influent", "stable", "conforme"],
        "questions_total": 16,  # 4 questions per style
        "scoring": "choice_based"  # Highest number of choices
    },
    "bien_etre": {
        "questions_total": 6,
        "max_score": 30,
        "levels": {
            "faible": (6, 14),
            "modéré": (15, 22),
            "élevé": (23, 30)
        }
    },
    "resilience_ie": {
        "questions_total": 8,
        "max_score": 40,
        "levels": {
            "faible": (8, 19),
            "modéré": (20, 29),
            "élevé": (30, 40)
        }
    }
}

# Big Five traits with complete descriptions
TRAITS_CONFIG = {
    "ouverture": {
        "fr": "Ouverture à l’expérience - créativité, curiosité, imagination",
        "en": "Openness to Experience - creativity, curiosity, imagination", 
        "ar": "الانفتاح على التجربة - الإبداع والفضول والخيال",
        "descriptions": {
            "faible": {
                "fr": "Préfère les routines, peu d’intérêt pour la nouveauté ou les idées abstraites.",
                "en": "Prefers routines, little interest in novelty or abstract ideas.",
                "ar": "يفضل الروتين، اهتمام قليل بالجديد أو الأفكار المجردة."
            },
            "modéré": {
                "fr": "Ouvert(e) à certaines idées nouvelles mais avec prudence.",
                "en": "Open to some new ideas but with caution.",
                "ar": "منفتح على بعض الأفكار الجديدة ولكن بحذر."
            },
            "élevé": {
                "fr": "Très créatif(ve), curieux(se), attiré(e) par l’innovation et les expériences variées.",
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
                "fr": "Peut manquer de rigueur, difficulté à respecter les délais ou à s’organiser.",
                "en": "May lack rigor, difficulty meeting deadlines or organizing.",
                "ar": "قد يفتقر للدقة، صعوبة في احترام المواعيد أو التنظيم."
            },
            "modéré": {
                "fr": "Responsable dans les tâches importantes, mais manque parfois de planification.",
                "en": "Responsible in important tasks, but sometimes lacks planning.",
                "ar": "مسؤول في المهام المهمة، ولكن يفتقر أحياناً للتخطيط."
            },
            "élevé": {
                "fr": "Très organisé(e), fiable, soucieux(se) de la qualité et de l’efficacité.",
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
                "fr": "A l’aise dans certaines interactions, mais aime aussi la solitude.",
                "en": "Comfortable in some interactions, but also enjoys solitude.",
                "ar": "مرتاح في بعض التفاعلات، ولكن يحب أيضاً الوحدة."
            },
            "élevé": {
                "fr": "Sociable, assertif(ve), prend l’initiative dans les groupes.",
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
                "fr": "Empathique, à l’écoute, privilégie l’harmonie dans les relations.",
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
    return "modéré"  # default

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

def clean_arabic_text(text):
    """Clean Arabic text from foreign characters"""
    if not text:
        return text
    
    cleaned = ""
    for char in text:
        if ('\u0600' <= char <= '\u06FF' or  # Arabic
            char in ' .,;:!?()[]{}"\'-\n\r\t' or  # Basic punctuation
            char.isdigit()):  # Numbers
            cleaned += char
    
    return cleaned.strip()


def get_behavioral_questions(trait, question_number, previous_answers, language, assessment_type):
    """Behavioral questions that analyze real situations and actions"""
    
    # Extract what was already covered to avoid repetition
    covered_topics = []
    if previous_answers:
        for answer in previous_answers:
            if answer and len(answer) > 10:
                # Extract key concepts from previous answers
                words = answer.lower().split()
                covered_topics.extend([w for w in words if len(w) > 4][:3])
    
    # SMART BEHAVIORAL QUESTIONS - Each explores different aspects
    behavioral_questions = {
        "big_five": {
            "ouverture": {
                "fr": [
                    "Décrivez votre réaction face à un changement majeur au travail.",
                    "Quelle est votre approche quand vous devez résoudre un problème complexe ?",
                    "Préférez-vous suivre les méthodes établies ou créer vos propres solutions ?",
                    "Dans quelles situations cherchez-vous activement de nouvelles expériences ?",
                    "Comment choisissez-vous entre sécurité et innovation dans vos décisions ?"
                ],
                "en": [
                    "Describe your reaction to a major change at work.",
                    "What's your approach when solving a complex problem?",
                    "Do you prefer following established methods or creating your own solutions?",
                    "In what situations do you actively seek new experiences?",
                    "How do you choose between security and innovation in decisions?"
                ],
                "ar": [
                    "صف ردة فعلك تجاه تغيير كبير في العمل.",
                    "ما منهجك عند حل مشكلة معقدة؟",
                    "هل تفضل اتباع الطرق المعمول بها أم إنشاء حلولك الخاصة؟",
                    "في أي مواقف تسعى بنشاط لتجارب جديدة؟",
                    "كيف تختار بين الأمان والابتكار في قراراتك؟"
                ]
            },
            "extraversion": {
                "fr": [
                    "Décrivez votre comportement lors d'une réunion avec des inconnus.",
                    "Où puisez-vous votre énergie après une journée difficile ?",
                    "Préférez-vous convaincre par l'exemple ou par la parole ?",
                    "Dans quelles situations prenez-vous naturellement la parole ?",
                    "Comment gérez-vous les situations où vous devez travailler seul longtemps ?"
                ],
                "en": [
                    "Describe your behavior in a meeting with strangers.",
                    "Where do you draw energy after a difficult day?",
                    "Do you prefer convincing by example or by speaking?",
                    "In what situations do you naturally take the floor?",
                    "How do you handle situations requiring long periods of solo work?"
                ],
                "ar": [
                    "صف سلوكك في اجتماع مع غرباء.",
                    "من أين تستمد طاقتك بعد يوم صعب؟",
                    "هل تفضل الإقناع بالمثال أم بالكلام؟",
                    "في أي مواقف تأخذ الكلمة بشكل طبيعي؟",
                    "كيف تتعامل مع المواقف التي تتطلب العمل وحيداً لفترات طويلة؟"
                ]
            },
            "stabilité émotionnelle": {
                "fr": [
                    "Décrivez votre dernière réaction face à une critique constructive.",
                    "Quelle stratégie utilisez-vous pour gérer le stress au quotidien ?",
                    "Préférez-vous anticiper les problèmes ou les résoudre quand ils arrivent ?",
                    "Dans quelles situations gardez-vous votre calme naturellement ?",
                    "Comment vous préparez-vous mentalement avant une présentation importante ?"
                ],
                "en": [
                    "Describe your last reaction to constructive criticism.",
                    "What strategy do you use to manage daily stress?",
                    "Do you prefer anticipating problems or solving them as they come?",
                    "In what situations do you naturally stay calm?",
                    "How do you mentally prepare before an important presentation?"
                ],
                "ar": [
                    "صف آخر ردة فعل لك على نقد بناء.",
                    "ما الاستراتيجية التي تستخدمها لإدارة التوتر اليومي؟",
                    "هل تفضل توقع المشاكل أم حلها عند حدوثها؟",
                    "في أي مواقف تحافظ على هدوئك بشكل طبيعي؟",
                    "كيف تحضر نفسك ذهنياً قبل عرض مهم؟"
                ]
            },
            "conscienciosité": {
                "fr": [
                    "Décrivez votre méthode d'organisation pour un projet complexe.",
                    "Quelle importance accordez-vous aux détails versus aux résultats globaux ?",
                    "Préférez-vous planifier à l'avance ou vous adapter en cours de route ?",
                    "Dans quelles situations acceptez-vous des compromis sur la qualité ?",
                    "Comment équilibrez-vous perfectionnisme et efficacité ?"
                ],
                "en": [
                    "Describe your organization method for a complex project.",
                    "What importance do you place on details versus overall results?",
                    "Do you prefer planning ahead or adapting along the way?",
                    "In what situations do you accept compromises on quality?",
                    "How do you balance perfectionism and efficiency?"
                ],
                "ar": [
                    "صف طريقة تنظيمك لمشروع معقد.",
                    "ما الأهمية التي توليها للتفاصيل مقابل النتائج الإجمالية؟",
                    "هل تفضل التخطيط المسبق أم التكيف أثناء المسير؟",
                    "في أي مواقف تقبل التنازلات حول الجودة؟",
                    "كيف توازن بين الكمالية والكفاءة؟"
                ]
            },
            "agréabilité": {
                "fr": [
                    "Décrivez votre approche pour résoudre un conflit entre collègues.",
                    "Quelle place accordez-vous aux besoins des autres dans vos décisions ?",
                    "Préférez-vous dire la vérité directement ou ménager les sentiments ?",
                    "Dans quelles situations défendez-vous fermement votre position ?",
                    "Comment réagissez-vous quand quelqu'un profite de votre gentillesse ?"
                ],
                "en": [
                    "Describe your approach to resolving conflict between colleagues.",
                    "What place do you give to others' needs in your decisions?",
                    "Do you prefer telling the truth directly or sparing feelings?",
                    "In what situations do you firmly defend your position?",
                    "How do you react when someone takes advantage of your kindness?"
                ],
                "ar": [
                    "صف منهجك لحل نزاع بين الزملاء.",
                    "ما المكانة التي تعطيها لحاجات الآخرين في قراراتك؟",
                    "هل تفضل قول الحقيقة مباشرة أم تجنب جرح المشاعر؟",
                    "في أي مواقف تدافع بحزم عن موقفك؟",
                    "كيف تتفاعل عندما يستغل أحد لطفك؟"
                ]
            }
        },
        "disc": {
            "dominant": {
                "fr": [
                    "Décrivez votre style de prise de décision sous pression.",
                    "Quelle approche adoptez-vous pour motiver une équipe démotivée ?",
                    "Préférez-vous déléguer ou superviser directement les tâches importantes ?",
                    "Dans quelles situations remettez-vous en question l'autorité ?",
                    "Comment réagissez-vous quand vos objectifs sont remis en cause ?"
                ],
                "en": [
                    "Describe your decision-making style under pressure.",
                    "What approach do you take to motivate a demotivated team?",
                    "Do you prefer delegating or directly supervising important tasks?",
                    "In what situations do you question authority?",
                    "How do you react when your objectives are challenged?"
                ],
                "ar": [
                    "صف أسلوب اتخاذ القرار لديك تحت الضغط.",
                    "ما المنهج الذي تتبعه لتحفيز فريق فاقد للحافز؟",
                    "هل تفضل التفويض أم الإشراف المباشر على المهام المهمة؟",
                    "في أي مواقف تشكك في السلطة؟",
                    "كيف تتفاعل عندما يتم تحدي أهدافك؟"
                ]
            },
            "influent": {
                "fr": [
                    "Décrivez votre technique pour convaincre quelqu'un de sceptique.",
                    "Quelle énergie apportez-vous dans un groupe peu motivé ?",
                    "Préférez-vous convaincre par les faits ou par l'émotion ?",
                    "Dans quelles situations votre charisme est-il le plus efficace ?",
                    "Comment maintenez-vous l'attention pendant une présentation longue ?"
                ],
                "en": [
                    "Describe your technique for convincing a skeptical person.",
                    "What energy do you bring to an unmotivated group?",
                    "Do you prefer convincing through facts or emotion?",
                    "In what situations is your charisma most effective?",
                    "How do you maintain attention during a long presentation?"
                ],
                "ar": [
                    "صف تقنيتك لإقناع شخص متشكك.",
                    "ما الطاقة التي تجلبها لمجموعة غير محفزة؟",
                    "هل تفضل الإقناع بالحقائق أم بالعاطفة؟",
                    "في أي مواقف تكون كاريزمتك أكثر فعالية؟",
                    "كيف تحافظ على الانتباه أثناء عرض طويل؟"
                ]
            },
            "stable": {
                "fr": [
                    "Décrivez votre réaction face à un changement organisationnel soudain.",
                    "Quelle valeur apportez-vous dans un environnement de travail tendu ?",
                    "Préférez-vous la stabilité des processus ou l'innovation constante ?",
                    "Dans quelles situations votre patience devient-elle un atout ?",
                    "Comment maintenez-vous la cohésion dans une équipe diverse ?"
                ],
                "en": [
                    "Describe your reaction to sudden organizational change.",
                    "What value do you bring to a tense work environment?",
                    "Do you prefer process stability or constant innovation?",
                    "In what situations does your patience become an asset?",
                    "How do you maintain cohesion in a diverse team?"
                ],
                "ar": [
                    "صف ردة فعلك تجاه تغيير تنظيمي مفاجئ.",
                    "ما القيمة التي تجلبها لبيئة عمل متوترة؟",
                    "هل تفضل استقرار العمليات أم الابتكار المستمر؟",
                    "في أي مواقف يصبح صبرك ميزة؟",
                    "كيف تحافظ على التماسك في فريق متنوع؟"
                ]
            },
            "conforme": {
                "fr": [
                    "Décrivez votre processus d'analyse avant une décision importante.",
                    "Quelle importance accordez-vous aux normes versus à l'innovation ?",
                    "Préférez-vous des instructions détaillées ou une liberté d'action ?",
                    "Dans quelles situations votre précision devient-elle cruciale ?",
                    "Comment équilibrez-vous respect des règles et pragmatisme ?"
                ],
                "en": [
                    "Describe your analysis process before an important decision.",
                    "What importance do you place on standards versus innovation?",
                    "Do you prefer detailed instructions or freedom of action?",
                    "In what situations does your precision become crucial?",
                    "How do you balance rule compliance and pragmatism?"
                ],
                "ar": [
                    "صف عملية التحليل لديك قبل قرار مهم.",
                    "ما الأهمية التي توليها للمعايير مقابل الابتكار؟",
                    "هل تفضل تعليمات مفصلة أم حرية التصرف؟",
                    "في أي مواقف تصبح دقتك حاسمة؟",
                    "كيف توازن بين احترام القواعد والبراغماتية؟"
                ]
            }
        }
    }
    
    # Get questions for current trait
    available_questions = behavioral_questions.get(assessment_type, {}).get(trait, {}).get(language, [])
    
    if not available_questions:
        # Backup situational questions
        backup_questions = {
            "fr": [
                "Décrivez une situation où vous avez dû adapter votre approche.",
                "Quelle est votre méthode pour gérer les priorités conflictuelles ?",
                "Préférez-vous travailler selon des règles claires ou avec flexibilité ?",
                "Dans quelles circonstances changez-vous d'avis facilement ?",
                "Comment mesurez-vous le succès dans votre travail ?"
            ],
            "en": [
                "Describe a situation where you had to adapt your approach.",
                "What's your method for managing conflicting priorities?",
                "Do you prefer working with clear rules or flexibility?",
                "In what circumstances do you easily change your mind?",
                "How do you measure success in your work?"
            ],
            "ar": [
                "صف موقفاً اضطررت فيه لتكييف منهجك.",
                "ما طريقتك لإدارة الأولويات المتضاربة؟",
                "هل تفضل العمل بقواعد واضحة أم بمرونة؟",
                "في أي ظروف تغير رأيك بسهولة؟",
                "كيف تقيس النجاح في عملك؟"
            ]
        }
        available_questions = backup_questions.get(language, backup_questions["fr"])
    
    # Filter out questions with similar themes to previous answers
    filtered_questions = []
    for question in available_questions:
        question_lower = question.lower()
        
        # Check for thematic overlap with covered topics
        has_overlap = False
        for topic in covered_topics:
            if len(topic) > 4 and topic in question_lower:
                has_overlap = True
                break
        
        if not has_overlap:
            filtered_questions.append(question)
    
    # If all filtered out, use all available
    if not filtered_questions:
        filtered_questions = available_questions
    
    # Select question based on question number for variety
    index = (question_number - 1) % len(filtered_questions)
    return filtered_questions[index]

def generate_question(trait, question_number, previous_answers, language, assessment_type="big_five"):
    """Generate behavioral questions that analyze real situations and decision-making"""
    
    # Build context to avoid repetition
    context = ""
    if previous_answers:
        latest_answer = previous_answers[-1] if previous_answers else ""
        context = f"Dernière réponse: \"{latest_answer[:100]}...\"\n\n"
        
        if len(previous_answers) >= 2:
            context += f"SUJETS DÉJÀ EXPLORÉS: {len(previous_answers)} réponses précédentes\n"
            context += f"ÉVITER LA RÉPÉTITION avec les thèmes précédents\n\n"
    
    # Generate varied behavioral questions
    if assessment_type == "big_five":
        prompts = {
            "fr": f"""Tu es un psychologue expert. Génère UNE question comportementale pour analyser "{trait}" (question {question_number}/3).

{context}STYLE REQUIS:
- Question situationnelle et comportementale (10-15 mots)
- Explore les ACTIONS, DÉCISIONS, PRÉFÉRENCES, STRATÉGIES
- VARIE les débuts: "Décrivez votre...", "Quelle est votre approche...", "Préférez-vous...", "Dans quelles situations...", "Comment gérez-vous..."
- Focus sur comportements concrets et choix réels
- ÉVITE: "Comment vous sentez-vous", "Que faites-vous quand", questions émotionnelles
- ANALYSE: situations professionnelles, prises de décision, méthodes de travail

EXEMPLES VARIÉS:
- "Décrivez votre méthode pour résoudre un conflit complexe."
- "Quelle approche adoptez-vous face à un deadline serré ?"
- "Préférez-vous innover ou suivre des méthodes éprouvées ?"
- "Dans quelles situations remettez-vous en question les règles ?"

Réponds UNIQUEMENT avec la question comportementale.""",

            "en": f"""You are an expert psychologist. Generate ONE behavioral question to analyze "{trait}" (question {question_number}/3).

{context}REQUIRED STYLE:
- Situational and behavioral question (10-15 words)
- Explore ACTIONS, DECISIONS, PREFERENCES, STRATEGIES
- VARY beginnings: "Describe your...", "What's your approach...", "Do you prefer...", "In what situations...", "How do you manage..."
- Focus on concrete behaviors and real choices
- AVOID: "How do you feel", "What do you do when", emotional questions
- ANALYZE: professional situations, decision-making, work methods

VARIED EXAMPLES:
- "Describe your method for resolving a complex conflict."
- "What approach do you take when facing a tight deadline?"
- "Do you prefer innovating or following proven methods?"
- "In what situations do you question established rules?"

Respond ONLY with the behavioral question.""",

            "ar": f"""أنت خبير نفسي. أنشئ سؤالاً سلوكياً واحداً لتحليل "{trait}" (السؤال {question_number}/3).

{context}النمط المطلوب:
- سؤال موقفي وسلوكي (10-15 كلمة)
- استكشف الأفعال والقرارات والتفضيلات والاستراتيجيات
- نوع البدايات: "صف طريقتك...", "ما منهجك...", "هل تفضل...", "في أي مواقف...", "كيف تدير..."
- التركيز على السلوكيات الملموسة والخيارات الحقيقية
- تجنب: "كيف تشعر", "ماذا تفعل عندما", الأسئلة العاطفية
- التحليل: المواقف المهنية، اتخاذ القرارات، طرق العمل

أمثلة متنوعة:
- "صف طريقتك لحل نزاع معقد."
- "ما منهجك عند مواجهة موعد نهائي ضيق؟"
- "هل تفضل الابتكار أم اتباع الطرق المجربة؟"
- "في أي مواقف تشكك في القواعد المعمول بها؟"

أجب فقط بالسؤال السلوكي."""
        }
    
    elif assessment_type == "disc":
        prompts = {
            "fr": f"""Génère une question comportementale DISC pour analyser le style "{trait}".

{context}APPROCHE COMPORTEMENTALE:
- Question sur les ACTIONS et STRATÉGIES professionnelles
- Explore la prise de décision, le leadership, la communication
- VARIE: "Décrivez votre style...", "Quelle approche...", "Préférez-vous...", "Dans quelles situations..."
- Focus sur comportements observables en contexte professionnel

Réponds UNIQUEMENT avec la question DISC comportementale.""",

            "en": f"""Generate a behavioral DISC question to analyze style "{trait}".

{context}BEHAVIORAL APPROACH:
- Question about professional ACTIONS and STRATEGIES
- Explore decision-making, leadership, communication
- VARY: "Describe your style...", "What approach...", "Do you prefer...", "In what situations..."
- Focus on observable behaviors in professional context

Respond ONLY with the behavioral DISC question.""",

            "ar": f"""أنشئ سؤالاً سلوكياً DISC لتحليل النمط "{trait}".

{context}النهج السلوكي:
- سؤال حول الأفعال والاستراتيجيات المهنية
- استكشف اتخاذ القرارات والقيادة والتواصل
- نوع: "صف أسلوبك...", "ما منهجك...", "هل تفضل...", "في أي مواقف..."
- التركيز على السلوكيات الملحوظة في السياق المهني

أجب فقط بسؤال DISC السلوكي."""
        }

    prompt = prompts.get(language, prompts["fr"])
      
    if not client:
        return get_behavioral_questions(trait, question_number, previous_answers, language, assessment_type)

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7,  # Higher for more creativity
        )
        
        question = response.choices[0].message.content.strip()
        
        # Clean formatting
        import re
        question = re.sub(r'^\d+[\.\)]\s*', '', question)
        question = re.sub(r'^Question\s*\d*\s*[:\-]?\s*', '', question, flags=re.IGNORECASE)
        question = question.strip('"\'`')
        
        if not question.endswith('?'):
            question += ' ?'
        
        # Validate it's behavioral/situational
        behavioral_indicators = {
            "fr": ["décrivez", "approche", "méthode", "préférez", "situations", "stratégie", "style"],
            "en": ["describe", "approach", "method", "prefer", "situations", "strategy", "style"],
            "ar": ["صف", "منهج", "طريقة", "تفضل", "مواقف", "استراتيجية", "أسلوب"]
        }
        
        question_lower = question.lower()
        indicators = behavioral_indicators.get(language, behavioral_indicators["fr"])
        
        if not any(indicator in question_lower for indicator in indicators):
            # Fallback to behavioral questions
            return get_behavioral_questions(trait, question_number, previous_answers, language, assessment_type)
        
        # Block repetitive emotional patterns
        forbidden_starts = ["comment vous sentez", "que faites-vous quand", "how do you feel", "what do you do when", "كيف تشعر", "ماذا تفعل عندما"]
        if any(start in question_lower for start in forbidden_starts):
            return get_behavioral_questions(trait, question_number, previous_answers, language, assessment_type)
        
        return question
        
    except Exception as e:
        print(f"Error generating question: {e}")
        return get_behavioral_questions(trait, question_number, previous_answers, language, assessment_type)

def validate_question_quality(question, trait, language):
    """Validate question focuses on behavior and decision-making"""
    
    if not question:
        return get_behavioral_questions(trait, 1, [], language, "big_five")
    
    question = question.strip()
    
    # Block emotional and story questions
    forbidden_patterns = [
        'comment vous sentez', 'que faites-vous quand', 'comment réagissez',
        'how do you feel', 'what do you do when', 'how do you react',
        'كيف تشعر', 'ماذا تفعل عندما', 'كيف تتفاعل',
        'tell me about', 'parlez-moi de', 'حدثني عن',
        'share your experience', 'describe a time when', 'racontez une fois'
    ]
    
    question_lower = question.lower()
    
    # Check for forbidden patterns
    for pattern in forbidden_patterns:
        if pattern in question_lower:
            logger.warning(f"BLOCKED EMOTIONAL/STORY QUESTION: {question}")
            return get_behavioral_questions(trait, 1, [], language, "big_five")
    
    # Ensure it's behavioral/analytical
    behavioral_patterns = {
        "fr": ["décrivez votre", "quelle est votre", "préférez-vous", "dans quelles situations", "comment gérez-vous", "quelle approche"],
        "en": ["describe your", "what is your", "do you prefer", "in what situations", "how do you manage", "what approach"],
        "ar": ["صف", "ما هو", "هل تفضل", "في أي مواقف", "كيف تدير", "ما منهج"]
    }
    
    patterns = behavioral_patterns.get(language, behavioral_patterns["fr"])
    is_behavioral = any(pattern in question_lower for pattern in patterns)
    
    if not is_behavioral:
        logger.info(f"Converting to behavioral style: {question}")
        return get_behavioral_questions(trait, 1, [], language, "big_five")
    
    return question

def analyze_answer(answer_text, trait, all_answers_for_trait, language, assessment_type="big_five"):
    """Analyze answers focusing on behavioral patterns and decision-making"""
    
    # Build context
    context = ""
    if all_answers_for_trait:
        context = f"All previous answers for trait '{trait}':\n"
        for i, ans in enumerate(all_answers_for_trait, 1):
            context += f"Answer {i}: {ans}\n"
        context += "\n"
    
    # Scoring based on behavioral analysis
    if assessment_type == "big_five":
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
    
    elif assessment_type in ["bien_etre", "resilience_ie"]:
        prompts = {
            "fr": f"""Analyse comportementale pour "{assessment_type}":

{context}Nouvelle réponse: "{answer_text}"

Évalue les stratégies et approches décrites sur une échelle de 1 à 5:
1 = Stratégies contre-productives
2 = Approches peu efficaces
3 = Stratégies modérément efficaces
4 = Bonnes stratégies
5 = Excellentes stratégies et approches

Réponds uniquement par un chiffre de 1 à 5.""",

            "en": f"""Behavioral analysis for "{assessment_type}":

{context}New answer: "{answer_text}"

Evaluate described strategies and approaches on scale 1 to 5:
1 = Counter-productive strategies
2 = Ineffective approaches
3 = Moderately effective strategies
4 = Good strategies
5 = Excellent strategies and approaches

Respond only with a number from 1 to 5.""",

            "ar": f"""تحليل سلوكي لـ "{assessment_type}":

{context}إجابة جديدة: "{answer_text}"

قيّم الاستراتيجيات والمناهج الموصوفة على مقياس من 1 إلى 5:
1 = استراتيجيات عكس الإنتاجية
2 = مناهج غير فعالة
3 = استراتيجيات فعالة نوعاً ما
4 = استراتيجيات جيدة
5 = استراتيجيات ومناهج ممتازة

أجب برقم فقط من 1 إلى 5."""
        }
    
    elif assessment_type == "disc":
        prompts = {
            "fr": f"""Analyse cette réponse pour le style DISC "{trait}":

{context}Nouvelle réponse: "{answer_text}"

Évalue à quel point les comportements décrits correspondent au style {trait} (1-5):

Réponds uniquement par un chiffre de 1 à 5.""",

            "en": f"""Analyze this answer for DISC style "{trait}":

{context}New answer: "{answer_text}"

Evaluate how much the described behaviors match {trait} style (1-5):

Respond only with a number from 1 to 5.""",

            "ar": f"""حلل هذه الإجابة لنمط DISC "{trait}":

{context}إجابة جديدة: "{answer_text}"

قيّم إلى أي مدى تطابق السلوكيات الموصوفة نمط {trait} (1-5):

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
        # Fallback based on answer quality and behavioral indicators
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

# Helper function - no fancy names
def extract_question_topics(previous_answers, language):
    """Extract key topics from previous answers to avoid repetition"""
    topics = []
    if not previous_answers:
        return topics
    
    for answer in previous_answers:
        if answer and len(answer) > 20:
            words = answer.lower().split()
            # Extract meaningful words (skip common words)
            meaningful_words = [w for w in words if len(w) > 4 and w not in ['when', 'that', 'this', 'with', 'have', 'very', 'much', 'more', 'some', 'other']]
            topics.extend(meaningful_words[:5])  # Take first 5 meaningful words
    
    return list(set(topics))  

def generate_detailed_analysis(trait, all_answers, total_score, language, assessment_type="big_five"):
    """Generate detailed analysis according to specifications"""
    
    # Determine level based on score and assessment type
    level = get_level_from_score(total_score, assessment_type)
    
    # Build context from all answers
    context = f"All answers for '{trait}' (Assessment: {assessment_type}):\n"
    for i, answer in enumerate(all_answers, 1):
        context += f"Answer {i}: {answer}\n"
    
    # Get appropriate description based on assessment type
    if assessment_type == "big_five":
        trait_description = TRAITS_CONFIG[trait]["descriptions"][level][language]
    elif assessment_type == "bien_etre":
        trait_description = WELLBEING_CONFIG["descriptions"][level][language]
    elif assessment_type == "resilience_ie":
        trait_description = RESILIENCE_CONFIG["descriptions"][level][language]
    else:
        trait_description = f"Score de {total_score} pour {trait}"
    
    prompts = {
        "fr": f"""Tu es un psychologue expert. Analyse en détail "{trait}" basé sur ces réponses:

{context}

Score total: {total_score} (Niveau: {level})
Description du niveau: {trait_description}

Génère une analyse détaillée selon les spécifications NextMind qui inclut:
1. **Observations principales** : Ce que révèlent les réponses
2. **Raisons du score** : Pourquoi ce score a été attribué selon le barème officiel
3. **Points forts** : Aspects positifs identifiés
4. **Zones d'amélioration** : Aspects à développer
5. **Conseils pratiques** : 2-3 suggestions concrètes

Format ta réponse en JSON avec ces clés : "observations", "raisons_score", "points_forts", "zones_amelioration", "conseils"

Réponds uniquement avec le JSON, sans texte additionnel.""",

        "en": f"""You are an expert psychologist. Analyze in detail "{trait}" based on these answers:

{context}

Total score: {total_score} (Level: {level})
Level description: {trait_description}

Generate a detailed analysis according to NextMind specifications that includes:
1. **Main observations**: What the answers reveal
2. **Score reasoning**: Why this score was assigned according to official scale
3. **Strengths**: Positive aspects identified
4. **Areas for improvement**: Aspects to develop
5. **Practical advice**: 2-3 concrete suggestions

Format your response as JSON with these keys: "observations", "score_reasoning", "strengths", "areas_for_improvement", "advice"

Respond only with JSON, no additional text.""",

        "ar": f"""أنت خبير نفسي. حلل بالتفصيل "{trait}" بناءً على هذه الإجابات:

{context}

النتيجة الإجمالية: {total_score} (المستوى: {level})
وصف المستوى: {trait_description}

أنشئ تحليلاً مفصلاً وفقاً لمواصفات NextMind يتضمن:
1. **الملاحظات الرئيسية**: ما تكشفه الإجابات
2. **أسباب النتيجة**: لماذا تم إعطاء هذه النتيجة وفقاً للمقياس الرسمي
3. **نقاط القوة**: الجوانب الإيجابية المحددة
4. **مناطق للتحسين**: الجوانب التي يجب تطويرها
5. **نصائح عملية**: 2-3 اقتراحات ملموسة

نسق إجابتك كـ JSON مع هذه المفاتيح: "observations", "score_reasoning", "strengths", "areas_for_improvement", "advice"

أجب بـ JSON فقط، بدون نص إضافي."""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7,
        )
        
        analysis_text = response.choices[0].message.content.strip()
        try:
            analysis = json.loads(analysis_text)
            return analysis
        except json.JSONDecodeError:
            # Fallback analysis
            return {
                "observations": f"Analysis based on {len(all_answers)} responses for {trait}",
                "score_reasoning": f"Score of {total_score} places this in {level} category according to specifications",
                "strengths": "Positive indicators identified",
                "areas_for_improvement": "Opportunities for development present",
                "advice": "Focus on continuous improvement in this area"
            }
    except Exception as e:
        logger.error(f"Error generating detailed analysis: {e}")
        return {
            "observations": f"Analysis for {trait} based on responses",
            "score_reasoning": f"Score reflects {level} level according to official scale", 
            "strengths": "Individual strengths noted",
            "areas_for_improvement": "Growth opportunities identified",
            "advice": "Continue personal development efforts"
        }

def should_recommend_coaching(all_assessment_scores, language):
    """Determine if coaching should be recommended based on complete profile according to specifications"""
    
    coaching_indicators = []
    
    # Check Big Five scores
    if "big_five" in all_assessment_scores:
        big_five_scores = all_assessment_scores["big_five"]
        low_scores = [trait for trait, data in big_five_scores.items() if data['total_score'] <= 11]  # Faible level
        
        if len(low_scores) >= 2:
            coaching_indicators.append("multiple_big_five_challenges")
        
        # Check emotional stability specifically
        if 'stabilité émotionnelle' in big_five_scores and big_five_scores['stabilité émotionnelle']['total_score'] <= 11:
            coaching_indicators.append("emotional_stability_low")
    
    # Check Well-being scores
    if "bien_etre" in all_assessment_scores:
        wellbeing_score = all_assessment_scores["bien_etre"]["total_score"]
        if wellbeing_score <= 14:  # Faible level
            coaching_indicators.append("low_wellbeing")
    
    # Check Resilience scores
    if "resilience_ie" in all_assessment_scores:
        resilience_score = all_assessment_scores["resilience_ie"]["total_score"]
        if resilience_score <= 19:  # Faible level
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
    
    # Set priority level
    if len(coaching_indicators) >= 3:
        recommendations["fr"]["priority"] = "high"
        recommendations["en"]["priority"] = "high"
        recommendations["ar"]["priority"] = "high"
    elif len(coaching_indicators) >= 2:
        recommendations["fr"]["priority"] = "medium"
        recommendations["en"]["priority"] = "medium"
        recommendations["ar"]["priority"] = "medium"
    
    # Add specific reasons
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

def analyze_and_score_answer_enhanced(answer_text, trait, previous_answers, language, assessment_type="big_five", psychological_context=None):
    """Enhanced scoring with psychological analysis including tone, timing, and user state"""
    
    if psychological_context is None:
        psychological_context = {}
    
    response_time = psychological_context.get('response_time', 0)
    answer_length = psychological_context.get('answer_length', len(answer_text))
    question_number = psychological_context.get('question_number', 1)
    user_patterns = psychological_context.get('user_patterns', {})
    
    # Build comprehensive psychological context
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
    
    # Enhanced prompts with deep psychological analysis
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
            # Parse JSON response
            result = json.loads(result_text)
            
            # Ensure score is valid
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
    
    # Base score from length and quality indicators
    score = 3  # Default
    
    # Adjust based on length
    if answer_length < 20:
        score = max(1, score - 1)
    elif answer_length > 100:
        score = min(5, score + 1)
    
    # Adjust based on response time (psychological indicators)
    if response_time < 5:  # Very quick - might be superficial
        score = max(1, score - 1)
    elif response_time > 60:  # Very slow - might indicate deep thought or confusion
        if answer_length > 50:
            score = min(5, score + 1)  # Thoughtful
        else:
            score = max(1, score - 1)  # Confused/stuck
    
    # Determine emotional tone from content markers
    emotional_tone = 'neutral'
    if any(word in answer_text.lower() for word in ['stress', 'anxieux', 'difficile', 'problème']):
        emotional_tone = 'stressed'
    elif any(word in answer_text.lower() for word in ['confiant', 'sûr', 'capable', 'facile']):
        emotional_tone = 'confident'
    elif any(word in answer_text.lower() for word in ['passionate', 'motivé', 'enthousiaste']):
        emotional_tone = 'engaged'

