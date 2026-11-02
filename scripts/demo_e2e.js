const { chromium } = require('playwright');
const fs = require('fs');
const pw = fs.readFileSync(process.argv[2], 'utf8').trim();
const OUT = process.argv[3];
const BASE = 'http://127.0.0.1:8000';
const log = [];
const step = (m) => { log.push(m); console.log(m); };
(async () => {
  const browser = await chromium.launch();
  async function as(user) {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
    const page = await ctx.newPage();
    await page.goto(BASE + '/contas/entrar/');
    await page.fill('#id_username', user); await page.fill('#id_password', pw);
    await Promise.all([page.waitForNavigation(), page.click('button[type=submit]')]);
    return page;
  }
  const shot = (page, name) => page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  const alertText = async (page) => (await page.locator('#mensagens .alert').allInnerTexts()).join(' | ').replace(/\s+/g, ' ').slice(0, 400);

  // 1. Projeto em fase inicial
  let g = await as('demo.gerente');
  await g.goto(BASE + '/projetos/'); await g.click('text=IA-2026-01'); await g.waitForLoadState();
  const projUrl = g.url(); await shot(g, '01-projeto-fase-inicial');
  await g.click('.stage-box >> nth=0'); await g.waitForLoadState();
  const stageUrl = g.url();
  step('1. Projeto IA-2026-01 aberto na fase 1: ' + (await g.locator('h1').innerText()));

  // 2. Pendência e recusa do gate
  await g.click('button:has-text("Solicitar passagem")'); await g.waitForLoadState();
  step('2. Solicitação de gate recusada: ' + (await alertText(g)));
  await shot(g, '02-gate-recusado');

  // 3. Evidência: revisão pelo aprovador (enviada pelo técnico, inspecionada pela segurança no seed)
  const ap = await as('demo.aprovador');
  await ap.goto(stageUrl); await ap.click('text=Caso de negócio v1 (sintético)'); await ap.waitForLoadState();
  await ap.fill('textarea[name=comment]', 'Caso de negócio completo e coerente com os objetivos.');
  await ap.click('button[name=decision][value=approved]'); await ap.waitForLoadState();
  step('3. Evidência revisada pelo aprovador: ' + (await alertText(ap)));
  await shot(ap, '03-evidencia-aprovada');

  // Requisitos: gerente registra atendimento; segurança valida (segregação)
  await g.goto(stageUrl);
  for (const code of ['F1-R1', 'F1-R3', 'F1-R4', 'F1-R5', 'F1-R6']) {
    const item = g.locator(`.list-group-item:has-text("${code}")`).first();
    await item.locator('input[name=note]').fill(`Atendimento de ${code} registrado com referência ao termo de abertura.`);
    await item.locator('button:has-text("Registrar atendimento")').click(); await g.waitForLoadState();
  }
  const sec = await as('demo.seguranca');
  await sec.goto(stageUrl);
  for (const code of ['F1-R1', 'F1-R3', 'F1-R4', 'F1-R5', 'F1-R6']) {
    const item = sec.locator(`.list-group-item:has-text("${code}")`).first();
    await item.locator('input[name=comment]').fill('Conferido.');
    await item.locator('button[name=decision][value=approved]').click(); await sec.waitForLoadState();
  }
  step('3b. Requisitos atendidos pelo gerente e validados pela segurança: ' + (await sec.locator('text=Requisitos obrigatórios validados').locator('..').innerText()).replace(/\s+/g, ' '));

  // 4. Gate ainda bloqueado pelo risco crítico → tratamento
  await g.goto(stageUrl); await g.click('button:has-text("Solicitar passagem")'); await g.waitForLoadState();
  step('4a. Gate bloqueado pelo risco crítico: ' + (await alertText(g)));
  await g.goto(projUrl + 'riscos/'); await shot(g, '04-matriz-riscos');
  await g.click('a:has-text("R-001")'); await g.waitForLoadState();
  await g.selectOption('#t-s', 'mitigate');
  await g.fill('#t-d', 'Anonimização das bases e controle de acesso por papel antes do treinamento.');
  await g.selectOption('#t-o', { label: 'Segurança e Conformidade Demo' });
  await g.fill('#t-p', new Date(Date.now() + 15 * 864e5).toISOString().slice(0, 10));
  await g.click('button:has-text("Registrar tratamento")'); await g.waitForLoadState();
  step('4b. Tratamento do risco crítico registrado: ' + (await alertText(g)));

  // 5. Aprovação por pessoa distinta
  await g.goto(stageUrl); await g.click('button:has-text("Solicitar passagem")'); await g.waitForLoadState();
  step('5a. Passagem solicitada: ' + (await alertText(g)));
  await ap.goto(BASE + '/gates/'); await shot(ap, '05-fila-aprovador');
  await ap.goto(stageUrl); await ap.fill('#gjust', 'Critérios da fase 1 atendidos; risco crítico com tratamento.');
  await ap.click('button:has-text("Aprovar")'); await ap.waitForLoadState();
  step('5b. Gate aprovado pelo aprovador: ' + (await alertText(ap)));
  await shot(ap, '05-gate-aprovado');
  await g.goto(projUrl); step('5c. Linha do tempo: ' + (await g.locator('.stage-timeline').innerText()).replace(/\s+/g, ' ').slice(0, 200));

  // 6. Custos e cronograma
  const sp = await as('demo.patrocinio');
  await sp.goto(projUrl + 'custos/'); await shot(sp, '06-custos');
  step('6. Custos: ' + (await sp.locator('.kpi').allInnerTexts()).join(' | ').replace(/\s+/g, ' '));

  // 7. KPI do PostgreSQL
  await g.goto(BASE + '/'); await shot(g, '07-visao-geral-kpis');
  await g.goto(BASE + '/inteligencia/indicadores/K02/'); await shot(g, '07-ficha-k02');
  step('7. K02: ' + (await g.locator('.kpi').first().innerText()).replace(/\s+/g, ' '));

  // 8. Insight explicável → revisão → aprovação → lição aprovada
  await g.goto(BASE + '/inteligencia/insights/'); await g.click('a:has-text("riscos altos/críticos")'); await g.waitForLoadState();
  const insightUrl = g.url(); await shot(g, '08-insight-proposto');
  step('8a. Insight: ' + (await g.locator('.card p').first().innerText()).slice(0, 200));
  await g.fill('textarea[name=note]', 'Confirmado: havia dois riscos sem plano de resposta na fase 1.');
  await g.click('button:has-text("Registrar revisão")'); await g.waitForLoadState();
  await sp.goto(insightUrl); await sp.fill('form[action$="aprovar/"] textarea[name=note]', 'Recomendação: exigir plano de resposta ao registrar risco alto.');
  await sp.click('button:has-text("Aprovar")'); await sp.waitForLoadState();
  step('8b. Insight aprovado pelo patrocinador: ' + (await alertText(sp)));
  await g.goto(insightUrl);
  await g.fill('form[action$="licao/"] input[name=title]', 'Plano de resposta obrigatório para riscos altos');
  await g.fill('form[action$="licao/"] textarea[name=lesson]', 'Riscos altos sem resposta atrasaram o gate da fase 1.');
  await g.fill('form[action$="licao/"] textarea[name=recommendation]', 'Registrar tratamento junto com o risco alto.');
  await g.click('button:has-text("Registrar lição")'); await g.waitForLoadState();
  const pf = await as('demo.portfolio');
  await pf.goto(projUrl + 'conhecimento/');
  await pf.fill('input[name=disclosure_justification]', 'Lição anonimizada, sem dados do projeto, autorizada para reuso.');
  await pf.selectOption('select[name=visibility]', 'organization');
  await pf.click('button:has-text("Aprovar lição")'); await pf.waitForLoadState();
  step('8c. Lição aprovada: ' + (await alertText(pf)));
  await pf.goto(BASE + '/inteligencia/licoes/'); await shot(pf, '08-licao-aprovada');

  // 9. Auditoria
  const au = await as('demo.auditor');
  await au.goto(BASE + '/auditoria/?acao=gate'); await shot(au, '09-auditoria');
  step('9. Eventos de gate na auditoria: ' + (await au.locator('tbody tr').count()));

  // 10. Exportação gerencial
  const [dl] = await Promise.all([g.waitForEvent('download'), g.goto(BASE + '/inteligencia/exportar/projetos.csv').catch(() => {})]);
  const p = await dl.path(); const csv = fs.readFileSync(p, 'utf8');
  fs.writeFileSync(`${OUT}/10-exportacao-projetos.csv`, csv);
  step('10. CSV exportado: ' + csv.split('\n').length + ' linhas; cabeçalho: ' + csv.split('\n')[0].slice(0, 120));

  // Isolamento
  const beta = await as('demo.beta.gerente');
  const r = await beta.goto(projUrl);
  step('Isolamento: usuário da Beta acessando projeto da Alfa → HTTP ' + r.status());
  fs.writeFileSync(`${OUT}/roteiro-log.txt`, log.join('\n') + '\n');
  await browser.close();
})().catch(e => { console.error('FALHA:', e.message); fs.writeFileSync(`${OUT}/roteiro-log.txt`, log.join('\n') + '\nFALHA: ' + e.message + '\n'); process.exit(1); });
