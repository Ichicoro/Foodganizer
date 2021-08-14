from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from website.forms import UpdateUserForm


def index(request):
    return render(request, "pages/index.html", {})


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
