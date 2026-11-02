"""Gatilho PostgreSQL que rejeita UPDATE/DELETE na trilha de auditoria (append-only).

Limitação: superusuário do PostgreSQL pode desabilitar o gatilho. TRUNCATE (usado pelo flush dos
testes) não é bloqueado por gatilhos de linha; em produção, o usuário da aplicação não deve ter
privilégio de TRUNCATE nesta tabela (ver docs/seguranca/auditoria.md).
"""

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION auditlog_block_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'auditlog_auditevent e append-only: % bloqueado', TG_OP
        USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS auditlog_auditevent_append_only ON auditlog_auditevent;
CREATE TRIGGER auditlog_auditevent_append_only
    BEFORE UPDATE OR DELETE ON auditlog_auditevent
    FOR EACH ROW EXECUTE FUNCTION auditlog_block_mutation();
"""

REVERSE = """
DROP TRIGGER IF EXISTS auditlog_auditevent_append_only ON auditlog_auditevent;
DROP FUNCTION IF EXISTS auditlog_block_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("auditlog", "0001_initial")]

    operations = [migrations.RunSQL(FORWARD, REVERSE)]
