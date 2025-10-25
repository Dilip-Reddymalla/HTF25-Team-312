from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.sign_up, name="signup"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout')
]