from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import time
import logging
import re

from .quiz import (
    generate_question, 
    analyze_answer,
    get_trait_intro,
    ASSESSMENT_STRUCTURE,
    generate_enhanced_detailed_analysis,
    generate_score_explanations,
    should_recommend_coaching,
    TRAITS_CONFIG,
    DISC_CONFIG
)
import random
from .fallback_content import (  # ADD THIS
    FALLBACK_QUESTIONS,
    fallback_score_answer,
    fallback_generate_analysis,
    fallback_score_explanation
)
# Configure minimal logging
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

VALIDATION_PATTERNS = {
    'meaningless_patterns': [
        r'^[a-z]{1,3}$',
        r'^[0-9]+$',
        r'^[!@#$%^&*(),.?":{}|<>]+$',
        r'^(.)\1{4,}$',
        r'^(test|test123|testing|lorem|ipsum)$',
        r'^(qwerty|asdf|hjkl|zxcv)$',
    ],
}

BEHAVIORAL_KEYWORDS = {
    'fr': {
        'relevant_words': [
            'je', 'moi', 'mon', 'ma', 'mes', 'suis', 'fais', 'pense', 'crois', 'ressens',
            'décide', 'choisis', 'préfère', 'aime', 'situation', 'expérience', 'comportement',
            'équipe', 'travail', 'projet', 'stress', 'émotion', 'sentiment'
        ],
    },
    'en': {
        'relevant_words': [
            'i', 'me', 'my', 'am', 'do', 'think', 'believe', 'feel',
            'decide', 'choose', 'prefer', 'like', 'situation', 'experience', 'behavior',
            'team', 'work', 'project', 'stress', 'emotion', 'feeling'
        ],
    },
    'ar': {
        'relevant_words': [
            'أنا', 'لي', 'عندي', 'أكون', 'أفعل', 'أعتقد', 'أشعر',
            'أقرر', 'أختار', 'أفضل', 'موقف', 'تجربة', 'سلوك',
            'فريق', 'عمل', 'مشروع', 'ضغط', 'عاطفة', 'شعور'
        ],
    }
}

# ============================================================================
# SIMPLIFIED VALIDATION - For DEMO
# ============================================================================

def validate_answer(answer_text, language, current_trait=None, current_assessment=None):
    """Simplified validation for DEMO - just check basic requirements"""
    if not answer_text or not answer_text.strip():
        return False, get_validation_error('empty', language)
    
    answer_clean = answer_text.strip()
    
    # Minimum length check (very permissive for demo)
    if len(answer_clean) < 3:
        return False, get_validation_error('too_short', language)
    
    # Maximum length check
    if len(answer_text) > 2000:
        return False, get_validation_error('too_long', language)
    
    # That's it! Accept almost everything for demo
    return True, None


def get_validation_error(error_type, language):
    """Get localized validation error messages"""
    errors = {
        'empty': {
            'fr': 'Veuillez fournir une réponse à cette question.',
            'en': 'Please provide an answer to this question.',
            'ar': 'يرجى تقديم إجابة على هذا السؤال.'
        },
        'too_short': {
            'fr': 'Votre réponse est trop courte. Minimum 3 caractères.',
            'en': 'Your answer is too short. Minimum 3 characters.',
            'ar': 'إجابتك قصيرة جداً. 3 أحرف على الأقل.'
        },
        'too_long': {
            'fr': 'Votre réponse est trop longue. Maximum 2000 caractères.',
            'en': 'Your answer is too long. Maximum 2000 characters.',
            'ar': 'إجابتك طويلة جداً. 2000 حرف كحد أقصى.'
        }
    }
    
    return errors.get(error_type, {}).get(language, errors.get(error_type, {}).get('fr', 'Réponse invalide'))

# ============================================================================
# ASSESSMENT CONFIGURATION
# ============================================================================

ASSESSMENTS = {
    'big_five': {
        'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
        'questions_per_trait': 1,
        'order': 1
    },
    'disc': {
        'traits': ['dominant', 'influent', 'stable', 'conforme'],
        'questions_per_trait': 1,
        'order': 2
    },
    'bien_etre': {
        'questions_total': 1,
        'order': 3
    },
    'resilience_ie': {
        'questions_total': 1,
        'order': 4
    }
}

