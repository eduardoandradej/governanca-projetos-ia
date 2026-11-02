# -*- coding: utf-8 -*-
"""Gera o artigo .docx a partir do template do evento, preservando cabeçalho do evento, rodapé e tabelas."""

import copy
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import conteudo as C

TEMPLATE, SAIDA = sys.argv[1], sys.argv[2]
BLACK = RGBColor(0, 0, 0)

doc = Document(TEMPLATE)

# Página A4 e margens ABNT (orientações do próprio template: sup./esq. 3 cm; inf./dir. 2 cm)
for s in doc.sections:
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.top_margin, s.left_margin, s.bottom_margin, s.right_margin = Cm(3), Cm(3), Cm(2), Cm(2)

# Títulos em Arial 11, negrito, cor preta
for name in ("Heading 1", "Heading 2"):
    st = doc.styles[name]
    st.font.name = "Arial"
    st.font.size = Pt(11)
    st.font.bold = True
    st.font.color.rgb = BLACK
    st.paragraph_format.space_before = Pt(12 if name == "Heading 1" else 6)
    st.paragraph_format.space_after = Pt(2)
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for att in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(att), "Arial")
    for att in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        rfonts.attrib.pop(qn(att), None)
doc.styles["Normal"].font.size = Pt(11)

body = doc.element.body
paras = list(doc.paragraphs)
tables = [copy.deepcopy(t._tbl) for t in doc.tables]
keep = {id(p._p) for p in paras[:4]}
for child in list(body):
    if child.tag == qn("w:sectPr") or id(child) in keep:
        continue
    body.remove(child)

TOKEN = re.compile(r"(\*\*.+?\*\*|(?<![\w/.@-])_[^_]+?_(?![\w]))")


