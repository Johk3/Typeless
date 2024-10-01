# messaging/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db import models
from .models import Message

@login_required
def index(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'messaging/index.html', {'users': users})

@login_required
def chat(request, user_id):
    other_user = User.objects.get(id=user_id)
    messages = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(receiver=other_user)) |
        (models.Q(sender=other_user) & models.Q(receiver=request.user))
    ).order_by('timestamp')
    
    room_name = f"{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"
    
    return render(request, 'messaging/chat.html', {
        'other_user': other_user,
        'messages': messages,
        'room_name': room_name,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'messaging/register.html', {'form': form})
