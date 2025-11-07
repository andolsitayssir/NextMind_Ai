"""
Fallback content system - NO API dependency
Complete questions, scoring, and analysis without external calls
"""

# ============================================================================
# FALLBACK QUESTIONS - Complete set for all assessments
# ============================================================================

FALLBACK_QUESTIONS = {
    'fr': {
        'big_five': {
            'ouverture': [
                "Donnez un exemple récent (la semaine ou le mois dernier) d’une idée originale que vous avez testée — que vous avez fait, pourquoi, et quel a été le résultat.",
                "À quelle fréquence (jamais / parfois / souvent) cherchez-vous des sources nouvelles (articles, cours, podcasts) pour un problème au travail ? Précisez lesquelles.",
                "Quand un sujet vous paraît confus, quelles actions concrètes entreprenez-vous pour le comprendre (ex : tester, demander, lire, prototyper) ?"
            ],
            'conscienciosité': [
                "Décrivez comment vous planifiez une tâche importante : outils, étapes et comment vous suivez l’avancement.",
                "Racontez une fois où un retard est survenu ; quelles mesures précises avez-vous prises pour rattraper le temps perdu ?",
                "Donnez un exemple d’une habitude quotidienne ou d’un checklist que vous utilisez pour éviter les erreurs."
            ],
            'extraversion': [
                "Lors d’un projet d’équipe, quelle action concrète prenez-vous pour lancer la collaboration (ex : proposer l’ordre du jour, contacter des personnes) ?",
                "Combien de fois par mois (0 / 1–2 / 3+) initiez-vous des conversations professionnelles pour faire avancer un sujet ?",
                "Décrivez une situation où vous avez créé du lien avec un collègue — ce que vous avez fait et l’impact."
            ],
            'agréabilité': [
                "Donnez un exemple récent où vous avez exprimé une opinion contre l’avis majoritaire : comment vous l’avez formulée et quel a été l’aboutissement.",
                "Quand un collègue demande de l’aide qui nuit à votre planning, quelles actions prenez-vous pour aider tout en protégeant vos priorités ?",
                "Expliquez une méthode que vous utilisez pour résoudre un désaccord de façon constructive (phrases, étapes, compromis)."
            ],
            'stabilité émotionnelle': [
                "Décrivez un incident stressant récent : ce que vous avez fait sur le moment (respiration, pause, escalation, plan d’action) et l’effet sur la situation.",
                "Quand vous vous sentez submergé·e, quelles deux actions concrètes vous aident à revenir à un état productif ?",
                "Donnez un exemple où vous avez transformé une critique en amélioration mesurable (ce que vous avez changé)."
            ]
        },
        'disc': {
            'dominant': [
                "Racontez une décision urgente que vous avez prise : quelles informations vous avez utilisées et quelle action immédiate vous avez menée.",
                "Quand un obstacle bloque l’avancement, quelle première mesure pratique prenez-vous pour débloquer le projet ?",
                "Donnez un exemple où vous avez imposé un cap clair — résultats et retours de l’équipe."
            ],
            'influent': [
                "Décrivez une situation où vous avez persuadé plusieurs personnes — quels arguments ou supports avez-vous utilisés (démonstration, storytelling, chiffres) ?",
                "Combien de présentations ou propositions par trimestre faites-vous pour mobiliser une équipe ou un client ?",
                "Donnez un exemple d’un message ou post (email, Slack, réseau) que vous avez utilisé pour motiver les autres et l’impact obtenu."
            ],
            'stable': [
                "Expliquez une routine que vous mettez en place pour conserver la stabilité d’un projet sur le long terme.",
                "Quand un changement est annoncé, quelles étapes pratiques suivez-vous pour aider l’équipe à s’adapter ?",
                "Donnez un exemple où votre présence ou votre soutien direct a stabilisé une situation difficile."
            ],
            'conforme': [
                "Comment vérifiez-vous la qualité d’un livrable (étapes, outils, personnes impliquées) ? Donnez un exemple concret.",
                "Quand une procédure vous semble inadaptée, quelles actions sures et respectueuses entreprenez-vous ?",
                "Décrivez un défaut repéré grâce à votre attention aux détails et comment vous l’avez corrigé."
            ]
        },
        'bien_etre': [
            "Décrivez vos trois actions régulières (ex : sport, sommeil, pause écran) pour préserver votre énergie pendant la semaine.",
            "Quand vous sentez que votre équilibre travail/vie perso bascule, quelles mesures immédiates prenez-vous (ex : couper notifications, déléguer) ?",
            "Donnez un exemple concret d’une semaine où vous avez amélioré votre bien-être et comment vous l’avez mesuré."
        ],
        'resilience_ie': [
            "Racontez un échec récent : quelles étapes concrètes avez-vous suivies pour analyser, apprendre et repartir ?",
            "Comment repérez-vous une émotion forte au travail et quelles actions pratiques faites-vous pour la gérer (ex : noter, parler, pause) ?",
            "Donnez un exemple où vous avez utilisé un feedback négatif pour obtenir un résultat mesurable différent."
        ]
    },

    'en': {
        'big_five': {
            'ouverture': [
                "Give a recent example (past week or month) of a new idea you tried — what you did, why, and what happened.",
                "How often (never / sometimes / often) do you seek new sources (articles, courses, podcasts) to solve a work problem? Name any you use.",
                "When a topic is unclear, what concrete steps do you take to understand it (prototype, ask, read, test)?"
            ],
            'conscienciosité': [
                "Describe how you plan an important task: tools, steps, and how you track progress.",
                "Tell about a time a delay happened; what exact actions did you take to recover lost time?",
                "Give an example of a daily habit or checklist you use to prevent mistakes."
            ],
            'extraversion': [
                "In a team project, what concrete action do you take to kick off collaboration (e.g., set agenda, contact stakeholders)?",
                "How many times per month (0 / 1–2 / 3+) do you proactively start conversations to move work forward?",
                "Describe a time you built rapport with a colleague — what you did and the impact."
            ],
            'agréabilité': [
                "Share a recent example when you voiced an opinion against the majority: how you said it and what followed.",
                "When a teammate asks for help that conflicts with your schedule, what do you do to help while protecting priorities?",
                "Explain a method you use to resolve disagreements constructively (phrases, steps, compromise)."
            ],
            'stabilité émotionnelle': [
                "Describe a stressful incident recently: what you did in the moment (breathing, pause, escalate, plan) and the outcome.",
                "When overwhelmed, which two concrete actions help you return to productive mode?",
                "Give an example where you turned criticism into a measurable improvement (what changed)."
            ]
        },
        'disc': {
            'dominant': [
                "Tell about an urgent decision you made: what info you used and what immediate action you took.",
                "When something blocks progress, what is the first practical step you take to unblock the project?",
                "Give an example where you set a clear direction — results and team feedback."
            ],
            'influent': [
                "Describe a time you persuaded a group — what arguments or materials did you use (demo, story, data)?",
                "How many presentations or proposals per quarter do you make to rally a team or client?",
                "Give an example of a message (email, Slack, post) you used to motivate others and its impact."
            ],
            'stable': [
                "Explain a routine you put in place to keep a project steady over time.",
                "When change is announced, what practical steps do you take to help the team adapt?",
                "Give an example where your presence or support stabilized a difficult situation."
            ],
            'conforme': [
                "How do you verify the quality of a deliverable (steps, tools, people involved)? Give a concrete instance.",
                "When a rule seems unnecessary, what respectful and safe actions do you take?",
                "Describe a defect you spotted thanks to attention to detail and how you fixed it."
            ]
        },
        'bien_etre': [
            "Describe three regular actions you take (e.g., exercise, sleep, screen breaks) to preserve energy during the week.",
            "If your work-life balance starts to slip, what immediate measures do you take (e.g., mute notifications, delegate)?",
            "Give an example of a week where you improved your well-being and how you measured it."
        ],
        'resilience_ie': [
            "Tell about a recent setback: the concrete steps you took to analyze, learn, and move forward.",
            "How do you notice strong emotions at work and what practical actions do you take (e.g., jot down, speak with someone, take a pause)?",
            "Give an example when negative feedback led to a measurable change in your results."
        ]
    },

    'ar': {
        'big_five': {
            'ouverture': [
                "اذكر مثالًا حديثًا (خلال الأسبوع أو الشهر الماضي) عن فكرة جديدة جربتها — ماذا فعلت ولماذا وما كانت النتيجة.",
                "كم مرة (أبدًا / أحيانًا / غالبًا) تبحث عن مصادر جديدة (مقالات، دورات، بودكاست) لحل مشكلة في العمل؟ اذكر أمثلة.",
                "عندما يكون الموضوع غير واضح، ما الإجراءات العملية التي تتخذها لتفهمه (اختبار، سؤال، قراءة، نموذج أولي)؟"
            ],
            'conscienciosité': [
                "صف كيف تخطط لمهمة مهمة: الأدوات، الخطوات، وكيف تتابع التقدم.",
                "اخبر عن مرة حدث فيها تأخير؛ ما الإجراءات المحددة التي اتخذتها لتعويض الوقت المفقود؟",
                "اذكر عادة يومية أو قائمة تحقق تستخدمها لتجنب الأخطاء."
            ],
            'extraversion': [
                "في مشروع فريق، ما الإجراء العملي الذي تقوم به لإطلاق التعاون (مثل تحديد جدول أعمال أو التواصل مع الأطراف)؟",
                "كم مرة في الشهر (0 / 1–2 / 3+) تبدأ محادثات مهنية لدفع العمل قدمًا؟",
                "صف موقفًا ربحت فيه علاقة جيدة مع زميل — ماذا فعلت وما الأثر."
            ],
            'agréabilité': [
                "قدم مثالًا حديثًا عندما عبرت عن رأي مخالف للأغلبية: كيف عبرت وما الذي حدث بعد ذلك.",
                "عندما يطلب زميل مساعدة تؤثر على جدولك، ماذا تفعل لمساعدته مع حماية أولوياتك؟",
                "اشرح طريقة تتبعها لحل الخلافات بشكل بنّاء (جمل، خطوات، حل وسط)."
            ],
            'stabilité émotionnelle': [
                "وصف موقفًا ضاغطًا حدث مؤخرًا: ماذا فعلت في اللحظة (تنفّس، استراحة، تصعيد، خطة) وما كانت النتيجة.",
                "عند الشعور بالإرهاق، ما خطوتان عمليتان تساعدانك على العودة إلى حالة إنتاجية؟",
                "اعط مثالًا كيف حولت نقدًا إلى تحسن قابل للقياس (ما الذي غيرته)."
            ]
        },
        'disc': {
            'dominant': [
                "احكِ عن قرار عاجل اتخذته: ما المعلومات التي اعتمدت عليها وما الإجراء الفوري الذي قمت به.",
                "عندما يتوقف التقدّم بسبب عقبة، ما أول خطوتين عمليتين تفعلهما لإزالة العائق؟",
                "اذكر مثالًا وضعت فيه اتجاهًا واضحًا — النتائج وردود فعل الفريق."
            ],
            'influent': [
                "صف موقفًا أقنعت فيه مجموعة — ما الحجج أو الوسائل التي استخدمتها (عرض عملي، قصة، بيانات)؟",
                "كم عدد العروض أو المقترحات التي تقدمها كل ربع سنة لتحفيز فريق أو عميل؟",
                "اذكر مثالًا لرسالة (بريد، Slack، منشور) استخدمتها لتحفيز الآخرين وما أثرها."
            ],
            'stable': [
                "اشرح روتينًا وضعته للحفاظ على استقرار المشروع على المدى الطويل.",
                "عند الإعلان عن تغيير، ما الخطوات العملية التي تتخذها لمساعدة الفريق على التكيّف؟",
                "اذكر مثالًا حيث كان لدعمك دور في استقرار موقف صعب."
            ],
            'conforme': [
                "كيف تتحقق من جودة مخرجاتك (خطوات، أدوات، من يشارك)؟ اذكر مثالًا محددًا.",
                "عندما تبدو قاعدة غير مناسبة، ما الإجراءات المهذبة والآمنة التي تتخذها؟",
                "صف عيبًا اكتشفته بفضل اهتمامك بالتفاصيل وكيف أصلحته."
            ]
        },
        'bien_etre': [
            "صف ثلاث أفعال منتظمة تقوم بها (مثل الرياضة، النوم، فواصل الشاشة) لتحافظ على طاقتك خلال الأسبوع.",
            "إذا بدأ توازنك بين العمل والحياة بالانهيار، ما الإجراءات الفورية التي تتخذها (مثل كتم الإشعارات، التفويض)؟",
            "اذكر أسبوعًا حسّنت فيه رفاهيتك وكيف قست ذلك."
        ],
        'resilience_ie': [
            "احكِ عن نكسة حديثة: الخطوات العملية التي اتبعتها لتحليلها، التعلم منها والمضي قدمًا.",
            "كيف تلاحظ مشاعرك القوية في العمل وما الأفعال العملية التي تقوم بها (مثل تدوين، التحدث مع شخص، أخذ استراحة)؟",
            "اذكر مثالًا عندما أدى تعليقات سلبية إلى تغيير ملموس في نتائجك."
        ]
    }
}


