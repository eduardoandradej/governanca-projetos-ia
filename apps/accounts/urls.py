from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import ThrottledAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path(
        "entrar/",
        auth_views.LoginView.as_view(authentication_form=ThrottledAuthenticationForm, redirect_authenticated_user=True),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "senha/alterar/",
        auth_views.PasswordChangeView.as_view(success_url=reverse_lazy("accounts:password_change_done")),
        name="password_change",
    ),
    path("senha/alterada/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path(
        "senha/recuperar/",
        auth_views.PasswordResetView.as_view(
            success_url=reverse_lazy("accounts:password_reset_done"),
            email_template_name="registration/password_reset_email.txt",
        ),
        name="password_reset",
    ),
    path("senha/recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy("accounts:password_reset_complete")),
        name="password_reset_confirm",
    ),
    path("senha/redefinida/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
