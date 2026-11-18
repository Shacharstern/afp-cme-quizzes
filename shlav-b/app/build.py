#!/usr/bin/env python3
"""Build the single-file app: python3 shlav-b/app/build.py out.html
Embeds shlav-b/data/shlav-b-data.json and every pack in shlav-b/packs/ marked built-in (default: incont)."""
import json, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
root = here.parent
data = json.loads((root / 'data' / 'shlav-b-data.json').read_text(encoding='utf-8'))
builtin = {p: json.loads((root / 'packs' / f'{p}.json').read_text(encoding='utf-8')) for p in ['incont']}
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
data_block = f'<script>\nconst DATA={dump(data)};\nconst BUILTIN_PACKS={dump(builtin)};\n</script>\n'
core = [(here / f).read_text(encoding='utf-8') for f in ('c-core.html', 'c2-srs.html', 'd-views.html', 'f-reel.html', 'h-podcast.html')]
custom = [f.read_text(encoding='utf-8') for f in sorted((here / 'reels').glob('*.html'))]  # topic-specific reel scenes
rest = [(here / f).read_text(encoding='utf-8') for f in ('g-game.html', 'e-player.html')]
parts = [(here / 'a-head.html').read_text(encoding='utf-8'), data_block] + core + custom + rest
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'shlav-b.html')
out.write_text(''.join(parts), encoding='utf-8')
print(f'wrote {out} ({out.stat().st_size} bytes)')
