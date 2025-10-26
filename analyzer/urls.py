from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # Landing page
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Protected dashboard for logged-in users
    
    # Resume analysis routes
    path('analyze/', views.analyze_view, name='analyze'),
    path('upload_resume/', views.upload_resume_view, name='upload_resume'),
    path('history/', views.history_view, name='history'),
    path('profile/', views.profile_view, name='profile'),
    
    # OAuth routes
    path('auth/google/login/', views.google_login, name='google_login'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
]