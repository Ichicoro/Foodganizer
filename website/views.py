from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, "pages/index.html", {})


def profile(request):
    return render(request, "pages/profile.html", {})
