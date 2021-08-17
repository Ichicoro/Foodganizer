from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

# Create your views here.
from website.forms import UpdateUserForm
from .forms import UserRegisterForm 


def index(request):
    return render(request, "pages/index.html", {})

def signup(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(data=request.POST, instance=request.user, files=request.FILES)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = UpdateUserForm(instance=request.user)
    print(f"{user_form.files=}")   # TODO: Remove me
    print(f"{user_form.is_valid()=}")   # TODO: Remove me
    return render(request, "pages/profile.html", {
        'user_form': user_form,
    })
