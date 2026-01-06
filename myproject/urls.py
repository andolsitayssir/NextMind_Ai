from django.contrib import admin
from django.urls import path
from APP import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),
    path('go-home/', views.go_home, name='go_home'),
    path('reset/', views.reset_assessment, name='reset_assessment'),  # AJOUTÉ
    path('set-language/<str:lang>/', views.set_language, name='set_language'),  
    path('start-quiz/', views.start_quiz, name='start_quiz'),
    path('quiz/', views.quiz, name='quiz'),
    path('report/', views.report, name='report'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)