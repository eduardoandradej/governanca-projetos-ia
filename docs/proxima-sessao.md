# Retomada da próxima sessão

## Identificação oficial do trabalho (usar em toda a documentação)
- Título: **Um modelo integrado de governança e gestão de projetos para implantação de plataformas corporativas de IA**
- Produto/artefato: TrajetórIA — Plataforma Integrada de Governança e Gestão de Projetos de Inteligência Artificial
- Alunos: Eduardo Andrade de Jesus · Matheus Fernandes Cunha · Thais Gonçalves de Alencar
- Orientação: Prof. Dr. Ricardo Kneipp
- IFRJ · Pós-Graduação em Gestão de Projetos e Negócios em TI
- I Mostra de Gestão de Projetos, Governança e Gerenciamento de Serviços de TI · 2026 (eixo: COBIT 2019, PMBOK e ágil)
- Pesquisa: questionário aberto de 04/11/2026 a 11/11/2026; o primeiro envio (04/11, 19:59) foi teste de funcionamento do formulário e não entra na análise; não mencioná-lo como resposta de integrante da equipe.
- Caso dos laudos periciais (S7): sempre anonimizado.

## Ambiente
- PostgreSQL 16 local (`service postgresql start`), banco `govia`, papel `govia` (CREATEDB). Credenciais no `.env` local (não versionado); recrie com `.env.example` + `scripts/setup_db.sh` se o container for novo.
- Python: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.lock`.
- Testes: `./scripts/test.sh`.

## Estado
Ver `docs/status-implementacao.md` (fonte da verdade) e `git log`.

## Estado (2026-11-02)
M0–M8 concluídos no escopo de laboratório; 142 testes verdes. Template v4 (ajustes da pesquisa, rodada 1). Identidade: TrajetórIA. Banco de demonstração local `govia_demo` (pode ser recriado).

## Primeira ação inequívoca da retomada
Executar `./scripts/test.sh`. Se verde, escolher entre as pendências listadas em `docs/status-implementacao.md`
(sugestão de ordem: MFA para perfis privilegiados → integração de antivírus nos anexos → tela de administração de
templates por organização → validação de Nginx/TLS na VM institucional). Para o artigo, partir de
`docs/pesquisa/subsidios-artigo.md` e verificar as referências marcadas "a verificar".
