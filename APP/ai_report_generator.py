"""
AI Report Generator for NextMind
Generates personalized insights and interpretations using AI
"""
import json
import logging
from .openrouter_client import OpenRouterClient
from .trait_guidelines import get_trait_guidelines

logger = logging.getLogger(__name__)


class AIReportGenerator:
    """Generates AI-powered psychological assessment reports"""
    
    def __init__(self):
        self.client = OpenRouterClient()
    
    def generate_trait_report(self, trait, assessment_type, q1_data, q2_data, language):
        """
        Generate comprehensive trait report with AI insights
        
        Args:
            trait: Trait name
            assessment_type: 'big_five' or 'disc'
            q1_data: Dict with Q1 answer and score
            q2_data: Dict with Q2 answer and score
            language: 'fr', 'en', or 'ar'
            
        Returns:
            Complete trait report dict
        """
        # Calculate mean score
        mean_score = (q1_data['score'] + q2_data['score']) / 2
        
        # Scale to 10-point system (2 questions × 5 points)
        scaled_score = mean_score * 2
        
        # Determine level based on cahier de charge
        level = self._determine_level(scaled_score, max_score=10)
        
        # Get standard interpretation
        standard_interpretation = self._get_standard_interpretation(trait, level, assessment_type, language)
        
        # Generate AI insights
        try:
            ai_insights = self._generate_ai_insights(
                trait=trait,
                assessment_type=assessment_type,
                q1_answer=q1_data['answer'],
                q2_answer=q2_data['answer'],
                mean_score=mean_score,
                scaled_score=scaled_score,
                level=level,
                language=language
            )
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            ai_insights = self._get_fallback_insights(trait, level, language)
        
        return {
            'trait': trait,
            'raw_scores': [q1_data['score'], q2_data['score']],
            'mean_score': round(mean_score, 1),
            'scaled_score': round(scaled_score, 1),
            'level': level,
            'standard_interpretation': standard_interpretation,
            'ai_insights': ai_insights,
            'strengths': ai_insights.get('strengths', []),
            'development_areas': ai_insights.get('development_areas', []),
            'recommendations': ai_insights.get('recommendations', []),
            'summary': ai_insights.get('summary', '')
        }
    
    def _determine_level(self, score, max_score):
        """Determine level based on cahier de charge thresholds"""
        if max_score == 10:  # Big Five / DISC (2 questions)
            if score <= 4:
                return 'Faible'
            elif score <= 7:
                return 'Modéré'
            else:
                return 'Élevé'
        elif max_score == 30:  # Well-being
            if score <= 14:
                return 'Faible'
            elif score <= 22:
                return 'Modéré'
            else:
                return 'Élevé'
        elif max_score == 40:  # Resilience
            if score <= 19:
                return 'Faible'
            elif score <= 29:
                return 'Modéré'
            else:
                return 'Élevé'
        else:
            return 'Modéré'
    
    def _get_standard_interpretation(self, trait, level, assessment_type, language):
        """Get standard interpretation from cahier de charge"""
        
        interpretations = {
            'big_five': {
                'ouverture': {
                    'Faible': {
                        'fr': "Préfère les routines, peu d'intérêt pour la nouveauté ou les idées abstraites.",
                        'en': "Prefers routines, little interest in novelty or abstract ideas."
                    },
                    'Modéré': {
                        'fr': "Ouvert(e) à certaines idées nouvelles mais avec prudence.",
                        'en': "Open to some new ideas but with caution."
                    },
                    'Élevé': {
                        'fr': "Très créatif(ve), curieux(se), attiré(e) par l'innovation et les expériences variées.",
                        'en': "Very creative, curious, attracted to innovation and varied experiences."
                    }
                },
                'conscienciosité': {
                    'Faible': {
                        'fr': "Peut manquer de rigueur, difficulté à respecter les délais ou à s'organiser.",
                        'en': "May lack rigor, difficulty meeting deadlines or organizing."
                    },
                    'Modéré': {
                        'fr': "Responsable dans les tâches importantes, mais manque parfois de planification.",
                        'en': "Responsible for important tasks, but sometimes lacks planning."
                    },
                    'Élevé': {
                        'fr': "Très organisé(e), fiable, soucieux(se) de la qualité et de l'efficacité.",
                        'en': "Very organized, reliable, concerned with quality and efficiency."
                    }
                },
                'extraversion': {
                    'Faible': {
                        'fr': "Préfère travailler seul(e), réservé(e), peu énergique socialement.",
                        'en': "Prefers working alone, reserved, low social energy."
                    },
                    'Modéré': {
                        'fr': "A l'aise dans certaines interactions, mais aime aussi la solitude.",
                        'en': "Comfortable in some interactions, but also enjoys solitude."
                    },
                    'Élevé': {
                        'fr': "Sociable, assertif(ve), prend l'initiative dans les groupes.",
                        'en': "Sociable, assertive, takes initiative in groups."
                    }
                },
                'agréabilité': {
                    'Faible': {
                        'fr': "Peut sembler distant(e), critique, peu conciliant(e).",
                        'en': "May seem distant, critical, uncompromising."
                    },
                    'Modéré': {
                        'fr': "Coopératif(ve), mais peut défendre fermement ses opinions.",
                        'en': "Cooperative, but can firmly defend opinions."
                    },
                    'Élevé': {
                        'fr': "Empathique, à l'écoute, privilégie l'harmonie dans les relations.",
                        'en': "Empathetic, listening, prioritizes harmony in relationships."
                    }
                },
                'stabilité émotionnelle': {
                    'Faible': {
                        'fr': "Stressé(e), sensible aux critiques, anxieux(se).",
                        'en': "Stressed, sensitive to criticism, anxious."
                    },
                    'Modéré': {
                        'fr': "Équilibré(e) mais réagit parfois fortement au stress.",
                        'en': "Balanced but sometimes reacts strongly to stress."
                    },
                    'Élevé': {
                        'fr': "Calme, confiant(e), gère bien les émotions et les tensions.",
                        'en': "Calm, confident, manages emotions and tensions well."
                    }
                }
            }
        }
        
        return interpretations.get(assessment_type, {}).get(trait, {}).get(level, {}).get(language, '')
    
    def generate_assessment_report(self, assessment_type, traits_data, language):
        """
        Generate report for an entire assessment (multiple traits) in ONE API call.
        
        Args:
            assessment_type: 'big_five' or 'disc'
            traits_data: Dict mapping trait names to {q1, q2} data
            language: 'fr', 'en', 'ar'
            
        Returns:
            Dict mapping trait names to their full report objects
        """
        # 1. Pre-calculate scores and levels for all traits
        processed_traits = {}
        prompt_data = []
        
        for trait, data in traits_data.items():
            q1_data = data['q1']
            q2_data = data['q2']
            
            mean_score = (q1_data['score'] + q2_data['score']) / 2
            scaled_score = mean_score * 2
            level = self._determine_level(scaled_score, max_score=10)
            standard_interpretation = self._get_standard_interpretation(trait, level, assessment_type, language)
            
            # Store base data
            processed_traits[trait] = {
                'trait': trait,
                'raw_scores': [q1_data['score'], q2_data['score']],
                'mean_score': round(mean_score, 1),
                'scaled_score': round(scaled_score, 1),
                'level': level,
                'standard_interpretation': standard_interpretation
            }
            
            # Prepare data for AI prompt
            guidelines = get_trait_guidelines(trait, assessment_type, language)
            prompt_data.append(f"""
TRAIT: {trait}
LEVEL: {level}
SCORE: {mean_score:.1f}/5
DESCRIPTION: {guidelines.get('description', '')[:200]}...
USER ANSWERS:
- "{q1_data.get('answer', '')}"
- "{q2_data.get('answer', '')}"
""")

        # 2. Build Single Aggregated Prompt
        prompt = f"""You are a professional psychological coach. Analyze these {len(prompt_data)} traits for the USER.

{'-'*20}
{chr(10).join(prompt_data)}
{'-'*20}

Generate personalized insights for EACH trait in {language}.
Response MUST be a JSON object where keys are trait names and values are objects with:
"strengths" (list), "development_areas" (list).

Example JSON structure:
{{
  "trait_name_1": {{ "strengths": [...], "development_areas": [...] }},
  "trait_name_2": {{ ... }}
}}
"""
        
        # 3. Call API
        try:
            response_json = self.client.generate_json(
                prompt=prompt,
                model='reasoning',
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"Batch generation failed for {assessment_type}: {e}")
            # Fallback for ALL traits
            for trait in processed_traits:
                processed_traits[trait]['ai_insights'] = self._get_fallback_insights(trait, processed_traits[trait]['level'], language)
                # Populate full fields
                processed_traits[trait].update(processed_traits[trait]['ai_insights'])
            return processed_traits

        # 4. Merge Results
        for trait, base_data in processed_traits.items():
            if trait in response_json:
                ai_data = response_json[trait]
                base_data['ai_insights'] = ai_data
                base_data['strengths'] = ai_data.get('strengths', [])
                base_data['development_areas'] = ai_data.get('development_areas', [])
                # Recommendations and summary removed per user request
            else:
                # Partial failure in JSON? Use fallback for this trait
                base_data['ai_insights'] = self._get_fallback_insights(trait, base_data['level'], language)
                base_data.update(base_data['ai_insights'])
        
        return processed_traits

    def _generate_ai_insights(self, trait, assessment_type, q1_answer, q2_answer, mean_score, scaled_score, level, language):
        """Generate personalized AI insights"""
        
        guidelines = get_trait_guidelines(trait, assessment_type, language)
        
        prompt = f"""You are a professional psychological coach analyzing assessment results.

TRAIT: {trait}
ASSESSMENT: {assessment_type}
LEVEL: {level}
SCORE: {mean_score:.1f}/5 (scaled: {scaled_score:.1f}/10)

TRAIT DESCRIPTION:
{guidelines.get('description', '')}

USER'S ANSWERS:
Question 1 Answer: "{q1_answer}"
Question 2 Answer: "{q2_answer}"

Generate personalized insights in {language} based on the ACTUAL ANSWERS provided.

Your analysis should include:
1. STRENGTHS: 2-3 specific strengths based on what the user actually said
2. DEVELOPMENT AREAS: 1-2 areas where they could improve (be constructive)
3. RECOMMENDATIONS: 2-3 actionable, practical recommendations
4. SUMMARY: One paragraph (3-4 sentences) summarizing the overall profile

Guidelines:
- Be SPECIFIC to the user's actual answers - reference what they said
- Use a professional but warm, encouraging tone
- Align with the {level} level interpretation
- Keep each section concise (2-3 sentences per point)
- Write in {language}
- Be constructive and actionable

Return your response in this EXACT JSON format:
{{
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "development_areas": ["area 1", "area 2"],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "summary": "One paragraph summary"
}}"""

        response = self.client.generate_json(
            prompt=prompt,
            model='reasoning',
            temperature=0.7  # Creative for personalization
        )
        
        return response
    
    def generate_fallback_report(self, trait, assessment_type, q1_data, q2_data, language):
        """Generate a complete report using fallback data (NO AI)"""
        # Calculate scores
        mean_score = (q1_data['score'] + q2_data['score']) / 2
        
        if assessment_type == 'big_five' or assessment_type == 'disc' or assessment_type == 'bien_etre' or assessment_type == 'resilience_ie':
             # All use 2 questions now, so logic is similar
             pass

        # Scale to 10-point system (2 questions × 5 points) -> max 10
        # Wait, Big Five uses 10 point max per trait.
        # Bien-être uses 2 questions -> max 10.
        # Resilience uses 2 questions -> max 10.
        
        scaled_score = mean_score * 2
        
        # Determine level
        # Note: update determine_level to handle new max_scores if needed, but for now max_score=10 is common
        level = self._determine_level(scaled_score, max_score=10)
        
        # Get standard interpretation
        standard_interpretation = self._get_standard_interpretation(trait, level, assessment_type, language)
        
        # Get fallback insights
        ai_insights = self._get_fallback_insights(trait, level, language)
        
        return {
            'trait': trait,
            'raw_scores': [q1_data['score'], q2_data['score']],
            'mean_score': round(mean_score, 1),
            'scaled_score': round(scaled_score, 1),
            'level': level,
            'standard_interpretation': standard_interpretation,
            'ai_insights': ai_insights,
            'strengths': ai_insights.get('strengths', []),
            'development_areas': ai_insights.get('development_areas', []),
            'recommendations': ai_insights.get('recommendations', []),
            'summary': ai_insights.get('summary', '')
        }

    def _get_fallback_insights(self, trait, level, language):
        """Fallback insights if AI generation fails"""
        # Improved fallback text
        
        # Generic texts based on level
        if language == 'fr':
            strengths = {
                'Faible': ["Potentiel de développement", "Marge de progression importante"],
                'Modéré': ["Compétences équilibrées", "Bonne base de connaissances"],
                'Élevé': ["Excellente maîtrise", "Atout majeur pour votre profil"]
            }
            areas = {
                'Faible': ["Nécessite une attention particulière", "Pratique régulière recommandée"],
                'Modéré': ["Peut être affiné avec l'expérience", "Renforcer la mise en pratique"],
                'Élevé': ["Maintenir ce niveau d'excellence", "Partager ces compétences"]
            }
            summary = f"Votre résultat indique un niveau {level}. Cela reflète votre auto-évaluation actuelle."
        elif language == 'ar':
            strengths = {
                'Faible': ["إمكانية للتطوير", "مجال كبير للتحسن"],
                'Modéré': ["مهارات متوازنة", "قاعدة معرفية جيدة"],
                'Élevé': ["إتقان ممتاز", "ميزة كبيرة لملفك الشخصي"]
            }
            areas = {
                'Faible': ["يتطلب اهتمامًا خاصًا", "يوصى بالممارسة المنتظمة"],
                'Modéré': ["يمكن صقله بالخبرة", "تعزيز التطبيق العملي"],
                'Élevé': ["الحفاظ على هذا المستوى من التميز", "مشاركة هذه المهارات"]
            }
            summary = f"تشير نتيجتك إلى مستوى {level}. هذا يعكس تقييمك الذاتي الحالي."
        else:  # English
            strengths = {
                'Faible': ["Development potential", "Significant room for growth"],
                'Modéré': ["Balanced skills", "Good knowledge base"],
                'Élevé': ["Excellent mastery", "Major asset for your profile"]
            }
            areas = {
                'Faible': ["Requires special attention", "Regular practice recommended"],
                'Modéré': ["Can be refined with experience", "Reinforce practical application"],
                'Élevé': ["Maintain this level of excellence", "Share these skills"]
            }
            summary = f"Your result indicates a {level} level. This reflects your current self-assessment."

        return {
            'strengths': strengths.get(level, ["Strength 1", "Strength 2"]),
            'development_areas': areas.get(level, ["Area 1", "Area 2"]),
            'recommendations': [
                "Review the detailed guidelines for this trait" if language == 'en' else "Consultez les directives détaillées pour ce trait" if language == 'fr' else "راجع الإرشادات التفصيلية لهذه السمة",
                "Set specific learning goals" if language == 'en' else "Fixez des objectifs d'apprentissage spécifiques" if language == 'fr' else "حدد أهداف تعلم محددة"
            ],
            'summary': summary
        }
