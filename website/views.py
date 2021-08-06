from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from website.forms import UpdateProfileForm, UpdateUserForm


def index(request):
    return render(request, "pages/index.html", {})


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(data=request.POST, instance=request.user)
        profile_form = UpdateProfileForm(data=request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)
    print(f"{user_form.is_valid()=} {profile_form.__dict__=}")
    return render(request, "pages/profile.html", {
        'user_form': user_form,
        'profile_form': profile_form
    })
