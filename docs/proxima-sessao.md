# Retomada da próxima sessão

## Ambiente
- PostgreSQL 16 local (`service postgresql start`), banco `govia`, papel `govia` (CREATEDB). Credenciais no `.env` local (não versionado); recrie com `.env.example` + `scripts/setup_db.sh` se o container for novo.
- Python: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.lock`.
- Testes: `./scripts/test.sh`.

## Estado
Ver `docs/status-implementacao.md` (fonte da verdade) e `git log`.

## Estado (2026-11-02)
M0–M8 concluídos no escopo de laboratório; 139 testes verdes. Identidade: BalizaVale. Banco de demonstração local `govia_demo` (pode ser recriado).

## Primeira ação inequívoca da retomada
Executar `./scripts/test.sh`. Se verde, escolher entre as pendências listadas em `docs/status-implementacao.md`
(sugestão de ordem: MFA para perfis privilegiados → integração de antivírus nos anexos → tela de administração de
templates por organização → validação de Nginx/TLS na VM institucional). Para o artigo, partir de
`docs/pesquisa/subsidios-artigo.md` e verificar as referências marcadas "a verificar".