def add_runs(p, text, size=None, bold=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        b, i = bold, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("_") and part.endswith("_") and len(part) > 2:
            part, i = part[1:-1], True
        r = p.add_run(part)
        r.bold, r.italic = b, i
        r.font.color.rgb = BLACK
        r.font.name = "Arial"
        if size:
            r.font.size = Pt(size)
    return p


def para(text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, bold=False, spacing=None, after=None):
    p = doc.add_paragraph(style="Normal")
    p.alignment = align
    pf = p.paragraph_format
    if indent:
        pf.first_line_indent = Cm(1.25)
    if spacing is not None:
        pf.line_spacing = spacing
    if after is not None:
        pf.space_after = Pt(after)
    return add_runs(p, text, size=size, bold=bold)


def h1(text):
    p = doc.add_paragraph(text, style="Heading 1")
    return p


def h2(text):
    return doc.add_paragraph(text, style="Heading 2")


def set_widths(t, widths_cm):
    from docx.oxml import OxmlElement

    tbl = t._tbl
    tblPr = tbl.tblPr
    w = tblPr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        tblPr.append(w)
    w.set(qn("w:w"), str(int(sum(widths_cm) * 567)))
    w.set(qn("w:type"), "dxa")
    grid = tbl.tblGrid
    for gc, wc in zip(grid.findall(qn("w:gridCol")), widths_cm, strict=False):
        gc.set(qn("w:w"), str(int(wc * 567)))
    for row in t.rows:
        trPr = row._tr.trPr
        if trPr is not None:
            for h in trPr.findall(qn("w:trHeight")):
                trPr.remove(h)
        for c, wc in zip(row.cells, widths_cm, strict=False):
            c.width = Cm(wc)


def put_table(tbl_xml, rows, header=None, widths=None):
    body.sectPr.addprevious(tbl_xml)
    from docx.table import Table

    t = Table(tbl_xml, doc._body)
    if header:
        for c, txt in zip(t.rows[0].cells, header, strict=True):
            set_cell(c, txt, bold=True)
    while len(t.rows) - 1 < len(rows):
        t._tbl.append(copy.deepcopy(t.rows[-1]._tr))
    while len(t.rows) - 1 > len(rows):
        t._tbl.remove(t.rows[-1]._tr)
    for r, values in zip(t.rows[1:], rows, strict=True):
        for c, txt in zip(r.cells, values, strict=True):
            set_cell(c, txt)
    if widths:
        set_widths(t, widths)
    for r in t.rows[:1]:
        for c in r.cells:
            for p in c.paragraphs:
                for run in p.runs:
                    run.bold = True
    return t


def set_cell(cell, text, bold=False):
    for p in cell.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    p = cell.paragraphs[0]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(0)
    add_runs(p, text, size=9, bold=bold)


def caption(text):
    p = para(text, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, size=10, bold=True, spacing=1.0, after=3)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True


def fonte():
    para(C.FONTE, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=10, spacing=1.0, after=8)


# ---------------------------------------------------------------------------------------------- Pré-textuais
h1("TÍTULO DO TRABALHO")
para(C.TITULO, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
h1("IDENTIFICAÇÃO DOS AUTORES")
for a in C.AUTORES:
    para(a, indent=False, align=WD_ALIGN_PARAGRAPH.RIGHT, size=9, spacing=1.15, after=0)
h1("EIXO TEMÁTICO")
para(C.EIXO, indent=False)
h1("MODALIDADE")
para(C.MODALIDADE, indent=False)
h1("RESUMO")
para(C.RESUMO, indent=False, spacing=1.0)
h2("PALAVRAS-CHAVE")
para(C.PALAVRAS_CHAVE, indent=False)

# ---------------------------------------------------------------------------------------------- Textuais
h1("1 INTRODUÇÃO")
for t in C.INTRODUCAO:
    para(t)
h1("2 PROBLEMA DE PESQUISA OU DESAFIO ORGANIZACIONAL")
for t in C.PROBLEMA:
    para(t)
h1("3 OBJETIVOS")
h2("3.1 Objetivo geral")
para(C.OBJETIVO_GERAL)
h2("3.2 Objetivos específicos")
for i, t in enumerate(C.OBJETIVOS_ESPECIFICOS, 1):
    para(f"{i}. {t}", indent=False)
h1("4 FUNDAMENTAÇÃO TEÓRICA E/OU REFERENCIAL PROFISSIONAL")
if C.FUNDAMENTACAO_INTRO:
    para(C.FUNDAMENTACAO_INTRO)
h2("4.1 Gestão de Projetos")
for t in C.GESTAO_PROJETOS:
    para(t)
h2("4.2 Gerenciamento de Serviços de TI")
for t in C.SERVICOS_TI:
    para(t)
h2("4.3 Governança de TI")
for t in C.GOVERNANCA_TI:
    para(t)
h1("5 METODOLOGIA")
h2("5.1 Natureza")
para(C.NATUREZA)
h2("5.2 Abordagem")
para(C.ABORDAGEM)
h2("5.3 Procedimentos")
para(C.PROCEDIMENTOS)
h2("5.4 Contexto, participantes e período")
para(C.CONTEXTO)
h2("5.5 Instrumentos e fontes de dados")
para(C.INSTRUMENTOS)
h2("5.6 Procedimentos de análise")
para(C.ANALISE)
h1("6 DESENVOLVIMENTO")
h2("6.1 Contexto organizacional")
para(C.CONTEXTO_ORG)
h2("6.2 Diagnóstico do problema ou oportunidade")
para(C.DIAGNOSTICO)
h2("6.3 Solução, intervenção ou abordagem adotada")
for t in C.SOLUCAO:
    para(t)
h2("6.4 Aplicação dos referenciais")
para(C.APLICACAO_REF)
caption(C.QUADRO1_TITULO)
put_table(tables[0], [(d, r, a) for d, r, a in C.QUADRO1], widths=[3.0, 3.6, 9.4])
fonte()
h1("7 RESULTADOS")
para(C.RESULTADOS)
h2("7.1 Indicadores e evidências")
caption(C.QUADRO2_TITULO)
put_table(tables[1], C.QUADRO2, header=C.QUADRO2_CABECALHO, widths=[3.4, 4.6, 5.8, 2.2])
fonte()
h1("8 DISCUSSÃO")
for t in C.DISCUSSAO:
    para(t)
h2("8.1 Contribuição acadêmica")
para(C.CONTRIB_ACAD)
h2("8.2 Contribuição profissional e para o mercado")
para(C.CONTRIB_PROF)
h1("9 CONSIDERAÇÕES FINAIS")
para(C.CONSIDERACOES)
h2("9.1 Limitações")
para(C.LIMITACOES)
h2("9.2 Trabalhos futuros")
para(C.TRABALHOS_FUTUROS)

# ---------------------------------------------------------------------------------------------- Referências
h1("REFERÊNCIAS")
for ref in C.REFERENCIAS:
    para(ref, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.0, after=10)

# Cor preta em todo o documento (inclusive cabeçalho do evento, tabelas e rodapé)
def blacken(paragraphs):
    for p in paragraphs:
        for r in p.runs:
            r.font.color.rgb = BLACK


blacken(doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            blacken(c.paragraphs)
for s in doc.sections:
    blacken(s.footer.paragraphs)
    blacken(s.header.paragraphs)

doc.save(SAIDA)
print("ok", SAIDA)
