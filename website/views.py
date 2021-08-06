from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, "pages/index.html", {})


@login_required
def profile(request):
    if request.POST: pass
    return render(request, "pages/profile.html", {})
