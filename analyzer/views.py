from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from .forms import SignupForm
from django.contrib.auth.models import User

def sign_up(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'sign_up.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm  # or use django.contrib.auth.forms.AuthenticationForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  # creates the session
                messages.success(request, "Signed in successfully.")
                # keep session for SESSION_COOKIE_AGE (default 2 weeks)
                request.session.set_expiry(None)  # uses settings.SESSION_COOKIE_AGE

                messages.success(request, f'Welcome back, {user.username}!')
                # redirect to next param if provided
                next_url = request.GET.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)  # clears the session
    messages.info(request, 'You have been logged out.')
    return redirect('login')