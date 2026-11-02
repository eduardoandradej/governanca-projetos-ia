# Backup, restauração e verificação

- Backup: `./scripts/backup.sh /destino` → `govia-<UTC>.dump` (pg_dump formato custom), `anexos-<UTC>.tar.gz`
  (PRIVATE_MEDIA_ROOT, se existir) e `SHA256SUMS-<UTC>`.
- Verificação: `./scripts/restore_check.sh /destino/govia-<UTC>.dump` restaura em banco **temporário**, compara contagens
  de 7 tabelas críticas com a origem e confirma o gatilho append-only; o banco temporário é removido ao final. Nunca
  sobrescreve o banco da aplicação.
- Restauração real (desastre): parar o serviço; `createdb govia_novo`; `pg_restore -d govia_novo --no-owner arquivo.dump`;
  extrair anexos para PRIVATE_MEDIA_ROOT; validar com `restore_check.sh`; apontar `DB_NAME` e reiniciar.

Execução real em 2026-11-02 (laboratório): backup gerado e restaurado; todas as contagens conferiram (`OK`) e o
gatilho foi restaurado (`1`). Recomenda-se agendar backup diário e testar a restauração ao menos mensalmente; um backup
não testado não deve ser considerado válido.
