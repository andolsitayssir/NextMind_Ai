from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
import json
import random
import time
from datetime import datetime, timedelta

from .utils import (
    generate_question, 
    analyze_answer,
    get_trait_intro,
    ASSESSMENT_STRUCTURE,
    generate_detailed_analysis,
    get_behavioral_questions,
    generate_score_explanations,
    generate_enhanced_detailed_analysis,
)
import logging
import re

# Store used questions to prevent repetition
USED_QUESTIONS = {}

def track_used_question(session_key, question_text):
    """Track used questions to prevent repetition"""
    if session_key not in USED_QUESTIONS:
        USED_QUESTIONS[session_key] = set()
    
    # Normalize question for comparison
    normalized = question_text.lower().strip('?.,!').replace(' ', '')
    USED_QUESTIONS[session_key].add(normalized)

def is_question_already_used(session_key, question_text):
    """Check if a question has already been used"""
    if session_key not in USED_QUESTIONS:
        return False
    
    normalized = question_text.lower().strip('?.,!').replace(' ', '')
    return normalized in USED_QUESTIONS[session_key]

def analyze_typing_speed(text_length, response_time):
    """Analyze typing speed and patterns"""
    if response_time <= 0:
        return {'speed': 'instant', 'pattern': 'copied'}
    
    # Calculate words per minute (assuming average 5 characters per word)
    words = text_length / 5
    minutes = response_time / 60
    wpm = words / minutes if minutes > 0 else 0
    
    if wpm > 80:
        speed_category = 'very_fast'
        pattern = 'possible_copy_paste'
    elif wpm > 40:
        speed_category = 'fast'
        pattern = 'fluent_typing'
    elif wpm > 20:
        speed_category = 'moderate'
        pattern = 'thoughtful_typing'
    elif wpm > 5:
        speed_category = 'slow'
        pattern = 'careful_consideration'
    else:
        speed_category = 'very_slow'
        pattern = 'deep_reflection'
    
    return {
        'wpm': round(wpm, 1),
        'speed': speed_category,
        'pattern': pattern,
        'analysis_time': max(0, response_time - (text_length / 20))  # Estimated thinking time
    }

def analyze_response_tone(text, response_time, text_length):
    """Enhanced tone analysis including typing patterns"""
    text_lower = text.lower()
    
    # Emotional indicators
    positive_words = ['aime', 'apprécie', 'plaisir', 'satisfait', 'heureux', 'motivé', 'love', 'enjoy', 'happy', 'satisfied', 'motivated']
    negative_words = ['difficile', 'problème', 'stress', 'inquiet', 'frustré', 'difficult', 'problem', 'stress', 'worried', 'frustrated']
    confident_words = ['confiant', 'sûr', 'certain', 'capable', 'efficace', 'confident', 'sure', 'certain', 'capable', 'effective']
    hesitant_words = ['peut-être', 'parfois', 'généralement', 'souvent', 'maybe', 'sometimes', 'usually', 'often']
    
    # Count indicators
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    confident_count = sum(1 for word in confident_words if word in text_lower)
    hesitant_count = sum(1 for word in hesitant_words if word in text_lower)
    
    # Typing speed analysis
    typing_analysis = analyze_typing_speed(text_length, response_time)
    
    # Determine primary tone
    if confident_count > hesitant_count and positive_count > negative_count:
        primary_tone = 'confident_positive'
    elif negative_count > positive_count:
        primary_tone = 'concerned' if response_time > 30 else 'stressed'
    elif hesitant_count > confident_count:
        primary_tone = 'uncertain'
    elif typing_analysis['speed'] == 'very_fast':
        primary_tone = 'impulsive'
    elif typing_analysis['speed'] == 'very_slow':
        primary_tone = 'reflective'
    else:
        primary_tone = 'balanced'
    
    # Engagement level based on multiple factors
    engagement_score = 0
    engagement_score += min(text_length / 20, 5)  # Length bonus (max 5)
    engagement_score += max(0, min(response_time / 10, 3))  # Time bonus (max 3)
    engagement_score += positive_count  # Positivity bonus
    engagement_score += confident_count  # Confidence bonus
    engagement_score -= negative_count * 0.5  # Negativity penalty
    
    if engagement_score >= 8:
        engagement_level = 'very_high'
    elif engagement_score >= 6:
        engagement_level = 'high'
    elif engagement_score >= 4:
        engagement_level = 'moderate'
    elif engagement_score >= 2:
        engagement_level = 'low'
    else:
        engagement_level = 'very_low'
    
    return {
        'primary_tone': primary_tone,
        'engagement_level': engagement_level,
        'emotional_balance': {
            'positive': positive_count,
            'negative': negative_count,
            'confident': confident_count,
            'hesitant': hesitant_count
        },
        'typing_analysis': typing_analysis,
        'engagement_score': round(engagement_score, 1)
    }

# Configure minimal logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Input validation patterns and keywords
VALIDATION_PATTERNS = {
    'meaningless_patterns': [
        r'^[a-z]{1,3}$',  # Single letters or very short combinations
        r'^[0-9]+$',  # Only numbers
        r'^[!@#$%^&*(),.?":{}|<>]+$',  # Only special characters
        r'^(.)\1{4,}$',  # Repeated characters (aaaaa, 11111)
        r'^(test|test123|testing|lorem|ipsum)$',  # Common test words
        r'^(qwerty|asdf|hjkl|zxcv)$',  # Keyboard patterns
    ],
    'gibberish_patterns': [
        r'^[a-z]*[0-9]+[a-z]*[0-9]+',  # Mixed random letters and numbers only
    ]
}

BEHAVIORAL_KEYWORDS = {
    'fr': {
        'relevant_words': [
            'je', 'moi', 'mon', 'ma', 'mes', 'suis', 'fais', 'pense', 'crois', 'ressens',
            'décide', 'choisis', 'préfère', 'aime', 'déteste', 'évite', 'cherche',
            'situation', 'moment', 'expérience', 'comportement', 'réaction', 'approche',
            'méthode', 'stratégie', 'habitude', 'tendance', 'personnalité', 'caractère',
            'équipe', 'groupe', 'travail', 'projet', 'tâche', 'objectif', 'défi',
            'stress', 'pression', 'problème', 'difficulté', 'conflit', 'solution',
            'émotion', 'sentiment', 'ressenti', 'humeur', 'motivation', 'passion'
        ],
        'question_words': [
            'comment', 'pourquoi', 'quand', 'où', 'que', 'quoi', 'quel', 'quelle'
        ]
    },
    'en': {
        'relevant_words': [
            'i', 'me', 'my', 'mine', 'am', 'do', 'think', 'believe', 'feel',
            'decide', 'choose', 'prefer', 'like', 'love', 'hate', 'avoid', 'seek',
            'situation', 'moment', 'experience', 'behavior', 'reaction', 'approach',
            'method', 'strategy', 'habit', 'tendency', 'personality', 'character',
            'team', 'group', 'work', 'project', 'task', 'goal', 'challenge',
            'stress', 'pressure', 'problem', 'difficulty', 'conflict', 'solution',
            'emotion', 'feeling', 'mood', 'motivation', 'passion'
        ],
        'question_words': [
            'how', 'why', 'when', 'where', 'what', 'which', 'who'
        ]
    },
    'ar': {
        'relevant_words': [
            'أنا', 'لي', 'عندي', 'أكون', 'أفعل', 'أعتقد', 'أشعر', 'أحس',
            'أقرر', 'أختار', 'أفضل', 'أحب', 'أكره', 'أتجنب', 'أبحث',
            'موقف', 'لحظة', 'تجربة', 'سلوك', 'رد فعل', 'طريقة',
            'استراتيجية', 'عادة', 'شخصية', 'طبع', 'فريق', 'مجموعة',
            'عمل', 'مشروع', 'هدف', 'تحدي', 'ضغط', 'مشكلة', 'صعوبة',
            'حل', 'عاطفة', 'شعور', 'دافع', 'شغف'
        ],
        'question_words': [
            'كيف', 'لماذا', 'متى', 'أين', 'ماذا', 'ما', 'من', 'أي'
        ]
    }
}

