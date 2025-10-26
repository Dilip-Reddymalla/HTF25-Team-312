from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, SignupForm, ResumeSubmissionForm
from .models import ResumeSubmission
from .gemini_client import analyze_resume as call_gemini
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
import logging


def home_view(request):
    """Landing page view (previously dashboard.html)"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'dashboard.html')  # Using dashboard.html as the landing page

@login_required
def dashboard_view(request):
    """Protected dashboard view for logged-in users"""
    return render(request, 'index.html')  # New dashboard view after login

@login_required
def analyze_view(request):
    """Handle resume analysis"""
    result = None
    if request.method == 'POST':
        form = ResumeSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            if request.user.is_authenticated:
                submission.user = request.user
            submission.save()

            # Placeholder analysis: you can wire your real analyzer here.
            # For now compute a mock score and echo back skills/recommendations.
            text = submission.resume_text or ''
            # If file was uploaded, we could parse it here. For now keep simple.
            if submission.resume_file and not text:
                text = f"(uploaded file: {submission.resume_file.name})"

            # Try to run the Gemini-backed analysis (or fallback to mock inside
            # gemini_client if credentials are missing)
            try:
                resume_text = submission.resume_text or ''
                if submission.resume_file and not resume_text:
                    # The gemini client expects text. For now, add filename as a
                    # placeholder; you could integrate a PDF/Doc parser to extract text.
                    resume_text = f"(uploaded file: {submission.resume_file.name})"

                # Use job description (if provided via the simpler upload form) as
                # the analysis target; fall back to submission.target_role.
                analysis_target = request.POST.get('job_description') or submission.target_role
                analysis = call_gemini(resume_text, analysis_target)
                score = int(analysis.get('score', 0))
                skills = analysis.get('skills', []) or []
                recommendations = analysis.get('recommendations', []) or []

            except Exception:
                # As a safe fallback use a simple heuristic (previous behavior)
                import logging

                logging.exception('Gemini analysis failed; falling back to simple heuristic')
                score = 60
                skills = ['Python', 'Django']
                recommendations = ['Add a projects section', 'Quantify achievements']

            submission.score = score
            submission.skills = skills
            submission.recommendations = recommendations
            submission.save()

            result = {
                'score': score,
                'skills': skills,
                'recommendations': recommendations,
            }
        else:
            # form invalid - show errors below
            return render(request, 'analyzer.html', {'form': form})
    else:
        form = ResumeSubmissionForm()

    # If the request is AJAX (fetch-based) or client expects JSON, return JSON
    xreq = request.headers.get('x-requested-with') or request.META.get('HTTP_X_REQUESTED_WITH')
    accept = request.headers.get('accept', '')
    if request.method == 'POST' and (xreq == 'XMLHttpRequest' or 'application/json' in accept):
        # Return JSON result (empty dict if analysis failed to produce one)
        return JsonResponse(result or {})

    return render(request, 'analyzer.html', {'form': form, 'result': result})

@login_required
def history_view(request):
    """Show analysis history"""
    return render(request, 'history.html')

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'profile.html')

def login_view(request):
    print("Login view accessed")
    if request.user.is_authenticated:
        return redirect('dashboard')
    print("User not authenticated")

    if request.method == 'POST':
        print("POST request received")
        print("POST data:", request.POST)
        form = LoginForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                print(f"Looking for user with email: {email}")
                # First find the user with this email
                user = User.objects.get(email=email)
                print(f"Found user: {user.username}")
                
                # Then authenticate with their username
                user = authenticate(request, username=user.username, password=password)
                print(f"Authentication result: {user is not None}")
                
                if user is not None:
                    print("Logging in user")
                    login(request, user)  # creates the session
                    messages.success(request, "Signed in successfully.")
                    print("Session created")
                    
                    # keep session for SESSION_COOKIE_AGE (default 2 weeks)
                    request.session.set_expiry(None)  # uses settings.SESSION_COOKIE_AGE
                    messages.success(request, f'Welcome back, {user.username}!')
                    
                    # redirect to next param if provided
                    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dashboard')
                    print(f"Redirecting to: {next_url}")
                    return redirect(next_url)
                else:
                    print("Authentication failed")
                    messages.error(request, 'Invalid password')
            except User.DoesNotExist:
                print(f"No user found with email: {email}")
                messages.error(request, 'No account found with this email address')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)  # clears the session
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    print("Dashboard view accessed")
    print("User:", request.user)
    print("Is authenticated:", request.user.is_authenticated)
    return render(request, 'dashboard.html')


def signup_view(request):
    if request.method == 'POST':
        print("POST data:", request.POST)  # Debug print
        fullname = request.POST.get('fullName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Create user with email as username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            # Set full name
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

# Google OAuth handlers
User = get_user_model()
logger = logging.getLogger(__name__)

def google_login(request):
    """
    STEP 1: Create the flow and redirect user to Google.
    """
    
    # Create the flow instance using the client secrets file and scopes
    flow = Flow.from_client_secrets_file(
        client_secrets_file=settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    # Generate the authorization URL and store the state
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    # Store the state in the session so we can verify it in the callback
    request.session['oauth_state'] = state

    # Debug logging to help diagnose session/state issues during development
    logger.debug(
        "google_login: session_key=%s stored_state=%s session_keys=%s",
        request.session.session_key,
        state,
        list(request.session.keys())
    )
    
    # This is the redirect to Google's login/consent screen
    return redirect(authorization_url)


def google_callback(request):
    """
    STEP 2: Handle the callback from Google.
    """
    
    # Get the state from the request and the stored session (don't pop yet)
    request_state = request.GET.get('state')
    stored_state = request.session.get('oauth_state')

    # Debug: log session and state info
    logger.debug(
        "google_callback: session_key=%s stored_state_present=%s request_state=%s session_keys=%s",
        request.session.session_key,
        bool(stored_state),
        request_state,
        list(request.session.keys())
    )

    # 1. Verify the state token to prevent CSRF
    if stored_state is None or stored_state != request_state:
        # Remove the state from session if present to avoid reuse
        request.session.pop('oauth_state', None)
        details = (
            f"Invalid state token. stored_state={stored_state!r} request_state={request_state!r} "
            f"session_key={request.session.session_key!r} session_keys={list(request.session.keys())}"
        )
        logger.warning(details)
        # In DEBUG show details to make troubleshooting easier
        if getattr(settings, 'DEBUG', False):
            return HttpResponse(details, status=400)
        return HttpResponse("Invalid state token.", status=400)

    # Create the flow again, with the same settings
    flow = Flow.from_client_secrets_file(
        client_secrets_file=settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    # 2. Exchange the authorization code for an access token
    # We pass the full URL from the request to fetch_token
    authorization_response = request.build_absolute_uri()
    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as e:
        return HttpResponse(f"Error fetching token: {e}", status=400)

    # 3. Get the user's profile information
    credentials = flow.credentials
    id_info = id_token.verify_oauth2_token(
        credentials.id_token,
        GoogleRequest(),  # Create a new Request object for token verification
        credentials.client_id
    )

    # 4. Get or Create the Django User
    email = id_info.get('email')
    first_name = id_info.get('given_name', '')
    last_name = id_info.get('family_name', '')

    if not email:
        return HttpResponse("Email not found in token.", status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Create a new user
        # We use email as username for simplicity
        user = User.objects.create_user(
            username=email, 
            email=email, 
            first_name=first_name, 
            last_name=last_name
        )
        user.set_unusable_password()  # User logs in via Google, so no local password needed
        user.save()

    # 5. Log the user into Django
    login(request, user)
    
    # Redirect to dashboard after successful login
    return redirect('dashboard')


from django.shortcuts import render
from django.core.files.storage import default_storage
from django.conf import settings
from .forms import ResumeUploadForm
from .text_classification import analyze_resume  # Import your refactored function
import os

def upload_resume_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['resume_file']
            job_desc = form.cleaned_data['job_description']
            
            # --- This is the key part ---
            # 1. Save the file temporarily
            file_name = default_storage.save(uploaded_file.name, uploaded_file)
            file_path = default_storage.path(file_name)
            # ---------------------------

            feedback = ""
            try:
                # 2. Call your script with the file path
                feedback = analyze_resume(file_path, job_desc)
            except Exception as e:
                feedback = f"An unexpected error occurred: {e}"
            finally:
                # 3. Delete the temporary file
                if default_storage.exists(file_name):
                    default_storage.delete(file_name)
            
            # 4. Render the results page
            return render(request, 'analyze', {'feedback': feedback})
    
    else:
        form = ResumeUploadForm()
        
    return render(request, 'analyze', {'form': form})
