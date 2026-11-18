"""Attach a recorded podcast episode to a pack: python3 attach_podcast.py <pack.json> <topic-podcast-marks.json> <asset url>

The url is what the artifact's asset store returned for <topic>-podcast.mp4. The pack gets
"podcast": {"src", "title", "dur", "hosts", "segs": [[sec, id, title]], "lines": [[sec, who, text] | [sec, "pause", secs, label]]}.
"""
import json, sys

pack_path, marks_path, url = sys.argv[1:4]
pack, m = json.load(open(pack_path)), json.load(open(marks_path))
pack['podcast'] = {'src': url, 'title': m['title'], 'dur': m['dur'], 'hosts': m['hosts'],
                   'segs': m['segs'], 'lines': m['lines'], 'engine': m.get('engine', ''), 'voices': m.get('voices', {})}
json.dump(pack, open(pack_path, 'w'), ensure_ascii=False, indent=1)
print(f'podcast attached: {m["dur"] / 60:.1f} min, {len(m["segs"])} segments, {len(m["lines"])} lines')
