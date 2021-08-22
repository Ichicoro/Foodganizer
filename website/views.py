from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Kitchen, Membership, User

# Create your views here.
from website.forms import UpdateUserForm
from .forms import NewKitchenForm, UserRegisterForm 


def index(request):
    user = request.user
    kitchens = []
    if user.is_authenticated:
        # for some reason this returns an empty queryset
        kitchens = user.kitchen_set.all()

    return render(request, "pages/index.html", {'kitchens': kitchens})

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

@login_required
def new_kitchen(request):
    if request.method == 'POST':
        form = NewKitchenForm(request.POST)
        if form.is_valid():
            k = form.save() # https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#the-save-method
            m = Membership(user=request.user, kitchen=k, is_admin=True)
            m.save()
            kitchen_name = form.cleaned_data.get('name')
            invite_other_users = form.cleaned_data.get('invite_other_users')
            # TODO: idk send an email to this addresses or something
            messages.success(request, f'Kitchen {kitchen_name} created successfully!')
            return redirect('index')
    else:
        form = NewKitchenForm()
    return render(request, 'pages/new-kitchen.html', {'form': form})

@login_required
def kitchen(request, id):
    k = request.user.kitchen_set.get(id=id)
    if k:
        users = k.users.all()
        memberships = k.membership_set.all()
        members = []
        for u in users:
            m = memberships.get(user=u)
            members.append({ "user": u, "is_admin": m.is_admin })
        
        return render(request, 'pages/kitchen.html', {'kitchen': k, 'members': members})
    else:
        return redirect('index')