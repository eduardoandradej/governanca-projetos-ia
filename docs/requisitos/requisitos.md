# Requisitos (resumo) e personas

Requisitos funcionais F01–F09 conforme a especificação (superprompt), implementados nos módulos indicados em
`docs/status-implementacao.md`. Regras de negócio: `regras-negocio.md` (RN-001..RN-037).

**Não funcionais:** PostgreSQL 16; Django 5.2 LTS; pt-BR; America/Sao_Paulo (armazenamento UTC); Decimal para dinheiro;
UUID em URLs; sem CDN; autorização no servidor; auditoria append-only; instalação reprodutível (`requirements.lock`);
testes em PostgreSQL de teste isolado.

**Personas (papéis):** administrador técnico da plataforma; administrador organizacional; gestor de portfólio;
patrocinador; gerente de projeto; executor técnico; segurança/conformidade; aprovador de gate; auditor; leitor.
Matriz de permissões: `docs/seguranca/matriz-rbac.md`.

**Casos de uso principais:** cadastrar projeto (recebe 7 fases); atender e validar requisito; anexar e revisar
evidência; solicitar/aprovar/rejeitar gate; conceder exceção; registrar risco, tratamento e custo; propor e aprovar
decisão; avaliar uso responsável de IA; catalogar ativo e linhagem; consultar indicadores; executar regras, revisar
insight e aprovar lição; consultar e exportar auditoria.

**Critérios de aceite:** `docs/pesquisa/protocolo-avaliacao.md` (C1–C10).
