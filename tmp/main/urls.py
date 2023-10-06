from django.urls import path
import main.views as views

urlpatterns = [
    path("history", views.history_render),
    path("api/get_user_tables", views.get_user_tables),
    path("api/get_user_operations", views.get_user_operations),
    path("api/delete_user_operations", views.delete_user_operation)
]