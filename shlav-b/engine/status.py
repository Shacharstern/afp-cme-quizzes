#!/usr/bin/env python3
"""Status of every Shlav B topic in the pipeline, and stamps that record a finished step.

  python3 shlav-b/engine/status.py                  # JSON for all topics with any work (the pane reads this)
  python3 shlav-b/engine/status.py ed               # one topic, readable
  python3 shlav-b/engine/status.py --stamp ed visual|narr|podcast|upload|sources|app

Most checks compare a fingerprint of what exists now with the fingerprint stamped when a step was done, so an edit
after the step (reel text changed after recording, pack changed after upload) shows as stale instead of done.
Stamps live in shlav-b/status/<topic>.json, together with what cannot be read from files: the sources the user
confirmed and the source sweep (every Drive file the topic's keywords hit, each with a verdict).
Long jobs report live progress by writing lines to /tmp/shlav-b-jobs/<topic>-<step>.log.
"""
import hashlib, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
JOBS = '/tmp/shlav-b-jobs'
P = lambda *a: os.path.join(ROOT, *a)


def load(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default


def fp(obj):
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def reel_fp(pack):
    ch = [{k: v for k, v in c.items() if k != 'narr'} for c in (pack.get('reel') or {}).get('chapters', [])]
    return fp(ch)


def pack_fp(pack):
    return fp(pack)


def narr_fp(narr, cid):
    return fp((narr or {}).get('chapters', {}).get(cid))


def manifest(tid):
    return load(P('status', tid + '.json'), {}) or {}


def save_manifest(tid, m):
    os.makedirs(P('status'), exist_ok=True)
    json.dump(m, open(P('status', tid + '.json'), 'w'), ensure_ascii=False, indent=1)


def stamp(tid, what):
    m = manifest(tid)
    pack = load(P('packs', tid + '.json'), {})
    now = time.strftime('%Y-%m-%dT%H:%M:%S')
    st = m.setdefault('stamps', {})
    if what == 'visual':
        st['visual'] = {'at': now, 'fp': reel_fp(pack)}
    elif what == 'narr':
        narr = load(P('narration', tid + '.json'), {})
        st['narr'] = {'at': now, 'chapters': {c['id']: narr_fp(narr, c['id']) for c in pack['reel']['chapters']}}
    elif what == 'podcast':
        st['podcast'] = {'at': now, 'fp': fp(load(P('podcast', tid + '.json')))}
    elif what == 'upload':
        st['upload'] = {'at': now, 'fp': pack_fp(pack)}
    elif what == 'sources':
        m.setdefault('sources', {})['confirmedAt'] = now
    elif what == 'app':
        g = load(P('status', '_app.json'), {}) or {}
        g['published'] = {'at': now, 'fp': app_fp()}
        json.dump(g, open(P('status', '_app.json'), 'w'), indent=1)
        return
    else:
        sys.exit('unknown stamp ' + what)
    save_manifest(tid, m)


def app_fp():
    h = hashlib.sha1()
    for f in sorted(os.listdir(P('app'))):
        if f.endswith('.html') or f == 'build.py':
            h.update(open(P('app', f), 'rb').read())
    for f in sorted(os.listdir(P('app', 'reels'))):
        h.update(open(P('app', 'reels', f), 'rb').read())
    h.update(open(P('data', 'shlav-b-data.json'), 'rb').read())
    return h.hexdigest()[:12]


def validate(path):
    r = subprocess.run([sys.executable, P('engine', 'validate_pack.py'), path], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    errs = [l.strip() for l in out if 'ERROR' in l]
    warns = [l.strip() for l in out if l.strip().startswith('warn')]
    return errs, warns, (out[0] if out else '')


def S(key, label, state, detail='', fix=''):
    return {'key': key, 'label': label, 'state': state, 'detail': detail, 'fix': fix}


def topic_status(t, data_ids, git_dirty, spotify, app_state):
    tid = t['id']
    m = manifest(tid)
    st = m.get('stamps', {})
    pack_path = P('packs', tid + '.json')
    pack = load(pack_path)
    out = []
    src = m.get('sources', {})
    out.append(S('sources', 'מקורות אושרו מולך', 'ok' if src.get('confirmedAt') else 'todo',
                 '; '.join(x.get('label', '') for x in src.get('used', [])) or 'עוד לא אושרו',
                 'לאשר את רשימת המקורות לפני כתיבה'))
    sw = m.get('sweep')
    if not sw:
        out.append(S('sweep', 'סריקת מקורות ב-Drive', 'fail', 'לא בוצעה: אין הוכחה ששום פרק רלוונטי לא נשמט',
                     'להריץ את סריקת המקורות (שלב 2b ב-SKILL)'))
    else:
        pend = [r for r in sw.get('results', []) if r.get('verdict') not in ('used', 'not-needed')]
        out.append(S('sweep', 'סריקת מקורות ב-Drive', 'warn' if pend else 'ok',
                     (f"{len(pend)} קבצים בלי החלטה: " + ', '.join(r['file'] for r in pend)) if pend else
                     f"{len(sw.get('results', []))} קבצים נבדקו; כולם בשימוש או נפסלו עם נימוק",
                     'לתת החלטה לכל קובץ' if pend else ''))
    out.append(S('topic', 'הנושא בנתוני האפליקציה', 'ok' if tid in data_ids else 'fail', '', 'להוסיף ל-shlav-b-data.json'))
    if not pack:
        out.append(S('pack', 'חבילת לימוד', 'todo', 'אין עדיין קובץ חבילה'))
        return out
    errs, warns, head = validate(pack_path)
    extra = []
    secs = [s['h'] for s in pack.get('summary', {}).get('sections', [])]
    if not any('הבדלים' in h for h in secs):
        extra.append('אין סעיף ״הבדלים בין המקורות״')
    used = src.get('used', [])
    if used and len(pack.get('sources', [])) < len(used):
        extra.append(f"בחבילה {len(pack.get('sources', []))} מקורות, אושרו {len(used)}")
    state = 'fail' if errs else ('warn' if (warns or extra) else 'ok')
    out.append(S('pack', 'חבילה עברה בדיקה', state, '; '.join(errs + warns + extra) or head.split(': ', 1)[-1]))
    v = st.get('visual')
    out.append(S('visual', 'בדיקה ויזואלית של הסרטון',
                 'ok' if v and v['fp'] == reel_fp(pack) else ('warn' if v else 'todo'),
                 'הסרטון השתנה מאז הבדיקה' if v and v['fp'] != reel_fp(pack) else (v['at'] if v else ''),
                 'לרנדר את כל הפרקים ולבדוק חפיפות'))
    narr = load(P('narration', tid + '.json'))
    chs = pack.get('reel', {}).get('chapters', [])
    if not chs:
        out.append(S('narr', 'קריינות', 'todo', 'אין סרטון'))
    elif not narr:
        out.append(S('narr', 'קריינות', 'todo', 'אין תסריט קריינות', 'לכתוב narration/<id>.json ולהקליט'))
    else:
        bad, stale, missing = [], [], []
        rec = (st.get('narr') or {}).get('chapters', {})
        for c in chs:
            ats = sorted({0, *[p[0] for p in c.get('points', [])], c.get('pearl', [None])[0]} - {None})
            lines = narr.get('chapters', {}).get(c['id'])
            if not lines or [l[0] for l in lines] != ats:
                bad.append(c['id'])
            if not c.get('narr'):
                missing.append(c['id'])
            elif rec and rec.get(c['id']) != narr_fp(narr, c['id']):
                stale.append(c['id'])
        d = []
        if bad: d.append('תזמון לא תואם: ' + ', '.join(bad))
        if missing: d.append('בלי שמע: ' + ', '.join(missing))
        if stale: d.append('הטקסט השתנה מאז ההקלטה: ' + ', '.join(stale))
        if not rec: d.append('אין חותמת הקלטה')
        out.append(S('narr', f'קריינות ({len(chs) - len(missing)}/{len(chs)} פרקים)',
                     'fail' if bad else ('warn' if d else 'ok'), '; '.join(d), 'להקליט מחדש את הפרקים שסומנו'))
    script = load(P('podcast', tid + '.json'))
    pst = st.get('podcast')
    if not script:
        out.append(S('podscript', 'תסריט פודקאסט', 'todo', '', 'לכתוב לפי PROMPT.md'))
    else:
        words = sum(len(l[1].split()) for g in script['segments'] for l in g['lines'] if l[0] != 'pause')
        out.append(S('podscript', 'תסריט פודקאסט', 'ok' if 2600 <= words <= 3200 and 12 <= len(script['segments']) <= 16 else 'warn',
                     f"{words} מילים · {len(script['segments'])} מקטעים"))
        rec_ok = pack.get('podcast') and pst and pst['fp'] == fp(script)
        out.append(S('podaudio', 'פודקאסט מוקלט ומחובר', 'ok' if rec_ok else ('warn' if pack.get('podcast') else 'todo'),
                     'התסריט השתנה מאז ההקלטה' if pack.get('podcast') and not rec_ok else
                     (f"{round(pack['podcast']['dur'] / 60)} דקות" if pack.get('podcast') else 'לא הוקלט'),
                     'להקליט ב-BlueTTS ולחבר'))
        nb = os.path.exists(P('podcast', tid + '-notebooklm.md'))
        md = P('podcast', tid + '-script.md')
        md_ok = os.path.exists(md) and os.path.getmtime(md) >= os.path.getmtime(P('podcast', tid + '.json')) - 1
        out.append(S('notebooklm', 'חומרים ל-NotebookLM', 'ok' if nb and md_ok else ('warn' if nb or os.path.exists(md) else 'todo'),
                     ('פרומפט ✓' if nb else 'אין פרומפט') + ' · ' + ('תסריט מעודכן ✓' if md_ok else 'תסריט חסר או ישן')))
    eps = [e for e in spotify.get('episodes', []) if e.get('topic') == tid]
    if eps:
        no_tx = [e['title'] for e in eps if not os.path.exists(P('podcast', 'transcripts', e['doc'] + '.json'))]
        no_link = [e['title'] for e in eps if not e.get('spotifyEpisode')]
        d = []
        if no_tx: d.append('בלי תמליל: ' + ', '.join(no_tx))
        if no_link: d.append('בלי קישור לפרק: ' + ', '.join(no_link))
        out.append(S('spotify', f'פרקי Spotify ({len(eps)})', 'warn' if d else 'ok', '; '.join(d) or 'מיובאים, עם תמליל וקישור'))
    up = st.get('upload')
    out.append(S('upload', 'החבילה באפליקציה', 'ok' if up and up['fp'] == pack_fp(pack) else ('warn' if up else 'todo'),
                 'החבילה השתנתה מאז ההעלאה' if up and up['fp'] != pack_fp(pack) else (up['at'] if up else 'לא הועלתה'),
                 'ArtifactData set ל-packs/' + tid))
    out.append(app_state)
    dirty = [f for f in git_dirty if f'/{tid}' in f or f'{tid}.' in f or f'{tid}-' in f]
    out.append(S('git', 'שמור ב-git', 'warn' if dirty else 'ok', ('לא נשמרו: ' + ', '.join(dirty)) if dirty else ''))
    return out


def jobs():
    res = []
    if not os.path.isdir(JOBS):
        return res
    now = time.time()
    for f in sorted(os.listdir(JOBS)):
        p = os.path.join(JOBS, f)
        try:
            lines = [l for l in open(p, errors='replace').read().splitlines() if l.strip()]
        except Exception:
            continue
        age = now - os.path.getmtime(p)
        last = lines[-1] if lines else ''
        done = last.startswith('done') or last.startswith('DONE')
        failed = 'Traceback' in '\n'.join(lines[-5:]) or last.startswith('FAIL')
        res.append({'name': f[:-4] if f.endswith('.log') else f, 'last': last[-160:], 'ageSec': int(age),
                    'state': 'fail' if failed else ('done' if done else ('running' if age < 120 else 'stalled'))})
    return res


def all_status(only=None):
    data = load(P('data', 'shlav-b-data.json'))
    topics = {t['id']: t for t in data['topics']}
    ids = set(topics)
    active = set()
    for d, suf in (('packs', '.json'), ('status', '.json'), ('podcast', '.json'), ('narration', '.json')):
        for f in os.listdir(P(d)) if os.path.isdir(P(d)) else []:
            if f.endswith(suf) and not f.startswith('_') and '-' not in f[:-len(suf)] and f[:-len(suf)] in ids:
                active.add(f[:-len(suf)])
    if only:
        active = {only}
    g = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'shlav-b'], cwd=REPO, capture_output=True, text=True).stdout
    dirty = [l[3:] for l in g.splitlines() if l.strip()]
    spotify = load(P('podcast', 'spotify.json'), {}) or {}
    pub = (load(P('status', '_app.json'), {}) or {}).get('published')
    afp = app_fp()
    app_state = S('app', 'האפליקציה פורסמה עם הקוד העדכני', 'ok' if pub and pub['fp'] == afp else 'warn',
                  pub['at'] if pub and pub['fp'] == afp else 'הקוד או הנתונים השתנו מאז הפרסום', 'build.py ופרסום ה-artifact')
    out = []
    for tid in sorted(active, key=lambda x: list(topics).index(x)):
        stages = topic_status(topics[tid], ids, dirty, spotify, app_state)
        n_ok = sum(1 for s in stages if s['state'] == 'ok')
        out.append({'id': tid, 'name': topics[tid]['name'], 'ok': n_ok, 'total': len(stages), 'stages': stages})
    return {'at': time.strftime('%H:%M:%S'), 'topics': out, 'jobs': jobs()}


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--stamp']:
        stamp(a[1], a[2])
        print('stamped', a[1], a[2])
    elif a:
        r = all_status(a[0])
        for t in r['topics']:
            print(f"{t['name']} ({t['id']}): {t['ok']}/{t['total']}")
            for s in t['stages']:
                print(f"  [{s['state']:5}] {s['label']}" + (f" · {s['detail']}" if s['detail'] else ''))
    else:
        print(json.dumps(all_status(), ensure_ascii=False))
