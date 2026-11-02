# ADR-004 — Eventos de negação gravados após o rollback

- **Status:** aceito (M1, 2026-11-02)
- **Contexto:** os serviços de domínio rodam dentro de `transaction.atomic`. Quando uma autorização é negada,
  o serviço grava um evento `denied` e lança exceção, o que desfazia a transação e **apagava o próprio
  evento de negação**. O defeito foi detectado pelo teste `test_no_self_elevation_even_for_org_admin`.
- **Decisão:** decorador `apps.auditlog.services.atomic_service`. Dentro dele, eventos com resultado
  diferente de `success` são enfileirados e gravados depois que a transação termina (com sucesso ou
  rollback). Eventos de sucesso continuam na mesma transação da alteração, garantindo atomicidade
  dado ↔ auditoria.
- **Consequências:** todo serviço de domínio deve usar `@audit.atomic_service` no lugar de `@transaction.atomic`.
