from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import UserSession, Question, Answer, AssessmentResult
from .utils import (
    generate_adaptive_question, 
    analyze_and_score_answer, 
    should_ask_followup_question,
    get_trait_intro,
    TRAITS_CONFIG,
    ASSESSMENT_STRUCTURE,
    generate_detailed_analysis,
    should_recommend_coaching,
    get_level_from_score
)
import json

# Assessment order: Big Five -> DISC -> Well-being -> Resilience
ASSESSMENT_ORDER = ["big_five", "disc", "bien_etre", "resilience_ie"]

# Big Five traits in order
TRAITS_BIG5 = ["ouverture", "conscienciosité", "extraversion", "agréabilité", "stabilité émotionnelle"]
DISC_STYLES = ["dominant", "influent", "stable", "conforme"]

def choose_language(request):
    if request.method == "POST":
        lang = request.POST.get("language", "fr")
        session = UserSession.objects.create(
            language=lang,
            current_assessment="big_five",
            current_trait=TRAITS_BIG5[0],
            current_question_number=1
        )
        return redirect('quiz', session_id=session.id)
    
    return render(request, 'choose_language.html')

def adaptive_quiz(request, session_id):
    session = get_object_or_404(UserSession, id=session_id)
    
    if session.is_completed:
        return redirect('report', session_id=session.id)
    
    if request.method == "POST":
        answer_text = request.POST.get("answer", "").strip()
        if not answer_text:
            return JsonResponse({"error": "Answer is required"}, status=400)
        
        # Get current question
        current_question = Question.objects.filter(
            session=session,
            trait=session.current_trait,
            assessment_type=session.current_assessment,
            question_number=session.current_question_number
        ).first()
        
        if not current_question:
            return JsonResponse({"error": "No current question found"}, status=400)
        
        # Get all previous answers for this trait
        previous_answers = Answer.objects.filter(
            question__session=session,
            question__trait=session.current_trait,
            question__assessment_type=session.current_assessment
        ).values_list('text', flat=True)
        
        # Score the answer
        score = analyze_and_score_answer(
            answer_text, 
            session.current_trait, 
            list(previous_answers), 
            session.language, 
            session.current_assessment
        )
        
        # Save the answer
        Answer.objects.create(
            question=current_question,
            text=answer_text,
            score=score
        )
        
        # Determine next step
        should_continue = should_ask_followup_question(
            session.current_trait,
            session.current_question_number,
            answer_text,
            session.language,
            session.current_assessment
        )
        
        if should_continue:
            # Ask another question for the same trait
            session.current_question_number += 1
            session.save()
        else:
            # Move to next trait/assessment
            next_trait, next_assessment = get_next_trait_or_assessment(session)
            if next_trait and next_assessment:
                session.current_trait = next_trait
                session.current_assessment = next_assessment
                session.current_question_number = 1
                session.save()
            else:
                # Complete assessment
                session.is_completed = True
                session.save()
                generate_final_results(session)
                return JsonResponse({"completed": True, "redirect": f"/report/{session.id}/"})
        
        return JsonResponse({"success": True})
    
    # GET request - show current question
    print(f"🔍 DEBUG: Starting question generation...")
    print(f"   - Trait: {session.current_trait}")
    print(f"   - Question Number: {session.current_question_number}")
    print(f"   - Language: {session.language}")
    print(f"   - Assessment Type: {session.current_assessment}")
    
    previous_answers = get_previous_answers_for_trait(session)
    print(f"   - Previous Answers Count: {len(previous_answers)}")
    
    try:
        question_text = generate_adaptive_question(
            session.current_trait,
            session.current_question_number,
            previous_answers,
            session.language,
            session.current_assessment
        )
        print(f"✅ Generated Question: {question_text}")
    except Exception as e:
        print(f"❌ Question Generation Failed: {str(e)}")
        print(f"   Exception Type: {type(e)}")
        import traceback
        traceback.print_exc()
        # Use a fallback question
        question_text = f"Please describe your experience with {session.current_trait}."
    
    # Save question
    Question.objects.create(
        session=session,
        text=question_text,
        trait=session.current_trait,
        assessment_type=session.current_assessment,
        question_number=session.current_question_number
    )
    
    # Get trait introduction
    trait_intro = get_trait_intro(session.current_trait, session.language, session.current_assessment)
    
    # Calculate progress
    progress = calculate_progress(session)
    
    context = {
        'session': session,
        'question': question_text,
        'trait_intro': trait_intro,
        'progress': progress,
        'current_trait': session.current_trait,
        'current_assessment': session.current_assessment
    }
    
    print(f"🔍 DEBUG: Template context:")
    print(f"   - question: '{context['question']}'")
    print(f"   - trait_intro: '{context['trait_intro']}'")
    print(f"   - progress: {context['progress']}")
    
    return render(request, 'quiz.html', context)

def get_previous_answers_for_trait(session):
    """Get previous answers for current trait"""
    return list(Answer.objects.filter(
        question__session=session,
        question__trait=session.current_trait,
        question__assessment_type=session.current_assessment
    ).values_list('text', flat=True))

def get_next_trait_or_assessment(session):
    """Determine next trait or assessment based on current progress"""
    current_assessment = session.current_assessment
    current_trait = session.current_trait
    
    if current_assessment == "big_five":
        current_index = TRAITS_BIG5.index(current_trait)
        if current_index < len(TRAITS_BIG5) - 1:
            return TRAITS_BIG5[current_index + 1], "big_five"
        else:
            # Move to DISC
            return DISC_STYLES[0], "disc"
    
    elif current_assessment == "disc":
        current_index = DISC_STYLES.index(current_trait)
        if current_index < len(DISC_STYLES) - 1:
            return DISC_STYLES[current_index + 1], "disc"
        else:
            # Move to well-being (single trait)
            return "bien_etre", "bien_etre"
    
    elif current_assessment == "bien_etre":
        # Move to resilience (single trait)
        return "resilience_ie", "resilience_ie"
    
    # Assessment completed
    return None, None