TRAIT_DISPLAY_NAMES = {
    'ouverture': {'fr': 'Ouverture', 'en': 'Openness', 'ar': 'الانفتاح'},
    'conscienciosité': {'fr': 'Conscienciosité', 'en': 'Conscientiousness', 'ar': 'الضمير'},
    'extraversion': {'fr': 'Extraversion', 'en': 'Extraversion', 'ar': 'الانبساط'},
    'agréabilité': {'fr': 'Agréabilité', 'en': 'Agreeableness', 'ar': 'الوداعة'},
    'stabilité émotionnelle': {'fr': 'Stabilité émotionnelle', 'en': 'Emotional Stability', 'ar': 'الاستقرار العاطفي'},
    'dominant': {'fr': 'Dominant', 'en': 'Dominant', 'ar': 'مهيمن'},
    'influent': {'fr': 'Influent', 'en': 'Influent', 'ar': 'مؤثر'},
    'stable': {'fr': 'Stable', 'en': 'Stable', 'ar': 'مستقر'},
    'conforme': {'fr': 'Conforme', 'en': 'Compliant', 'ar': 'ملتزم'},
    'bien_etre': {'fr': 'Bien-être', 'en': 'Well-being', 'ar': 'الرفاهة'},
    'resilience_ie': {'fr': 'Résilience & IE', 'en': 'Resilience & EI', 'ar': 'المرونة والذكاء العاطفي'}
}

# ============================================================================
# VIEW FUNCTIONS
# ============================================================================

def home(request):
    """Home page"""
    if 'language' not in request.session:
        request.session['language'] = 'fr'
    return render(request, "home.html")

def go_home(request):
    """Redirect to home"""
    return redirect('home')

def set_language(request, lang):
    """Set session language"""
    lang = (lang or "fr").lower()
    if lang not in ("fr", "en", "ar"):
        lang = "fr"
    request.session['language'] = lang

    if 'user_data' in request.session:
        request.session['user_data']['language'] = lang
        request.session.modified = True

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)

def start_quiz(request):
    """Initialize quiz session"""
    lang = request.session.get('language', 'fr')
    
    request.session['user_data'] = {
        'language': lang,
        'start_time': time.time(),
        'current_assessment': 'big_five',
        'current_trait': ASSESSMENTS['big_five']['traits'][0],
        'current_question_number': 1,
        'is_completed': False,
        'responses': [],
        'assessment_progress': {
            'big_five': {'completed_traits': [], 'current_trait_index': 0},
            'disc': {'completed_traits': [], 'current_trait_index': 0},
            'bien_etre': {'questions_completed': 0},
            'resilience_ie': {'questions_completed': 0}
        },
        'results': {}
    }
    request.session.modified = True
    
    return redirect('quiz')

def quiz(request):
    """Main quiz view - DEMO VERSION with fallback scoring"""
    lang = request.session.get('language', 'fr')
    
    if 'user_data' not in request.session:
        return redirect('start_quiz')
    
    user_data = request.session['user_data']
    
    if user_data.get('is_completed'):
        return redirect('report')
    
    if request.method == "POST":
        answer_text = request.POST.get('answer', '').strip()
        
        current_assessment = user_data['current_assessment']
        current_trait = user_data.get('current_trait', 'general')
        language = user_data['language']
        question_number = user_data['current_question_number']
        
        # Validate answer - SIMPLIFIED
        is_valid, error_message = validate_answer(answer_text, language, current_trait, current_assessment)
        
        if not is_valid:
            return JsonResponse({
                'error': error_message,
                'validation_failed': True
            }, status=400)
        
        # Score answer using RANDOM fallback scoring
        try:
            score = fallback_score_answer(
                answer_text=answer_text,
                trait=current_trait,
                assessment_type=current_assessment,
                language=language
            )
        except Exception as e:
            logger.error(f"Scoring error: {e}")
            # Emergency fallback - completely random
            if current_assessment == 'disc':
                score = random.uniform(2.0, 4.5)
            else:
                score = random.uniform(4.0, 8.0)
        
        # Store response
        response_data = {
            'assessment': current_assessment,
            'trait': current_trait,
            'question_number': question_number,
            'text': answer_text,
            'score': score,
            'timestamp': datetime.now().isoformat(),
            'answer_length': len(answer_text)
        }
        
        user_data['responses'].append(response_data)
        
        # Determine next step
        next_step = get_next_step(user_data)
        
        if next_step.get('completed', False):
            user_data['is_completed'] = True
            request.session['user_data'] = user_data
            request.session.modified = True
            return JsonResponse({
                'completed': True,
                'redirect': '/report/'
            })
        else:
            user_data.update(next_step)
            request.session['user_data'] = user_data
            request.session.modified = True
            return JsonResponse({'success': True})
    
    # GET request - generate question
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait', 'general')
    question_number = user_data['current_question_number']
    
    # Get question from fallback
    try:
        questions = FALLBACK_QUESTIONS.get(user_data['language'], FALLBACK_QUESTIONS['fr'])
        
        if current_assessment in ['bien_etre', 'resilience_ie']:
            q_list = questions.get(current_assessment, [])
        else:
            q_list = questions.get(current_assessment, {}).get(current_trait, [])
        
        if not q_list:
            question_text = "Décrivez votre expérience dans ce domaine."
        else:
            question_idx = (question_number - 1) % len(q_list)
            question_text = q_list[question_idx]
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        question_text = "Décrivez votre expérience dans ce domaine."
    
    user_data['question_start_time'] = time.time()
    request.session['user_data'] = user_data
    request.session.modified = True
    
    # Calculate progress
    total_questions = calculate_total_questions()
    completed_questions = len(user_data['responses'])
    progress_percentage = (completed_questions / total_questions) * 100
    
    trait_intro = get_trait_intro(current_trait, user_data['language'], current_assessment)
    
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
        'trait_progress': f"{question_number}/{ASSESSMENTS[current_assessment].get('questions_per_trait', ASSESSMENTS[current_assessment].get('questions_total', 3))}",
        'assessment_name': get_assessment_name(current_assessment, user_data['language']),
    }
    
    return render(request, 'quiz.html', context)

