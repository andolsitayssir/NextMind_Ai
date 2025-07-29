from django.db import models

class UserSession(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, default='fr')  # fr / en / ar
    current_assessment = models.CharField(max_length=50, default='big_five')  # big_five, disc, bien_etre, resilience_ie
    current_trait = models.CharField(max_length=50, null=True, blank=True)  # Current trait being assessed
    current_question_number = models.IntegerField(default=0)  # Question number for current trait
    is_completed = models.BooleanField(default=False)

class Question(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    text = models.TextField()
    trait = models.CharField(max_length=50)  # trait name or assessment dimension
    assessment_type = models.CharField(max_length=50, default="big_five")  # big_five, disc, bien_etre, resilience_ie
    question_number = models.IntegerField(default=1)  # Question number for this trait
    created_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    score = models.IntegerField(default=0)  # 1-5 score for this answer
    created_at = models.DateTimeField(auto_now_add=True)

class AssessmentResult(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    assessment_type = models.CharField(max_length=50)  # big_five, disc, bien_etre, resilience_ie
    trait = models.CharField(max_length=50)  # trait or dimension name
    total_score = models.IntegerField(default=0)  # Sum of all answer scores for this trait
    level = models.CharField(max_length=20, default='modéré')  # faible, modéré, élevé
    analysis = models.JSONField(null=True, blank=True)  # Detailed analysis from AI
    created_at = models.DateTimeField(auto_now_add=True)