import random

# ============================================================================
# RANDOM REALISTIC SCORING - For DEMO purposes
# ============================================================================
   
def fallback_score_answer(answer_text, trait, assessment_type, language='fr'):
    """
    Generate realistic random score for DEMO
    Scores vary based on answer length to appear more realistic

    """
    answer_length = len(answer_text.split())
    
    # More realistic scoring based on effort
    if answer_length < 5:
        # Very short answer = lower score range
        score = random.uniform(2.0, 4.5)
    elif answer_length < 15:
        # Short answer = moderate-low score
        score = random.uniform(3.5, 6.0)
    elif answer_length < 40:
        # Medium answer = moderate-good score
        score = random.uniform(5.0, 7.5)
    elif answer_length < 80:
        # Good answer = good-high score
        score = random.uniform(6.5, 8.5)
    else:
        # Detailed answer = high score range
        score = random.uniform(7.0, 9.5)
    
    # Add slight variation for realism
    score += random.uniform(-0.3, 0.3)
    
    # Adjust for assessment type
    if assessment_type == 'disc':
        # DISC uses 1-5 scale
        score = score / 2
        return max(1.0, min(5.0, round(score, 1)))
    else:
        # Big Five, Bien-être, Resilience use 1-10 scale
        return max(1.0, min(10.0, round(score, 1)))


