"""Generate reel narration locally with Pocket TTS (Hebrew), free and offline after the first model fetch.

usage (from a pocket-tts-onnx checkout's venv):
  python pocket.py <topic> <out_dir> [--dry] [--voice omer] [chapter_id ...]

Each line of narration/<topic>.json is synthesized on its own and the lines are joined
with a short pause, so the start of every line is known exactly. Output:
  <out_dir>/<topic>-<chapter>.mp4   AAC audio in an mp4 box (the artifact asset store takes video/mp4)
  <out_dir>/<topic>-marks.json      {chapter: {dur, marks: [[at, seconds], ...]}}
--dry only prints the phonemes, to catch mispronunciations before generating.
LEXICON fixes words the Hebrew vowelizer gets wrong, as [[IPA]].
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
from pocket_tts_onnx import PocketTTS, phonemize_mixed

LEXICON = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lexicon.json')))
GAP = 0.45  # seconds of silence between lines

def fix(text):
    for k in sorted(LEXICON, key=len, reverse=True):
        text = text.replace(k, '[[' + LEXICON[k] + ']]')
    return text

def main():
    args = sys.argv[1:]
    dry = '--dry' in args
    voice = 'omer'
    if '--voice' in args:
        voice = args[args.index('--voice') + 1]
        args = [a for a in args if a not in ('--voice', voice)]
    args = [a for a in args if a != '--dry']
    topic, out, only = args[0], args[1], set(args[2:])
    here = os.path.dirname(os.path.abspath(__file__))
    script = json.load(open(os.path.join(here, topic + '.json')))
    os.makedirs(out, exist_ok=True)
    mpath = os.path.join(out, topic + '-marks.json')
    allm = json.load(open(mpath)) if os.path.exists(mpath) else {}
    tts = None if dry else PocketTTS.from_pretrained('english-ipa')
    for cid, lines in script['chapters'].items():
        if only and cid not in only:
            continue
        parts, marks, t, sr = [], [[0, 0.0]], 0.0, 24000
        for at, text in lines:
            ph = phonemize_mixed(fix(text))
            if dry:
                print(f'{cid} {at}: {ph}')
                continue
            samples, sr = tts.create(ph, voice=voice, phonemes=True, temperature=0.3, decode_steps=2)
            if at > 0:
                marks.append([at, round(t, 2)])
            parts += [samples.astype(np.float32), np.zeros(int(GAP * sr), np.float32)]
            t += len(samples) / sr + GAP
        if dry:
            continue
        audio = np.concatenate(parts)
        wav = os.path.join(out, f'{topic}-{cid}.wav')
        sf.write(wav, audio, sr)
        marks.append([1, round(t, 2)])
        subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-18:TP=-1.5',
                               '-c:a', 'aac', '-b:a', '64k', '-ar', '24000', '-movflags', '+faststart',
                               os.path.join(out, f'{topic}-{cid}.mp4')])
        allm[cid] = {'dur': round(t, 2), 'marks': marks}
        print(cid, round(t, 1), 's', flush=True)
        json.dump(allm, open(mpath, 'w'), indent=1)

if __name__ == '__main__':
    main()
