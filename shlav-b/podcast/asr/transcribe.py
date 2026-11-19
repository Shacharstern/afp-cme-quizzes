import sys,json,time
from faster_whisper import WhisperModel
import soundfile as sf
src,out=sys.argv[1],sys.argv[2]
t0=time.time();m=WhisperModel('ivrit-ai/whisper-large-v3-turbo-ct2',device='cpu',compute_type='int8',cpu_threads=4)
print('loaded',round(time.time()-t0),flush=True)
audio,_=sf.read(src,dtype='float32')
segs,info=m.transcribe(audio,language='he',word_timestamps=True,vad_filter=True,beam_size=5,condition_on_previous_text=False)
res=[]
for s in segs:
    res.append({'start':s.start,'end':s.end,'text':s.text,'words':[[w.start,w.end,w.word,round(w.probability,3)] for w in (s.words or [])]})
    if len(res)%20==0:print(round(s.end),'s',round(time.time()-t0),'wall',flush=True)
json.dump(res,open(out,'w'),ensure_ascii=False)
print('done',round(time.time()-t0),'s for',round(info.duration),'s audio',flush=True)
