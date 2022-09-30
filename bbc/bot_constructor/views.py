from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def vue(request):
    """"
        Display vue main file
    """
    return render(request, 'root.html') 