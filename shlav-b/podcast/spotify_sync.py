#!/usr/bin/env python3
"""Find new episodes of the Spotify show and prepare them for the app.

usage: python3 shlav-b/podcast/spotify_sync.py <out_dir>

Reads the show's RSS (address in podcast/spotify.json), skips episodes already listed there by guid, and for each new
one downloads the audio and re-encodes it to mono AAC 64 kbps in MP4 (the app's asset store takes video/mp4, up to
20 MB; about 0.5 MB a minute). Writes <out_dir>/new.json: [{guid, title, pub, file, dur, size, link, desc}].
Needs anchor.fm and d3ctxlq1ktw2nl.cloudfront.net allowed, and ffmpeg.

Then, by hand (see the Spotify section of .claude/skills/shlav-b-pack/SKILL.md): pick each episode's topic id, upload
the files as artifact assets, write one "podcasts" document per episode (source "spotify", spotify = the episode's
open.spotify.com link, or the show link until it is known), and append the episode to podcast/spotify.json.
"""
import email.utils, json, os, subprocess, sys, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, 'spotify.json')
NS = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 shlav-b-sync'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    state = json.load(open(STATE))
    known = {e['guid'] for e in state['episodes']}
    ch = ET.fromstring(get(state['rss'])).find('channel')
    new = []
    for it in ch.findall('item'):
        guid = it.findtext('guid')
        if guid in known:
            continue
        enc = it.find('enclosure')
        raw = os.path.join(out, guid + '.src')
        dst = os.path.join(out, guid + '.mp4')
        open(raw, 'wb').write(get(enc.get('url')))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-ac', '1', '-c:a', 'aac', '-b:a', '64k',
                        '-movflags', '+faststart', dst], check=True)
        os.remove(raw)
        dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                             '-of', 'csv=p=0', dst]).decode())
        size = os.path.getsize(dst)
        pub = email.utils.parsedate_to_datetime(it.findtext('pubDate')).isoformat().replace('+00:00', 'Z')
        new.append({'guid': guid, 'title': it.findtext('title'), 'pub': pub, 'file': dst, 'dur': round(dur, 2),
                    'size': size, 'link': it.findtext('link'), 'desc': (it.findtext('description') or '')[:300]})
        print(f"new: {it.findtext('title')} · {dur / 60:.1f} min · {size / 1048576:.1f} MB"
              + ('  (OVER 20 MB: lower the bitrate)' if size > 20 * 1048576 else ''))
    json.dump(new, open(os.path.join(out, 'new.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'{len(new)} new episode(s); {len(known)} already in the app')


if __name__ == '__main__':
    main()
