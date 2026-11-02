# ADR-001 — Monólito modular em Django 5.2 LTS

- **Status:** aceito (M0, 2026-11-02)
- **Contexto:** MVP acadêmico com equipe pequena, prazo curto e necessidade de regras transacionais
  fortes (gates, aprovações, auditoria). A familiaridade da equipe com aplicações web Linux e PostgreSQL
  favorece uma pilha simples, aberta e implantável em uma VM.
- **Decisão:** aplicação monolítica modular (`apps/<domínio>`) com Django 5.2 LTS, templates server-side,
  HTMX para interações parciais e Bootstrap 5 servido localmente. Regras críticas ficam em serviços de
  domínio (`services.py`) com `transaction.atomic` e `select_for_update`; views e APIs apenas orquestram.
- **Alternativas consideradas:** microsserviços (rejeitado: complexidade operacional sem benefício no MVP);
  SPA React + API (rejeitado: dependência de Node e duplicação de validação sem ganho comprovado).
- **Consequências:** implantação simples (Gunicorn + Nginx + systemd); evolução para Kubernetes/OpenShift
  possível depois, se requisitos reais justificarem. Fronteiras entre módulos mantidas por convenção e testes.
