"""Generate reel narration with ElevenLabs (eleven_v3, Hebrew) and sync marks.

usage: python3 tts.py <topic> <out_dir> [voice_id] [chapter_id ...]

For each chapter in narration/<topic>.json: one TTS call with timestamps, saved as
<out_dir>/<topic>-<chapter>.mp4 (AAC audio, the asset store takes video/mp4), plus
<out_dir>/<topic>-marks.json: {chapter: {dur, marks: [[at, seconds], ...]}}.
The key is never read here: the session's network proxy adds the xi-api-key header.
"""
import base64, json, os, subprocess, sys, urllib.request

topic, out = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else 'JBFqnCBsd6RMkjVDRZzb'
only = set(sys.argv[4:])
here = os.path.dirname(os.path.abspath(__file__))
script = json.load(open(os.path.join(here, topic + '.json')))
os.makedirs(out, exist_ok=True)
marks_path = os.path.join(out, topic + '-marks.json')
allm = json.load(open(marks_path)) if os.path.exists(marks_path) else {}

for cid, lines in script['chapters'].items():
    if only and cid not in only:
        continue
    text, starts = '', []
    for at, t in lines:
        if text:
            text += ' '
        starts.append((at, len(text)))
        text += t
    body = json.dumps({'text': text, 'model_id': 'eleven_v3', 'language_code': 'he'}).encode()
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128',
        data=body, headers={'Content-Type': 'application/json', 'xi-api-key': 'proxy-injected'})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    mp3 = os.path.join(out, f'{topic}-{cid}.mp3')
    open(mp3, 'wb').write(base64.b64decode(d['audio_base64']))
    al = d['alignment']
    st, ch = al['character_start_times_seconds'], al['characters']
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp3]).decode())
    ok = ''.join(ch) == text
    marks = [[0, 0.0]]
    for at, off in starts:
        sec = st[off] if ok else dur * off / len(text)
        if at > marks[-1][0] and sec >= marks[-1][1]:
            marks.append([at, round(sec, 2)])
    marks.append([1, round(dur, 2)])
    subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp3, '-c:a', 'aac', '-b:a', '80k', '-movflags', '+faststart',
                           os.path.join(out, f'{topic}-{cid}.mp4')])
    allm[cid] = {'dur': round(dur, 2), 'marks': marks, 'aligned': ok}
    print(cid, round(dur, 1), 's', 'aligned' if ok else 'PROPORTIONAL', flush=True)
    json.dump(allm, open(marks_path, 'w'), indent=1)