# ============================================================================
# RANDOM ANALYSIS GENERATION - For DEMO
# ============================================================================

def fallback_generate_analysis(trait, score, assessment_type, language='fr'):
    """
    Generate random but realistic analysis for DEMO
    """
    analysis_templates = _get_analysis_templates(language)
    
    # Determine score category
    if assessment_type == 'disc':
        max_score = 5
    else:
        max_score = 10
    
    percentage = (score / max_score) * 100
    
    # Randomize category slightly for variety
    if percentage >= 75:
        categories = ['high', 'moderate_high']
        category = random.choice(categories)
    elif percentage >= 55:
        categories = ['moderate_high', 'moderate']
        category = random.choice(categories)
    elif percentage >= 35:
        categories = ['moderate', 'low']
        category = random.choice(categories)
    else:
        category = 'low'
    
    # Get base template
    trait_templates = analysis_templates.get(trait, {})
    template = trait_templates.get(category, trait_templates.get('moderate', {}))
    
    # If no template, generate generic
    if not template:
        return {
            'observations': f"Votre score de {score:.1f} reflète votre niveau dans ce trait.",
            'points_forts': [
                "Capacité de réflexion",
                "Expression personnelle",
                "Conscience de soi"
            ],
            'zones_developpement': [
                "Continuer à développer ce trait",
                "Explorer de nouvelles approches"
            ]
        }
    
    return {
        'observations': template.get('observations', ''),
        'points_forts': template.get('strengths', []),
        'zones_developpement': template.get('development', [])
    }


