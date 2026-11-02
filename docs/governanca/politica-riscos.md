# Política de classificação de riscos (padrão do MVP)

- Escalas: probabilidade 1–5 e impacto 1–5; pontuação = P × I (1–25), calculada no servidor.
- Limiares padrão: **crítico ≥ 20**, **alto ≥ 12**, **médio ≥ 6**, baixo < 6. Configuráveis por organização
  (`RiskPolicy`, com restrição de ordem no banco). São uma convenção do projeto e **não** afirmam alinhamento automático
  a ISO 31000, COBIT ou NIST.
- Categorias operacionais: dados, privacidade, segurança, GPU/capacidade, fornecedor, integração, custo, prazo,
  qualidade, operação, ética.
- Categoria de risco de IA (opcional), conforme ISACA (2025), *Leveraging COBIT for Effective AI System Governance*,
  fig. 5, p. 16: uso ético; política e governança; tecnologia e infraestrutura; operacional e organizacional;
  emergente e estratégico.
- **Risco crítico não tratado** (bloqueia gate quando a fase está configurada para isso): nível crítico, status
  diferente de aceito/encerrado e sem tratamento planejado, em execução ou concluído.
- Aceite de risco residual: somente patrocinador, com justificativa, registrado na auditoria.