def generate_results(user_data):
    """Generate results using FALLBACK - DEMO VERSION"""
    results = {}
    responses = user_data['responses']
    language = user_data['language']
    
    # Big Five
    big_five_results = {}
    for trait in ASSESSMENTS['big_five']['traits']:
        trait_responses = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if trait_responses:
            scores = [r['score'] for r in trait_responses]
            total_score = sum(scores)
            avg_score = total_score / len(scores) if scores else 5.0
            
            big_five_results[trait] = {
                'score': round(avg_score, 1),
                'responses': trait_responses,
                'detailed_analysis': fallback_generate_analysis(
                    trait, avg_score, 'big_five', language
                )
            }
    
    results['big_five'] = big_five_results
    
    # DISC
    disc_results = {}
    for style in ASSESSMENTS['disc']['traits']:
        style_responses = [r for r in responses if r['trait'] == style and r['assessment'] == 'disc']
        if style_responses:
            scores = [r['score'] for r in style_responses]
            total_score = sum(scores)
            avg_score = total_score / len(scores) if scores else 2.5
            
            disc_results[style] = {
                'score': round(avg_score, 1),
                'responses': style_responses,
                'detailed_analysis': fallback_generate_analysis(
                    style, avg_score, 'disc', language
                )
            }
    
    results['disc'] = disc_results
    
    # Bien-être
    wellbeing_responses = [r for r in responses if r['assessment'] == 'bien_etre']
    if wellbeing_responses:
        scores = [r['score'] for r in wellbeing_responses]
        avg_score = sum(scores) / len(scores) if scores else 5.0
        
        results['bien_etre'] = {
            'score': round(avg_score, 1),
            'responses': wellbeing_responses,
            'detailed_analysis': fallback_generate_analysis(
                'bien_etre', avg_score, 'bien_etre', language
            )
        }
    
    # Resilience
    resilience_responses = [r for r in responses if r['assessment'] == 'resilience_ie']
    if resilience_responses:
        scores = [r['score'] for r in resilience_responses]
        avg_score = sum(scores) / len(scores) if scores else 5.0
        
        results['resilience_ie'] = {
            'score': round(avg_score, 1),
            'responses': resilience_responses,
            'detailed_analysis': fallback_generate_analysis(
                'resilience_ie', avg_score, 'resilience_ie', language
            )
        }
    
    return results

def get_next_step(user_data):
    """Determine next step in assessment"""
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait')
    current_question = user_data['current_question_number']
    
    result = {'completed': False}
    
    if current_assessment == 'big_five':
        if current_question >= ASSESSMENTS['big_five']['questions_per_trait']:
            progress = user_data['assessment_progress']['big_five']
            progress['completed_traits'].append(current_trait)
            progress['current_trait_index'] += 1
            
            if progress['current_trait_index'] < len(ASSESSMENTS['big_five']['traits']):
                next_trait = ASSESSMENTS['big_five']['traits'][progress['current_trait_index']]
                result.update({
                    'current_assessment': 'big_five',
                    'current_trait': next_trait,
                    'current_question_number': 1
                })
            else:
                result.update({
                    'current_assessment': 'disc',
                    'current_trait': ASSESSMENTS['disc']['traits'][0],
                    'current_question_number': 1
                })
        else:
            result.update({'current_question_number': current_question + 1})
    
    elif current_assessment == 'disc':
        if current_question >= ASSESSMENTS['disc']['questions_per_trait']:
            progress = user_data['assessment_progress']['disc']
            progress['completed_traits'].append(current_trait)
            progress['current_trait_index'] += 1
            
            if progress['current_trait_index'] < len(ASSESSMENTS['disc']['traits']):
                next_trait = ASSESSMENTS['disc']['traits'][progress['current_trait_index']]
                result.update({
                    'current_assessment': 'disc',
                    'current_trait': next_trait,
                    'current_question_number': 1
                })
            else:
                result.update({
                    'current_assessment': 'bien_etre',
                    'current_trait': 'bien_etre',
                    'current_question_number': 1
                })
        else:
            result.update({'current_question_number': current_question + 1})
    
    elif current_assessment == 'bien_etre':
        if current_question >= ASSESSMENTS['bien_etre']['questions_total']:
            result.update({
                'current_assessment': 'resilience_ie',
                'current_trait': 'resilience_ie',
                'current_question_number': 1
            })
        else:
            result.update({'current_question_number': current_question + 1})
    
    elif current_assessment == 'resilience_ie':
        if current_question >= ASSESSMENTS['resilience_ie']['questions_total']:
            result.update({'completed': True})
        else:
            result.update({'current_question_number': current_question + 1})
    
    return result

