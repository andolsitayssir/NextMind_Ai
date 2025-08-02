from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import random
import time
from datetime import datetime
from .utils import (
    generate_question, 
    analyze_answer,
    get_trait_intro,
    ASSESSMENT_STRUCTURE,
    generate_detailed_analysis,
    should_recommend_coaching,
    get_behavioral_questions  # Import our behavioral questions function
)

# Assessment configuration - 3 questions per trait/dimension
ASSESSMENTS = {
    'big_five': {
        'traits': ['ouverture', 'conscienciosité', 'extraversion', 'agréabilité', 'stabilité émotionnelle'],
        'questions_per_trait': 3,
        'order': 1
    },
    'disc': {
        'traits': ['dominant', 'influent', 'stable', 'conforme'],
        'questions_per_trait': 3,
        'order': 2
    },
    'bien_etre': {
        'questions_total': 3,
        'order': 3
    },
    'resilience_ie': {
        'questions_total': 3,
        'order': 4
    }
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
        
        if not answer_text:
            return JsonResponse({'error': 'Answer required'}, status=400)
        
        # Enhanced behavioral analysis
        current_assessment = user_data['current_assessment']
        current_trait = user_data.get('current_trait', 'general')
        
        # Get previous responses for context
        previous_responses = [r for r in user_data['responses'] 
                            if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
        
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
            # Fallback scoring based on answer quality indicators
            score = calculate_fallback_score(answer_text)
        
        # Analyze behavioral patterns
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
            'answer_length': len(answer_text)
        }
        
        user_data['responses'].append(response_data)
        
        # Update psychological profile
        user_data['psychological_profile']['response_times'].append(response_time)
        user_data['psychological_profile']['answer_lengths'].append(len(answer_text))
        user_data['psychological_profile']['emotional_patterns'].append(emotional_tone)
        
        # Determine next step
        try:
            next_step = get_next_step(user_data)
            
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
            # Fallback: progress naturally
            if user_data['current_question_number'] < 3:
                user_data['current_question_number'] += 1
            else:
                user_data['is_completed'] = True
            
            request.session['user_data'] = user_data
            request.session.modified = True
            
            if user_data['is_completed']:
                return JsonResponse({'completed': True, 'redirect': '/report/'})
            else:
                return JsonResponse({'success': True})
    
    # Generate next question using optimized system
    current_assessment = user_data['current_assessment']
    current_trait = user_data.get('current_trait', 'general')
    question_number = user_data['current_question_number']
    
    # Get previous responses for context
    previous_responses = [r for r in user_data['responses'] 
                        if r.get('trait') == current_trait and r.get('assessment') == current_assessment]
    
    # Generate behavioral question using optimized function
    try:
        question_text = generate_question(
            trait=current_trait,
            question_number=question_number,
            previous_answers=[r['text'] for r in previous_responses],
            language=user_data['language'],
            assessment_type=current_assessment
        )
    except Exception as e:
        # Use behavioral fallback instead of story questions
        question_text = get_behavioral_questions(
            trait=current_trait,
            question_number=question_number,
            previous_answers=[r['text'] for r in previous_responses],
            language=user_data['language'],
            assessment_type=current_assessment
        )
    
    # Store question start time for response time tracking
    user_data['question_start_time'] = time.time()
    request.session['user_data'] = user_data
    
    # Calculate progress
    total_questions = calculate_total_questions()
    completed_questions = len(user_data['responses'])
    progress_percentage = (completed_questions / total_questions) * 100
    
    # Get trait introduction
    try:
        trait_intro = get_trait_intro(current_trait, user_data['language'], current_assessment)
    except:
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
        'trait_progress': f"{question_number}/{ASSESSMENTS[current_assessment].get('questions_per_trait', 3)}",
        'assessment_name': get_assessment_name(current_assessment, user_data['language'])
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
            if current_question >= 3:  # 3 questions per trait
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
            if current_question >= 3:  # 3 questions per style
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
            if current_question >= 3:
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
            if current_question >= 3:
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
        # If anything goes wrong, just mark as completed
        result.update({'completed': True})
    
    return result

def calculate_total_questions():
    """Calculate total number of questions across all assessments"""
    total = 0
    total += len(ASSESSMENTS['big_five']['traits']) * 3  # 5 traits × 3 questions
    total += len(ASSESSMENTS['disc']['traits']) * 3      # 4 styles × 3 questions  
    total += 3  # bien_etre
    total += 3  # resilience_ie
    return total  # Total: 23 questions

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

def report(request):
    if 'user_data' not in request.session or not request.session['user_data'].get('is_completed'):
        return redirect('choose_language')
    
    user_data = request.session['user_data']
    language = user_data['language']
    
    # Generate comprehensive results
    results = generate_results(user_data)
    
    # Generate coaching recommendations
    try:
        coaching_recommendation = should_recommend_coaching(results, language)
    except:
        coaching_recommendation = {
            'should_recommend': False,
            'message': 'Analyse terminée avec succès.',
            'priority': 'normal'
        }
    
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

def generate_results(user_data):
    """Generate results for all assessments"""
    results = {}
    responses = user_data['responses']
    
    # Big Five results
    big_five_results = {}
    for trait in ASSESSMENTS['big_five']['traits']:
        trait_responses = [r for r in responses if r['trait'] == trait and r['assessment'] == 'big_five']
        if trait_responses:
            scores = [r['score'] for r in trait_responses]
            avg_score = sum(scores) / len(scores)
            total_score = avg_score * 5  # Scale to 25
            
            big_five_results[trait] = {
                'score': round(total_score, 1),
                'level': get_level_from_score(total_score, 'big_five'),
                'responses': trait_responses
            }
    
    results['big_five'] = big_five_results
    
    # DISC results
    disc_results = {}
    for style in ASSESSMENTS['disc']['traits']:
        style_responses = [r for r in responses if r['trait'] == style and r['assessment'] == 'disc']
        if style_responses:
            scores = [r['score'] for r in style_responses]
            avg_score = sum(scores) / len(scores)
            
            disc_results[style] = {
                'score': round(avg_score, 1),
                'preference_strength': 'high' if avg_score >= 4 else 'medium' if avg_score >= 3 else 'low',
                'responses': style_responses
            }
    
    results['disc'] = disc_results
    
    # Well-being results
    wellbeing_responses = [r for r in responses if r['assessment'] == 'bien_etre']
    if wellbeing_responses:
        scores = [r['score'] for r in wellbeing_responses]
        total_score = sum(scores) * 2  # Scale to 30
        
        results['bien_etre'] = {
            'score': total_score,
            'level': get_level_from_score(total_score, 'bien_etre'),
            'responses': wellbeing_responses
        }
    
    # Resilience results
    resilience_responses = [r for r in responses if r['assessment'] == 'resilience_ie']
    if resilience_responses:
        scores = [r['score'] for r in resilience_responses]
        total_score = sum(scores) * 2.67  # Scale to 40
        
        results['resilience_ie'] = {
            'score': round(total_score, 1),
            'level': get_level_from_score(total_score, 'resilience_ie'),
            'responses': resilience_responses
        }
    
    return results

def get_level_from_score(score, assessment_type):
    """Determine level based on score"""
    if assessment_type == "big_five":
        if score <= 11:
            return "faible"
        elif score <= 18:
            return "modéré"
        else:
            return "élevé"
    elif assessment_type == "bien_etre":
        if score <= 14:
            return "faible"
        elif score <= 22:
            return "modéré"
        else:
            return "élevé"
    elif assessment_type == "resilience_ie":
        if score <= 19:
            return "faible"
        elif score <= 29:
            return "modéré"
        else:
            return "élevé"
    else:
        return "modéré"

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