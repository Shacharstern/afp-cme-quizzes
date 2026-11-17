// Playwright test of the spaced-repetition store. Run from a folder holding test.html (the built app): node test-srs.js
const { chromium } = require('playwright'); const fs = require('fs');
const packs = ['vte', 'af'].map(id => JSON.parse(fs.readFileSync('/home/user/afp-cme-quizzes/shlav-b/packs/' + id + '.json', 'utf8')));
const U = 'file://' + process.cwd() + '/test.html';
const day0 = new Date('2026-12-01T09:00:00');
const plus = n => new Date(day0.getTime() + n * 86400000);
let ok = 0, bad = 0; const check = (name, cond, extra) => { if (cond) ok++; else bad++; console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra !== undefined ? ' · ' + JSON.stringify(extra) : '')); };
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1100, height: 900 } }); const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.clock.install({ time: day0 });
  const load = async (hash) => { await pg.goto(U + (hash || '#today')); await pg.reload(); await pg.waitForTimeout(200); await pg.evaluate(ps => { ps.forEach(p => PACKS[p.id] = p); render(); }, packs); await pg.waitForTimeout(100); };
  // migration of the old oral repetition
  await pg.goto(U); await pg.evaluate(() => { localStorage.setItem('shlavb-v1', JSON.stringify({ v: 1, examDate: '2027-06-01', topics: {}, log: [], packs: { vte: { box: {}, proc: {}, cases: {}, oral: {}, sr: { 'vo1a#2': { q: 'vo1a', i: 2, streak: 1, due: Date.now() } }, srDone: 0 } }, xp: 0 })); });
  await load();
  check('migration: old oral point moved', await pg.evaluate(() => JSON.stringify(SRS.st().c['o|vte|vo1a|2'])) !== undefined && await pg.evaluate(() => !!SRS.st().c['o|vte|vo1a|2'] && SRS.st().c['o|vte|vo1a|2'][0] === 2));
  // grading rules
  const r = await pg.evaluate(() => { const n = SRS.dayN(); const a = SRS.grade('d|vte|d3', 'right'), w = SRS.grade('d|vte|d4', 'wrong'), c = SRS.grade('c|vte|c1|0', 'right'), o = SRS.grade('o|vte|vo1a|0', 'wrong'), cl = SRS.grade('d|vte|d10', 'close');
    save(); return { n, a: [a.box, a.iv], w: [w.box, w.iv], c: [c.box, c.iv], o: [o.box, o.iv], cl: [cl.box, cl.iv] }; });
  check('first right → box 2, 3 days', r.a[0] === 2 && r.a[1] === 3, r.a);
  check('first wrong → box 1, tomorrow', r.w[0] === 1 && r.w[1] === 1, r.w);
  check('case decision right → box 2', r.c[0] === 2, r.c);
  check('close on new → box 1', r.cl[0] === 1, r.cl);
  check('day 0: only the migrated oral point is due', await pg.evaluate(() => SRS.counts(null).all) === 1);
  // a day later
  await pg.clock.setFixedTime(plus(1)); await load();
  const due1 = await pg.evaluate(() => SRS.counts(null));
  check('day 1: wrong drill, close drill and missed oral point are due', due1.d === 2 && due1.o === 2 && due1.c === 0, due1);
  await pg.screenshot({ path: 'srs-today.png', fullPage: false });
  const plan = await pg.evaluate(() => { const p = SRS.plan(null); return { due: p.due.length, fresh: p.fresh.length }; });
  check('plan adds new drills from started topics (cap 20)', plan.due === 4 && plan.fresh === 20, plan);
  await pg.evaluate(() => { SRS.st().cfg.newCap = 0; save(); });
  // run the daily review through the UI
  await pg.evaluate(() => runDaily(null)); await pg.waitForTimeout(200);
  let steps = 0;
  while (steps++ < 12) {
    const kind = await pg.evaluate(() => { const g = document.querySelector('.gm'); if (!g) return 'none'; if (g.querySelector('.screen.res')) return 'end'; if (g.querySelector('.judge')) return 'judge'; if ([...g.querySelectorAll('button')].some(b => b.textContent === 'סיימתי לענות')) return 'oral';
      if (g.querySelector('.next.nx')) return 'next'; if (g.querySelector('.opts .opt:not([disabled])')) return 'pick'; if (g.querySelector('.dial,.lock,button.lock')) return 'dial'; return 'other'; });
    if (kind === 'end' || kind === 'none') break;
    if (kind === 'oral') await pg.click('text=סיימתי לענות');
    else if (kind === 'judge') await pg.click('.judge .y');
    else if (kind === 'next') await pg.click('.next.nx');
    else if (kind === 'pick') { // answer correctly: find the drill's right option
      await pg.evaluate(() => { const q = document.querySelector('.gm .q').textContent; const all = Object.values(PACKS).flatMap(p => (p.drills || []).map(d => d)); const d = all.find(x => x.q === q);
        const btns = [...document.querySelectorAll('.gm .opts .opt')]; if (d && d.k === 'pick') { const b = btns.find(b => b.textContent.slice(1) === d.o[d.a]); (b || btns[0]).click(); } else if (d && d.k === 'swipe') { btns[d.a].click(); } else btns[0].click(); });
    } else { await pg.screenshot({ path: 'srs-other.png' }); console.log('state', kind); await pg.evaluate(() => { const b = document.querySelector('.gm .opts .opt, .gm button.lock, .gm .gbtn'); if (b) b.click(); }); }
    await pg.waitForTimeout(150);
  }
  await pg.screenshot({ path: 'srs-end.png' });
  const after = await pg.evaluate(() => ({ d4: SRS.st().c['d|vte|d4'], o: SRS.st().c['o|vte|vo1a|0'], done: SRS.st().day.done, n: SRS.dayN() }));
  check('after review: wrong drill answered right → box 2, due in 3 days', after.d4[0] === 2 && after.d4[1] === after.n + 3, after.d4);
  check('after review: oral point said → box 2', after.o[0] === 2, after.o);
  check('daily counter counts answered cards', after.done === 4, after.done);
  // exam compression
  const ex = await pg.evaluate(() => { S.examDate = addDays(today(), 10); SRS.st().c['d|af|x1'] = [4, SRS.dayN(), 0]; const g = SRS.grade('d|af|x1', 'right'); S.examDate = addDays(today(), 200); const g2 = SRS.grade('d|af|x2', 'right'); SRS.st().c['d|af|x3'] = [4, SRS.dayN(), 0]; const g3 = SRS.grade('d|af|x3', 'right'); return [g.box, g.iv, g3.box, g3.iv]; });
  check('exam in 10 days: box 5 waits 3 days instead of 35', ex[0] === 5 && ex[1] === 3, ex);
  check('exam far away: box 5 waits 35 days', ex[2] === 5 && ex[3] === 35, ex);
  // topic status follows the cards
  const stt = await pg.evaluate(() => ({ s: T('vte').s, next: T('vte').next }));
  check('topic status and next review date set from cards', stt.s >= 1 && !!stt.next, stt);
  // game home and topic card render
  await load('#t-vte'); await pg.screenshot({ path: 'srs-topic.png', fullPage: true });
  await pg.click('.mode.game'); await pg.waitForTimeout(300); await pg.screenshot({ path: 'srs-game.png' });
  console.log(errs.join('\n') || 'no page errors'); console.log(ok + ' passed, ' + bad + ' failed'); await b.close();
})();
