# Implantação em VM Ubuntu Server 24.04 (Nginx + Gunicorn + systemd + PostgreSQL 16)

> Situação: procedimento **documentado e parcialmente verificado** em laboratório (container Ubuntu 24.04): `check --deploy`,
> `collectstatic`, Gunicorn com `config.settings.prod`, `healthz`, recusa de Host inválido. Nginx/TLS/systemd **não**
> foram executados neste ambiente e precisam de validação na VM institucional.

1. Pacotes: `sudo apt install -y python3.12 python3.12-venv postgresql-16 nginx`.
2. Usuário e diretórios: `sudo useradd --system --home /opt/govia govia`; `/opt/govia` (código), `/var/lib/govia/{staticfiles,private_media}` (dono `govia`, modo 750), `/etc/govia/govia.env` (modo 600).
3. Código e dependências: clonar em `/opt/govia`; `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.lock`.
4. Banco: `DB_PASSWORD=... ./scripts/setup_db.sh`; em produção remova `CREATEDB` do papel (`ALTER ROLE govia NOCREATEDB`) e revogue `TRUNCATE` na tabela de auditoria.
5. Variáveis (`/etc/govia/govia.env`): `DJANGO_SECRET_KEY` (aleatória, ≥ 50), `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://govia.exemplo.local`, `DB_*`, `PRIVATE_MEDIA_ROOT=/var/lib/govia/private_media`, `DJANGO_STATIC_ROOT=/var/lib/govia/staticfiles`, `DJANGO_EMAIL_BACKEND` (SMTP institucional), `APP_ENVIRONMENT_LABEL` (vazio em produção).
6. `DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py migrate && ... collectstatic --noinput && ... check --deploy`.
7. Conta administrativa técnica: `manage.py createsuperuser` (senha digitada no prompt). Papéis de negócio são concedidos pela tela *Organizações e papéis*.
8. Serviços: copiar `deploy/govia-gunicorn.service` e `deploy/nginx-govia.conf`; `systemctl enable --now govia-gunicorn`; `nginx -t && systemctl reload nginx`.
9. Verificação: `curl -fsS https://govia.exemplo.local/healthz` → `{"status": "ok", "database": "ok"}`.

`check --deploy` (resultado real): apenas o aviso `security.W021` (HSTS preload), mantido desligado de propósito —
a inclusão na lista de preload é praticamente irreversível e deve ser decisão institucional.

**Não usar `seed_demo` em produção.** Não declarar o ambiente pronto para dados sensíveis sem MFA, antivírus de anexos e
avaliação de segurança independente.

**Trilha de auditoria:** o gatilho do PostgreSQL bloqueia `UPDATE`/`DELETE`, mas não `TRUNCATE` nem um superusuário;
por isso revogue `TRUNCATE` do papel da aplicação e não use superusuário na conexão do Django.
