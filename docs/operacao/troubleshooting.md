# Solução de problemas

| Sintoma | Verificação |
|---|---|
| `healthz` retorna 503 `database: error` | `systemctl status postgresql`; credenciais `DB_*`; logs do Gunicorn (`journalctl -u govia-gunicorn`) |
| 400 Bad Request | Host fora de `DJANGO_ALLOWED_HOSTS` |
| 403 CSRF em formulários | `DJANGO_CSRF_TRUSTED_ORIGINS` com esquema https; proxy enviando `X-Forwarded-Proto` |
| Usuário bloqueado no login | Aguardar a janela (`LOGIN_THROTTLE_WINDOW_MINUTES`) ou registrar login bem-sucedido; ver eventos `auth.login_blocked` |
| Anexo não baixa | Versão em quarentena: inspeção por segurança/conformidade na página da evidência |
| Gate não avança | Painel da fase lista os bloqueios exatos (requisito, evidência, risco crítico, revalidação, uso responsável de IA) |
| Correlacionar erro | Cabeçalho `X-Request-ID` da resposta = `correlation_id` nos logs e na auditoria |
| Site sem formatação (CSS não carrega) | `curl -sI https://<dominio>/static/css/app.css`: 403 = permissão (`sudo chmod 755 /var/lib/govia && sudo chmod -R o+rX /var/lib/govia/staticfiles`); 404 = refazer `collectstatic` e conferir o `alias` no Nginx |
| `password authentication failed` / `no password supplied` | Senha do banco diferente no PostgreSQL e no `govia.env`, ou com caractere especial (`&`, `$`, `!`, aspas): use só letras, números, `-`, `_`, `.` |