def calculate_progress(session):
    """Calculate overall progress percentage"""
    total_traits = len(TRAITS_BIG5) + len(DISC_STYLES) + 2  # +2 for bien_etre and resilience_ie
    
    completed_traits = 0
    
    # Count completed Big Five traits
    if session.current_assessment == "big_five":
        completed_traits = TRAITS_BIG5.index(session.current_trait)
    elif session.current_assessment == "disc":
        completed_traits = len(TRAITS_BIG5) + DISC_STYLES.index(session.current_trait)
    elif session.current_assessment == "bien_etre":
        completed_traits = len(TRAITS_BIG5) + len(DISC_STYLES)
    elif session.current_assessment == "resilience_ie":
        completed_traits = len(TRAITS_BIG5) + len(DISC_STYLES) + 1
    
    return int((completed_traits / total_traits) * 100)

def generate_final_results(session):
    """Generate final assessment results for all modules"""
    
    # Process Big Five results
    for trait in TRAITS_BIG5:
        answers = Answer.objects.filter(
            question__session=session,
            question__trait=trait,
            question__assessment_type="big_five"
        )
        
        total_score = sum(answer.score for answer in answers)
        level = get_level_from_score(total_score, "big_five")
        
        # Generate detailed analysis
        answer_texts = [answer.text for answer in answers]
        analysis = generate_detailed_analysis(
            trait, answer_texts, total_score, session.language, "big_five"
        )
        
        AssessmentResult.objects.create(
            session=session,
            assessment_type="big_five",
            trait=trait,
            total_score=total_score,
            level=level,
            analysis=analysis
        )
    
    # Process DISC results
    disc_scores = {}
    for style in DISC_STYLES:
        answers = Answer.objects.filter(
            question__session=session,
            question__trait=style,
            question__assessment_type="disc"
        )
        
        total_score = sum(answer.score for answer in answers)
        disc_scores[style] = total_score
        
        answer_texts = [answer.text for answer in answers]
        analysis = generate_detailed_analysis(
            style, answer_texts, total_score, session.language, "disc"
        )
        
        AssessmentResult.objects.create(
            session=session,
            assessment_type="disc",
            trait=style,
            total_score=total_score,
            level="dominant" if total_score == max(disc_scores.values()) else "secondary",
            analysis=analysis
        )
    
    # Process Well-being results
    wellbeing_answers = Answer.objects.filter(
        question__session=session,
        question__assessment_type="bien_etre"
    )
    
    wellbeing_total = sum(answer.score for answer in wellbeing_answers)
    wellbeing_level = get_level_from_score(wellbeing_total, "bien_etre")
    
    wellbeing_texts = [answer.text for answer in wellbeing_answers]
    wellbeing_analysis = generate_detailed_analysis(
        "bien_etre", wellbeing_texts, wellbeing_total, session.language, "bien_etre"
    )
    
    AssessmentResult.objects.create(
        session=session,
        assessment_type="bien_etre",
        trait="bien_etre",
        total_score=wellbeing_total,
        level=wellbeing_level,
        analysis=wellbeing_analysis
    )
    
    # Process Resilience results
    resilience_answers = Answer.objects.filter(
        question__session=session,
        question__assessment_type="resilience_ie"
    )
    
    resilience_total = sum(answer.score for answer in resilience_answers)
    resilience_level = get_level_from_score(resilience_total, "resilience_ie")
    
    resilience_texts = [answer.text for answer in resilience_answers]
    resilience_analysis = generate_detailed_analysis(
        "resilience_ie", resilience_texts, resilience_total, session.language, "resilience_ie"
    )
    
    AssessmentResult.objects.create(
        session=session,
        assessment_type="resilience_ie",
        trait="resilience_ie",
        total_score=resilience_total,
        level=resilience_level,
        analysis=resilience_analysis
    )

def report(request, session_id):
    session = get_object_or_404(UserSession, id=session_id)
    
    if not session.is_completed:
        return redirect('quiz', session_id=session.id)
    
    # Get all results
    results = AssessmentResult.objects.filter(session=session).order_by('assessment_type', 'trait')
    
    # Organize results by assessment type
    big_five_results = results.filter(assessment_type="big_five")
    disc_results = results.filter(assessment_type="disc")
    wellbeing_result = results.filter(assessment_type="bien_etre").first()
    resilience_result = results.filter(assessment_type="resilience_ie").first()
    
    # Prepare scores for coaching recommendation
    all_scores = {}
    
    # Big Five scores
    all_scores["big_five"] = {}
    for result in big_five_results:
        all_scores["big_five"][result.trait] = {
            'total_score': result.total_score,
            'level': result.level
        }
    
    # Other assessments
    if wellbeing_result:
        all_scores["bien_etre"] = {
            'total_score': wellbeing_result.total_score,
            'level': wellbeing_result.level
        }
    
    if resilience_result:
        all_scores["resilience_ie"] = {
            'total_score': resilience_result.total_score,
            'level': resilience_result.level
        }
    
    # Get coaching recommendation
    coaching_recommendation = should_recommend_coaching(all_scores, session.language)
    
    context = {
        'session': session,
        'big_five_results': big_five_results,
        'disc_results': disc_results,
        'wellbeing_result': wellbeing_result,
        'resilience_result': resilience_result,
        'coaching_recommendation': coaching_recommendation,
        'traits_config': TRAITS_CONFIG
    }
    
    return render(request, 'report.html', context)
