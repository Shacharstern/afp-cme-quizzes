"""Words with timestamps + audio -> transcript lines with two speakers (by pitch).
usage: post.py <audio16k.wav> <words.json> <out.json>
Assumes two hosts with clearly different voice pitch (NotebookLM: one female, one male).
'n' = higher voice, 'y' = lower voice.
"""
import json, sys
import numpy as np, parselmouth

wav, wj, out = sys.argv[1:4]
snd = parselmouth.Sound(wav)
pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=70, pitch_ceiling=450)
f0 = pitch.selected_array['frequency']; tt = pitch.xs()

segs = json.load(open(wj))
words = [w for s in segs for w in s['words']]
def med_f0(a, b):
    m = (tt >= a) & (tt <= b) & (f0 > 0)
    return float(np.median(f0[m])) if m.sum() >= 3 else 0.0
W = [{'s': w[0], 'e': w[1], 't': w[2], 'f': med_f0(w[0], w[1])} for w in words]

# two pitch clusters (1-D k-means on log f0)
lf = np.log([w['f'] for w in W if w['f'] > 0])
c = np.percentile(lf, [20, 80])
for _ in range(30):
    lab = np.abs(lf[:, None] - c[None, :]).argmin(1)
    c = np.array([lf[lab == k].mean() for k in (0, 1)])
cut = float(np.exp(c.mean()))
print('clusters Hz', np.exp(c).round(1), 'cut', round(cut, 1))

# raw label per word, then smooth: words without pitch take neighbours; mode filter over 5 words
raw = [None if w['f'] == 0 else ('n' if w['f'] > cut else 'y') for w in W]
def fill(r):
    r = r[:]
    last = next((x for x in r if x), 'n')
    for i, x in enumerate(r):
        if x is None: r[i] = last
        else: last = x
    return r
lab = fill(raw)
K = 2
sm = []
for i in range(len(lab)):
    win = [l for l in lab[max(0, i - K):i + K + 1]]
    sm.append('n' if win.count('n') > win.count('y') else 'y')
# a speaker turn also needs a gap or a run of >= 3 words; remove 1-2 word islands without a pause before them
lab = sm
i = 0
while i < len(lab):
    j = i
    while j < len(lab) and lab[j] == lab[i]: j += 1
    if j - i <= 2 and i > 0 and j < len(lab) and lab[i - 1] == lab[j]:
        gap = W[i]['s'] - W[i - 1]['e']
        if gap < 0.25:
            for k in range(i, j): lab[k] = lab[i - 1]
    i = j

# move every turn boundary to the widest pause within 3 words of it, then relabel by majority between boundaries
chg=[i for i in range(1,len(lab)) if lab[i]!=lab[i-1]]
bounds=[]
for i in chg:
    cand=range(max(1,i-3),min(len(W),i+4))
    j=max(cand,key=lambda k:(W[k]['s']-W[k-1]['e'])+ (0.05 if W[k-1]['t'].rstrip().endswith(('.','?','!',',')) else 0))
    if not bounds or j>bounds[-1]: bounds.append(j)
edges=[0]+bounds+[len(W)]
new=[]
for a_,b_ in zip(edges,edges[1:]):
    seg=raw[a_:b_];nn=seg.count('n');yy=seg.count('y')
    new+= ['n' if nn>=yy else 'y']*(b_-a_)
lab=new
# short sentences (<= 4 words, e.g. "בדיוק." "נכון.") take their own pitch label: backchannels from the other host
sent=[];st_=0
for i,w in enumerate(W):
    if w['t'].rstrip().endswith(('.','?','!')) or i==len(W)-1:
        sent.append((st_,i+1));st_=i+1
for a_,b_ in sent:
    if b_-a_<=4:
        seg=[r for r in raw[a_:b_] if r]
        if seg:
            l='n' if seg.count('n')>seg.count('y') else ('y' if seg.count('y')>seg.count('n') else None)
            if l:
                for k in range(a_,b_): lab[k]=l
# lines: split at speaker change; inside a turn, split after a sentence end when the line has >= 25 words
lines = []
cur = None
for w, l in zip(W, lab):
    if cur is None or l != cur['who'] or (cur['n'] >= 25 and cur['txt'].rstrip().endswith(('.', '?', '!'))):
        if cur: lines.append(cur)
        cur = {'s': w['s'], 'e': w['e'], 'who': l, 'txt': '', 'n': 0}
    cur['txt'] += w['t']; cur['e'] = w['e']; cur['n'] += 1
if cur: lines.append(cur)
res = [[round(x['s'], 2), x['who'], x['txt'].strip(), round(x['e'], 2)] for x in lines]
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=0)
nn = sum(1 for x in res if x[1] == 'n'); print(len(res), 'lines;', nn, 'n /', len(res) - nn, 'y')
