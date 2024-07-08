import uuid
import msal
import requests
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login, logout 
from django.contrib import messages
from django.conf import settings

AUTHORITY = "https://login.microsoftonline.com/" + settings.MSAL_TENANT_ID
ENDPOINT = 'https://graph.microsoft.com/v1.0/users'
SCOPE = ['User.Read'] 
SESSION_TYPE = "filesystem"  # So the token cache will be stored in a server-side session

REDIRECT_AFTER_LOGIN = 'clients:list'
REDIRECT_LOGIN = 'sso:login'
CALLBACK_URL = 'sso:callback'

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(settings.MSAL_CLIENT_ID, settings.MSAL_CLIENT_SECRET, AUTHORITY, token_cache=cache)

def login_page(request):
    if request.user.is_authenticated:
        login_next = request.session.get('login_next')
        if login_next is not None:
            del request.session['login_next']
            return redirect(login_next)
        return redirect(REDIRECT_AFTER_LOGIN)
    next = request.GET.get('next')
    if next is not None:
        messages.info(request, "You need to log in first." )
        request.session['login_next'] = next
    return render(request, 'login.html')

def sso_redirect(request):
    request.session['state'] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        SCOPE,  
        state=request.session['state'],
        redirect_uri=request.build_absolute_uri(reverse(CALLBACK_URL)))
    return redirect(auth_url)

def sso_callback(request):
    if request.GET['state'] != request.session.get('state'):
        messages.info(request, "Please, try again." )
        return redirect (REDIRECT_LOGIN)
    
    token = _build_msal_app().acquire_token_by_authorization_code(request.GET['code'], SCOPE, request.build_absolute_uri(reverse(CALLBACK_URL)))
    
    if "error" in token:
        messages.error(request, token['error'] + ": " + token['error_description'])
        return redirect (REDIRECT_LOGIN)
    if not token:
        return redirect (REDIRECT_LOGIN)
    
    headers = {'Authorization': 'Bearer ' + token['access_token']}
    graph_data = requests.get('https://graph.microsoft.com/v1.0/me/', headers=headers,).json()
    try:
        user = User.objects.get(username=graph_data['userPrincipalName'])
    except User.DoesNotExist:
        messages.error(request, "You do not have permission to access this app. Please, contact administrator." )
        return redirect (REDIRECT_LOGIN)
    if not user.is_active:
        messages.error(request, "Permission denied, please contact administrator.")
        return redirect (REDIRECT_LOGIN)
    
    print(graph_data['userPrincipalName'])
    print(headers)

    login(request, user)
    if user.first_name != graph_data['givenName'] or user.last_name != graph_data['surname']:
        user.first_name = graph_data['givenName']
        user.last_name = graph_data['surname']
        user.save()
    messages.success(request, "You've been logged in")
    avatar_request = requests.get('https://graph.microsoft.com/v1.0/me/photo/$value', headers=headers,)
    if avatar_request.status_code == requests.codes.ok:
        user.employee.sso_update_avatar(avatar_request.content)
    return redirect (REDIRECT_LOGIN)

def sso_logout(request):
    logout(request)
    messages.success(request, "You've been logged out." )
    return redirect(AUTHORITY + "/oauth2/v2.0/logout" + "?post_logout_redirect_uri=" + request.build_absolute_uri(reverse(REDIRECT_LOGIN)))