def _get_analysis_templates(language='fr'):
    """Analysis templates by trait - same as before"""
    if language == 'fr':
        return {
            'ouverture': {
                'high': {
                    'observations': "Vous démontrez une forte ouverture d'esprit, avec une curiosité intellectuelle marquée.",
                    'strengths': [
                        "Excellence dans l'innovation et la créativité",
                        "Capacité à voir les situations sous différents angles",
                        "Facilité d'adaptation aux changements"
                    ],
                    'development': [
                        "Équilibrer l'innovation avec la mise en œuvre pratique",
                        "Développer la patience envers les approches traditionnelles"
                    ]
                },
                'moderate_high': {
                    'observations': "Vous montrez une bonne ouverture aux nouvelles idées tout en maintenant un certain pragmatisme.",
                    'strengths': [
                        "Équilibre entre innovation et tradition",
                        "Capacité à évaluer objectivement les nouvelles approches"
                    ],
                    'development': [
                        "Oser davantage sortir de votre zone de confort",
                        "Développer votre créativité dans des contextes variés"
                    ]
                },
                'moderate': {
                    'observations': "Votre ouverture d'esprit est équilibrée, vous savez quand innover et quand suivre les méthodes établies.",
                    'strengths': [
                        "Pragmatisme dans l'adoption de nouvelles idées",
                        "Capacité à évaluer les risques et bénéfices"
                    ],
                    'development': [
                        "Explorer davantage de perspectives alternatives",
                        "Développer votre curiosité intellectuelle"
                    ]
                },
                'low': {
                    'observations': "Vous préférez les approches éprouvées et la stabilité aux changements fréquents.",
                    'strengths': [
                        "Cohérence dans vos méthodes de travail",
                        "Fiabilité et prévisibilité"
                    ],
                    'development': [
                        "S'ouvrir progressivement aux nouvelles idées",
                        "Cultiver la curiosité et l'expérimentation contrôlée"
                    ]
                }
            },
            'conscienciosité': {
                'high': {
                    'observations': "Vous faites preuve d'une grande rigueur organisationnelle et d'une discipline remarquable.",
                    'strengths': [
                        "Excellence dans la planification et l'organisation",
                        "Fiabilité et respect systématique des engagements",
                        "Attention remarquable aux détails"
                    ],
                    'development': [
                        "Apprendre à déléguer et faire confiance",
                        "Développer la flexibilité face aux imprévus"
                    ]
                },
                'moderate': {
                    'observations': "Votre niveau d'organisation est adapté aux besoins, sans rigidité excessive.",
                    'strengths': [
                        "Flexibilité dans l'approche organisationnelle",
                        "Capacité d'adaptation aux contextes"
                    ],
                    'development': [
                        "Développer des routines plus structurées",
                        "Améliorer la planification à long terme"
                    ]
                },
                'low': {
                    'observations': "Vous privilégiez la spontanéité et l'adaptabilité à la planification stricte.",
                    'strengths': [
                        "Grande flexibilité et adaptabilité",
                        "Créativité dans la résolution de problèmes"
                    ],
                    'development': [
                        "Mettre en place des systèmes d'organisation de base",
                        "Développer la discipline dans le suivi des tâches"
                    ]
                }
            },
            'extraversion': {
                'high': {
                    'observations': "Vous êtes très énergique et tirez votre énergie des interactions sociales.",
                    'strengths': [
                        "Excellentes compétences en communication",
                        "Capacité à motiver et énergiser les équipes",
                        "Aisance dans les situations sociales"
                    ],
                    'development': [
                        "Prendre du temps pour la réflexion individuelle",
                        "Respecter le besoin de calme des introvertis"
                    ]
                },
                'moderate': {
                    'observations': "Vous équilibrez interactions sociales et moments de solitude.",
                    'strengths': [
                        "Adaptabilité sociale",
                        "Capacité à travailler seul ou en équipe"
                    ],
                    'development': [
                        "Développer davantage votre réseau professionnel",
                        "Améliorer votre présence en groupe"
                    ]
                },
                'low': {
                    'observations': "Vous préférez les interactions en petits groupes et la réflexion individuelle.",
                    'strengths': [
                        "Capacité d'écoute approfondie",
                        "Réflexion posée et analyse détaillée"
                    ],
                    'development': [
                        "Développer votre aisance en grand groupe",
                        "Exprimer davantage vos idées spontanément"
                    ]
                }
            },
            'agréabilité': {
                'high': {
                    'observations': "Vous privilégiez l'harmonie et la coopération dans vos relations professionnelles.",
                    'strengths': [
                        "Excellente capacité de collaboration",
                        "Empathie et compréhension des autres",
                        "Facilitation des relations d'équipe"
                    ],
                    'development': [
                        "Apprendre à dire non quand nécessaire",
                        "Défendre vos propres intérêts"
                    ]
                },
                'moderate': {
                    'observations': "Vous trouvez un équilibre entre coopération et affirmation de soi.",
                    'strengths': [
                        "Diplomatie dans les relations",
                        "Capacité à négocier efficacement"
                    ],
                    'development': [
                        "Renforcer votre assertivité",
                        "Développer votre capacité d'influence"
                    ]
                },
                'low': {
                    'observations': "Vous êtes direct et privilégiez l'efficacité sur l'harmonie.",
                    'strengths': [
                        "Capacité à prendre des décisions difficiles",
                        "Communication directe et claire"
                    ],
                    'development': [
                        "Développer votre empathie",
                        "Améliorer votre diplomatie"
                    ]
                }
            },
            'stabilité émotionnelle': {
                'high': {
                    'observations': "Vous maintenez un équilibre émotionnel remarquable même sous pression.",
                    'strengths': [
                        "Gestion exemplaire du stress",
                        "Capacité à rester calme en situation de crise",
                        "Résilience émotionnelle"
                    ],
                    'development': [
                        "Continuer à cultiver votre équilibre",
                        "Partager vos stratégies avec les autres"
                    ]
                },
                'moderate': {
                    'observations': "Vous gérez généralement bien vos émotions avec quelques moments de stress.",
                    'strengths': [
                        "Bonne régulation émotionnelle",
                        "Capacité de récupération"
                    ],
                    'development': [
                        "Développer des techniques de gestion du stress",
                        "Renforcer votre résilience"
                    ]
                },
                'low': {
                    'observations': "Vous ressentez intensément vos émotions et le stress.",
                    'strengths': [
                        "Sensibilité émotionnelle",
                        "Conscience de vos ressentis"
                    ],
                    'development': [
                        "Apprendre des techniques de relaxation",
                        "Développer votre intelligence émotionnelle"
                    ]
                }
            },
            # DISC styles
            'dominant': {
                'high': {
                    'observations': "Vous êtes orienté résultats avec un style de leadership direct et décisif.",
                    'strengths': [
                        "Prise de décision rapide",
                        "Orientation forte vers les objectifs",
                        "Leadership en situation de crise"
                    ],
                    'development': [
                        "Développer la patience avec les processus plus lents",
                        "Améliorer l'écoute des autres perspectives"
                    ]
                },
                'moderate': {
                    'observations': "Vous savez être décisif quand nécessaire tout en consultant les autres.",
                    'strengths': [
                        "Équilibre entre action et réflexion",
                        "Capacité d'adaptation du style de leadership"
                    ],
                    'development': [
                        "Développer davantage votre assertivité",
                        "Prendre plus d'initiatives"
                    ]
                }
            },
            'influent': {
                'high': {
                    'observations': "Vous excellez dans la communication et l'influence des autres par votre enthousiasme.",
                    'strengths': [
                        "Excellentes compétences de persuasion",
                        "Capacité à motiver et inspirer",
                        "Communication charismatique"
                    ],
                    'development': [
                        "Équilibrer enthousiasme et rigueur",
                        "Développer le suivi des engagements"
                    ]
                },
                'moderate': {
                    'observations': "Vous utilisez votre communication de manière équilibrée.",
                    'strengths': [
                        "Bonne capacité de persuasion",
                        "Communication efficace"
                    ],
                    'development': [
                        "Développer votre charisme",
                        "Améliorer vos présentations"
                    ]
                }
            },
            'stable': {
                'high': {
                    'observations': "Vous êtes un pilier de stabilité et de soutien pour votre équipe.",
                    'strengths': [
                        "Excellente capacité d'écoute",
                        "Soutien constant de l'équipe",
                        "Patience et persévérance"
                    ],
                    'development': [
                        "Oser davantage le changement",
                        "Développer votre assertivité"
                    ]
                },
                'moderate': {
                    'observations': "Vous équilibrez stabilité et adaptation au changement.",
                    'strengths': [
                        "Fiabilité dans le soutien",
                        "Adaptabilité progressive"
                    ],
                    'development': [
                        "Renforcer votre rôle de médiateur",
                        "Améliorer la cohésion d'équipe"
                    ]
                }
            },
            'conforme': {
                'high': {
                    'observations': "Vous accordez une grande importance à la qualité et au respect des normes.",
                    'strengths': [
                        "Attention exceptionnelle aux détails",
                        "Rigueur dans l'application des procédures",
                        "Excellence dans le contrôle qualité"
                    ],
                    'development': [
                        "Développer la flexibilité face aux imprévus",
                        "Équilibrer perfection et pragmatisme"
                    ]
                },
                'moderate': {
                    'observations': "Vous êtes rigoureux tout en gardant une certaine flexibilité.",
                    'strengths': [
                        "Bon sens du détail",
                        "Respect équilibré des procédures"
                    ],
                    'development': [
                        "Renforcer votre attention aux détails",
                        "Améliorer la documentation"
                    ]
                }
            },
            'bien_etre': {
                'high': {
                    'observations': "Vous jouissez d'un excellent équilibre et d'un bien-être professionnel remarquable.",
                    'strengths': [
                        "Équilibre vie pro/perso optimal",
                        "Gestion efficace du stress",
                        "Satisfaction professionnelle élevée"
                    ],
                    'development': [
                        "Maintenir cet équilibre dans la durée",
                        "Partager vos bonnes pratiques"
                    ]
                },
                'moderate': {
                    'observations': "Votre bien-être est globalement satisfaisant avec des axes d'amélioration.",
                    'strengths': [
                        "Conscience de vos besoins",
                        "Efforts pour maintenir l'équilibre"
                    ],
                    'development': [
                        "Améliorer votre équilibre vie pro/perso",
                        "Développer des stratégies anti-stress"
                    ]
                },
                'low': {
                    'observations': "Votre bien-être professionnel nécessite une attention particulière.",
                    'strengths': [
                        "Conscience du besoin de changement",
                        "Volonté d'amélioration"
                    ],
                    'development': [
                        "Identifier les sources de stress",
                        "Mettre en place un plan d'action bien-être",
                        "Considérer un accompagnement professionnel"
                    ]
                }
            },
            'resilience_ie': {
                'high': {
                    'observations': "Vous démontrez une excellente résilience et intelligence émotionnelle.",
                    'strengths': [
                        "Capacité de rebond remarquable",
                        "Excellente gestion des émotions",
                        "Apprentissage efficace des difficultés"
                    ],
                    'development': [
                        "Continuer à développer ces compétences",
                        "Accompagner les autres dans leur développement"
                    ]
                },
                'moderate': {
                    'observations': "Vous avez une bonne capacité de résilience avec des marges de progression.",
                    'strengths': [
                        "Capacité de récupération",
                        "Conscience émotionnelle"
                    ],
                    'development': [
                        "Renforcer votre intelligence émotionnelle",
                        "Développer des stratégies de coping"
                    ]
                },
                'low': {
                    'observations': "Votre résilience et intelligence émotionnelle peuvent être renforcées.",
                    'strengths': [
                        "Conscience de vos émotions",
                        "Volonté de progression"
                    ],
                    'development': [
                        "Développer des techniques de résilience",
                        "Travailler votre intelligence émotionnelle",
                        "Considérer un coaching spécialisé"
                    ]
                }
            }
        }
    return {}


