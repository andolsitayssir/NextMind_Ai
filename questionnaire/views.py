# Clean views.py - keep only HTTP handling logic
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import time
from datetime import datetime
from .utils import (
    analyze_answer,
    analyze_behavioral_tone,
    analyze_response_quality,
    generate_question,
    get_next_step,
    calculate_total_questions,
    get_assessment_name,
    get_trait_intro,
    generate_detailed_results,
    generate_insights,
    generate_summary,
    should_recommend_coaching,
    
)
import logging

# Configure minimal logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Assessment configuration - synchronized with utils.py
ASSESSMENTS = {
    'big_five': {
        'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
        'questions_per_trait': 2,
        'order': 1
    },
    'disc': {
        'traits': ['dominant', 'influent', 'stable', 'conforme'],
        'questions_per_trait': 2,
        'order': 2
    },
    'bien_etre': {
        'questions_total': 2,
        'order': 3
    },
    'resilience_ie': {
        'questions_total': 2,
        'order': 4
    }
}

def choose_language(request):
    """Handle language selection and session initialization"""
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
    """Handle quiz flow and question generation"""
    # Check if session exists
    if 'user_data' not in request.session:
        return redirect('choose_language')
    
    user_data = request.session['user_data']
    
    if user_data['is_completed']:
        return redirect('report')
    
    if request.method == "POST":
        # Process answer submission
        answer_text = request.POST.get('answer', '').strip()
        response_time = time.time() - user_data.get('question_start_time', time.time())
        
        if not answer_text:
            return JsonResponse({'error': 'Answer required'}, status=400)
        
        # Get assessment context
        current_assessment = user_data['current_assessment']
        current_trait = user_data.get('current_trait', 'general')
        
        # Get previous responses for context
        previous_responses = [r for r in user_data['responses'] 
                            if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
        
        # Score the answer using utility functions
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
            score = calculate_enhanced_fallback_score(answer_text, current_trait, current_assessment, response_time)
        
        # Analyze behavioral patterns using utility functions
        emotional_tone = analyze_behavioral_tone(answer_text, response_time)
        engagement_level = analyze_response_quality(answer_text, response_time)
        
        # Store response data
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
            'answer_length': len(answer_text)
        }
        
        user_data['responses'].append(response_data)
        
        # Update psychological profile
        user_data['psychological_profile']['response_times'].append(response_time)
        user_data['psychological_profile']['answer_lengths'].append(len(answer_text))
        user_data['psychological_profile']['emotional_patterns'].append(emotional_tone)
        
        # Determine next step using utility function
        try:
            next_step = get_next_step(user_data)
            
            if next_step.get('completed', False):
                user_data['is_completed'] = True
                request.session['user_data'] = user_data
                return JsonResponse({'completed': True, 'redirect': '/report/'})
            else:
                user_data.update(next_step)
                request.session['user_data'] = user_data
                request.session.modified = True
                return JsonResponse({'success': True})
                
        except Exception as e:
            logger.error(f"Error determining next step: {e}")
            # Fallback: mark as completed
            user_data['is_completed'] = True
            request.session['user_data'] = user_data
            request.session.modified = True
            return JsonResponse({'completed': True, 'redirect': '/report/'})
    
    # Generate next question
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait', 'general')
    question_number = user_data['current_question_number']
    
    # Get context for question generation
    previous_responses = [r for r in user_data['responses'] 
                        if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
    
    previous_score = None
    if previous_responses:
        previous_score = previous_responses[-1].get('score')
    
    # Generate question using utility functions
    try:
        question_text = generate_question(
            trait=current_trait,
            question_number=question_number,
            previous_answers=[r['text'] for r in previous_responses],
            previous_score=previous_score,
            language=user_data['language'],
            assessment_type=current_assessment
        )
        
        if not question_text:
            raise Exception("API returned no question")
            
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        question_text = get_behavioral_questions(
            trait=current_trait,
            question_number=question_number,
            previous_answers=[r['text'] for r in previous_responses],
            previous_score=previous_score,
            language=user_data['language'],
            assessment_type=current_assessment
        )
    
    # Store question start time
    user_data['question_start_time'] = time.time()
    request.session['user_data'] = user_data
    request.session.modified = True
    
    # Calculate progress
    total_questions = calculate_total_questions()
    completed_questions = len(user_data['responses'])
    progress_percentage = (completed_questions / total_questions) * 100
    
    # Get trait introduction
    try:
        trait_intro = get_trait_intro(current_trait, user_data['language'], current_assessment)
    except Exception as e:
        logger.error(f"Error getting trait intro: {e}")
        trait_intro = ""
    
    # Prepare context for template
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
        'trait_progress': f"{question_number}/{ASSESSMENTS[current_assessment].get('questions_per_trait', 2)}",
        'assessment_name': get_assessment_name(current_assessment, user_data['language'])
    }
    
    return render(request, 'quiz.html', context)

def report(request):
    """Handle report generation and display"""
    if 'user_data' not in request.session or not request.session['user_data'].get('is_completed'):
        return redirect('choose_language')
    
    user_data = request.session['user_data']
    language = user_data['language']
    
    # Generate comprehensive results using utility functions
    results = generate_detailed_results(user_data)
    
    # Generate coaching recommendations using utility functions
    try:
        coaching_recommendation = should_recommend_coaching(results, language)
    except Exception as e:
        logger.error(f"Error generating coaching recommendation: {e}")
        coaching_recommendation = {
            'should_recommend': False,
            'message': 'Analyse terminée avec succès.',
            'priority': 'normal',
            'reasons': []
        }
    
    # Prepare context for template
    context = {
        'session': {
            'language': language,
            'is_completed': True,
        },
        'results': results,
        'coaching_recommendation': coaching_recommendation,
        'psychological_insights': generate_insights(user_data, language),
        'assessment_summary': generate_summary(user_data, language)
    }
    
    return render(request, 'report.html', context)