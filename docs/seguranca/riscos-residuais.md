# Riscos residuais e pendências antes de uso institucional

1. **MFA** para perfis privilegiados não implementado.
2. **Antivírus** de anexos ausente: mitigado por quarentena e inspeção manual; integrar ClamAV ou serviço equivalente.
3. Imutabilidade da auditoria depende do banco (ver `auditoria.md`).
4. Rotina de retenção/anonimização (IP, anexos) documentada, não automatizada.
5. Nginx/TLS/systemd não validados neste laboratório.
6. Sem teste de carga nem avaliação de segurança independente (pentest).
7. Recuperação de senha depende de SMTP institucional (console no desenvolvimento).
8. Interface de administração de templates de ciclo de vida por organização apenas via admin técnico.

Conclusão: **MVP funcional e testado em laboratório; não pronto para produção com dados sensíveis.**
