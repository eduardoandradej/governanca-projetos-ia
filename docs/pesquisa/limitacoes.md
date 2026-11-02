# Limitações

1. Avaliação funcional em laboratório com **dados sintéticos**; sem usuários reais nem organização real.
2. Não mede eficácia organizacional, produtividade ou adoção; não há grupo de comparação.
3. Associações COBIT/PMBOK são interpretação da equipe (exceto as citadas na ISACA 2025 com página); COBIT 2019 Framework
   e PMBOK foram consultados apenas nas partes indicadas em `fontes.md`.
4. Insights vêm de 6 regras determinísticas com limiares arbitrados (parametrizáveis), não de modelos estatísticos.
5. Segurança: sem MFA, antivírus de anexos, pentest nem teste de carga; Nginx/TLS/systemd não validados aqui.
6. Interface avaliada por testes automatizados e roteiro E2E, sem avaliação de usabilidade com usuários.
7. Integrações externas apenas como contratos (NoOp); data lake apenas conceitual.
