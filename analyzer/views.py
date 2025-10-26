from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from django.core.files.storage import default_storage
import logging

from .forms import LoginForm, SignupForm, ResumeSubmissionForm, ResumeUploadForm
from .models import ResumeSubmission
from .text_classification import analyze_resume  # ML model function

User = get_user_model()
logger = logging.getLogger(__name__)


def home_view(request):
    """Landing page view (previously dashboard.html)"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'dashboard.html')


@login_required
def dashboard_view(request):
    """Protected dashboard view for logged-in users"""
    return render(request, 'index.html')


@login_required
def analyze_view(request):
    """Store resume submissions without calling ML API directly"""
    result = None
    if request.method == 'POST':
        form = ResumeSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            if request.user.is_authenticated:
                submission.user = request.user
            submission.save()

            result = {'message': 'Resume submitted successfully.'}
        else:
            return render(request, 'analyzer.html', {'form': form})
    else:
        form = ResumeSubmissionForm()

    return render(request, 'analyzer.html', {'form': form, 'result': result})


@login_required
def history_view(request):
    return render(request, 'history.html')


@login_required
def profile_view(request):
    return render(request, 'profile.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    login(request, user)
                    request.session.set_expiry(None)  # Use SESSION_COOKIE_AGE
                    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid password')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def signup_view(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
            first_name = fullname.split()[0] if fullname else ""
            last_name = " ".join(fullname.split()[1:]) if fullname and len(fullname.split()) > 1 else ""
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'sign_up.html')
    return render(request, 'sign_up.html')


def google_login(request):
    flow = Flow.from_client_secrets_file(
        client_secrets_file=settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    request.session['oauth_state'] = state
    return redirect(authorization_url)


def google_callback(request):
    request_state = request.GET.get('state')
    stored_state = request.session.get('oauth_state')
    if stored_state is None or stored_state != request_state:
        request.session.pop('oauth_state', None)
        return HttpResponse("Invalid state token.", status=400)

    flow = Flow.from_client_secrets_file(
        client_secrets_file=settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(credentials.id_token, GoogleRequest(), credentials.client_id)

    email = id_info.get('email')
    first_name = id_info.get('given_name', '')
    last_name = id_info.get('family_name', '')

    if not email:
        return HttpResponse("Email not found in token.", status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(username=email, email=email, first_name=first_name, last_name=last_name)
        user.set_unusable_password()
        user.save()

    login(request, user)
    return redirect('dashboard')


def upload_resume_view(request):
    feedback = None
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data.get('resume_file')
            job_desc = form.cleaned_data.get('job_description', '')

            file_name = default_storage.save(uploaded_file.name, uploaded_file)
            file_path = default_storage.path(file_name)

            try:
                feedback = analyze_resume(file_path, job_desc)  # API key is handled inside ML function
            except Exception as e:
                feedback = f"Error during analysis: {e}"
            finally:
                if default_storage.exists(file_name):
                    default_storage.delete(file_name)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'feedback': feedback})
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": "Invalid form data."}, status=400)
    else:
        form = ResumeUploadForm()

    return render(request, 'analyzer.html', {'form': form, 'feedback': feedback})