def validate_answer(answer_text, language, current_trait=None, current_assessment=None):
    """
    Comprehensive answer validation to prevent nonsense, empty, or irrelevant responses
    Returns: (is_valid, error_message)
    """
    if not answer_text or not answer_text.strip():
        return False, get_validation_error('empty', language)
    
    answer_clean = answer_text.strip().lower()
    
    # Check minimum length (more lenient)
    if len(answer_clean) < 5:
        return False, get_validation_error('too_short', language)
    
    # Check maximum length (prevent spam)
    if len(answer_text) > 1000:
        return False, get_validation_error('too_long', language)
    
    # Check if answer is just the question repeated (common copy-paste issue) - more lenient
    question_indicators = [
        'in what situations', 'dans quelles situations', 'gérer une situation', 'manage a situation'
    ]
    
    # Only flag as copied if it's clearly a question format
    if any(indicator in answer_clean for indicator in question_indicators):
        if '?' in answer_text and answer_clean.startswith(('comment', 'pourquoi', 'when', 'how', 'what', 'in what')):
            return False, get_validation_error('question_copied', language)
    
    # Check for meaningless patterns
    for pattern in VALIDATION_PATTERNS['meaningless_patterns']:
        if re.match(pattern, answer_clean):
            return False, get_validation_error('meaningless', language)
    
    # Check for gibberish patterns
    for pattern in VALIDATION_PATTERNS['gibberish_patterns']:
        if re.match(pattern, answer_clean):
            return False, get_validation_error('gibberish', language)
    
    # Check for repeated words (spam detection) - more lenient
    words = answer_clean.split()
    if len(words) > 5:  # Only check if more than 5 words
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.2:  # Less than 20% unique words (was 30%)
            return False, get_validation_error('repetitive', language)
    
    # Check for relevant behavioral content - more lenient
    relevant_score = calculate_relevance_score(answer_clean, language, current_trait, current_assessment)
    if relevant_score < 0.1:  # Less than 10% relevance (was 20%)
        return False, get_validation_error('irrelevant', language)
    
    # Check for copy-paste detection (common phrases that might be copied) - DISABLED for less restriction
    # if is_likely_copied(answer_clean, language):
    #     return False, get_validation_error('copied', language)
    
    return True, None

def calculate_relevance_score(answer_text, language, current_trait=None, current_assessment=None):
    """Calculate how relevant the answer is to psychological assessment - more lenient"""
    if language not in BEHAVIORAL_KEYWORDS:
        return 0.6  # Higher default score for unsupported languages
    
    keywords = BEHAVIORAL_KEYWORDS[language]['relevant_words']
    words = answer_text.split()
    
    if not words:
        return 0
    
    # Count relevant words
    relevant_count = sum(1 for word in words if word in keywords)
    base_score = relevant_count / len(words)
    
    # Bonus for personal pronouns (indicates personal reflection)
    personal_pronouns = {
        'fr': ['je', 'moi', 'mon', 'ma', 'mes', 'j', 'me', 'nous'],
        'en': ['i', 'me', 'my', 'mine', 'we', 'us', 'our'],
        'ar': ['أنا', 'لي', 'عندي', 'نحن', 'لنا']
    }
    
    if language in personal_pronouns:
        personal_count = sum(1 for word in words if word in personal_pronouns[language])
        if personal_count > 0:
            base_score += 0.3  # Higher bonus for personal reflection
    
    # Give bonus for reasonable length (people writing real answers usually write more)
    if len(answer_text) > 20:
        base_score += 0.2
    
    # Give bonus for common words that indicate genuine responses
    common_positive_words = {
        'fr': ['toujours', 'souvent', 'parfois', 'jamais', 'beaucoup', 'peu', 'très', 'assez', 'plutôt', 'généralement', 'habituellement'],
        'en': ['always', 'often', 'sometimes', 'never', 'much', 'little', 'very', 'quite', 'rather', 'generally', 'usually'],
        'ar': ['دائماً', 'غالباً', 'أحياناً', 'أبداً', 'كثيراً', 'قليلاً', 'جداً', 'نوعاً', 'عادة']
    }
    
    if language in common_positive_words:
        common_count = sum(1 for word in words if word in common_positive_words[language])
        if common_count > 0:
            base_score += 0.2
    
    # Bonus for trait-specific keywords
    if current_trait and current_assessment:
        trait_bonus = get_trait_specific_score(answer_text, current_trait, current_assessment, language)
        base_score += trait_bonus
    
    return min(base_score, 1.0)  # Cap at 1.0

def get_trait_specific_score(answer_text, trait, assessment, language):
    """Get bonus score for trait-specific keywords"""
    trait_keywords = {
        'fr': {
            'ouverture': ['créatif', 'imagination', 'nouveau', 'innovation', 'curiosité', 'exploration'],
            'conscienciosité': ['organisation', 'planification', 'discipline', 'responsabilité', 'méthode', 'ordre'],
            'extraversion': ['social', 'groupe', 'énergie', 'communication', 'interaction', 'extérieur'],
            'agréabilité': ['coopération', 'empathie', 'bienveillance', 'aide', 'harmonie', 'confiance'],
            'stabilité émotionnelle': ['calme', 'stress', 'pression', 'émotion', 'gestion', 'contrôle'],
            'dominant': ['leadership', 'décision', 'contrôle', 'autorité', 'direction', 'pouvoir'],
            'influent': ['persuasion', 'communication', 'inspiration', 'motivation', 'influence', 'social'],
            'stable': ['patience', 'écoute', 'soutien', 'stabilité', 'persévérance', 'régularité'],
            'conforme': ['règles', 'précision', 'qualité', 'détail', 'analyse', 'exactitude']
        },
        'en': {
            'ouverture': ['creative', 'imagination', 'new', 'innovation', 'curiosity', 'exploration'],
            'conscienciosité': ['organization', 'planning', 'discipline', 'responsibility', 'method', 'order'],
            'extraversion': ['social', 'group', 'energy', 'communication', 'interaction', 'outgoing'],
            'agréabilité': ['cooperation', 'empathy', 'kindness', 'help', 'harmony', 'trust'],
            'stabilité émotionnelle': ['calm', 'stress', 'pressure', 'emotion', 'management', 'control'],
            'dominant': ['leadership', 'decision', 'control', 'authority', 'direction', 'power'],
            'influent': ['persuasion', 'communication', 'inspiration', 'motivation', 'influence', 'social'],
            'stable': ['patience', 'listening', 'support', 'stability', 'perseverance', 'consistency'],
            'conforme': ['rules', 'precision', 'quality', 'detail', 'analysis', 'accuracy']
        }
    }
    
    if language not in trait_keywords or trait not in trait_keywords[language]:
        return 0
    
    keywords = trait_keywords[language][trait]
    words = answer_text.split()
    
    trait_count = sum(1 for word in words if any(keyword in word for keyword in keywords))
    return min(trait_count * 0.1, 0.3)  # Max 0.3 bonus

def is_likely_copied(answer_text, language):
    """Detect if answer is likely copied from somewhere"""
    # Common copied phrases that don't reflect personal experience
    copied_patterns = {
        'fr': [
            'selon moi', 'il est important de noter que', 'en conclusion',
            'd\'une manière générale', 'il faut savoir que', 'comme chacun sait'
        ],
        'en': [
            'in my opinion', 'it is important to note that', 'in conclusion',
            'generally speaking', 'it should be noted that', 'as everyone knows'
        ]
    }
    
    if language not in copied_patterns:
        return False
    
    patterns = copied_patterns[language]
    return any(pattern in answer_text for pattern in patterns)

