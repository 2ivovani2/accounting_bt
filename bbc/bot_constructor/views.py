from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def vue(request):
    """"
        Функция для отображения страницы с front-end
    """
    return render(request, 'root.html') 