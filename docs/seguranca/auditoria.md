# Trilha de auditoria

- Eventos: autenticação (sucesso, falha, bloqueio, logout), negações de permissão, criação/edição/status de projeto,
  transições de fase, solicitações/aprovações/rejeições/cancelamentos/revalidações de gate, exceções e ciência,
  atendimento/validação de requisitos, upload/nova versão/inspeção/revisão/download/arquivamento de evidência,
  riscos/tratamentos/aceite residual, custos, decisões, ações, ativos e linhagem, snapshots, insights, lições,
  uso responsável de IA, exportações e concessão/revogação de papéis.
- Campos: UUID, instante UTC, ator (ou sistema/anônimo), organização, projeto, ação, entidade, id, versão, antes/depois
  sanitizados, IP (`REMOTE_ADDR`), correlation_id, resultado, justificativa.
- Integridade: `save()` de evento existente e `delete()` bloqueados; gatilho `BEFORE UPDATE OR DELETE` no PostgreSQL.
  Negações dentro de transações são gravadas após o rollback (ADR-004).
- **Limitação**: superusuário do PostgreSQL pode desabilitar o gatilho; `TRUNCATE` não é bloqueado por gatilho de linha
  (revogar o privilégio em produção). Inviolabilidade forte exige envio a armazenamento externo imutável (WORM/SIEM).
- Retenção proposta: 5 anos para eventos de governança; IP pode ser anonimizado após 12 meses (rotina a implementar).
