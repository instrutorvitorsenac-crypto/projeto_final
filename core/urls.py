from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("conta/entrar/", views.login_view, name="login"),
    path("conta/cadastrar/", views.register, name="register"),
    path(
        "conta/senha/redefinir/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "conta/senha/redefinir/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "conta/senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "conta/senha/redefinir/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("conta/sair/", views.logout_view, name="logout"),
    path("perfil/", views.dashboard, name="dashboard"),
    path("perfil/configurar/", views.profile_setup, name="profile_setup"),
    path("obras/", views.artwork_list, name="artworks"),
    path(
        "promocoes/",
        views.artwork_list,
        {"category": "promotions"},
        name="promotions",
    ),
    path(
        "artistas/",
        views.artwork_list,
        {"category": "artists"},
        name="artists",
    ),
    path("obras/nova/", views.artwork_create, name="artwork_create"),
    path("obras/<int:pk>/editar/", views.artwork_edit, name="artwork_edit"),
    path("obras/<int:pk>/", views.artwork_detail, name="artwork_detail"),
    path("obras/<int:pk>/curtir/", views.toggle_like, name="toggle_like"),
    path(
        "artistas/<int:pk>/acompanhar/",
        views.toggle_follow,
        name="toggle_follow",
    ),
    path(
        "obras/<int:pk>/interesse/",
        views.register_interest,
        name="register_interest",
    ),
]