def get_validation_error(error_type, language):
    """Get localized validation error messages"""
    errors = {
        'empty': {
            'fr': 'Veuillez fournir une réponse à cette question.',
            'en': 'Please provide an answer to this question.',
            'ar': 'يرجى تقديم إجابة على هذا السؤال.'
        },
        'too_short': {
            'fr': 'Votre réponse est trop courte. Veuillez décrire votre approche plus en détail (minimum 5 caractères).',
            'en': 'Your answer is too short. Please describe your approach in more detail (minimum 5 characters).',
            'ar': 'إجابتك قصيرة جداً. يرجى وصف نهجك بتفصيل أكثر (5 أحرف على الأقل).'
        },
        'too_long': {
            'fr': 'Votre réponse est trop longue. Veuillez la raccourcir (maximum 1000 caractères).',
            'en': 'Your answer is too long. Please shorten it (maximum 1000 characters).',
            'ar': 'إجابتك طويلة جداً. يرجى تقصيرها (1000 حرف كحد أقصى).'
        },
        'meaningless': {
            'fr': 'Veuillez fournir une réponse significative qui décrit votre comportement ou votre approche.',
            'en': 'Please provide a meaningful response that describes your behavior or approach.',
            'ar': 'يرجى تقديم إجابة ذات معنى تصف سلوكك أو نهجك.'
        },
        'gibberish': {
            'fr': 'Votre réponse semble contenir du texte incohérent. Veuillez décrire clairement votre approche.',
            'en': 'Your response appears to contain unclear text. Please describe your approach clearly.',
            'ar': 'يبدو أن إجابتك تحتوي على نص غير مفهوم. يرجى وصف نهجك بوضوح.'
        },
        'repetitive': {
            'fr': 'Votre réponse contient trop de répétitions. Veuillez varier votre vocabulaire.',
            'en': 'Your response contains too much repetition. Please vary your vocabulary.',
            'ar': 'إجابتك تحتوي على تكرار مفرط. يرجى تنويع مفرداتك.'
        },
        'irrelevant': {
            'fr': 'Votre réponse ne semble pas pertinente par rapport à la question. Veuillez décrire comment vous vous comportez personnellement dans cette situation.',
            'en': 'Your response doesn\'t seem relevant to the question. Please describe how you personally behave in this situation.',
            'ar': 'إجابتك لا تبدو ذات صلة بالسؤال. يرجى وصف كيف تتصرف شخصياً في هذا الموقف.'
        },
        'copied': {
            'fr': 'Votre réponse semble copiée. Veuillez décrire votre expérience personnelle avec vos propres mots.',
            'en': 'Your response appears to be copied. Please describe your personal experience in your own words.',
            'ar': 'يبدو أن إجابتك منسوخة. يرجى وصف تجربتك الشخصية بكلماتك الخاصة.'
        },
        'question_copied': {
            'fr': 'Il semble que vous ayez copié la question. Veuillez répondre en décrivant votre comportement personnel dans cette situation.',
            'en': 'It appears you have copied the question. Please answer by describing your personal behavior in this situation.',
            'ar': 'يبدو أنك نسخت السؤال. يرجى الإجابة بوصف سلوكك الشخصي في هذا الموقف.'
        }
    }
    
    return errors.get(error_type, {}).get(language, errors.get(error_type, {}).get('fr', 'Réponse invalide'))

def is_question_language_mixed(question_text, expected_language):
    """Detect if a question mixes languages inappropriately"""
    if not question_text:
        return False
    
    question_lower = question_text.lower()
    
    # Define language-specific indicators
    french_indicators = ['vous', 'votre', 'dans', 'quelles', 'situations', 'comment', 'gérer', 'une', 'des', 'pour', 'avec']
    english_indicators = ['you', 'your', 'what', 'situations', 'how', 'manage', 'when', 'the', 'in', 'do', 'are']
    
    if expected_language == 'fr':
        # For French questions, check for English contamination
        english_word_count = sum(1 for word in english_indicators if word in question_lower)
        french_word_count = sum(1 for word in french_indicators if word in question_lower)
        
        # If we find more English words than French words, it's mixed
        if english_word_count > french_word_count and english_word_count > 2:
            return True
    
    elif expected_language == 'en':
        # For English questions, check for French contamination
        french_word_count = sum(1 for word in french_indicators if word in question_lower)
        english_word_count = sum(1 for word in english_indicators if word in question_lower)
        
        # If we find more French words than English words, it's mixed
        if french_word_count > english_word_count and french_word_count > 2:
            return True
    
    # Check for specific mixed patterns that are problematic
    mixed_patterns = [
        'in what situations do you gérer',
        'comment do you manage',
        'quelles situations you',
        'how gérer vous'
    ]
    
    for pattern in mixed_patterns:
        if pattern in question_lower:
            return True
    
    return False

# Assessment configuration - SHORTENED VERSION
ASSESSMENTS = {
    'big_five': {
        'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
        'questions_per_trait': 1,  # Reduced from 2 to 1
        'order': 1
    },
    'disc': {
        'traits': ['dominant', 'influent', 'stable', 'conforme'],
        'questions_per_trait': 1,  # Reduced from 2 to 1
        'order': 2
    },
    'bien_etre': {
        'questions_total': 1,  # Reduced from 2 to 1
        'order': 3
    },
    'resilience_ie': {
        'questions_total': 1,  # Reduced from 2 to 1
        'order': 4
    }
}

