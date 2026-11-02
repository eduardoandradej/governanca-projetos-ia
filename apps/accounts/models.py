import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário da plataforma.

    `is_superuser`/`is_staff` representam o **administrador da plataforma** (técnico).
    Esse perfil NÃO recebe implicitamente direito de aprovar decisões de negócio,
    gates ou acessar dados de projetos: tais direitos dependem de papéis atribuídos
    com escopo de organização/projeto (ver apps/organizations/rbac.py).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("e-mail", blank=True)
    full_name = models.CharField("nome completo", max_length=150, blank=True)

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return self.full_name or self.get_username()

    @property
    def display_name(self) -> str:
        return self.full_name or self.get_full_name() or self.username


class LoginAttempt(models.Model):
    """Tentativas de autenticação para controle de força bruta (não armazena senha)."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    successful = models.BooleanField(default=False)

    class Meta:
        verbose_name = "tentativa de login"
        verbose_name_plural = "tentativas de login"
        indexes = [models.Index(fields=["username", "created_at"]), models.Index(fields=["ip_address", "created_at"])]
