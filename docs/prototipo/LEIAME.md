# Protótipo navegável (estático)

`nexfase-prototipo.zip` contém uma cópia navegável do NexFase gerada a partir do sistema real rodando com
**dados sintéticos**. Para usar: descompacte e abra `prototipo/index.html` no navegador (não precisa de servidor).

- Perfis: gerente de projeto (62 telas), aprovador de gate (57) e auditor (20); a barra azul troca de perfil.
- Botões e formulários ficam desativados: nada é gravado.
- Para regenerar a partir do banco de demonstração:

```bash
DB_NAME=govia_demo .venv/bin/python manage.py shell -c "exec(open('scripts/export_static_prototype.py').read())"
```

A saída vai para `var/prototipo/` (fora do Git); compacte e substitua o zip desta pasta.
