"""Gera docs/seguranca/matriz-rbac.md a partir de apps/organizations/rbac.py (fonte única da verdade)."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.organizations.models import Role
from apps.organizations.rbac import PERMISSIONS, PLATFORM_PERMISSIONS


class Command(BaseCommand):
    help = "Exporta a matriz de permissões RBAC para Markdown."

    def handle(self, *args, **opts):
        roles = list(Role)
        header = "| Permissão | " + " | ".join(r.label for r in roles) + " |"
        sep = "|---|" + "---|" * len(roles)
        lines = [
            "# Matriz RBAC (gerada automaticamente)",
            "",
            "Gerada por `python manage.py export_rbac_matrix` a partir de `apps/organizations/rbac.py`.",
            "Escopo: papel atribuído à organização inteira ou a um projeto específico; exige vínculo ativo.",
            "Segregação de funções (solicitante ≠ aprovador; quem atende ≠ quem valida) é aplicada nos serviços.",
            "",
            header,
            sep,
        ]
        for perm in sorted(PERMISSIONS):
            allowed = PERMISSIONS[perm]
            lines.append(f"| `{perm}` | " + " | ".join("✔" if r.value in allowed else "" for r in roles) + " |")
        lines += [
            "",
            "## Administrador da plataforma (superusuário técnico)",
            "",
            "Possui apenas: " + ", ".join(f"`{p}`" for p in sorted(PLATFORM_PERMISSIONS)) + ".",
            "Não aprova gates nem decisões de negócio e não lê projetos sem papel atribuído.",
            "",
        ]
        path = Path(settings.BASE_DIR) / "docs" / "seguranca" / "matriz-rbac.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Gerado: {path}"))
