"""Exporta uma cópia navegável ESTÁTICA do NexFase (HTML) a partir do banco de demonstração.

Uso (banco de demonstração, nunca produção):
    DB_NAME=govia_demo .venv/bin/python manage.py shell -c "exec(open('scripts/export_static_prototype.py').read())"

Percorre as telas como alguns perfis demo, reescreve links internos para arquivos locais, desativa formulários
(sem servidor, nada é gravado) e injeta um aviso de protótipo. Saída: var/prototipo/.
"""

import re
import shutil
from collections import deque
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.test.utils import override_settings

OUT = Path(settings.BASE_DIR) / "var" / "prototipo"
PERSONAS = [
    ("gerente", "demo.gerente", "Gerência de Projeto", ["/"], 140),
    ("aprovador", "demo.aprovador", "Aprovação de Gates", ["/gates/", "/"], 90),
    ("auditor", "demo.auditor", "Auditoria", ["/auditoria/", "/"], 20),
]
SKIP = re.compile(r"^/(static|admin-tecnico|api|contas)/|/baixar/|\.csv$|/exportar")
HREF = re.compile(r'(href|action|hx-post)="(/[^"]*)"')

shutil.rmtree(OUT, ignore_errors=True)
(OUT / "static").mkdir(parents=True)
for rel in ("vendor/bootstrap/bootstrap.min.css", "vendor/bootstrap/bootstrap.bundle.min.js", "css/app.css"):
    dst = OUT / "static" / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(settings.BASE_DIR) / "static" / rel, dst)


def fname(path: str) -> str:
    path = path.split("?")[0].split("#")[0]
    if path in ("", "/"):
        return "inicio.html"
    slug = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                  lambda m: m.group(0)[:8], path.strip("/"))
    slug = re.sub(r"[^A-Za-z0-9]+", "-", slug).strip("-").lower()
    return f"{slug[:80]}.html"


BANNER = """
<div id="proto-bar" style="position:sticky;top:0;z-index:2000;background:#0b3d5c;color:#fff;font:13px system-ui,sans-serif;
padding:6px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center">
<strong>Protótipo navegável</strong><span>dados sintéticos · ações desativadas · perfil: {label}</span>
<span style="margin-left:auto;display:flex;gap:8px;flex-wrap:wrap">{switch}<a href="../index.html" style="color:#cfe3f5">sobre o protótipo</a></span>
</div>
<div id="proto-toast" role="status" aria-live="polite" style="display:none;position:fixed;right:16px;bottom:16px;max-width:360px;
z-index:2001;background:#1f2d3d;color:#fff;padding:12px 14px;border-radius:8px;font:13px system-ui,sans-serif;box-shadow:0 4px 16px rgba(0,0,0,.25)"></div>
<script>
(function(){{
 var t=document.getElementById('proto-toast');
 function say(m){{t.textContent=m;t.style.display='block';clearTimeout(say.h);say.h=setTimeout(function(){{t.style.display='none'}},4200);}}
 document.addEventListener('submit',function(e){{e.preventDefault();
   say('Protótipo estático: nada é gravado. No NexFase instalado, esta ação seria validada no servidor e registrada na auditoria.');}},true);
 document.addEventListener('click',function(e){{var a=e.target.closest('a[data-proto-off]');
   if(a){{e.preventDefault();say('Esta tela não faz parte do protótipo (download, exportação ou área técnica).');}}}},true);
 document.querySelectorAll('[hx-post]').forEach(function(el){{el.removeAttribute('hx-post');}});
}})();
</script>
"""

pages = {}  # persona -> {path: html}
User = get_user_model()
with override_settings(ALLOWED_HOSTS=["*"], DEBUG=False):
    for key, username, _label, starts, limit in PERSONAS:
        client = Client(raise_request_exception=False)
        client.force_login(User.objects.get(username=username))
        seen, queue, got = set(), deque(starts), {}
        while queue and len(got) < limit:
            path = queue.popleft().split("?")[0].split("#")[0] or "/"
            if path in seen or SKIP.search(path):
                continue
            seen.add(path)
            resp = client.get(path)
            if resp.status_code != 200 or "text/html" not in resp.get("Content-Type", ""):
                continue
            html = resp.content.decode()
            got[path] = html
            for _, link in HREF.findall(html):
                link = link.split("?")[0].split("#")[0]
                if link not in seen and not SKIP.search(link) and "/sair/" not in link:
                    queue.append(link)
        pages[key] = got
        print(f"{key}: {len(got)} páginas")

for key, _username, label, _starts, _ in PERSONAS:
    got = pages[key]
    folder = OUT / key
    folder.mkdir(parents=True)
    for path, html in got.items():
        def rewrite(m, got=got):
            attr, link = m.group(1), m.group(2)
            if link.startswith("/static/"):
                return f'{attr}="../static/{link[len("/static/"):]}"'
            base = link.split("?")[0].split("#")[0] or "/"
            if attr != "href":
                return f'{attr}="#"'
            if base in got:
                return f'href="{fname(base)}"'
            return 'href="#" data-proto-off="1"'
        out = HREF.sub(rewrite, html)
        out = re.sub(r'<script src="/static/vendor/htmx/htmx.min.js"></script>', "", out)
        out = re.sub(r'<script src="\.\./static/vendor/htmx/htmx.min.js"></script>', "", out)
        out = re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', 'name="csrfmiddlewaretoken" value=""', out)
        out = re.sub(r'hx-headers=\'\{[^\']*\}\'', "", out)
        switch = " ".join(
            f'<a href="../{k}/{fname(path)}" style="color:#fff;{"font-weight:700;text-decoration:underline" if k == key else "opacity:.85"}">{lbl}</a>'
            for k, _, lbl, _, _ in PERSONAS if path in pages[k]
        )
        out = out.replace("<body", "<body data-proto=\"1\"", 1)
        out = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + BANNER.format(label=label, switch=switch), out, count=1)
        (folder / fname(path)).write_text(out, encoding="utf-8")

total = sum(1 for _ in OUT.rglob("*") if _.is_file())
size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
print(f"arquivos: {total}, tamanho: {size/1e6:.1f} MB")
