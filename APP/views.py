from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import datetime
import time
import logging

# Import new adaptive system
from .adaptive_question_generator import AdaptiveQuestionGenerator
from .nlp_scorer import NLPScorer
from .ai_report_generator import AIReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# ASSESSMENT CONFIGURATION - Updated for 2 questions per trait
# ============================================================================

ASSESSMENTS = {
    'big_five': {
        'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
        'questions_per_trait': 2,  # EXACTLY 2
        'max_score_per_trait': 10,  # 2 × 5
        'order': 1
    },
    'disc': {
        'traits': ['dominant', 'influent', 'stable', 'conforme'],
        'questions_per_trait': 2,  # EXACTLY 2
        'scoring_method': 'count_based',
        'order': 2
    },
    'bien_etre': {
        'trait': 'general',  # Single trait
        'questions_total': 2,  # 2 questions
        'max_score': 10,  # 2 × 5
        'order': 3
    },
    'resilience_ie': {
        'trait': 'general',  # Single trait
        'questions_total': 2,  # 2 questions
        'max_score': 10,  # 2 × 5
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
    'general': {'fr': 'Général', 'en': 'General', 'ar': 'عام'},
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
        'current_question': None,
        'assessment_progress': {
            'big_five': {'completed_traits': [], 'current_trait_index': 0},
            'disc': {'completed_traits': [], 'current_trait_index': 0},
            'bien_etre': {'questions_completed': 0},
            'resilience_ie': {'questions_completed': 0}
        }
    }
    request.session.modified = True
    
    return redirect('quiz')

def quiz(request):
    """Main quiz view with 3-step adaptive workflow"""
    lang = request.session.get('language', 'fr')
    
    if 'user_data' not in request.session:
        return redirect('start_quiz')
    
    user_data = request.session['user_data']
    
    if user_data.get('is_completed'):
        return redirect('report')
    
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait', 'general')
    question_number = user_data['current_question_number']
    
    if request.method == "POST":
        # User submitted answer
        answer_text = request.POST.get('answer', '').strip()
        
        # Basic validation
        if not answer_text or len(answer_text) < 3:
            return JsonResponse({
                'error': 'Veuillez fournir une réponse (minimum 3 caractères).',
                'validation_failed': True
            }, status=400)
        
        # STEP 2: Score answer with NLP + LLM
        try:
            scorer = NLPScorer()
            score_result = scorer.score_answer(
                question=user_data['current_question'],
                answer=answer_text,
                trait=current_trait,
                assessment_type=current_assessment,
                language=user_data['language']
            )
            
            logger.info(f"Scored Q{question_number} for {current_trait}: {score_result['score']}/5")
            
        except Exception as e:
            logger.error(f"Scoring error: {e}")
            return JsonResponse({
                'error': 'Erreur lors de l\'analyse de votre réponse. Veuillez réessayer.',
                'validation_failed': True
            }, status=500)
        
        # Store response
        user_data['responses'].append({
            'assessment': current_assessment,
            'trait': current_trait,
            'question_number': question_number,
            'question': user_data['current_question'],
            'answer': answer_text,
            'score': score_result['score'],
            'reasoning': score_result.get('reasoning', ''),
            'timestamp': datetime.now().isoformat()
        })
        
        # Determine next step
        if question_number == 1:
            # Just answered Q1, move to Q2
            user_data['current_question_number'] = 2
            request.session['user_data'] = user_data
            request.session.modified = True
            return JsonResponse({'success': True})
        else:
            # Just answered Q2, move to next trait
            logger.info(f"📊 Before next_step: {current_assessment}/{current_trait}, progress_index={user_data['assessment_progress'].get(current_assessment, {}).get('current_trait_index', 'N/A')}")
            next_step = get_next_step(user_data)
            logger.info(f"📊 After next_step: {next_step}")
            user_data.update(next_step)
            request.session['user_data'] = user_data
            request.session.modified = True
            
            if next_step.get('completed'):
                user_data['is_completed'] = True
                request.session['user_data'] = user_data
                request.session.modified = True
                return JsonResponse({'completed': True, 'redirect': '/report/'})
            return JsonResponse({'success': True})
    
    # GET request - STEP 1: Generate question
    try:
        generator = AdaptiveQuestionGenerator()
        
        if question_number == 1:
            # Generate first question (broad, exploratory)
            question = generator.generate_first_question(
                trait=current_trait,
                assessment_type=current_assessment,
                language=user_data['language']
            )
            logger.info(f"Generated Q1 for {current_trait}")
            
        else:
            # Generate adaptive second question based on Q1
            q1_response = [r for r in user_data['responses'] 
                          if r['trait'] == current_trait and r['assessment'] == current_assessment and r['question_number'] == 1][0]
            
            # Analyze Q1 answer for adaptation
            nlp_analysis = NLPScorer().analyze_answer_semantics(
                q1_response['answer'],
                user_data['language']
            )
            
            question = generator.generate_adaptive_second_question(
                trait=current_trait,
                assessment_type=current_assessment,
                q1_answer=q1_response['answer'],
                q1_score=q1_response['score'],
                language=user_data['language'],
                nlp_analysis=nlp_analysis
            )
            logger.info(f"Generated adaptive Q2 for {current_trait} (Q1 score: {q1_response['score']})")
            
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        question = "Décrivez votre expérience dans ce domaine."
    
    user_data['current_question'] = question
    request.session['user_data'] = user_data
    request.session.modified = True
    
    # Calculate progress
    total_questions = calculate_total_questions()
    completed_questions = len(user_data['responses'])
    progress_percentage = (completed_questions / total_questions) * 100
    
    context = {
        'session': {
            'language': user_data['language'],
            'current_assessment': current_assessment,
            'current_trait': current_trait,
            'current_question_number': question_number,
        },
        'question': question,
        'progress': int(progress_percentage),
        'current_assessment': current_assessment,
        'current_trait_display': get_localized_trait_name(current_trait, user_data['language']),
        'trait_progress': f"{question_number}/2",
        'assessment_name': get_assessment_name(current_assessment, user_data['language']),
    }
    
    return render(request, 'quiz.html', context)

def get_next_step(user_data):
    """Determine next step in assessment"""
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait')
    
    result = {'completed': False}
    
    if current_assessment == 'big_five':
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
            # Transition to DISC - RESET disc progress
            user_data['assessment_progress']['disc'] = {
                'completed_traits': [],
                'current_trait_index': 0
            }
            result.update({
                'current_assessment': 'disc',
                'current_trait': ASSESSMENTS['disc']['traits'][0],
                'current_question_number': 1
            })
    
    elif current_assessment == 'disc':
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
            # Transition to bien_etre - RESET progress
            user_data['assessment_progress']['bien_etre'] = {
                'questions_completed': 0
            }
            result.update({
                'current_assessment': 'bien_etre',
                'current_trait': 'general',
                'current_question_number': 1
            })
    
    elif current_assessment == 'bien_etre':
        progress = user_data['assessment_progress']['bien_etre']
        progress['questions_completed'] += 1
        
        if progress['questions_completed'] < ASSESSMENTS['bien_etre']['questions_total']:
            result.update({
                'current_assessment': 'bien_etre',
                'current_trait': 'general',
                'current_question_number': progress['questions_completed'] + 1
            })
        else:
            # Transition to resilience_ie - RESET progress
            user_data['assessment_progress']['resilience_ie'] = {
                'questions_completed': 0
            }
            result.update({
                'current_assessment': 'resilience_ie',
                'current_trait': 'general',
                'current_question_number': 1
            })
    
    elif current_assessment == 'resilience_ie':
        progress = user_data['assessment_progress']['resilience_ie']
        progress['questions_completed'] += 1
        
        if progress['questions_completed'] < ASSESSMENTS['resilience_ie']['questions_total']:
            result.update({
                'current_assessment': 'resilience_ie',
                'current_trait': 'general',
                'current_question_number': progress['questions_completed'] + 1
            })
        else:
            # All assessments completed!
            result.update({'completed': True})
    
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
    """Generate and display report with AI insights"""
    if 'user_data' not in request.session or not request.session['user_data'].get('is_completed'):
        return redirect('home')
    
    user_data = request.session['user_data']
    language = user_data['language']
    
    # Check for manual retry
    if request.GET.get('retry') == 'true':
        if 'report_results' in user_data:
            del user_data['report_results']
            request.session.modified = True
    
    # Check if results are already generated and COMPLETE
    force_regenerate = False
    results = user_data.get('report_results')
    
    if results:
        # Check if new assessments are present in cached results
        # Also check for previous errors to allow retry
        if 'error' in results or 'bien_etre' not in results or 'resilience_ie' not in results:
            force_regenerate = True
            logger.info("Cached results incomplete or error, forcing regeneration")
    else:
        force_regenerate = True
    
    if force_regenerate:
        # STEP 3: Generate AI-powered report
        try:
            # Validate user data before generation
            if 'responses' not in user_data or not user_data['responses']:
                 logger.error("No responses in user_data during report generation")
                 results = {'error': "No responses found. Session may have been lost."}
            else:
                results = generate_ai_results(user_data)
            
                # Save results to session if at least Big Five is present
                # We allow partial results to avoid showing nothing if one API call fails
                if results and 'big_five' in results and results['big_five']:
                    user_data['report_results'] = results
                    request.session['user_data'] = user_data
                    request.session.modified = True
                    logger.info("Saved report results (potentially partial)")
                else:
                    logger.warning("Generated results invalid (missing Big Five), not caching.")
                
        except Exception as e:
            logger.error(f"Critical error in report generation: {e}")
            # Fallback to prevent crash
            results = {'error': str(e)}

    # Ensure results is not just empty dicts
    if results and not results.get('error'):
        has_data = any(results.get(k) for k in ['big_five', 'disc', 'bien_etre', 'resilience_ie'])
        if not has_data:
            logger.warning("Results dict exists but contains no data")
            results = {'error': "Data generation failed. Please retry."}

    context = {
        'session': {'language': language, 'is_completed': True},
        'results': results,
        'results': results,
    }
    
    return render(request, 'report.html', context)

def generate_ai_results(user_data):
    """Generate results using AI Report Generator with Parallel Execution"""
    from concurrent.futures import ThreadPoolExecutor
    
    results = {}
    responses = user_data['responses']
    language = user_data['language']
    generator = AIReportGenerator()
    
    # Prepare Data for Batch Processing
    
    # 1. Big Five Data (normalize to {q1, q2})
    big_five_data = {}
    for trait in ASSESSMENTS['big_five']['traits']:
        qs = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if qs:
            # Ensure ordering by question_number and pick first two
            qs_sorted = sorted(qs, key=lambda x: x.get('question_number', 1))[:2]
            if len(qs_sorted) >= 2:
                big_five_data[trait] = {'q1': qs_sorted[0], 'q2': qs_sorted[1]}
            
    # 2. DISC Data (normalize to {q1, q2})
    disc_data = {}
    for trait in ASSESSMENTS['disc']['traits']:
         qs = [r for r in responses if r['trait'] == trait and r['assessment'] == 'disc']
         if qs:
            qs_sorted = sorted(qs, key=lambda x: x.get('question_number', 1))[:2]
            if len(qs_sorted) >= 2:
                disc_data[trait] = {'q1': qs_sorted[0], 'q2': qs_sorted[1]}
            
    # 3. Bien-être Data (support >=2 answers, pick first two by question_number)
    bien_etre_data = {}
    qs_be = [r for r in responses if r['assessment'] == 'bien_etre']
    if qs_be:
        qs_be_sorted = sorted(qs_be, key=lambda x: x.get('question_number', 1))[:2]
        if len(qs_be_sorted) >= 2:
            bien_etre_data['general'] = {'q1': qs_be_sorted[0], 'q2': qs_be_sorted[1]}
        
    # 4. Resilience Data (support >=2 answers, pick first two by question_number)
    resilience_data = {}
    qs_res = [r for r in responses if r['assessment'] == 'resilience_ie']
    if qs_res:
        qs_res_sorted = sorted(qs_res, key=lambda x: x.get('question_number', 1))[:2]
        if len(qs_res_sorted) >= 2:
            resilience_data['general'] = {'q1': qs_res_sorted[0], 'q2': qs_res_sorted[1]}
        
    # Execute in Parallel
    # Using 4 threads for the 4 assessment types
    with ThreadPoolExecutor(max_workers=4) as executor:
        logger.info("Starting parallel report generation...")
        future_bf = executor.submit(generator.generate_assessment_report, 'big_five', big_five_data, language)
        future_disc = executor.submit(generator.generate_assessment_report, 'disc', disc_data, language)
        future_be = executor.submit(generator.generate_assessment_report, 'bien_etre', bien_etre_data, language)
        future_res = executor.submit(generator.generate_assessment_report, 'resilience_ie', resilience_data, language)
        
        # Gather Results
        # Note: generate_assessment_report handles its own fallbacks, so .result() should return dicts
        try:
            results['big_five'] = future_bf.result()
            logger.info("Big Five generated")
            
            results['disc'] = future_disc.result()
            logger.info("DISC generated")
            
            be_res = future_be.result()
            if 'general' in be_res:
                results['bien_etre'] = be_res['general']
                logger.info("Bien-être generated")
            
            res_res = future_res.result()
            if 'general' in res_res:
                results['resilience_ie'] = res_res['general']
                logger.info("Resilience generated")
                
        except Exception as e:
            logger.error(f"Error in parallel execution results: {e}")
            # Consider implementing global fallback here if threads die catastrophically
            
    # Adapt results to template-expected structure
    results = _adapt_results_for_template(results)
    return results

def _adapt_results_for_template(results):
    """Adapt generator output to the structure used in report.html."""
    if not results:
        return results

    adapted = {}

    # Big Five: map each trait to {score, detailed_analysis}
    bf = results.get('big_five') or {}
    if bf:
        adapted_bf = {}
        for trait, data in bf.items():
            if not isinstance(data, dict):
                continue
            score10 = data.get('scaled_score') or data.get('score') or data.get('mean_score', 0) * 2
            strengths = data.get('strengths') or []
            dev = data.get('development_areas') or []
            summary = data.get('summary') or data.get('standard_interpretation', '')
            adapted_bf[trait] = {
                'score': round(score10 or 0, 1),
                'detailed_analysis': {
                    'observations': summary,
                    'points_forts': strengths,
                    'zones_developpement': dev,
                }
            }
        if adapted_bf:
            adapted['big_five'] = adapted_bf

    # DISC: template expects score out of 5
    disc = results.get('disc') or {}
    if disc:
        adapted_disc = {}
        for trait, data in disc.items():
            if not isinstance(data, dict):
                continue
            score5 = data.get('mean_score') or (data.get('scaled_score', 0) / 2 if data.get('scaled_score') is not None else 0)
            strengths = data.get('strengths') or []
            dev = data.get('development_areas') or []
            summary = data.get('summary') or data.get('standard_interpretation', '')
            adapted_disc[trait] = {
                'score': round(score5 or 0, 1),
                'detailed_analysis': {
                    'observations': summary,
                    'points_forts': strengths,
                    'zones_developpement': dev,
                }
            }
        if adapted_disc:
            adapted['disc'] = adapted_disc

    # Bien-être & Resilience: each is a single object in template with {score, detailed_analysis}
    for key in ('bien_etre', 'resilience_ie'):
        data = results.get(key)
        if not data:
            continue
        # When parallel returns, we extracted the 'general' entry into results[key]; keep mapping
        score10 = data.get('scaled_score') or data.get('score') or data.get('mean_score', 0) * 2
        strengths = data.get('strengths') or []
        dev = data.get('development_areas') or []
        summary = data.get('summary') or data.get('standard_interpretation', '')
        adapted[key] = {
            'score': round(score10 or 0, 1),
            'detailed_analysis': {
                'observations': summary,
                'points_forts': strengths,
                'zones_developpement': dev,
            }
        }

    # Preserve error if any
    if results.get('error'):
        adapted['error'] = results['error']

    return adapted

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

def reset_assessment(request):
    """Reset assessment"""
    language = request.session.get('language', 'fr')
    request.session.clear()
    request.session['language'] = language
    request.session.modified = True
    return redirect('home')