def fallback_score_explanation(score, trait, assessment_type, language='fr'):
    """Generate score explanation - random but realistic"""
    max_score = 5 if assessment_type == 'disc' else 10
    percentage = (score / max_score) * 100
    
    explanations = {
        'fr': {
            'high': f"Votre score de {score:.1f}/{max_score} indique une forte expression de ce trait dans votre comportement professionnel.",
            'moderate': f"Votre score de {score:.1f}/{max_score} reflète un niveau équilibré pour ce trait.",
            'low': f"Votre score de {score:.1f}/{max_score} suggère que ce trait s'exprime de manière plus modérée chez vous."
        },
        'en': {
            'high': f"Your score of {score:.1f}/{max_score} indicates a strong expression of this trait in your professional behavior.",
            'moderate': f"Your score of {score:.1f}/{max_score} reflects a balanced level for this trait.",
            'low': f"Your score of {score:.1f}/{max_score} suggests this trait is expressed more moderately in you."
        },
        'ar': {
            'high': f"درجتك {score:.1f}/{max_score} تشير إلى تعبير قوي عن هذه السمة في سلوكك المهني.",
            'moderate': f"درجتك {score:.1f}/{max_score} تعكس مستوى متوازن لهذه السمة.",
            'low': f"درجتك {score:.1f}/{max_score} تشير إلى أن هذه السمة تعبر عن نفسها بشكل معتدل فيك."
        }
    }
    
    if percentage >= 70:
        category = 'high'
    elif percentage >= 40:
        category = 'moderate'
    else:
        category = 'low'
    
    return explanations.get(language, explanations['fr'])[category]