def calculate_total_questions():
    """Calculate total questions"""
    total = 0
    total += len(ASSESSMENTS['big_five']['traits']) * ASSESSMENTS['big_five']['questions_per_trait']
    total += len(ASSESSMENTS['disc']['traits']) * ASSESSMENTS['disc']['questions_per_trait']
    total += ASSESSMENTS['bien_etre']['questions_total']
    total += ASSESSMENTS['resilience_ie']['questions_total']
    return total

def report(request):
    """Generate and display report - FALLBACK ONLY"""
    if 'user_data' not in request.session or not request.session['user_data'].get('is_completed'):
        return redirect('home')
    
    user_data = request.session['user_data']
    language = user_data['language']
    
    results = generate_results(user_data)
    score_explanations = generate_score_explanations(results, language)
    
    context = {
        'session': {'language': language, 'is_completed': True},
        'results': results,
        'score_explanations': score_explanations,
    }
    
    return render(request, 'report.html', context)

def generate_results(user_data):
    """Generate results using FALLBACK"""
    results = {}
    responses = user_data['responses']
    language = user_data['language']
    
    # Big Five
    big_five_results = {}
    for trait in ASSESSMENTS['big_five']['traits']:
        trait_responses = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if trait_responses:
            scores = [r['score'] for r in trait_responses]
            total_score = sum(scores)
            
            big_five_results[trait] = {
                'score': round(total_score, 1),
                'responses': trait_responses,
                'detailed_analysis': generate_enhanced_detailed_analysis(
                    trait, [r['text'] for r in trait_responses], total_score, language, 'big_five'
                )
            }
    
    results['big_five'] = big_five_results
    
    # DISC
    disc_results = {}
    for style in ASSESSMENTS['disc']['traits']:
        style_responses = [r for r in responses if r['trait'] == style and r['assessment'] == 'disc']
        if style_responses:
            scores = [r['score'] for r in style_responses]
            total_score = sum(scores)
            
            disc_results[style] = {
                'score': round(total_score, 1),
                'responses': style_responses,
                'detailed_analysis': generate_enhanced_detailed_analysis(
                    style, [r['text'] for r in style_responses], total_score, language, 'disc'
                )
            }
    
    results['disc'] = disc_results
    
    # Bien-être
    wellbeing_responses = [r for r in responses if r['assessment'] == 'bien_etre']
    if wellbeing_responses:
        scores = [r['score'] for r in wellbeing_responses]
        total_score = sum(scores)
        
        results['bien_etre'] = {
            'score': round(total_score, 1),
            'responses': wellbeing_responses,
            'detailed_analysis': generate_enhanced_detailed_analysis(
                'bien_etre', [r['text'] for r in wellbeing_responses], total_score, language, 'bien_etre'
            )
        }
    
    # Resilience
    resilience_responses = [r for r in responses if r['assessment'] == 'resilience_ie']
    if resilience_responses:
        scores = [r['score'] for r in resilience_responses]
        total_score = sum(scores)
        
        results['resilience_ie'] = {
            'score': round(total_score, 1),
            'responses': resilience_responses,
            'detailed_analysis': generate_enhanced_detailed_analysis(
                'resilience_ie', [r['text'] for r in resilience_responses], total_score, language, 'resilience_ie'
            )
        }
    
    return results

def get_assessment_name(assessment_type, language):
    """Get localized assessment name"""
    names = {
        'big_five': {'fr': 'Big Five', 'en': 'Big Five', 'ar': 'العوامل الخمسة'},
        'disc': {'fr': 'DISC', 'en': 'DISC', 'ar': 'DISC'},
        'bien_etre': {'fr': 'Bien-être', 'en': 'Well-being', 'ar': 'الرفاهة'},
        'resilience_ie': {'fr': 'Résilience & IE', 'en': 'Resilience & EI', 'ar': 'المرونة والذكاء العاطفي'}
    }
    return names.get(assessment_type, {}).get(language, assessment_type)

def get_localized_trait_name(trait, language):
    """Get localized trait name"""
    return TRAIT_DISPLAY_NAMES.get(trait, {}).get(language, trait)