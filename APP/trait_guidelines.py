"""
Trait guidelines from cahier de charge for question generation and scoring
"""

TRAIT_GUIDELINES = {
    'big_five': {
        'ouverture': {
            'fr': {
                'description': "Ouverture à l'expérience - créativité, curiosité, innovation",
                'scoring': """
                1-2: Préfère les routines, peu d'intérêt pour la nouveauté ou les idées abstraites
                3: Ouvert(e) à certaines idées nouvelles mais avec prudence
                4-5: Très créatif(ve), curieux(se), attiré(e) par l'innovation et les expériences variées
                """,
                'keywords_high': ['créatif', 'innovation', 'curiosité', 'nouveau', 'idée', 'explorer', 'imagination'],
                'keywords_low': ['routine', 'habituel', 'traditionnel', 'stable', 'prévisible']
            },
            'en': {
                'description': "Openness to experience - creativity, curiosity, innovation",
                'scoring': """
                1-2: Prefers routines, little interest in novelty or abstract ideas
                3: Open to some new ideas but with caution
                4-5: Very creative, curious, attracted to innovation and varied experiences
                """,
                'keywords_high': ['creative', 'innovation', 'curiosity', 'new', 'idea', 'explore', 'imagination'],
                'keywords_low': ['routine', 'usual', 'traditional', 'stable', 'predictable']
            },
            'ar': {
                'description': "الانفتاح على التجربة - الإبداع، الفضول، الابتكار",
                'scoring': """
                1-2: يفضل الروتين، اهتمام قليل بالجديد أو الأفكار المجردة
                3: منفتح على بعض الأفكار الجديدة ولكن بحذر
                4-5: مبدع جداً، فضولي، منجذب للابتكار والتجارب المتنوعة
                """,
                'keywords_high': ['إبداع', 'ابتكار', 'فضول', 'جديد', 'فكرة', 'استكشاف', 'خيال'],
                'keywords_low': ['روتين', 'معتاد', 'تقليدي', 'مستقر', 'متوقع']
            }
        },
        'conscienciosité': {
            'fr': {
                'description': "Conscienciosité - organisation, rigueur, fiabilité",
                'scoring': """
                1-2: Peut manquer de rigueur, difficulté à respecter les délais ou à s'organiser
                3: Responsable dans les tâches importantes, mais manque parfois de planification
                4-5: Très organisé(e), fiable, soucieux(se) de la qualité et de l'efficacité
                """,
                'keywords_high': ['organisé', 'planification', 'rigueur', 'détail', 'qualité', 'efficace', 'responsable'],
                'keywords_low': ['désorganisé', 'retard', 'improvisation', 'spontané']
            },
            'en': {
                'description': "Conscientiousness - organization, rigor, reliability",
                'scoring': """
                1-2: May lack rigor, difficulty meeting deadlines or organizing
                3: Responsible for important tasks, but sometimes lacks planning
                4-5: Very organized, reliable, concerned with quality and efficiency
                """,
                'keywords_high': ['organized', 'planning', 'rigor', 'detail', 'quality', 'efficient', 'responsible'],
                'keywords_low': ['disorganized', 'late', 'improvisation', 'spontaneous']
            },
            'ar': {
                'description': "الضمير - التنظيم، الدقة، الموثوقية",
                'scoring': """
                1-2: قد يفتقر للدقة، صعوبة في الالتزام بالمواعيد أو التنظيم
                3: مسؤول في المهام المهمة، لكن يفتقر أحياناً للتخطيط
                4-5: منظم جداً، موثوق، مهتم بالجودة والكفاءة
                """,
                'keywords_high': ['منظم', 'تخطيط', 'دقة', 'تفاصيل', 'جودة', 'كفاءة', 'مسؤول'],
                'keywords_low': ['غير منظم', 'تأخير', 'ارتجال', 'عفوي']
            }
        },
        'extraversion': {
            'fr': {
                'description': "Extraversion - sociabilité, énergie sociale, assertivité",
                'scoring': """
                1-2: Préfère travailler seul(e), réservé(e), peu énergique socialement
                3: A l'aise dans certaines interactions, mais aime aussi la solitude
                4-5: Sociable, assertif(ve), prend l'initiative dans les groupes
                """,
                'keywords_high': ['social', 'équipe', 'groupe', 'communication', 'énergie', 'initiative'],
                'keywords_low': ['seul', 'calme', 'réservé', 'introverti', 'solitude']
            },
            'en': {
                'description': "Extraversion - sociability, social energy, assertiveness",
                'scoring': """
                1-2: Prefers working alone, reserved, low social energy
                3: Comfortable in some interactions, but also enjoys solitude
                4-5: Sociable, assertive, takes initiative in groups
                """,
                'keywords_high': ['social', 'team', 'group', 'communication', 'energy', 'initiative'],
                'keywords_low': ['alone', 'quiet', 'reserved', 'introverted', 'solitude']
            },
            'ar': {
                'description': "الانبساط - الاجتماعية، الطاقة الاجتماعية، الحزم",
                'scoring': """
                1-2: يفضل العمل بمفرده، متحفظ، طاقة اجتماعية منخفضة
                3: مرتاح في بعض التفاعلات، لكن يستمتع أيضاً بالعزلة
                4-5: اجتماعي، حازم، يأخذ المبادرة في المجموعات
                """,
                'keywords_high': ['اجتماعي', 'فريق', 'مجموعة', 'تواصل', 'طاقة', 'مبادرة'],
                'keywords_low': ['وحيد', 'هادئ', 'متحفظ', 'انطوائي', 'عزلة']
            }
        },
        'agréabilité': {
            'fr': {
                'description': "Agréabilité - empathie, coopération, harmonie",
                'scoring': """
                1-2: Peut sembler distant(e), critique, peu conciliant(e)
                3: Coopératif(ve), mais peut défendre fermement ses opinions
                4-5: Empathique, à l'écoute, privilégie l'harmonie dans les relations
                """,
                'keywords_high': ['empathie', 'écoute', 'coopération', 'harmonie', 'aide', 'compréhension'],
                'keywords_low': ['critique', 'conflit', 'distant', 'ferme', 'indépendant']
            },
            'en': {
                'description': "Agreeableness - empathy, cooperation, harmony",
                'scoring': """
                1-2: May seem distant, critical, uncompromising
                3: Cooperative, but can firmly defend opinions
                4-5: Empathetic, listening, prioritizes harmony in relationships
                """,
                'keywords_high': ['empathy', 'listening', 'cooperation', 'harmony', 'help', 'understanding'],
                'keywords_low': ['critical', 'conflict', 'distant', 'firm', 'independent']
            },
            'ar': {
                'description': "الوداعة - التعاطف، التعاون، الانسجام",
                'scoring': """
                1-2: قد يبدو بعيداً، ناقداً، غير متساهل
                3: متعاون، لكن يمكنه الدفاع بحزم عن آرائه
                4-5: متعاطف، مستمع، يعطي الأولوية للانسجام في العلاقات
                """,
                'keywords_high': ['تعاطف', 'استماع', 'تعاون', 'انسجام', 'مساعدة', 'فهم'],
                'keywords_low': ['نقد', 'صراع', 'بعيد', 'حازم', 'مستقل']
            }
        },
        'stabilité émotionnelle': {
            'fr': {
                'description': "Stabilité émotionnelle - gestion du stress, confiance, calme",
                'scoring': """
                1-2: Stressé(e), sensible aux critiques, anxieux(se)
                3: Équilibré(e) mais réagit parfois fortement au stress
                4-5: Calme, confiant(e), gère bien les émotions et les tensions
                """,
                'keywords_high': ['calme', 'confiance', 'gestion', 'équilibre', 'sérénité', 'contrôle'],
                'keywords_low': ['stress', 'anxiété', 'inquiet', 'nerveux', 'sensible']
            },
            'en': {
                'description': "Emotional stability - stress management, confidence, calm",
                'scoring': """
                1-2: Stressed, sensitive to criticism, anxious
                3: Balanced but sometimes reacts strongly to stress
                4-5: Calm, confident, manages emotions and tensions well
                """,
                'keywords_high': ['calm', 'confidence', 'management', 'balance', 'serenity', 'control'],
                'keywords_low': ['stress', 'anxiety', 'worried', 'nervous', 'sensitive']
            },
            'ar': {
                'description': "الاستقرار العاطفي - إدارة الضغط، الثقة، الهدوء",
                'scoring': """
                1-2: متوتر، حساس للنقد، قلق
                3: متوازن لكن يتفاعل أحياناً بقوة مع الضغط
                4-5: هادئ، واثق، يدير العواطف والتوترات بشكل جيد
                """,
                'keywords_high': ['هدوء', 'ثقة', 'إدارة', 'توازن', 'سكينة', 'سيطرة'],
                'keywords_low': ['ضغط', 'قلق', 'متوتر', 'عصبي', 'حساس']
            }
        }
    },
    'disc': {
        'dominant': {
            'fr': {
                'description': "Dominant - décideur, orienté résultats, directif",
                'scoring': """
                1-2: Évite les confrontations, suit plutôt que dirige
                3: Peut prendre des décisions mais préfère le consensus
                4-5: Décideur, orienté résultats, directif, aime les challenges
                """,
                'keywords_high': ['décision', 'résultats', 'challenge', 'contrôle', 'directif', 'action'],
                'keywords_low': ['consensus', 'suivre', 'éviter', 'prudent']
            },
            'en': {
                'description': "Dominant - decision-maker, results-oriented, directive",
                'scoring': """
                1-2: Avoids confrontations, follows rather than leads
                3: Can make decisions but prefers consensus
                4-5: Decision-maker, results-oriented, directive, enjoys challenges
                """,
                'keywords_high': ['decision', 'results', 'challenge', 'control', 'directive', 'action'],
                'keywords_low': ['consensus', 'follow', 'avoid', 'cautious']
            }
        },
        'influent': {
            'fr': {
                'description': "Influent - charismatique, communicatif, inspirant",
                'scoring': """
                1-2: Préfère l'action à la communication, peu expressif
                3: Communique efficacement quand nécessaire
                4-5: Charismatique, communicatif, inspirant, aime convaincre et motiver
                """,
                'keywords_high': ['communication', 'convaincre', 'motiver', 'inspiration', 'charisme', 'enthousiasme'],
                'keywords_low': ['discret', 'action', 'résultats', 'technique']
            },
            'en': {
                'description': "Influential - charismatic, communicative, inspiring",
                'scoring': """
                1-2: Prefers action to communication, not very expressive
                3: Communicates effectively when necessary
                4-5: Charismatic, communicative, inspiring, enjoys convincing and motivating
                """,
                'keywords_high': ['communication', 'convince', 'motivate', 'inspiration', 'charisma', 'enthusiasm'],
                'keywords_low': ['discreet', 'action', 'results', 'technical']
            }
        },
        'stable': {
            'fr': {
                'description': "Stable - loyal, calme, patient, préfère la stabilité",
                'scoring': """
                1-2: Aime le changement, impatient, cherche la nouveauté
                3: Équilibre entre stabilité et changement
                4-5: Loyal, calme, patient, préfère la stabilité et les relations harmonieuses
                """,
                'keywords_high': ['stabilité', 'loyal', 'patience', 'équipe', 'harmonie', 'soutien'],
                'keywords_low': ['changement', 'rapide', 'nouveau', 'impatient']
            },
            'en': {
                'description': "Stable - loyal, calm, patient, prefers stability",
                'scoring': """
                1-2: Enjoys change, impatient, seeks novelty
                3: Balance between stability and change
                4-5: Loyal, calm, patient, prefers stability and harmonious relationships
                """,
                'keywords_high': ['stability', 'loyal', 'patience', 'team', 'harmony', 'support'],
                'keywords_low': ['change', 'fast', 'new', 'impatient']
            }
        },
        'conforme': {
            'fr': {
                'description': "Conforme - précis, analytique, rigoureux, valorise les normes",
                'scoring': """
                1-2: Préfère l'intuition à l'analyse, flexible sur les normes
                3: Analytique quand nécessaire, respecte les normes importantes
                4-5: Précis, analytique, rigoureux, valorise les normes et la qualité
                """,
                'keywords_high': ['analyse', 'précision', 'qualité', 'normes', 'méthode', 'détail'],
                'keywords_low': ['intuition', 'flexible', 'rapide', 'global']
            },
            'en': {
                'description': "Compliant - precise, analytical, rigorous, values standards",
                'scoring': """
                1-2: Prefers intuition to analysis, flexible on standards
                3: Analytical when necessary, respects important standards
                4-5: Precise, analytical, rigorous, values standards and quality
                """,
                'keywords_high': ['analysis', 'precision', 'quality', 'standards', 'method', 'detail'],
                'keywords_low': ['intuition', 'flexible', 'fast', 'global']
            }
        }
    },
    'bien_etre': {
        'general': {
            'fr': {
                'description': "Bien-être au travail - satisfaction, autonomie, valorisation",
                'scoring': """
                1-2: Faible bien-être, risque de démotivation ou surcharge
                3: Bien-être modéré, présence de points à améliorer
                4-5: Bien-être élevé, engagement et satisfaction professionnelle
                """,
                'keywords_high': ['satisfait', 'valorisé', 'autonomie', 'écouté', 'respecté', 'accord', 'valeurs'],
                'keywords_low': ['insatisfait', 'stress', 'surcharge', 'ignoré', 'non valorisé']
            },
            'en': {
                'description': "Well-being at work - satisfaction, autonomy, recognition",
                'scoring': """
                1-2: Low well-being, risk of demotivation or overload
                3: Moderate well-being, areas to improve
                4-5: High well-being, engagement and professional satisfaction
                """,
                'keywords_high': ['satisfied', 'valued', 'autonomy', 'heard', 'respected', 'aligned', 'values'],
                'keywords_low': ['dissatisfied', 'stress', 'overload', 'ignored', 'undervalued']
            },
            'ar': {
                'description': "الرفاهة في العمل - الرضا، الاستقلالية، التقدير",
                'scoring': """
                1-2: رفاهة منخفضة، خطر فقدان الحافز أو الحمل الزائد
                3: رفاهة متوسطة، وجود نقاط للتحسين
                4-5: رفاهة عالية، التزام ورضا مهني
                """,
                'keywords_high': ['راض', 'مقدر', 'استقلالية', 'مسموع', 'محترم', 'متوافق', 'قيم'],
                'keywords_low': ['غير راض', 'ضغط', 'حمل زائد', 'متجاهل', 'غير مقدر']
            }
        }
    },
    'resilience_ie': {
        'general': {
            'fr': {
                'description': "Résilience et intelligence émotionnelle - gestion émotions, adaptation, apprentissage",
                'scoring': """
                1-2: Faible, difficultés à gérer émotions et imprévus
                3: Modéré, bonnes bases à renforcer pour plus de fluidité
                4-5: Élevé, maîtrise émotionnelle et bonne capacité d'adaptation
                """,
                'keywords_high': ['émotions', 'adaptation', 'apprentissage', 'résilience', 'motivation', 'recul', 'écoute'],
                'keywords_low': ['difficulté', 'frustration', 'rigide', 'démotivé', 'agressif']
            },
            'en': {
                'description': "Resilience and emotional intelligence - emotion management, adaptation, learning",
                'scoring': """
                1-2: Low, difficulties managing emotions and unexpected events
                3: Moderate, good foundation to strengthen for more fluidity
                4-5: High, emotional mastery and good adaptation capacity
                """,
                'keywords_high': ['emotions', 'adaptation', 'learning', 'resilience', 'motivation', 'perspective', 'listening'],
                'keywords_low': ['difficulty', 'frustration', 'rigid', 'demotivated', 'aggressive']
            },
            'ar': {
                'description': "المرونة والذكاء العاطفي - إدارة العواطف، التكيف، التعلم",
                'scoring': """
                1-2: منخفض، صعوبات في إدارة العواطف والأحداث غير المتوقعة
                3: متوسط، أساس جيد لتعزيزه لمزيد من السلاسة
                4-5: عالي، إتقان عاطفي وقدرة تكيف جيدة
                """,
                'keywords_high': ['عواطف', 'تكيف', 'تعلم', 'مرونة', 'حافز', 'منظور', 'استماع'],
                'keywords_low': ['صعوبة', 'إحباط', 'جامد', 'محبط', 'عدواني']
            }
        }
    }
}


def get_trait_guidelines(trait, assessment_type='big_five', language='fr'):
    """Get guidelines for a specific trait"""
    guidelines = TRAIT_GUIDELINES.get(assessment_type, {}).get(trait, {}).get(language, {})
    return guidelines


def get_scoring_guide(trait, assessment_type='big_five', language='fr'):
    """Get scoring guide for a trait"""
    guidelines = get_trait_guidelines(trait, assessment_type, language)
    return guidelines.get('scoring', '')


def get_trait_keywords(trait, assessment_type='big_five', language='fr'):
    """Get keywords for trait detection"""
    guidelines = get_trait_guidelines(trait, assessment_type, language)
    return {
        'high': guidelines.get('keywords_high', []),
        'low': guidelines.get('keywords_low', [])
    }
