import openai
import os
from openai import OpenAI
import json
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure OpenAI client for Groq
try:
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    logger.info("Groq client initialized successfully")
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

def generate_adaptive_question(trait, question_number, previous_answers, language, assessment_type="big_five"):
    """Generate adaptive questions for different assessment types according to specifications"""
    
    logger.info(f"Generating question for trait: {trait}, question_number: {question_number}, language: {language}, assessment_type: {assessment_type}")
    
    # Build context from previous answers with psychological insight
    context = ""
    adaptation_insight = ""
    if previous_answers:
        context = "Réponses précédentes de l'utilisateur:\n" if language == "fr" else "Previous user answers:\n" if language == "en" else "إجابات المستخدم السابقة:\n"
        for i, answer in enumerate(previous_answers, 1):
            context += f"Q{i}: {answer}\n"
        context += "\n"
        
        # Add psychological adaptation instruction
        adaptation_insight = {
            "fr": f"ADAPTATION PSYCHOLOGIQUE INTELLIGENTE: Analyse les patterns psychologiques dans les réponses précédentes. Si tu détectes de l'anxiété, explore les mécanismes de défense. Si tu vois de la confiance, teste la consistance. Si tu observes de l'évitement, creuse avec bienveillance. Adapte ta question pour révéler des aspects authentiques du trait {trait}.\n\n",
            "en": f"INTELLIGENT PSYCHOLOGICAL ADAPTATION: Analyze psychological patterns in previous responses. If you detect anxiety, explore defense mechanisms. If you see confidence, test consistency. If you observe avoidance, dig with kindness. Adapt your question to reveal authentic aspects of trait {trait}.\n\n",
            "ar": f"التكيف النفسي الذكي: حلل الأنماط النفسية في الإجابات السابقة. إذا اكتشفت قلقاً، استكشف آليات الدفاع. إذا رأيت ثقة، اختبر الاتساق. إذا لاحظت تجنباً، احفر بلطف. كيف سؤالك لكشف الجوانب الأصيلة للسمة {trait}.\n\n"
        }[language]
    
    # Enhanced prompts with psychological depth and personalization
    if assessment_type == "big_five":
        max_questions = ASSESSMENT_STRUCTURE["big_five"]["questions_per_trait"]
        prompts = {
            "fr": f"""Tu es un psychologue expert qui combine l'évaluation Big Five avec une approche conversationnelle personnalisée. Tu évalues le trait "{trait}" (question {question_number}/{max_questions}).

{adaptation_insight}{context}MISSION PSYCHOLOGIQUE:
Cette question doit évaluer précisément le niveau de "{trait}" pour contribuer au score final de 5-25 points (5 questions × 1-5 points chacune).

INTELLIGENCE PSYCHOLOGIQUE REQUISE:
- Analyse les réponses précédentes pour détecter les patterns comportementaux et émotionnels
- Personnalise selon le style psychologique de la personne (défensive, ouverte, analytique, émotionnelle)
- Utilise des situations concrètes qui révèlent les véritables manifestations du trait
- Adapte le niveau de profondeur selon la capacité d'introspection montrée

STYLE CONVERSATIONNEL INTELLIGENT:
- Question courte et naturelle (10-18 mots)
- Commence par "Comment", "Que faites-vous", "Décrivez-moi", "Racontez-moi"
- Utilise des situations authentiques et réalistes
- Révèle les nuances psychologiques du trait
- Évite le jargon mais maintient la profondeur psychologique

EXEMPLES DE QUESTIONS PSYCHOLOGIQUEMENT INTELLIGENTES:
- "Comment réagissez-vous intérieurement face à une critique de votre patron ?"
- "Que se passe-t-il en vous quand vos plans changent à la dernière minute ?"
- "Décrivez-moi ce que vous ressentez lors d'une présentation importante."

SCORING: Cette question doit permettre une évaluation précise sur l'échelle 1-5 du trait "{trait}".

Réponds UNIQUEMENT avec la question, sans numéro ni explication.""",

            "en": f"""You are an expert psychologist combining Big Five assessment with a personalized conversational approach. You are evaluating trait "{trait}" (question {question_number}/{max_questions}).

{adaptation_insight}{context}PSYCHOLOGICAL MISSION:
This question must precisely assess the level of "{trait}" to contribute to the final score of 5-25 points (5 questions × 1-5 points each).

REQUIRED PSYCHOLOGICAL INTELLIGENCE:
- Analyze previous responses to detect behavioral and emotional patterns
- Personalize according to the person's psychological style (defensive, open, analytical, emotional)
- Use concrete situations that reveal true trait manifestations
- Adapt depth level according to introspective capacity shown

INTELLIGENT CONVERSATIONAL STYLE:
- Short and natural question (10-18 words)
- Start with "How", "What do you do", "Describe", "Tell me"
- Use authentic and realistic situations
- Reveal psychological nuances of the trait
- Avoid jargon but maintain psychological depth

EXAMPLES OF PSYCHOLOGICALLY INTELLIGENT QUESTIONS:
- "How do you react internally when your boss criticizes you?"
- "What happens inside you when your plans change last minute?"
- "Describe what you feel during an important presentation."

SCORING: This question should enable precise assessment on the 1-5 scale for trait "{trait}".

Respond ONLY with the question, no number or explanation.""",

            "ar": f"""أنت خبير نفسي يجمع بين تقييم العوامل الخمسة الكبرى والنهج المحادثي الشخصي. تقيم السمة "{trait}" (السؤال {question_number}/{max_questions}).

{adaptation_insight}{context}المهمة النفسية:
هذا السؤال يجب أن يقيم بدقة مستوى "{trait}" للمساهمة في النتيجة النهائية 5-25 نقطة (5 أسئلة × 1-5 نقاط لكل منها).

الذكاء النفسي المطلوب:
- حلل الإجابات السابقة لاكتشاف الأنماط السلوكية والعاطفية
- شخصن وفقاً للنمط النفسي للشخص (دفاعي، منفتح، تحليلي، عاطفي)
- استخدم مواقف ملموسة تكشف المظاهر الحقيقية للسمة
- كيف مستوى العمق وفقاً لقدرة الاستبطان المظهرة

النمط المحادثي الذكي:
- سؤال قصير وطبيعي (10-18 كلمة)
- ابدأ بـ "كيف", "ماذا تفعل", "صف لي", "حدثني"
- استخدم مواقف أصيلة وواقعية
- اكشف الفروق النفسية الدقيقة للسمة
- تجنب المصطلحات لكن احتفظ بالعمق النفسي

أمثلة على الأسئلة الذكية نفسياً:
- "كيف تتفاعل داخلياً عندما ينتقدك مديرك؟"
- "ماذا يحدث بداخلك عندما تتغير خططك في اللحظة الأخيرة؟"
- "صف لي ما تشعر به أثناء عرض مهم."

التقييم: هذا السؤال يجب أن يمكن التقييم الدقيق على مقياس 1-5 للسمة "{trait}".

أجب فقط بالسؤال، بدون رقم أو شرح."""
        }
    
    elif assessment_type == "disc":
        prompts = {
            "fr": f"""Tu es un expert DISC qui utilise une approche psychologique personnalisée pour identifier le style comportemental "{trait}".

{adaptation_insight}{context}MISSION COMPORTEMENTALE:
Identifier les préférences comportementales naturelles et les motivations profondes du style {trait}.

INTELLIGENCE COMPORTAMENTALE:
- Adapte selon les patterns comportementaux révélés dans les réponses précédentes
- Personnalise selon l'environnement professionnel et le niveau hiérarchique apparent
- Utilise des situations professionnelles authentiques qui révèlent les vraies préférences
- Détecte les comportements adaptés vs naturels

STYLE PROFESSIONNEL INTELLIGENT:
- Question courte et situationnelle (10-18 mots)
- Commence par "Comment", "Que faites-vous", "Décrivez-moi"
- Situations de travail concrètes et réalistes
- Révèle les motivations et craintes profondes du style

EXEMPLES INTELLIGENTS pour {trait}:
- Dominant: "Comment prenez-vous le contrôle quand l'équipe hésite ?"
- Influent: "Comment persuadez-vous un client sceptique de vos idées ?"
- Stable: "Comment réagissez-vous quand tout change rapidement autour de vous ?"
- Conforme: "Comment vous assurez-vous qu'aucun détail n'est oublié ?"

Réponds UNIQUEMENT avec la question.""",

            "en": f"""You are a DISC expert using a personalized psychological approach to identify behavioral style "{trait}".

{adaptation_insight}{context}BEHAVIORAL MISSION:
Identify natural behavioral preferences and deep motivations of {trait} style.

BEHAVIORAL INTELLIGENCE:
- Adapt based on behavioral patterns revealed in previous responses
- Personalize according to professional environment and apparent hierarchical level
- Use authentic professional situations that reveal true preferences
- Detect adapted vs natural behaviors

INTELLIGENT PROFESSIONAL STYLE:
- Short and situational question (10-18 words)
- Start with "How", "What do you do", "Describe"
- Concrete and realistic work situations
- Reveal deep motivations and fears of the style

INTELLIGENT EXAMPLES for {trait}:
- Dominant: "How do you take control when the team hesitates?"
- Influential: "How do you persuade a skeptical client of your ideas?"
- Steady: "How do you react when everything changes rapidly around you?"
- Compliant: "How do you ensure no detail is forgotten?"

Respond ONLY with the question.""",

            "ar": f"""أنت خبير DISC يستخدم نهجاً نفسياً شخصياً لتحديد النمط السلوكي "{trait}".

{adaptation_insight}{context}المهمة السلوكية:
حدد التفضيلات السلوكية الطبيعية والدوافع العميقة لنمط {trait}.

الذكاء السلوكي:
- تكيف بناءً على الأنماط السلوكية المكشوفة في الإجابات السابقة
- شخصن وفقاً للبيئة المهنية والمستوى الهرمي الظاهر
- استخدم مواقف مهنية أصيلة تكشف التفضيلات الحقيقية
- اكتشف السلوكيات المتكيفة مقابل الطبيعية

النمط المهني الذكي:
- سؤال قصير وموقفي (10-18 كلمة)
- ابدأ بـ "كيف", "ماذا تفعل", "صف لي"
- مواقف عمل ملموسة وواقعية
- اكشف الدوافع والمخاوف العميقة للنمط

أمثلة ذكية لـ {trait}:
- مهيمن: "كيف تسيطر على الوضع عندما يتردد الفريق؟"
- مؤثر: "كيف تقنع عميلاً متشككاً بأفكارك؟"
- مستقر: "كيف تتفاعل عندما يتغير كل شيء بسرعة حولك؟"
- ملتزم: "كيف تتأكد من عدم نسيان أي تفصيل؟"

أجب فقط بالسؤال."""
        }
    
    elif assessment_type == "bien_etre":
        max_questions = ASSESSMENT_STRUCTURE["bien_etre"]["questions_total"]
        prompts = {
            "fr": f"""Tu es un psychologue spécialisé en bien-être professionnel qui utilise une approche empathique et personnalisée. Question {question_number}/{max_questions}.

{adaptation_insight}{context}MISSION BIEN-ÊTRE:
Évaluer authentiquement le bien-être, l'engagement et la satisfaction professionnelle pour contribuer au score 6-30 points.

INTELLIGENCE EMPATHIQUE:
- Adapte selon les signaux émotionnels dans les réponses précédentes
- Personnalise selon le contexte professionnel et les défis évoqués
- Détecte les sources cachées de stress ou d'épanouissement
- Révèle les besoins professionnels non exprimés

STYLE BIENVEILLANT INTELLIGENT:
- Question courte et chaleureuse (10-18 mots)
- Commence par "Comment", "Que ressentez-vous", "Décrivez-moi"
- Situations professionnelles concrètes et émotionnellement significatives
- Révèle l'authenticité des sentiments professionnels

EXEMPLES INTELLIGENTS:
- "Que ressentez-vous dimanche soir en pensant au lundi ?"
- "Comment votre énergie évolue-t-elle au cours d'une journée type ?"
- "Décrivez-moi un moment récent où vous vous êtes senti épanoui au travail."

Réponds UNIQUEMENT avec la question.""",

            "en": f"""You are a psychologist specializing in professional well-being using an empathetic and personalized approach. Question {question_number}/{max_questions}.

{adaptation_insight}{context}WELL-BEING MISSION:
Authentically assess well-being, engagement and professional satisfaction to contribute to 6-30 points score.

EMPATHETIC INTELLIGENCE:
- Adapt based on emotional signals in previous responses
- Personalize according to professional context and mentioned challenges
- Detect hidden sources of stress or fulfillment
- Reveal unexpressed professional needs

INTELLIGENT CARING STYLE:
- Short and warm question (10-18 words)
- Start with "How", "What do you feel", "Describe"
- Concrete and emotionally significant professional situations
- Reveal authenticity of professional feelings

INTELLIGENT EXAMPLES:
- "What do you feel Sunday night thinking about Monday?"
- "How does your energy evolve during a typical day?"
- "Describe a recent moment when you felt fulfilled at work."

Respond ONLY with the question.""",

            "ar": f"""أنت خبير نفسي متخصص في الرفاهة المهنية يستخدم نهجاً تعاطفياً وشخصياً. السؤال {question_number}/{max_questions}.

{adaptation_insight}{context}مهمة الرفاهة:
قيم بأصالة الرفاهة والالتزام والرضا المهني للمساهمة في نتيجة 6-30 نقطة.

الذكاء التعاطفي:
- تكيف بناءً على الإشارات العاطفية في الإجابات السابقة
- شخصن وفقاً للسياق المهني والتحديات المذكورة
- اكتشف مصادر التوتر أو الإشباع المخفية
- اكشف الاحتياجات المهنية غير المعبر عنها

النمط الرعائي الذكي:
- سؤال قصير ودافئ (10-18 كلمة)
- ابدأ بـ "كيف", "ماذا تشعر", "صف لي"
- مواقف مهنية ملموسة ومهمة عاطفياً
- اكشف أصالة المشاعر المهنية

أمثلة ذكية:
- "ماذا تشعر ليلة الأحد وأنت تفكر في الاثنين؟"
- "كيف تتطور طاقتك خلال يوم عادي؟"
- "صف لي لحظة حديثة شعرت فيها بالإشباع في العمل."

أجب فقط بالسؤال."""
        }
    
    elif assessment_type == "resilience_ie":
        max_questions = ASSESSMENT_STRUCTURE["resilience_ie"]["questions_total"]
        prompts = {
            "fr": f"""Tu es un expert en psychologie de la résilience et intelligence émotionnelle utilisant une approche perspicace et personnalisée. Question {question_number}/{max_questions}.

{adaptation_insight}{context}MISSION RÉSILIENCE:
Évaluer les capacités réelles de gestion émotionnelle, d'adaptation et de résilience pour contribuer au score 8-40 points.

INTELLIGENCE ÉMOTIONNELLE:
- Adapte selon les mécanismes de défense et stratégies révélés précédemment
- Personnalise selon le niveau de maturité émotionnelle apparent
- Détecte les ressources internes et les vulnérabilités
- Révèle les patterns d'adaptation authentiques

STYLE PROFOND INTELLIGENT:
- Question courte et perspicace (10-18 mots)
- Commence par "Comment", "Que faites-vous", "Décrivez-moi"
- Situations émotionnellement challengeantes et réalistes
- Révèle les capacités réelles d'adaptation et de régulation

EXEMPLES INTELLIGENTS:
- "Comment votre corps et votre esprit réagissent-ils face à une injustice ?"
- "Que faites-vous quand vous sentez la colère monter en réunion ?"
- "Décrivez-moi comment vous récupérez après une journée difficile."

Réponds UNIQUEMENT avec la question.""",

            "en": f"""You are an expert in resilience psychology and emotional intelligence using an insightful and personalized approach. Question {question_number}/{max_questions}.

{adaptation_insight}{context}RESILIENCE MISSION:
Assess real capacities for emotional management, adaptation and resilience to contribute to 8-40 points score.

EMOTIONAL INTELLIGENCE:
- Adapt based on defense mechanisms and strategies previously revealed
- Personalize according to apparent emotional maturity level
- Detect internal resources and vulnerabilities
- Reveal authentic adaptation patterns

INTELLIGENT DEEP STYLE:
- Short and insightful question (10-18 words)
- Start with "How", "What do you do", "Describe"
- Emotionally challenging and realistic situations
- Reveal real adaptation and regulation capacities

INTELLIGENT EXAMPLES:
- "How do your body and mind react when facing injustice?"
- "What do you do when you feel anger rising in a meeting?"
- "Describe how you recover after a difficult day."

Respond ONLY with the question.""",

            "ar": f"""أنت خبير في علم نفس المرونة والذكاء العاطفي يستخدم نهجاً ثاقباً وشخصياً. السؤال {question_number}/{max_questions}.

{adaptation_insight}{context}مهمة المرونة:
قيم القدرات الحقيقية للإدارة العاطفية والتكيف والمرونة للمساهمة في نتيجة 8-40 نقطة.

الذكاء العاطفي:
- تكيف بناءً على آليات الدفاع والاستراتيجيات المكشوفة سابقاً
- شخصن وفقاً لمستوى النضج العاطفي الظاهر
- اكتشف الموارد الداخلية ونقاط الضعف
- اكشف أنماط التكيف الأصيلة

النمط العميق الذكي:
- سؤال قصير وثاقب (10-18 كلمة)
- ابدأ بـ "كيف", "ماذا تفعل", "صف لي"
- مواقف صعبة عاطفياً وواقعية
- اكشف قدرات التكيف والتنظيم الحقيقية

أمثلة ذكية:
- "كيف يتفاعل جسدك وعقلك عند مواجهة الظلم؟"
- "ماذا تفعل عندما تشعر بالغضب يتصاعد في اجتماع؟"
- "صف لي كيف تتعافى بعد يوم صعب."

أجب فقط بالسؤال."""
        }
    
    prompt = prompts.get(language, prompts["fr"])
      
    # Check if client is available
    if not client:
        logger.error("Groq client not available, using fallback")
        return get_fallback_question(trait, question_number, language, assessment_type)

    # Try AI generation with psychological intelligence parameters
    try:
        logger.info("Calling Groq API with psychological intelligence...")
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=70,  # Optimized for psychological questions
            temperature=0.75,  # Balanced for psychological creativity and consistency
        )
        
        generated_question = response.choices[0].message.content.strip()
        logger.info(f"Generated psychological question: {generated_question}")
        
        # Enhanced cleaning for psychological questions
        generated_question = generated_question.strip('"\'`')
        
        # Remove any psychological jargon that might have slipped through
        psychological_terms = ['névrotique', 'psychotique', 'pathologique', 'diagnostic', 'thérapie']
        for term in psychological_terms:
            if term in generated_question.lower():
                logger.warning(f"Psychological jargon detected: {term}, using fallback")
                return get_fallback_question(trait, question_number, language, assessment_type)
        
        # Remove any numbering or formatting
        import re
        generated_question = re.sub(r'^\d+[\.\)]\s*', '', generated_question)
        generated_question = re.sub(r'^Question\s*\d*\s*[:\-]?\s*', '', generated_question, flags=re.IGNORECASE)
        
        # Ensure proper question format
        if not generated_question.endswith('?'):
            generated_question += ' ?'
        
        # Clean and validate for Arabic
        if language == "ar":
            generated_question = clean_arabic_text(generated_question)
            arabic_chars = any('\u0600' <= c <= '\u06FF' for c in generated_question)
            if not arabic_chars or len(generated_question) < 8:
                logger.warning("Arabic validation failed, using fallback")
                return get_fallback_question(trait, question_number, language, assessment_type)
        
        # Ensure reasonable length for psychological questions
        words = generated_question.split()
        if len(words) > 22:
            generated_question = ' '.join(words[:18]) + " ?"
        elif len(words) < 5:
            # Too short for psychological depth, use fallback
            logger.warning("Generated question too short for psychological assessment, using fallback")
            return get_fallback_question(trait, question_number, language, assessment_type)
        
        # Validate psychological relevance
        action_words = {
            "fr": ["comment", "que", "quoi", "décrivez", "racontez", "ressentez", "faites-vous"],
            "en": ["how", "what", "describe", "tell", "feel", "do you"],
            "ar": ["كيف", "ماذا", "صف", "حدثني", "تشعر", "تفعل"]
        }
        
        question_lower = generated_question.lower()
        if not any(word in question_lower for word in action_words.get(language, action_words["fr"])):
            logger.warning("Generated question lacks psychological engagement, using fallback")
            return get_fallback_question(trait, question_number, language, assessment_type)
        
        return generated_question
        
    except Exception as e:
        logger.error(f"Error generating psychological question: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return get_fallback_question(trait, question_number, language, assessment_type)

def get_fallback_question(trait, question_number, language, assessment_type):
    """Get fallback questions for different assessment types"""
    
    logger.info(f"Using fallback question for {trait}, {language}, {assessment_type}")
    
    # Expanded fallback questions for each assessment type
    fallback_questions = {
        "big_five": {
            "ouverture": {
                "fr": [
                    "Comment réagissez-vous face à une idée complètement nouvelle ?",
                    "Décrivez une situation où votre curiosité vous a mené vers une découverte.",
                    "Que faites-vous quand vous cherchez l'inspiration ?",
                    "Comment abordez-vous les défis créatifs ?",
                    "Quel rôle joue l'imagination dans votre vie quotidienne ?"
                ],
                "en": [
                    "How do you react when faced with a completely new idea?",
                    "Describe a situation where your curiosity led you to a discovery.",
                    "What do you do when you're looking for inspiration?",
                    "How do you approach creative challenges?",
                    "What role does imagination play in your daily life?"
                ],
                "ar": [
                    "كيف تتفاعل عندما تواجه فكرة جديدة تماماً؟",
                    "صف موقفاً حيث قادك فضولك إلى اكتشاف.",
                    "ماذا تفعل عندما تبحث عن الإلهام؟",
                    "كيف تتعامل مع التحديات الإبداعية؟",
                    "ما دور الخيال في حياتك اليومية؟"
                ]
            },
            "conscienciosité": {
                "fr": [
                    "Comment organisez-vous votre journée de travail ?",
                    "Racontez-moi un moment où vous avez dû persévérer.",
                    "Comment gérez-vous vos échéances importantes ?",
                    "Que faites-vous pour maintenir votre discipline ?",
                    "Comment planifiez-vous vos objectifs à long terme ?"
                ],
                "en": [
                    "How do you organize your work day?",
                    "Tell me about a time when you had to persevere.",
                    "How do you manage important deadlines?",
                    "What do you do to maintain your discipline?",
                    "How do you plan your long-term goals?"
                ],
                "ar": [
                    "كيف تنظم يوم عملك؟",
                    "حدثني عن وقت اضطررت فيه للمثابرة.",
                    "كيف تدير المواعيد النهائية المهمة؟",
                    "ماذا تفعل للحفاظ على انضباطك؟",
                    "كيف تخطط لأهدافك طويلة المدى؟"
                ]
            },
            "extraversion": {
                "fr": [
                    "Comment vous sentez-vous dans les situations sociales ?",
                    "Préférez-vous travailler en équipe ou individuellement ?",
                    "Comment rechargez-vous vos batteries ?",
                    "Que faites-vous pour rencontrer de nouvelles personnes ?",
                    "Comment exprimez-vous vos idées en public ?"
                ],
                "en": [
                    "How do you feel in social situations?",
                    "Do you prefer working in teams or individually?",
                    "How do you recharge your batteries?",
                    "What do you do to meet new people?",
                    "How do you express your ideas in public?"
                ],
                "ar": [
                    "كيف تشعر في المواقف الاجتماعية؟",
                    "هل تفضل العمل في فريق أم بشكل فردي؟",
                    "كيف تجدد طاقتك؟",
                    "ماذا تفعل للقاء أشخاص جدد؟",
                    "كيف تعبر عن أفكارك في العلن؟"
                ]
            },
            "agréabilité": {
                "fr": [
                    "Comment réagissez-vous quand quelqu'un vous demande de l'aide ?",
                    "Décrivez une situation de conflit que vous avez gérée.",
                    "Comment maintenez-vous de bonnes relations avec les autres ?",
                    "Que faites-vous face à une personne difficile ?",
                    "Comment exprimez-vous votre désaccord avec respect ?"
                ],
                "en": [
                    "How do you react when someone asks for your help?",
                    "Describe a conflict situation you've handled.",
                    "How do you maintain good relationships with others?",
                    "What do you do when facing a difficult person?",
                    "How do you express disagreement respectfully?"
                ],
                "ar": [
                    "كيف تتفاعل عندما يطلب منك شخص المساعدة؟",
                    "صف موقف صراع تعاملت معه.",
                    "كيف تحافظ على علاقات جيدة مع الآخرين؟",
                    "ماذا تفعل عند مواجهة شخص صعب؟",
                    "كيف تعبر عن اختلافك في الرأي باحترام؟"
                ]
            },
            "stabilité émotionnelle": {
                "fr": [
                    "Comment gérez-vous le stress au quotidien ?",
                    "Racontez-moi comment vous surmontez les difficultés.",
                    "Que faites-vous quand vous vous sentez anxieux ?",
                    "Comment maintenez-vous votre équilibre émotionnel ?",
                    "Comment réagissez-vous aux critiques ?"
                ],
                "en": [
                    "How do you manage daily stress?",
                    "Tell me how you overcome difficulties.",
                    "What do you do when you feel anxious?",
                    "How do you maintain your emotional balance?",
                    "How do you react to criticism?"
                ],
                "ar": [
                    "كيف تدير التوتر اليومي؟",
                    "حدثني كيف تتغلب على الصعوبات.",
                    "ماذا تفعل عندما تشعر بالقلق؟",
                    "كيف تحافظ على توازنك العاطفي؟",
                    "كيف تتفاعل مع النقد؟"
                ]
            }
        },
        "disc": {
            "dominant": {
                "fr": ["Comment prenez-vous vos décisions importantes ?", "Que faites-vous face à un défi urgent ?"],
                "en": ["How do you make important decisions?", "What do you do when facing an urgent challenge?"],
                "ar": ["كيف تتخذ قراراتك المهمة؟", "ماذا تفعل عند مواجهة تحدٍ عاجل؟"]
            },
            "influent": {
                "fr": ["Comment motivez-vous les autres ?", "Comment convainquez-vous les gens de vos idées ?"],
                "en": ["How do you motivate others?", "How do you convince people of your ideas?"],
                "ar": ["كيف تحفز الآخرين؟", "كيف تقنع الناس بأفكارك؟"]
            },
            "stable": {
                "fr": ["Comment créez-vous la stabilité dans votre équipe ?", "Que valorisez-vous dans les relations ?"],
                "en": ["How do you create stability in your team?", "What do you value in relationships?"],
                "ar": ["كيف تخلق الاستقرار في فريقك؟", "ما الذي تقدره في العلاقات؟"]
            },
            "conforme": {
                "fr": ["Comment assurez-vous la qualité de votre travail ?", "Que faites-vous pour respecter les procédures ?"],
                "en": ["How do you ensure quality in your work?", "What do you do to follow procedures?"],
                "ar": ["كيف تضمن جودة عملك؟", "ماذا تفعل لاتباع الإجراءات؟"]
            }
        },
        "bien_etre": {
            "fr": [
                "Comment évaluez-vous votre satisfaction au travail ?",
                "Que vous apporte le plus d'épanouissement professionnel ?",
                "Comment maintenez-vous votre motivation au travail ?",
                "Quel est votre niveau d'engagement dans vos tâches ?",
                "Comment gérez-vous l'équilibre vie privée-professionnelle ?",
                "Que changeriez-vous dans votre environnement de travail ?"
            ],
            "en": [
                "How do you evaluate your job satisfaction?",
                "What brings you the most professional fulfillment?",
                "How do you maintain your motivation at work?",
                "What is your level of engagement in your tasks?",
                "How do you manage work-life balance?",
                "What would you change in your work environment?"
            ],
            "ar": [
                "كيف تقيم رضاك عن العمل؟",
                "ما الذي يجلب لك أكبر إشباع مهني؟",
                "كيف تحافظ على دافعيتك في العمل؟",
                "ما مستوى التزامك في مهامك؟",
                "كيف تدير التوازن بين الحياة والعمل؟",
                "ما الذي تغيره في بيئة عملك؟"
            ]
        },
        "resilience_ie": {
            "fr": [
                "Comment gérez-vous les émotions fortes ?",
                "Que faites-vous face aux changements imprévus ?",
                "Comment vous adaptez-vous aux situations difficiles ؟",
                "Quelle est votre stratégie pour surmonter l'échec ?",
                "Comment développez-vous votre intelligence émotionnelle ?",
                "Comment aidez-vous les autres dans les moments difficiles ?",
                "Que faites-vous pour maintenir votre résilience ?",
                "Comment gérez-vous la pression et le stress ?"
            ],
            "en": [
                "How do you manage strong emotions?",
                "What do you do when facing unexpected changes?",
                "How do you adapt to difficult situations?",
                "What is your strategy for overcoming failure?",
                "How do you develop your emotional intelligence?",
                "How do you help others during difficult times?",
                "What do you do to maintain your resilience?",
                "How do you handle pressure and stress?"
            ],
            "ar": [
                "كيف تدير المشاعر القوية؟",
                "ماذا تفعل عند مواجهة تغييرات غير متوقعة؟",
                "كيف تتكيف مع المواقف الصعبة؟",
                "ما استراتيجيتك للتغلب على الفشل؟",
                "كيف تطور ذكاءك العاطفي؟",
                "كيف تساعد الآخرين في الأوقات الصعبة؟",
                "ماذا تفعل للحفاظ على مرونتك؟",
                "كيف تتعامل مع الضغط والتوتر؟"
            ]
        }
    }
    
    # Get questions for the specific assessment and trait
    if assessment_type in fallback_questions:
        if assessment_type == "big_five" and trait in fallback_questions[assessment_type]:
            questions = fallback_questions[assessment_type][trait].get(language, [])
            if questions and question_number <= len(questions):
                return questions[question_number - 1]
        elif assessment_type == "disc" and trait in fallback_questions[assessment_type]:
            questions = fallback_questions[assessment_type][trait].get(language, [])
            if questions and question_number <= len(questions):
                return questions[question_number - 1]
        elif assessment_type in ["bien_etre", "resilience_ie"]:
            questions = fallback_questions[assessment_type].get(language, [])
            if questions and question_number <= len(questions):
                return questions[question_number - 1]
    
    # Final fallback
    fallbacks = {
        "fr": f"Parlez-moi de votre expérience avec {trait}.",
        "en": f"Tell me about your experience with {trait}.",
        "ar": f"حدثني عن تجربتك مع {trait}."
    }
    
    return fallbacks.get(language, fallbacks["fr"])

def analyze_and_score_answer(answer_text, trait, all_answers_for_trait, language, assessment_type="big_five"):
    """Analyze and score answers according to specifications (score 1-5 per question)"""
    
    # Build context
    context = ""
    if all_answers_for_trait:
        context = f"All previous answers for trait/dimension '{trait}':\n"
        for i, ans in enumerate(all_answers_for_trait, 1):
            context += f"Answer {i}: {ans}\n"
        context += "\n"
    
    # Different scoring based on assessment type
    if assessment_type == "big_five":
        prompts = {
            "fr": f"""Tu es un psychologue expert en Big Five. Analyse cette réponse pour le trait "{trait}":

{context}Nouvelle réponse: "{answer_text}"

Évalue cette réponse sur une échelle de 1 à 5 pour contribuer au score total de 5-25 points:
1 = Très faible manifestation du trait
2 = Faible manifestation  
3 = Manifestation modérée
4 = Forte manifestation
5 = Très forte manifestation

Réponds uniquement par un chiffre de 1 à 5.""",

            "en": f"""You are a Big Five expert psychologist. Analyze this answer for trait "{trait}":

{context}New answer: "{answer_text}"

Rate this answer on a scale of 1 to 5 to contribute to total score of 5-25 points:
1 = Very low trait manifestation
2 = Low manifestation
3 = Moderate manifestation  
4 = High manifestation
5 = Very high manifestation

Respond only with a number from 1 to 5.""",

            "ar": f"""أنت خبير نفسي في العوامل الخمسة الكبرى. حلل هذه الإجابة للسمة "{trait}":

{context}إجابة جديدة: "{answer_text}"

قيّم هذه الإجابة على مقياس من 1 إلى 5 للمساهمة في النتيجة الإجمالية 5-25 نقطة:
1 = مظهر ضعيف جداً للسمة
2 = مظهر ضعيف
3 = مظهر متوسط
4 = مظهر قوي
5 = مظهر قوي جداً

أجب برقم واحد فقط من 1 إلى 5."""
        }
    
    elif assessment_type in ["bien_etre", "resilience_ie"]:
        prompts = {
            "fr": f"""Tu es un expert en évaluation psychologique. Analyse cette réponse pour "{assessment_type}":

{context}Nouvelle réponse: "{answer_text}"

Évalue cette réponse sur une échelle de 1 à 5:
1 = Niveau très faible
2 = Niveau faible
3 = Niveau modéré  
4 = Niveau élevé
5 = Niveau très élevé

Réponds uniquement par un chiffre de 1 à 5.""",

            "en": f"""You are a psychological assessment expert. Analyze this answer for "{assessment_type}":

{context}New answer: "{answer_text}"

Rate this answer on a scale of 1 to 5:
1 = Very low level
2 = Low level
3 = Moderate level
4 = High level
5 = Very high level

Respond only with a number from 1 to 5.""",

            "ar": f"""أنت خبير في التقييم النفسي. حلل هذه الإجابة لـ "{assessment_type}":

{context}إجابة جديدة: "{answer_text}"

قيّم هذه الإجابة على مقياس من 1 إلى 5:
1 = مستوى منخفض جداً
2 = مستوى منخفض
3 = مستوى متوسط
4 = مستوى عالي
5 = مستوى عالي جداً

أجب برقم واحد فقط من 1 إلى 5."""
        }
    
    elif assessment_type == "disc":
        # DISC uses different scoring - just return preference strength
        prompts = {
            "fr": f"""Analyse cette réponse pour le style DISC "{trait}":

{context}Nouvelle réponse: "{answer_text}"

Sur une échelle de 1 à 5, à quel point cette réponse montre-t-elle une préférence pour le style {trait}?

Réponds uniquement par un chiffre de 1 à 5.""",

            "en": f"""Analyze this answer for DISC style "{trait}":

{context}New answer: "{answer_text}"

On a scale of 1 to 5, how much does this answer show a preference for {trait} style?

Respond only with a number from 1 to 5.""",

            "ar": f"""حلل هذه الإجابة لنمط DISC "{trait}":

{context}إجابة جديدة: "{answer_text}"

على مقياس من 1 إلى 5، إلى أي مدى تظهر هذه الإجابة تفضيلاً لنمط {trait}؟

أجب برقم واحد فقط من 1 إلى 5."""
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
        # Fallback scoring based on answer quality
        if not answer_text.strip():
            return 1
        elif len(answer_text.split()) < 5:
            return 2
        elif len(answer_text.split()) < 15:
            return 3
        elif len(answer_text.split()) < 30:
            return 4
        else:
            return 5

def should_ask_followup_question(trait, question_number, latest_answer, language, assessment_type="big_five"):
    """Determine if we should ask a follow-up question based on assessment structure"""
    
    # Get max questions for this assessment type
    if assessment_type == "big_five":
        max_questions = ASSESSMENT_STRUCTURE["big_five"]["questions_per_trait"]
    elif assessment_type == "disc":
        max_questions = 4  # 4 questions per DISC style
    elif assessment_type == "bien_etre":
        max_questions = ASSESSMENT_STRUCTURE["bien_etre"]["questions_total"]
    elif assessment_type == "resilience_ie":
        max_questions = ASSESSMENT_STRUCTURE["resilience_ie"]["questions_total"]
    else:
        max_questions = 4
    
    if question_number >= max_questions:
        return False
    
    # For Big Five, ask all 5 questions as per specifications
    if assessment_type == "big_five":
        return question_number < 5
    
    # For other assessments, use AI to determine
    prompts = {
        "fr": f"""Basé sur cette réponse pour "{trait}" (question {question_number}/{max_questions}): "{latest_answer}"

Dois-je poser une autre question pour mieux évaluer cette dimension?

Réponds UNIQUEMENT "OUI" ou "NON".""",

        "en": f"""Based on this answer for "{trait}" (question {question_number}/{max_questions}): "{latest_answer}"

Should I ask another question to better assess this dimension?

Respond ONLY "YES" or "NO".""",

        "ar": f"""بناءً على هذه الإجابة لـ "{trait}" (السؤال {question_number}/{max_questions}): "{latest_answer}"

هل يجب أن أطرح سؤالاً آخر لتقييم هذا البعد بشكل أفضل؟

أجب فقط بـ "نعم" أو "لا"."""
    }

    prompt = prompts.get(language, prompts["fr"])

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.1,
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer in ["OUI", "YES", "نعم"] and question_number < max_questions
    except Exception as e:
        logger.error(f"Error determining follow-up: {e}")
        return question_number < (max_questions - 1)  # Default: ask n-1 questions

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