# Localized trait names for display
TRAIT_DISPLAY_NAMES = {
    'ouverture': {
        'fr': 'Ouverture',
        'en': 'Openness',
        'ar': 'الانفتاح'
    },
    'conscienciosité': {
        'fr': 'Conscienciosité',
        'en': 'Conscientiousness',
        'ar': 'الضمير'
    },
    'extraversion': {
        'fr': 'Extraversion',
        'en': 'Extraversion',
        'ar': 'الانبساط'
    },
    'agréabilité': {
        'fr': 'Agréabilité',
        'en': 'Agreeableness',
        'ar': 'الوداعة'
    },
    'stabilité émotionnelle': {
        'fr': 'Stabilité émotionnelle',
        'en': 'Emotional Stability',
        'ar': 'الاستقرار العاطفي'
    },
    'dominant': {
        'fr': 'Dominant',
        'en': 'Dominant',
        'ar': 'مهيمن'
    },
    'influent': {
        'fr': 'Influent',
        'en': 'Influent',
        'ar': 'مؤثر'
    },
    'stable': {
        'fr': 'Stable',
        'en': 'Stable',
        'ar': 'مستقر'
    },
    'conforme': {
        'fr': 'Conforme',
        'en': 'Compliant',
        'ar': 'ملتزم'
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

# Database utility functions
# Database utility functions - RESULTS ONLY, NO INDIVIDUAL ANSWERS
def get_or_create_assessment_session(request):
    """Get or create assessment session for database storage"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Get or create assessment session
    try:
        assessment_session = AssessmentSession.objects.get(session_key=session_key)
    except AssessmentSession.DoesNotExist:
        language = request.session.get('user_data', {}).get('language', 'fr')
        assessment_session = AssessmentSession.objects.create(
            session_key=session_key,
            language=language,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    return assessment_session

def save_final_assessment_results(assessment_session, all_results):
    """Save final assessment results to database - NO individual answers stored"""
    try:
        with transaction.atomic():
            # Update session completion
            assessment_session.completed_at = timezone.now()
            assessment_session.total_duration = assessment_session.completed_at - assessment_session.started_at
            assessment_session.is_completed = True
            
            # Calculate session totals
            total_responses = 0
            
            for assessment_type, traits in all_results.items():
                for trait_name, trait_data in traits.items():
                    total_responses += len(trait_data.get('answers', []))
            
            assessment_session.total_questions = total_responses
            
            # Store final results in JSON fields
            assessment_session.big_five_results = all_results.get('big_five', {})
            assessment_session.disc_results = all_results.get('disc', {})
            assessment_session.wellbeing_result = all_results.get('bien_etre', {})
            assessment_session.resilience_result = all_results.get('resilience_ie', {})
            
          
            assessment_session.save()
            
            # Create individual trait results (final scores only)
            for assessment_type, traits in all_results.items():
                for trait_name, trait_data in traits.items():
                    # Generate detailed analysis
                    detailed_analysis = generate_detailed_analysis(
                        trait_name, 
                        trait_data.get('answers', []), 
                        trait_data.get('total_score', 0), 
                        assessment_session.language, 
                        assessment_type
                    )
                    
                    TraitResult.objects.update_or_create(
                        session=assessment_session,
                        assessment_type=assessment_type,
                        trait_name=trait_name,
                        defaults={
                            'final_score': trait_data.get('total_score', 0),
                            'max_possible_score': trait_data.get('max_score', 10),
                            'percentage_score': (trait_data.get('total_score', 0) / trait_data.get('max_score', 10)) * 100,
                            'level': trait_data.get('level', 'modéré'),
                            'detailed_analysis': detailed_analysis,
                            'strengths': detailed_analysis.get('points_forts', []) if isinstance(detailed_analysis, dict) else [],
                            'areas_for_improvement': detailed_analysis.get('zones_amelioration', []) if isinstance(detailed_analysis, dict) else [],
                            'recommendations': detailed_analysis.get('conseils', []) if isinstance(detailed_analysis, dict) else [],
                            'response_patterns': {
                                'total_responses': len(trait_data.get('answers', [])),
                                'average_score': trait_data.get('total_score', 0) / max(len(trait_data.get('answers', [])), 1),
                                'level': trait_data.get('level', 'modéré')
                            }
                        }
                    )
            
            # Create assessment summary
            summary_data = prepare_assessment_summary(all_results, assessment_session.language)
            
            AssessmentSummary.objects.update_or_create(
                session=assessment_session,
                defaults={
                    'completion_rate': 100.0,
                    'average_engagement': summary_data.get('avg_engagement', 0.0),
                    'overall_authenticity': summary_data.get('avg_authenticity', 0.0),
                    'dominant_personality_traits': summary_data.get('dominant_traits', []),
                    'key_strengths': summary_data.get('key_strengths', []),
                    'development_priorities': summary_data.get('development_priorities', []),
                    'response_style': summary_data.get('response_style', ''),
                    'decision_making_style': summary_data.get('decision_style', ''),
                    'communication_style': summary_data.get('communication_style', ''),
                    'personality_narrative': summary_data.get('personality_narrative', ''),
                    'development_plan': summary_data.get('development_plan', '')
                }
            )
            
            return True
    
    except Exception as e:
        logger.error(f"Error saving final assessment results: {e}")
        return False

def prepare_assessment_summary(all_results, language):
    """Prepare comprehensive summary data"""
    dominant_traits = []
    key_strengths = []
    development_priorities = []
    
    # Analyze Big Five results
    if 'big_five' in all_results:
        for trait_name, trait_data in all_results['big_five'].items():
            level = trait_data.get('level', 'modéré')
            score = trait_data.get('total_score', 0)
            
            if level == 'élevé' or score >= 8:
                dominant_traits.append(trait_name)
                key_strengths.append(f"Fort en {trait_name}")
            elif level == 'faible' or score <= 4:
                development_priorities.append(f"Développer {trait_name}")
    
    # Analyze DISC results
    if 'disc' in all_results:
        disc_scores = [(trait, data.get('total_score', 0)) for trait, data in all_results['disc'].items()]
        disc_scores.sort(key=lambda x: x[1], reverse=True)
        if disc_scores:
            dominant_style = disc_scores[0][0]
            dominant_traits.append(f"Style {dominant_style}")
    
    return {
        'dominant_traits': dominant_traits,
        'key_strengths': key_strengths,
        'development_priorities': development_priorities,
        'avg_engagement': 75.0,  # Can be calculated from response patterns
        'avg_authenticity': 80.0,  # Can be calculated from response patterns
        'response_style': 'analytical' if len(dominant_traits) > 2 else 'balanced',
        'decision_style': 'thoughtful',
        'communication_style': 'direct' if 'dominant' in [t.lower() for t in dominant_traits] else 'collaborative',
        'personality_narrative': f"Profil dominé par: {', '.join(dominant_traits[:3])}",
        'development_plan': f"Focus sur: {', '.join(development_priorities[:3])}"
    }

def choose_language(request):
    if request.method == "POST":
        lang = request.POST.get("language", "fr")
        
        # Initialize comprehensive session data
        request.session['user_data'] = {
            'language': lang,
            'start_time': time.time(),
            'current_assessment': 'big_five',
            'current_trait': ASSESSMENTS['big_five']['traits'][0],
            'current_question_number': 1,
            'is_completed': False,
            'responses': [],
            'psychological_profile': {
                'response_times': [],
                'answer_lengths': [],
                'emotional_patterns': [],
                'consistency_scores': []
            },
            'assessment_progress': {
                'big_five': {'completed_traits': [], 'current_trait_index': 0},
                'disc': {'completed_traits': [], 'current_trait_index': 0},
                'bien_etre': {'questions_completed': 0},
                'resilience_ie': {'questions_completed': 0}
            },
            'results': {}
        }
        
        return redirect('quiz')
    
    return render(request, 'choose_language.html')

def quiz(request):
    # Check if session exists
    if 'user_data' not in request.session:
        return redirect('choose_language')
    
    user_data = request.session['user_data']
    
    if user_data['is_completed']:
        return redirect('report')
    
    if request.method == "POST":
        # Capture behavioral metrics
        answer_text = request.POST.get('answer', '').strip()
        response_time = time.time() - user_data.get('question_start_time', time.time())
        
        # Comprehensive input validation
        current_assessment = user_data['current_assessment']
        current_trait = user_data.get('current_trait', 'general')
        language = user_data['language']
        
        # Validate the answer
        is_valid, error_message = validate_answer(
            answer_text, 
            language, 
            current_trait, 
            current_assessment
        )
        
        if not is_valid:
            return JsonResponse({
                'error': error_message,
                'validation_failed': True
            }, status=400)
        
        # Enhanced behavioral analysis
        # Get session key for question tracking
        session_key = request.session.session_key or f"temp_{hash(user_data['start_time'])}"
        
        # Get previous responses for context
        previous_responses = [r for r in user_data['responses'] 
                            if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
        
        # Enhanced tone and typing analysis
        enhanced_tone_analysis = analyze_response_tone(answer_text, response_time, len(answer_text))
        
        # Behavioral scoring using optimized function
        try:
            score = analyze_answer(
                answer_text=answer_text,
                trait=current_trait,
                all_answers_for_trait=[r['text'] for r in previous_responses],
                language=user_data['language'],
                assessment_type=current_assessment
            )
        except Exception as e:
            logger.error(f"Error analyzing answer: {e}")
            # Fallback scoring based on answer quality indicators
            score = calculate_fallback_score(answer_text)
        
        # Analyze behavioral patterns (keeping for compatibility)
        emotional_tone = analyze_behavioral_tone(answer_text, response_time)
        engagement_level = analyze_response_quality(answer_text, response_time)
        
        # Store comprehensive response data
        response_data = {
            'assessment': current_assessment,
            'trait': current_trait,
            'question_number': user_data['current_question_number'],
            'text': answer_text,
            'score': score,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat(),
            'emotional_tone': emotional_tone,
            'engagement_level': engagement_level,
            'answer_length': len(answer_text),
            'enhanced_analysis': enhanced_tone_analysis  # Add enhanced analysis
        }
        
        user_data['responses'].append(response_data)
        
        # Create or get assessment session for final results (no individual responses saved)
        try:
            assessment_session = get_or_create_assessment_session(request)
            # Only creating session here, no individual responses saved
        except Exception as e:
            logger.error(f"Error creating assessment session: {e}")
            # Continue without database on error
        
        # Update psychological profile
        user_data['psychological_profile']['response_times'].append(response_time)
        user_data['psychological_profile']['answer_lengths'].append(len(answer_text))
        user_data['psychological_profile']['emotional_patterns'].append(emotional_tone)
        
        # Determine next step
        try:
            next_step = get_next_step(user_data)
            
            # Debug logging
            logger.error(f"Progress Debug - Current: {current_assessment}, Trait: {current_trait}, Question: {user_data['current_question_number']}")
            logger.error(f"Next step: {next_step}")
            
            if next_step.get('completed', False):
                user_data['is_completed'] = True
                request.session['user_data'] = user_data
                return JsonResponse({'completed': True, 'redirect': '/report/'})
            else:
                # Update session with next step
                user_data.update(next_step)
                request.session['user_data'] = user_data
                request.session.modified = True
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error determining next step: {e}")
            # Fallback: progress naturally
            if user_data['current_question_number'] < ASSESSMENTS[current_assessment].get('questions_per_trait', 2):
                user_data['current_question_number'] += 1
            else:
                user_data['is_completed'] = True
            
            request.session['user_data'] = user_data
            request.session.modified = True
            
            if user_data['is_completed']:
                return JsonResponse({'completed': True, 'redirect': '/report/'})
            else:
                return JsonResponse({'success': True})
    
    # Generate next question using optimized system with repetition prevention
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait', 'general')
    question_number = user_data['current_question_number']
    session_key = request.session.session_key or f"temp_{hash(user_data['start_time'])}"
    
    # Get previous responses for context
    previous_responses = [r for r in user_data['responses'] 
                        if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
    
    # Determine previous_score
    previous_score = None
    if previous_responses:
        previous_score = previous_responses[-1].get('score')
    
    # Generate behavioral question using optimized function with repetition check
    max_attempts = 3
    question_text = None
    
    for attempt in range(max_attempts):
        try:
            candidate_question = generate_question(
                trait=current_trait,
                question_number=question_number,
                previous_answers=[r['text'] for r in previous_responses],
                previous_score=previous_score,
                language=user_data['language'],
                assessment_type=current_assessment
            )
            
            # Check for repetition
            if not is_question_already_used(session_key, candidate_question):
                # Validate question for language mixing
                if not is_question_language_mixed(candidate_question, user_data['language']):
                    question_text = candidate_question
                    track_used_question(session_key, question_text)
                    break
                else:
                    logger.error(f"Mixed language question detected: {candidate_question}")
            else:
                logger.error(f"Question repetition detected, attempt {attempt + 1}")
        except Exception as e:
            logger.error(f"Error generating question attempt {attempt + 1}: {e}")
    
    # Fallback if all attempts failed
    if not question_text:
        question_text = get_behavioral_questions(
            trait=current_trait,
            question_number=question_number,
            previous_answers=[r['text'] for r in previous_responses],
            previous_score=previous_score,
            language=user_data['language'],
            assessment_type=current_assessment
        )
        # Track fallback question too
        if not is_question_already_used(session_key, question_text):
            track_used_question(session_key, question_text)
    
    # Store question start time for response time tracking
    user_data['question_start_time'] = time.time()
    request.session['user_data'] = user_data
    request.session.modified = True
    
    # Calculate progress
    total_questions = calculate_total_questions()
    completed_questions = len(user_data['responses'])
    progress_percentage = (completed_questions / total_questions) * 100
    
    # Debug logging
    logger.error(f"Progress calculation - Completed: {completed_questions}, Total: {total_questions}, Percentage: {progress_percentage}")
    logger.error(f"Current state - Assessment: {current_assessment}, Trait: {current_trait}, Question: {question_number}")
    
    # Get trait introduction
    try:
        trait_intro = get_trait_intro(current_trait, user_data['language'], current_assessment)
    except Exception as e:
        logger.error(f"Error getting trait intro: {e}")
        trait_intro = ""
    
    context = {
        'session': {
            'language': user_data['language'],
            'current_assessment': current_assessment,
            'current_trait': current_trait,
            'current_question_number': question_number,
        },
        'question': question_text,
        'progress': int(progress_percentage),
        'trait_intro': trait_intro,
        'current_assessment': current_assessment,
        'current_trait_display': get_localized_trait_name(current_trait, user_data['language']),
        'trait_progress': f"{question_number}/{ASSESSMENTS[current_assessment].get('questions_per_trait', 2)}",
        'assessment_name': get_assessment_name(current_assessment, user_data['language']),
        'ui_text': {
            'submit_button': get_ui_text('submit_button', user_data['language']),
            'answer_placeholder': get_ui_text('answer_placeholder', user_data['language']),
            'trait_analysis': get_ui_text('trait_analysis_title', user_data['language'])
        }
    }
    
    return render(request, 'quiz.html', context)

def calculate_fallback_score(answer_text):
    """Improved fallback scoring based on behavioral indicators"""
    if not answer_text.strip():
        return 1
    
    # Score based on behavioral content quality
    behavioral_words = ['décide', 'stratégie', 'approche', 'méthode', 'gère', 'organise', 'planifie', 'adapte']
    answer_lower = answer_text.lower()
    
    behavioral_count = sum(1 for word in behavioral_words if word in answer_lower)
    length_factor = min(len(answer_text) // 30, 3)  # Length bonus
    
    score = max(2, min(5, 2 + behavioral_count + length_factor))
    return score

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
    total += len(ASSESSMENTS['big_five']['traits']) * ASSESSMENTS['big_five']['questions_per_trait']  # 5 traits × 1 question
    total += len(ASSESSMENTS['disc']['traits']) * ASSESSMENTS['disc']['questions_per_trait']  # 4 styles × 1 question  
    total += ASSESSMENTS['bien_etre']['questions_total']  # 1 question
    total += ASSESSMENTS['resilience_ie']['questions_total']  # 1 question
    return total  # Total: 11 questions

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

def get_localized_trait_name(trait, language):
    """Get localized trait name for display"""
    return TRAIT_DISPLAY_NAMES.get(trait, {}).get(language, trait)

def get_ui_text(key, language):
    """Get localized UI text"""
    ui_texts = {
        'next_button': {
            'fr': 'Continuer',
            'en': 'Continue',
            'ar': 'متابعة'
        },
        'submit_button': {
            'fr': 'Soumettre',
            'en': 'Submit',
            'ar': 'إرسال'
        },
        'progress_text': {
            'fr': 'Question {current} sur {total}',
            'en': 'Question {current} of {total}',
            'ar': 'السؤال {current} من {total}'
        },
        'answer_placeholder': {
            'fr': 'Décrivez votre approche en détail...',
            'en': 'Describe your approach in detail...',
            'ar': 'صف نهجك بالتفصيل...'
        },
        'trait_analysis_title': {
            'fr': 'Analyse comportementale',
            'en': 'Behavioral Analysis',
            'ar': 'التحليل السلوكي'
        }
    }
    return ui_texts.get(key, {}).get(language, ui_texts.get(key, {}).get('fr', key))

def report(request):
    if 'user_data' not in request.session or not request.session['user_data'].get('is_completed'):
        return redirect('choose_language')
    
    user_data = request.session['user_data']
    language = user_data['language']
    
    # Generate comprehensive results
    results = generate_results(user_data)
    
    # Save final results to database (no individual answers)
    try:
        assessment_session = get_or_create_assessment_session(request)
        save_final_assessment_results(assessment_session, results)
        logger.info(f"Final assessment results saved for session {assessment_session.session_key}")
    except Exception as e:
        logger.error(f"Error saving final results to database: {e}")
        # Continue even if database save fails
    
   
    
    # Generate score explanations
    try:
        score_explanations = generate_score_explanations(results, language)
        # Format explanations for template access
        formatted_explanations = {}
        if 'big_five' in results:
            for trait in results['big_five'].keys():
                key = f'big_five_{trait}'
                if key in score_explanations:
                    formatted_explanations[trait] = score_explanations[key]
        
        if 'disc' in results:
            for style in results['disc'].keys():
                key = f'disc_{style}'
                if key in score_explanations:
                    formatted_explanations[f'disc_{style}'] = score_explanations[key]
        
        if 'bien_etre' in score_explanations:
            formatted_explanations['bien_etre'] = score_explanations['bien_etre']
        if 'resilience_ie' in score_explanations:
            formatted_explanations['resilience_ie'] = score_explanations['resilience_ie']
            
    except Exception as e:
        logger.error(f"Error generating score explanations: {e}")
        formatted_explanations = {}

    context = {
        'session': {
            'language': language,
            'is_completed': True,
        },
        'results': results,
        'score_explanations': formatted_explanations,
        'assessment_summary': generate_summary(user_data, language),
        'development_recommendations': generate_development_recommendations(results, language),
    
    }
    
    return render(request, 'report.html', context)

def generate_results(user_data):
    """Generate results for all assessments"""
    results = {}
    responses = user_data['responses']
    language = user_data['language']
    
    # Big Five results
    big_five_results = {}
    for trait in ASSESSMENTS['big_five']['traits']:
        trait_responses = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if trait_responses:
            scores = [r['score'] for r in trait_responses]
            avg_score = sum(scores) / len(scores)
            # For single questions, scale directly to 10 (instead of *5)
            total_score = avg_score * 2  # Scale 5-point to 10-point scale
            
            big_five_results[trait] = {
             'score': round(total_score, 1),
             'level': get_level_from_score(total_score, 'big_five', language),
             'responses': trait_responses,
            'detailed_analysis': generate_enhanced_detailed_analysis(trait, [r['text'] for r in trait_responses], total_score, language, 'big_five')
} 
    
    results['big_five'] = big_five_results
    
    # DISC results
    disc_results = {}
    for style in ASSESSMENTS['disc']['traits']:
        style_responses = [r for r in responses if r['trait'] == style and r['assessment'] == 'disc']
        if style_responses:
            scores = [r['score'] for r in style_responses]
            avg_score = sum(scores) / len(scores)
            
           
    
    results['disc'] = disc_results
    
    # Well-being results
    wellbeing_responses = [r for r in responses if r['assessment'] == 'bien_etre']
    if wellbeing_responses:
        scores = [r['score'] for r in wellbeing_responses]
        # For single question, scale directly
        total_score = sum(scores) * 2  # Scale 5-point to 10-point scale
        
        results['bien_etre'] = {
    'score': round(total_score, 1),
    'level': get_level_from_score(total_score, 'bien_etre', language),
    'responses': wellbeing_responses,
    'detailed_analysis': generate_enhanced_detailed_analysis('bien_etre', [r['text'] for r in wellbeing_responses], total_score, language, 'bien_etre')
}
    
    # Resilience results
    resilience_responses = [r for r in responses if r['assessment'] == 'resilience_ie']
    if resilience_responses:
        scores = [r['score'] for r in resilience_responses]
        # For single question, scale directly
        total_score = sum(scores) * 2  # Scale 5-point to 10-point scale
        
        results['resilience_ie'] = {
    'score': round(total_score, 1),
    'level': get_level_from_score(total_score, 'resilience_ie', language),
    'responses': resilience_responses,
    'detailed_analysis': generate_enhanced_detailed_analysis('resilience_ie', [r['text'] for r in resilience_responses], total_score, language, 'resilience_ie')
}
    
    return results

def get_level_from_score(score, assessment_type, language="fr"):
    """Determine level based on score"""
    if assessment_type == "big_five":
        if score <= 4:
            return {"fr": "faible", "en": "low", "ar": "منخفض"}[language]
        elif score <= 7:
            return {"fr": "modéré", "en": "moderate", "ar": "متوسط"}[language]
        else:
            return {"fr": "élevé", "en": "high", "ar": "عالي"}[language]
    elif assessment_type == "bien_etre":
        if score <= 4:
            return {"fr": "faible", "en": "low", "ar": "منخفض"}[language]
        elif score <= 7:
            return {"fr": "modéré", "en": "moderate", "ar": "متوسط"}[language]
        else:
            return {"fr": "élevé", "en": "high", "ar": "عالي"}[language]
    elif assessment_type == "resilience_ie":
        if score <= 4:
            return {"fr": "faible", "en": "low", "ar": "منخفض"}[language]
        elif score <= 7:
            return {"fr": "modéré", "en": "moderate", "ar": "متوسط"}[language]
        else:
            return {"fr": "élevé", "en": "high", "ar": "عالي"}[language]
    else:
        return {"fr": "modéré", "en": "moderate", "ar": "متوسط"}[language]

def generate_insights(user_data, language):
    """Generate insights from behavioral patterns"""
    profile = user_data['psychological_profile']
    
    insights = {
        'response_patterns': analyze_patterns(profile, language),
        'engagement_level': analyze_engagement(profile, language),
        'consistency': analyze_consistency(profile, language)
    }
    
    return insights

def analyze_patterns(profile, language):
    """Analyze response time and length patterns"""
    if not profile['response_times']:
        return "Données insuffisantes" if language == 'fr' else "Insufficient data" if language == 'en' else "بيانات غير كافية"
    
    avg_time = sum(profile['response_times']) / len(profile['response_times'])
    avg_length = sum(profile['answer_lengths']) / len(profile['answer_lengths'])
    
    patterns = {
        'fr': f"Temps de réponse moyen: {avg_time:.1f}s, Longueur moyenne: {avg_length:.0f} caractères",
        'en': f"Average response time: {avg_time:.1f}s, Average length: {avg_length:.0f} characters",
        'ar': f"متوسط وقت الاستجابة: {avg_time:.1f}ث، متوسط الطول: {avg_length:.0f} حرف"
    }
    
    return patterns.get(language, patterns['fr'])

def analyze_engagement(profile, language):
    """Analyze overall engagement based on multiple factors"""
    if not profile['answer_lengths']:
        return "Modéré" if language == 'fr' else "Moderate" if language == 'en' else "متوسط"
    
    avg_length = sum(profile['answer_lengths']) / len(profile['answer_lengths'])
    
    if avg_length > 100:
        level = "Élevé" if language == 'fr' else "High" if language == 'en' else "عالي"
    elif avg_length > 50:
        level = "Modéré" if language == 'fr' else "Medium" if language == 'en' else "متوسط"
    else:
        level = "Faible" if language == 'fr' else "Low" if language == 'en' else "منخفض"
    
    return level

def analyze_consistency(profile, language):
    """Analyze response consistency"""
    if len(profile['answer_lengths']) < 3:
        return "Données insuffisantes" if language == 'fr' else "Insufficient data" if language == 'en' else "بيانات غير كافية"
    
    lengths = profile['answer_lengths']
    times = profile['response_times']
    
    # Calculate variance
    length_variance = sum((x - sum(lengths)/len(lengths))**2 for x in lengths) / len(lengths)
    time_variance = sum((x - sum(times)/len(times))**2 for x in times) / len(times)
    
    if length_variance < 500 and time_variance < 10:
        consistency = "Élevée" if language == 'fr' else "High" if language == 'en' else "عالية"
    elif length_variance < 1000 and time_variance < 20:
        consistency = "Modérée" if language == 'fr' else "Medium" if language == 'en' else "متوسطة"
    else:
        consistency = "Variable" if language == 'fr' else "Variable" if language == 'en' else "متغيرة"
    
    return consistency

def generate_comprehensive_insights(user_data, results, language):
    """Generate comprehensive psychological insights based on all responses"""
    responses = user_data['responses']
    profile = user_data['psychological_profile']
    
    insights = {
        'decision_making_style': analyze_decision_making_style(responses, language),
        'stress_management': analyze_stress_patterns(responses, language),
        'communication_style': analyze_communication_patterns(responses, language),
        'work_preferences': analyze_work_preferences(responses, language),
        'cognitive_style': analyze_cognitive_approach(responses, language),
        'emotional_intelligence': assess_emotional_intelligence(responses, language),
        'adaptability': analyze_adaptability(responses, language)
    }
    
    return insights

def analyze_decision_making_style(responses, language):
    """Analyze how the user makes decisions based on their responses"""
    decision_indicators = {
        'analytical': ['analyse', 'évalue', 'examine', 'compare', 'données', 'facts', 'analyze', 'evaluate', 'examine', 'data'],
        'intuitive': ['instinct', 'ressens', 'impression', 'intuition', 'feel', 'sense', 'gut'],
        'collaborative': ['équipe', 'consulte', 'discute', 'avis', 'team', 'consult', 'discuss', 'advice'],
        'decisive': ['décide', 'rapidement', 'action', 'decide', 'quickly', 'immediate']
    }
    
    style_scores = {style: 0 for style in decision_indicators}
    
    for response in responses:
        text_lower = response['text'].lower()
        for style, keywords in decision_indicators.items():
            style_scores[style] += sum(1 for keyword in keywords if keyword in text_lower)
    
    # Find dominant style
    dominant_style = max(style_scores, key=style_scores.get)
    
    descriptions = {
        'analytical': {
            'fr': "Style analytique - Vous prenez des décisions basées sur l'analyse approfondie des données et des faits.",
            'en': "Analytical style - You make decisions based on thorough analysis of data and facts.",
            'ar': "النمط التحليلي - تتخذ القرارات بناءً على التحليل الشامل للبيانات والحقائق."
        },
        'intuitive': {
            'fr': "Style intuitif - Vous faites confiance à votre instinct et à vos impressions pour prendre des décisions.",
            'en': "Intuitive style - You trust your instincts and impressions when making decisions.",
            'ar': "النمط البديهي - تثق في غرائزك وانطباعاتك عند اتخاذ القرارات."
        },
        'collaborative': {
            'fr': "Style collaboratif - Vous préférez consulter et impliquer les autres dans vos décisions.",
            'en': "Collaborative style - You prefer to consult and involve others in your decisions.",
            'ar': "النمط التعاوني - تفضل استشارة وإشراك الآخرين في قراراتك."
        },
        'decisive': {
            'fr': "Style décisif - Vous prenez des décisions rapidement et passez à l'action.",
            'en': "Decisive style - You make decisions quickly and take action.",
            'ar': "النمط الحاسم - تتخذ القرارات بسرعة وتنتقل إلى العمل."
        }
    }
    
    return {
        'style': dominant_style,
        'description': descriptions[dominant_style].get(language, descriptions[dominant_style]['en']),
        'confidence': min(100, (style_scores[dominant_style] / max(1, sum(style_scores.values()))) * 100)
    }

def analyze_stress_patterns(responses, language):
    """Analyze how the user handles stress and pressure"""
    stress_indicators = {
        'problem_solver': ['solution', 'résoudre', 'plan', 'organize', 'stratégie', 'solve', 'strategy'],
        'support_seeker': ['aide', 'soutien', 'équipe', 'conseil', 'help', 'support', 'team', 'advice'],
        'self_reliant': ['seul', 'autonome', 'indépendant', 'alone', 'independent', 'self'],
        'avoidant': ['évite', 'difficile', 'stress', 'avoid', 'difficult', 'pressure']
    }
    
    pattern_scores = {pattern: 0 for pattern in stress_indicators}
    
    for response in responses:
        if any(word in response['text'].lower() for word in ['stress', 'pressure', 'difficile', 'challenge', 'crise', 'crisis']):
            text_lower = response['text'].lower()
            for pattern, keywords in stress_indicators.items():
                pattern_scores[pattern] += sum(1 for keyword in keywords if keyword in text_lower)
    
    dominant_pattern = max(pattern_scores, key=pattern_scores.get) if sum(pattern_scores.values()) > 0 else 'problem_solver'
    
    descriptions = {
        'problem_solver': {
            'fr': "Vous abordez le stress en cherchant activement des solutions et en planifiant.",
            'en': "You approach stress by actively seeking solutions and planning.",
            'ar': "تتعامل مع التوتر من خلال البحث النشط عن الحلول والتخطيط."
        },
        'support_seeker': {
            'fr': "Vous gérez le stress en cherchant du soutien auprès des autres.",
            'en': "You manage stress by seeking support from others.",
            'ar': "تدير التوتر من خلال طلب الدعم من الآخرين."
        },
        'self_reliant': {
            'fr': "Vous préférez gérer le stress de manière autonome et indépendante.",
            'en': "You prefer to manage stress autonomously and independently.",
            'ar': "تفضل إدارة التوتر بشكل مستقل وذاتي."
        },
        'avoidant': {
            'fr': "Vous avez tendance à éviter les situations stressantes quand possible.",
            'en': "You tend to avoid stressful situations when possible.",
            'ar': "تميل إلى تجنب المواقف المجهدة عندما يكون ذلك ممكناً."
        }
    }
    
    return {
        'pattern': dominant_pattern,
        'description': descriptions[dominant_pattern].get(language, descriptions[dominant_pattern]['en'])
    }

def analyze_communication_patterns(responses, language):
    """Analyze communication and interpersonal style"""
    comm_indicators = {
        'direct': ['direct', 'clair', 'précis', 'clear', 'straightforward', 'honest'],
        'diplomatic': ['diplomate', 'tactful', 'nuancé', 'diplomatic', 'careful', 'considerate'],
        'expressive': ['exprime', 'partage', 'communique', 'express', 'share', 'communicate'],
        'reserved': ['réservé', 'écoute', 'observe', 'reserved', 'listen', 'observe']
    }
    
    style_scores = {style: 0 for style in comm_indicators}
    
    for response in responses:
        text_lower = response['text'].lower()
        for style, keywords in comm_indicators.items():
            style_scores[style] += sum(1 for keyword in keywords if keyword in text_lower)
    
    dominant_style = max(style_scores, key=style_scores.get)
    
    descriptions = {
        'direct': {
            'fr': "Communication directe - Vous privilégiez la clarté et la franchise dans vos échanges.",
            'en': "Direct communication - You prioritize clarity and honesty in your interactions.",
            'ar': "التواصل المباشر - تعطي الأولوية للوضوح والصدق في تفاعلاتك."
        },
        'diplomatic': {
            'fr': "Communication diplomatique - Vous adaptez votre message selon le contexte et l'audience.",
            'en': "Diplomatic communication - You adapt your message based on context and audience.",
            'ar': "التواصل الدبلوماسي - تكيف رسالتك حسب السياق والجمهور."
        },
        'expressive': {
            'fr': "Communication expressive - Vous partagez ouvertement vos idées et émotions.",
            'en': "Expressive communication - You openly share your ideas and emotions.",
            'ar': "التواصل التعبيري - تشارك أفكارك ومشاعرك بانفتاح."
        },
        'reserved': {
            'fr': "Communication réservée - Vous préférez écouter et observer avant de vous exprimer.",
            'en': "Reserved communication - You prefer to listen and observe before expressing yourself.",
            'ar': "التواصل المتحفظ - تفضل الاستماع والمراقبة قبل التعبير عن نفسك."
        }
    }
    
    return {
        'style': dominant_style,
        'description': descriptions[dominant_style].get(language, descriptions[dominant_style]['en'])
    }

def analyze_work_preferences(responses, language):
    """Analyze preferred work environment and style"""
    work_indicators = {
        'collaborative': ['équipe', 'collaboration', 'team', 'together', 'group'],
        'independent': ['seul', 'autonome', 'indépendant', 'alone', 'independent', 'solo'],
        'structured': ['organisation', 'planifie', 'structure', 'organize', 'plan', 'schedule'],
        'flexible': ['flexible', 'adaptable', 'changement', 'change', 'variety']
    }
    
    preference_scores = {pref: 0 for pref in work_indicators}
    
    for response in responses:
        text_lower = response['text'].lower()
        for pref, keywords in work_indicators.items():
            preference_scores[pref] += sum(1 for keyword in keywords if keyword in text_lower)
    
    dominant_pref = max(preference_scores, key=preference_scores.get)
    
    descriptions = {
        'collaborative': {
            'fr': "Préférence collaborative - Vous excellez dans le travail d'équipe et les projets collectifs.",
            'en': "Collaborative preference - You excel in teamwork and collective projects.",
            'ar': "التفضيل التعاوني - تتميز في العمل الجماعي والمشاريع الجماعية."
        },
        'independent': {
            'fr': "Préférence autonome - Vous préférez travailler de manière indépendante avec une grande autonomie.",
            'en': "Independent preference - You prefer to work independently with high autonomy.",
            'ar': "التفضيل المستقل - تفضل العمل بشكل مستقل مع استقلالية عالية."
        },
        'structured': {
            'fr': "Préférence structurée - Vous fonctionnez mieux dans des environnements organisés et planifiés.",
            'en': "Structured preference - You function better in organized and planned environments.",
            'ar': "التفضيل المنظم - تعمل بشكل أفضل في البيئات المنظمة والمخططة."
        },
        'flexible': {
            'fr': "Préférence flexible - Vous appréciez la variété et l'adaptabilité dans votre travail.",
            'en': "Flexible preference - You appreciate variety and adaptability in your work.",
            'ar': "التفضيل المرن - تقدر التنوع والقدرة على التكيف في عملك."
        }
    }
    
    return {
        'preference': dominant_pref,
        'description': descriptions[dominant_pref].get(language, descriptions[dominant_pref]['en'])
    }

def analyze_cognitive_approach(responses, language):
    """Analyze thinking and problem-solving style"""
    cognitive_indicators = {
        'systematic': ['système', 'méthodique', 'étape', 'systematic', 'methodical', 'step'],
        'creative': ['créatif', 'innovant', 'original', 'creative', 'innovative', 'original'],
        'logical': ['logique', 'rationnel', 'analyse', 'logical', 'rational', 'analyze'],
        'holistic': ['global', 'ensemble', 'vue', 'big picture', 'overall', 'whole']
    }
    
    approach_scores = {approach: 0 for approach in cognitive_indicators}
    
    for response in responses:
        text_lower = response['text'].lower()
        for approach, keywords in cognitive_indicators.items():
            approach_scores[approach] += sum(1 for keyword in keywords if keyword in text_lower)
    
    dominant_approach = max(approach_scores, key=approach_scores.get)
    
    descriptions = {
        'systematic': {
            'fr': "Approche systématique - Vous abordez les problèmes de manière méthodique et structurée.",
            'en': "Systematic approach - You tackle problems methodically and structurally.",
            'ar': "المنهج المنتظم - تتعامل مع المشاكل بطريقة منهجية ومنظمة."
        },
        'creative': {
            'fr': "Approche créative - Vous privilégiez l'innovation et les solutions originales.",
            'en': "Creative approach - You favor innovation and original solutions.",
            'ar': "المنهج الإبداعي - تفضل الابتكار والحلول الأصيلة."
        },
        'logical': {
            'fr': "Approche logique - Vous basez vos décisions sur l'analyse rationnelle.",
            'en': "Logical approach - You base your decisions on rational analysis.",
            'ar': "المنهج المنطقي - تؤسس قراراتك على التحليل العقلاني."
        },
        'holistic': {
            'fr': "Approche holistique - Vous considérez la situation dans son ensemble.",
            'en': "Holistic approach - You consider the situation as a whole.",
            'ar': "المنهج الشمولي - تنظر في الوضع ككل."
        }
    }
    
    return {
        'approach': dominant_approach,
        'description': descriptions[dominant_approach].get(language, descriptions[dominant_approach]['en'])
    }

def assess_emotional_intelligence(responses, language):
    """Assess emotional intelligence based on responses"""
    ei_indicators = {
        'self_awareness': ['ressens', 'émotions', 'conscient', 'feel', 'emotions', 'aware'],
        'empathy': ['comprends', 'autres', 'empathie', 'understand', 'others', 'empathy'],
        'social_skills': ['relation', 'communication', 'social', 'relationship', 'interact'],
        'regulation': ['contrôle', 'gère', 'calme', 'control', 'manage', 'calm']
    }
    
    ei_scores = {skill: 0 for skill in ei_indicators}
    
    for response in responses:
        text_lower = response['text'].lower()
        for skill, keywords in ei_indicators.items():
            ei_scores[skill] += sum(1 for keyword in keywords if keyword in text_lower)
    
    total_score = sum(ei_scores.values())
    ei_level = 'high' if total_score >= 10 else 'moderate' if total_score >= 5 else 'developing'
    
    descriptions = {
        'high': {
            'fr': "Intelligence émotionnelle élevée - Vous montrez une excellente compréhension des émotions.",
            'en': "High emotional intelligence - You show excellent understanding of emotions.",
            'ar': "ذكاء عاطفي عالي - تُظهر فهماً ممتازاً للمشاعر."
        },
        'moderate': {
            'fr': "Intelligence émotionnelle modérée - Vous avez une bonne conscience émotionnelle.",
            'en': "Moderate emotional intelligence - You have good emotional awareness.",
            'ar': "ذكاء عاطفي متوسط - لديك وعي عاطفي جيد."
        },
        'developing': {
            'fr': "Intelligence émotionnelle en développement - Opportunité de croissance dans ce domaine.",
            'en': "Developing emotional intelligence - Growth opportunity in this area.",
            'ar': "ذكاء عاطفي في طور التطوير - فرصة للنمو في هذا المجال."
        }
    }
    
    return {
        'level': ei_level,
        'description': descriptions[ei_level].get(language, descriptions[ei_level]['en']),
        'scores': ei_scores
    }

def analyze_adaptability(responses, language):
    """Analyze adaptability and flexibility"""
    adaptability_keywords = ['adaptable', 'flexible', 'changement', 'change', 'adjust', 'new', 'nouveau']
    
    adaptability_score = 0
    for response in responses:
        text_lower = response['text'].lower()
        adaptability_score += sum(1 for keyword in adaptability_keywords if keyword in text_lower)
    
    if adaptability_score >= 5:
        level = 'high'
    elif adaptability_score >= 2:
        level = 'moderate'
    else:
        level = 'low'
    
    descriptions = {
        'high': {
            'fr': "Haute adaptabilité - Vous vous ajustez facilement aux changements et nouvelles situations.",
            'en': "High adaptability - You easily adjust to changes and new situations.",
            'ar': "قدرة تكيف عالية - تتكيف بسهولة مع التغييرات والمواقف الجديدة."
        },
        'moderate': {
            'fr': "Adaptabilité modérée - Vous gérez bien les changements avec du temps d'adaptation.",
            'en': "Moderate adaptability - You handle changes well with some adjustment time.",
            'ar': "قدرة تكيف متوسطة - تتعامل جيداً مع التغييرات مع بعض وقت التكيف."
        },
        'low': {
            'fr': "Préférence pour la stabilité - Vous fonctionnez mieux dans des environnements stables.",
            'en': "Preference for stability - You function better in stable environments.",
            'ar': "تفضيل للاستقرار - تعمل بشكل أفضل في البيئات المستقرة."
        }
    }
    
    return {
        'level': level,
        'description': descriptions[level].get(language, descriptions[level]['en'])
    }

def generate_personality_profile(user_data, results, language):
    """Generate a comprehensive personality profile"""
    responses = user_data['responses']
    
    # Dominant traits analysis
    dominant_traits = []
    if 'big_five' in results:
        for trait, data in results['big_five'].items():
            if data.get('score', 0) >= 15:  # High score threshold
                dominant_traits.append(trait)
    
    # Response patterns
    avg_response_time = sum(user_data['psychological_profile']['response_times']) / len(user_data['psychological_profile']['response_times'])
    avg_response_length = sum(user_data['psychological_profile']['answer_lengths']) / len(user_data['psychological_profile']['answer_lengths'])
    
    # Generate profile summary
    profile_texts = {
        'fr': f"""Profil de personnalité basé sur {len(responses)} réponses analysées.
        
Temps de réflexion moyen: {avg_response_time:.1f} secondes
Profondeur des réponses: {avg_response_length:.0f} caractères en moyenne

Traits dominants: {', '.join(dominant_traits) if dominant_traits else 'Profil équilibré'}""",
        'en': f"""Personality profile based on {len(responses)} analyzed responses.
        
Average reflection time: {avg_response_time:.1f} seconds
Response depth: {avg_response_length:.0f} characters on average

Dominant traits: {', '.join(dominant_traits) if dominant_traits else 'Balanced profile'}""",
        'ar': f"""ملف الشخصية بناءً على {len(responses)} إجابة تم تحليلها.
        
متوسط وقت التفكير: {avg_response_time:.1f} ثانية
عمق الإجابات: {avg_response_length:.0f} حرف في المتوسط

السمات المهيمنة: {', '.join(dominant_traits) if dominant_traits else 'ملف متوازن'}"""
    }
    
    return {
        'summary': profile_texts.get(language, profile_texts['en']),
        'dominant_traits': dominant_traits,
        'response_style': {
            'avg_time': avg_response_time,
            'avg_length': avg_response_length,
            'consistency': analyze_consistency(user_data['psychological_profile'], language)
        }
    }

def generate_development_recommendations(results, language):
    """Generate personalized development recommendations"""
    recommendations = []
    
    # Analyze Big Five results for development areas
    if 'big_five' in results:
        for trait, data in results['big_five'].items():
            score = data.get('score', 0)
            if score < 10:  # Low score - development opportunity
                recommendations.append({
                    'area': trait,
                    'type': 'development',
                    'priority': 'high'
                })
            elif score > 20:  # High score - leverage strength
                recommendations.append({
                    'area': trait,
                    'type': 'leverage',
                    'priority': 'medium'
                })
    
    # Generate recommendation texts
    rec_texts = {
        'fr': {
            'ouverture_dev': "Développez votre ouverture en explorant de nouvelles expériences et idées.",
            'conscienciosité_dev': "Renforcez votre organisation et votre discipline personnelle.",
            'extraversion_dev': "Pratiquez la prise de parole et les interactions sociales.",
            'agréabilité_dev': "Travaillez sur l'empathie et la coopération avec les autres.",
            'stabilité émotionnelle_dev': "Développez des techniques de gestion du stress et des émotions.",
            'ouverture_lev': "Utilisez votre créativité pour innover dans vos projets.",
            'conscienciosité_lev': "Votre rigueur est un atout - partagez vos méthodes avec l'équipe.",
            'extraversion_lev': "Votre leadership naturel peut inspirer et motiver les autres.",
            'agréabilité_lev': "Votre empathie fait de vous un excellent médiateur.",
            'stabilité émotionnelle_lev': "Votre calme sous pression est précieux en situations difficiles."
        },
        'en': {
            'ouverture_dev': "Develop your openness by exploring new experiences and ideas.",
            'conscienciosité_dev': "Strengthen your organization and personal discipline.",
            'extraversion_dev': "Practice public speaking and social interactions.",
            'agréabilité_dev': "Work on empathy and cooperation with others.",
            'stabilité émotionnelle_dev': "Develop stress and emotion management techniques.",
            'ouverture_lev': "Use your creativity to innovate in your projects.",
            'conscienciosité_lev': "Your rigor is an asset - share your methods with the team.",
            'extraversion_lev': "Your natural leadership can inspire and motivate others.",
            'agréabilité_lev': "Your empathy makes you an excellent mediator.",
            'stabilité émotionnelle_lev': "Your calm under pressure is valuable in difficult situations."
        },
        'ar': {
            'ouverture_dev': "طور انفتاحك من خلال استكشاف تجارب وأفكار جديدة.",
            'conscienciosité_dev': "عزز تنظيمك وانضباطك الشخصي.",
            'extraversion_dev': "مارس الخطابة والتفاعلات الاجتماعية.",
            'agréabilité_dev': "اعمل على التعاطف والتعاون مع الآخرين.",
            'stabilité émotionnelle_dev': "طور تقنيات إدارة التوتر والمشاعر.",
            'ouverture_lev': "استخدم إبداعك للابتكار في مشاريعك.",
            'conscienciosité_lev': "دقتك ميزة - شارك طرقك مع الفريق.",
            'extraversion_lev': "قيادتك الطبيعية يمكن أن تلهم وتحفز الآخرين.",
            'agréabilité_lev': "تعاطفك يجعلك وسيطاً ممتازاً.",
            'stabilité émotionnelle_lev': "هدوؤك تحت الضغط قيم في المواقف الصعبة."
        }
    }
    
    formatted_recommendations = []
    for rec in recommendations:
        trait = rec['area']
        rec_type = rec['type']
        key = f"{trait}_{rec_type}"
        text = rec_texts.get(language, rec_texts['en']).get(key, "")
        if text:
            formatted_recommendations.append({
                'area': trait,
                'type': rec_type,
                'priority': rec['priority'],
                'description': text
            })
    
    return formatted_recommendations

def generate_summary(user_data, language):
    """Generate summary of assessment completion"""
    total_time = time.time() - user_data['start_time']
    total_responses = len(user_data['responses'])
    
    summary = {
        'total_time': f"{total_time/60:.1f} minutes",
        'total_responses': total_responses,
        'completion_rate': "100%"
    }
    
    return summary
