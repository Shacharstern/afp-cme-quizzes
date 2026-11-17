"""Attach narration to a pack: python3 attach.py <pack.json> <marks.json> <urls.json>

urls.json maps chapter id -> the asset URL the artifact's asset store returned for <topic>-<chapter>.mp4.
Each reel chapter gets "narr": {"src", "dur", "marks"}; the player follows the voice using the marks.
"""
import json, sys

pack_path, marks_path, urls_path = sys.argv[1:4]
pack, marks, urls = (json.load(open(x)) for x in (pack_path, marks_path, urls_path))
n = 0
for ch in pack['reel']['chapters']:
    m, u = marks.get(ch['id']), urls.get(ch['id'])
    if m and u:
        ch['narr'] = {'src': u, 'dur': m['dur'], 'marks': m['marks']}
        n += 1
    else:
        ch.pop('narr', None)
json.dump(pack, open(pack_path, 'w'), ensure_ascii=False, indent=1)
print(f'narration attached to {n}/{len(pack["reel"]["chapters"])} chapters')
