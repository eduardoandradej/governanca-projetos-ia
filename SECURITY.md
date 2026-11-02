# Política de Segurança

Este repositório contém o **Modelo Integrado de Governança e Gestão de Projetos de IA**.
Ele é **privado** e deve conter apenas documentação, políticas e templates — nunca dados reais.

## O que NUNCA deve ser gravado aqui

| Proibido | Exemplos |
|---|---|
| Credenciais e segredos | senhas, tokens de API, chaves privadas, arquivos `.env` |
| Dados pessoais (LGPD) | nomes, CPF, e-mails, telefones, dados de saúde ou financeiros de pessoas |
| Dados de clientes ou contratos | bases de dados, planilhas com informações reais, contratos assinados |
| Modelos treinados | arquivos `.pkl`, `.pt`, `.onnx` etc. |

Templates devem usar apenas **dados fictícios** (ex.: "Projeto Exemplo", "Fulano de Tal").

## Controles adotados

- Repositório **privado**, com acesso apenas a quem precisa.
- `.gitignore` bloqueando credenciais, dados e modelos.
- Verificação automática de segredos (**gitleaks**) em todo *push* e *pull request*.
- `CODEOWNERS` exigindo revisão do responsável.
- Alterações feitas em branches de trabalho e integradas ao `main` via *pull request*.

### Pendências de configuração (fazer no GitHub)

- [ ] Proteger o branch `main` (exigir PR com aprovação, bloquear *force push* e exclusão).
- [ ] Ativar *Secret scanning* e *Push protection* (Settings → Code security), se disponível no plano.
- [ ] Ativar autenticação em dois fatores (2FA) para todos os colaboradores.
- [ ] Revisar periodicamente colaboradores e apps com acesso.

## Se um segredo ou dado for gravado por engano

1. **Revogue/troque imediatamente** a credencial exposta (apagar o commit não basta).
2. Avise o responsável pelo repositório.
3. Remova o conteúdo do histórico (ex.: `git filter-repo`) com apoio do responsável.
4. Se envolver dados pessoais, acione o Encarregado (DPO) para avaliar comunicação à ANPD.

## Como reportar um problema de segurança

Não abra *issue* pública. Entre em contato diretamente com o responsável pelo repositório.
