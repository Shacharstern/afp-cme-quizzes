#!/usr/bin/env python3
"""Validate a Shlav B study pack (schema 1). Usage: python3 validate_pack.py pack.json [more.json ...]
Exit code 0 when every pack is valid; prints each problem otherwise."""
import json, re, sys

HEB = re.compile(r'[֐-׿]')
KINDS = {'pick', 'swipe', 'num'}


def check(p):
    errs, warn = [], []
    E = errs.append
    for k in ('id', 'schema', 'title', 'updated', 'sources'):
        if k not in p: E(f'missing top-level "{k}"')
    if p.get('schema') != 1: E('schema must be 1')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', str(p.get('id', ''))): E('id must be the topic id (letters, digits, _ or -)')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(p.get('updated', ''))): E('updated must be YYYY-MM-DD')
    for s in p.get('sources', []):
        if not {'label', 'kind', 'year'} <= set(s): E(f'source needs label, kind, year: {s}')
    if not HEB.search(p.get('title', '')): E('title must be Hebrew')
    modes = [m for m in ('summary', 'drills', 'pathway', 'oral') if p.get(m)]
    if not modes: E('pack has no study modes')

    sm = p.get('summary')
    if sm:
        if not sm.get('oneLiner'): E('summary.oneLiner missing')
        for i, s in enumerate(sm.get('sections', [])):
            if not s.get('h') or not s.get('points'): E(f'summary.sections[{i}] needs h and points')

    ids = set()
    decks = p.get('decks', {})
    secs = {s['id'] for s in p.get('drillSections', [])}
    for d in p.get('drills', []):
        tag = f"drill {d.get('id')}"
        if d.get('id') in ids: E(f'{tag}: duplicate id')
        ids.add(d.get('id'))
        if d.get('k') not in KINDS: E(f'{tag}: k must be pick, swipe or num')
        if secs and d.get('sec') not in secs: E(f'{tag}: sec not in drillSections')
        if not d.get('q') or not d.get('w'): E(f'{tag}: needs q and w (the why)')
        if d.get('k') == 'pick':
            o = d.get('o') or []
            if len(o) < 2: E(f'{tag}: pick needs 2+ options')
            if not isinstance(d.get('a'), int) or not 0 <= d['a'] < len(o): E(f'{tag}: a out of range')
        if d.get('k') == 'swipe':
            if d.get('d') not in decks: E(f'{tag}: deck "{d.get("d")}" not in decks')
            if d.get('a') not in (0, 1): E(f'{tag}: swipe a must be 0 or 1')
        if d.get('k') == 'num':
            try:
                mn, mx, lo, hi, st = (float(d[x]) for x in ('min', 'max', 'lo', 'hi', 'start'))
                if not (mn <= lo <= hi <= mx): E(f'{tag}: need min <= lo <= hi <= max')
                if not mn <= st <= mx: E(f'{tag}: start outside range')
                if lo <= st <= hi: warn.append(f'{tag}: start already inside the correct range')
            except (KeyError, TypeError, ValueError):
                E(f'{tag}: num needs min, max, lo, hi, start')
    for k, v in decks.items():
        if not (isinstance(v, list) and len(v) == 2): E(f'deck {k} must have 2 labels')

    pw = p.get('pathway')
    if pw:
        st = [s.get('k') for s in pw.get('stations', [])]
        if len(st) < 3: E('pathway needs 3+ stations')
        for s in pw.get('stations', []):
            if not s.get('t') or not s.get('rule'): E(f'station {s.get("k")}: needs t and rule')
        for c in pw.get('cases', []):
            if not c.get('steps'): E(f'case {c.get("id")}: no steps')
            for j, s in enumerate(c.get('steps', [])):
                if s.get('st') not in st: E(f'case {c.get("id")} step {j}: station "{s.get("st")}" unknown')
                if not isinstance(s.get('a'), int) or not 0 <= s['a'] < len(s.get('o', [])): E(f'case {c.get("id")} step {j}: a out of range')

    qids = set()
    for s in p.get('oral', []):
        for q in s.get('q', []):
            if q.get('id') in qids: E(f'oral {q.get("id")}: duplicate id')
            qids.add(q.get('id'))
            if not q.get('q') or len(q.get('p', [])) < 2: E(f'oral {q.get("id")}: needs q and 2+ key points')
            if not q.get('f'): warn.append(f'oral {q.get("id")}: no structure line (f)')
            fu = q.get('fu')
            if fu and (not fu.get('q') or len(fu.get('p', [])) < 2): E(f'oral {q.get("id")}: follow-up needs q and 2+ points')
            if not fu: warn.append(f'oral {q.get("id")}: no follow-up')

    size = len(json.dumps(p, ensure_ascii=False).encode())
    if size > 240_000: E(f'pack is {size} bytes; keep it under 240000')
    return errs, warn, size, modes


def main(paths):
    ok = True
    for path in paths:
        p = json.load(open(path, encoding='utf-8'))
        errs, warn, size, modes = check(p)
        print(f'{path}: {"OK" if not errs else "INVALID"} · {size} bytes · modes: {", ".join(modes)} · '
              f'{len(p.get("drills", []))} drills · {len((p.get("pathway") or {}).get("cases", []))} cases · '
              f'{sum(len(s["q"]) for s in p.get("oral", []))} oral questions')
        for e in errs: print('  ERROR', e)
        for w in warn: print('  warn ', w)
        ok &= not errs
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
