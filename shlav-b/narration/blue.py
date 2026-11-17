"""Generate reel narration locally with BlueTTS (Hebrew, ONNX), free and offline after the model download.

usage (from a BlueTTS checkout, with its bundle downloaded to ./bluev3_onnx):
  uv run python <repo>/shlav-b/narration/blue.py <topic> <out_dir> [--dry] [--voice david] [chapter_id ...]

Each line of narration/<topic>.json is synthesized on its own and the lines are joined with a
short pause, so the start of every line is known exactly. Output:
  <out_dir>/<topic>-<chapter>.mp4   AAC audio in an mp4 box (the artifact asset store takes video/mp4)
  <out_dir>/<topic>-marks.json      {chapter: {dur, marks: [[at, seconds], ...]}}
--dry prints the phonemes, to catch mispronunciations before generating.
narration/lexicon.json fixes words the Hebrew G2P gets wrong: the word is replaced by its IPA.
"""
import json, os, re, subprocess, sys
import numpy as np
import soundfile as sf

sys.path.insert(0, 'src')
from blue_onnx import BlueTTS

HERE = os.path.dirname(os.path.abspath(__file__))
LEXICON = {} if os.environ.get('BLUE_NOLEX') else json.load(open(os.path.join(HERE, 'lexicon.json')))
KEYS = sorted(LEXICON, key=len, reverse=True)
LEX_RE = re.compile('|'.join(re.escape(k) for k in KEYS)) if KEYS else None
GAP = 0.45


def phonemes(tts, text):
    """IPA for one line: Hebrew G2P for the text, lexicon IPA spliced in for listed words."""
    g2p = tts.tts.g2p
    parts, last = [], 0
    for m in (LEX_RE.finditer(text) if LEX_RE else []):
        if m.start() > last:
            parts.append(('he', text[last:m.start()]))
        parts.append(('ipa', LEXICON[m.group(0)]))
        last = m.end()
    parts.append(('he', text[last:]))
    out = []
    for kind, s in parts:
        if kind == 'ipa':
            out.append(s)
        elif s.strip():
            if any(c.isalnum() for c in s):
                out.append(re.sub(r'</?he>', '', g2p.phonemize(s.strip(), lang='he')))
            else:
                out.append(s.strip())
    ipa = ' '.join(out)
    return re.sub(r'\s+([,.:?!])', r'\1', re.sub(r'\s+', ' ', ipa)).strip()


def main():
    args = sys.argv[1:]
    dry = '--dry' in args
    voice = 'david'
    if '--voice' in args:
        voice = args[args.index('--voice') + 1]
        args = [a for a in args if a not in ('--voice', voice)]
    args = [a for a in args if a != '--dry']
    topic, out, only = args[0], args[1], set(args[2:])
    script = json.load(open(os.path.join(HERE, topic + '.json')))
    tts = BlueTTS(onnx_dir='bluev3_onnx/onnx', style_json=f'bluev3_onnx/voices/{voice}.json')
    os.makedirs(out, exist_ok=True)
    mpath = os.path.join(out, topic + '-marks.json')
    allm = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for cid, lines in script['chapters'].items():
        if only and cid not in only:
            continue
        parts, marks, t, sr = [], [[0, 0.0]], 0.0, tts.sample_rate
        for at, text in lines:
            ph = phonemes(tts, text)
            if dry:
                print(f'{cid} {at}: {ph}')
                continue
            samples, sr = tts.synthesize(f'<he>{ph}</he>', lang='he', text_is_phonemes=True, normalize_text=False)
            if at > 0:
                marks.append([at, round(t, 2)])
            parts += [samples.astype(np.float32), np.zeros(int(GAP * sr), np.float32)]
            t += len(samples) / sr + GAP
        if dry:
            continue
        wav = os.path.join(out, f'{topic}-{cid}.wav')
        sf.write(wav, np.concatenate(parts), sr)
        marks.append([1, round(t, 2)])
        subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-18:TP=-1.5',
                               '-c:a', 'aac', '-b:a', '80k', '-ar', '44100', '-movflags', '+faststart',
                               os.path.join(out, f'{topic}-{cid}.mp4')])
        allm[cid] = {'dur': round(t, 2), 'marks': marks, 'voice': voice, 'engine': 'BlueTTS v3'}
        print(cid, round(t, 1), 's', flush=True)
        json.dump(allm, open(mpath, 'w'), indent=1)


if __name__ == '__main__':
    main()
