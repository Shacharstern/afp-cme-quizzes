"""Join a topic's chapter narrations into one audio file, so the reel never has to start a new audio file
between chapters (browsers may block that). usage:
  python3 combine.py <pack.json> <wav_dir> <out.mp4>
Reads <wav_dir>/<topic>-<chapter>.wav in the pack's chapter order, writes one AAC/mp4 file and prints
the chapter start offsets (seconds), measured from the samples. Then, after uploading the file:
  python3 combine.py <pack.json> --attach <asset-url> <offsets.json>
"""
import json, os, subprocess, sys
if sys.argv[2] == '--attach':
    pack_path, url, offs_path = sys.argv[1], sys.argv[3], sys.argv[4]
    pack, info = json.load(open(pack_path)), json.load(open(offs_path))
    pack['reel']['audio'] = {'src': url, 'offs': info['offs']}
    for c, d in zip(pack['reel']['chapters'], info['durs']):
        if c.get('narr'):
            c['narr']['dur'] = d
            c['narr']['marks'][-1][1] = d
    json.dump(pack, open(pack_path, 'w'), ensure_ascii=False, indent=1)
    print('attached', url)
    sys.exit()
import numpy as np, soundfile as sf
pack_path, wav_dir, out = sys.argv[1:4]
pack = json.load(open(pack_path))
parts, offs, durs, t, sr0 = [], [], [], 0.0, None
for c in pack['reel']['chapters']:
    a, sr = sf.read(os.path.join(wav_dir, f"{pack['id']}-{c['id']}.wav"), dtype='float32')
    sr0 = sr0 or sr
    assert sr == sr0, 'mixed sample rates'
    offs.append(round(t, 3)); durs.append(round(len(a) / sr, 3)); t += len(a) / sr; parts.append(a)
wav = out.rsplit('.', 1)[0] + '.wav'
sf.write(wav, np.concatenate(parts), sr0)
subprocess.check_call(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-18:TP=-1.5', '-c:a', 'aac', '-b:a', '80k',
                       '-ar', str(sr0), '-movflags', '+faststart', out])
info = {'offs': offs, 'durs': durs, 'total': round(t, 3)}
json.dump(info, open(out.rsplit('.', 1)[0] + '-offs.json', 'w'), indent=1)
print(json.dumps(info))
