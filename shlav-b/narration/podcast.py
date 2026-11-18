"""Record a two-voice podcast episode with BlueTTS (Hebrew, ONNX), free and offline after the model download.

usage (from a BlueTTS checkout, with its bundle in ./bluev3_onnx):
  uv run python <repo>/shlav-b/narration/podcast.py <topic> <out_dir> [--dry]

Reads shlav-b/podcast/<topic>.json (format: shlav-b/podcast/PROMPT.md). Each host speaks with the voice named in
"hosts"; every sentence is synthesized on its own (with the lexicon from narration/lexicon.json) and cached by its
phonemes, so re-recording after a fix only synthesizes the lines that changed. Output:
  <out_dir>/<topic>-podcast.mp4         AAC audio in an mp4 box (the artifact asset store takes video/mp4)
  <out_dir>/<topic>-podcast-marks.json  {dur, segs: [[sec, id, title]], lines: [[sec, who, text]]}
The transcript text in the marks is the display form: podcast/display.json turns spoken forms back into the
written terms (די-דיימר -> D-dimer).
--dry prints the phonemes of every line and the estimated length, without synthesizing.
"""
import hashlib, json, os, re, subprocess, sys
import numpy as np
import soundfile as sf

sys.path.insert(0, 'src')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from blue_onnx import BlueTTS, load_voice_style  # noqa: E402
from blue import phonemes  # noqa: E402

ROOT = os.path.dirname(HERE)
GAP_SENT, GAP_SAME, GAP_TURN, GAP_SEG = 0.22, 0.32, 0.42, 0.7
TARGET_RMS = 0.075


def display_map():
    m = json.load(open(os.path.join(ROOT, 'podcast', 'display.json')))
    keys = sorted(m, key=len, reverse=True)
    rx = re.compile(r'(?<![א-ת])([ובלהמשכ]{0,2})(' + '|'.join(re.escape(k) for k in keys) + r')(?![א-ת])')
    return lambda s: rx.sub(lambda g: g.group(1) + ('-' if g.group(1) else '') + m[g.group(2)], s)


def tone(sr, freqs, dur=0.5, amp=0.11):
    """A soft chime between segments: a few decaying sine notes."""
    out = []
    for f in freqs:
        t = np.arange(int(dur * sr)) / sr
        out.append(amp * np.sin(2 * np.pi * f * t) * np.exp(-t * 6) * np.minimum(1, t * 200))
    return np.concatenate(out).astype(np.float32)


def level(x):
    r = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0
    if r < 1e-4:
        return x
    y = x * (TARGET_RMS / r)
    pk = float(np.max(np.abs(y)))
    return y * (0.95 / pk) if pk > 0.95 else y


def main():
    args = sys.argv[1:]
    dry = '--dry' in args
    args = [a for a in args if a != '--dry']
    topic, out = args[0], args[1]
    ep = json.load(open(os.path.join(ROOT, 'podcast', topic + '.json')))
    hosts = ep['hosts']
    tts = BlueTTS(onnx_dir='bluev3_onnx/onnx', style_json=f'bluev3_onnx/voices/{hosts[next(iter(hosts))]["voice"]}.json')
    styles = {k: load_voice_style([f'bluev3_onnx/voices/{h["voice"]}.json']) for k, h in hosts.items()}
    sr = tts.sample_rate
    show = display_map()
    cache = os.path.join(out, 'cache')
    os.makedirs(cache, exist_ok=True)

    def say(who, sentence):
        ph = phonemes(tts, sentence)
        if dry:
            return ph, None
        key = hashlib.sha1((hosts[who]['voice'] + '|' + ph).encode()).hexdigest()[:16]
        f = os.path.join(cache, key + '.wav')
        if os.path.exists(f):
            x, _ = sf.read(f, dtype='float32')
        else:
            x, _ = tts.synthesize(f'<he>{ph}</he>', lang='he', text_is_phonemes=True, normalize_text=False,
                                  style=styles[who])
            x = level(x.astype(np.float32))
            sf.write(f, x, sr)
        return ph, x

    parts, segs, lines, t, prev, words = [tone(sr, [659.3, 880.0])], [], [], 0.0, None, 0
    t += len(parts[0]) / sr + 0.3
    parts.append(np.zeros(int(0.3 * sr), np.float32))
    for si, seg in enumerate(ep['segments']):
        if si:
            ch = tone(sr, [880.0, 659.3], 0.35, 0.07)
            for x in (np.zeros(int(GAP_SEG * sr), np.float32), ch, np.zeros(int(0.35 * sr), np.float32)):
                parts.append(x)
                t += len(x) / sr
            prev = None
        segs.append([round(t, 2), seg['id'], seg['title']])
        for ln in seg['lines']:
            if ln[0] == 'pause':
                lines.append([round(t, 2), 'pause', ln[1], ln[2] if len(ln) > 2 else ''])
                x = np.zeros(int(ln[1] * sr), np.float32)
                parts.append(x)
                t += ln[1]
                prev = None
                continue
            who, text = ln[0], ln[1]
            if prev is not None:
                g = np.zeros(int((GAP_SAME if prev == who else GAP_TURN) * sr), np.float32)
                parts.append(g)
                t += len(g) / sr
            lines.append([round(t, 2), who, show(text)])
            words += len(text.split())
            for k, s in enumerate(x for x in re.split(r'(?<=[.?!:])\s+', text.strip()) if x):
                ph, x = say(who, s)
                if dry:
                    print(f'{seg["id"]} {who}: {ph}')
                    continue
                if k:
                    parts.append(np.zeros(int(GAP_SENT * sr), np.float32))
                    t += GAP_SENT
                parts.append(x)
                t += len(x) / sr
            prev = who
        print(seg['id'], round(t / 60, 1), 'min', flush=True)
    if dry:
        print(f'{words} words, about {words / 135:.0f} minutes')
        return
    parts.append(np.zeros(int(0.4 * sr), np.float32))
    parts.append(tone(sr, [659.3, 880.0]))
    wav = os.path.join(out, f'{topic}-podcast.wav')
    sf.write(wav, np.concatenate(parts), sr)
    dur = round(sum(len(p) for p in parts) / sr, 2)
    subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-17:TP=-1.5',
                           '-ac', '1', '-c:a', 'aac', '-b:a', '64k', '-ar', '44100', '-movflags', '+faststart',
                           os.path.join(out, f'{topic}-podcast.mp4')])
    marks = {'title': ep['title'], 'dur': dur, 'segs': segs, 'lines': lines,
             'hosts': {k: {'name': h['name'], 'role': h['role']} for k, h in hosts.items()},
             'engine': 'BlueTTS v3', 'voices': {k: h['voice'] for k, h in hosts.items()}}
    json.dump(marks, open(os.path.join(out, f'{topic}-podcast-marks.json'), 'w'), ensure_ascii=False, indent=1)
    print('done', round(dur / 60, 1), 'min', words, 'words')


if __name__ == '__main__':
    main()
