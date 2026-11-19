# Transcripts for Spotify / NotebookLM episodes

Free and local: Whisper fine-tuned for Hebrew (ivrit-ai/whisper-large-v3-turbo-ct2, faster-whisper, CPU int8;
about 1 minute per 3.5 minutes of audio on 4 cores) and speakers by voice pitch (praat-parselmouth; works for two
hosts with clearly different pitch, as in NotebookLM).

    uv venv .venv && uv pip install --python .venv/bin/python faster-whisper praat-parselmouth numpy soundfile
    ffmpeg -i episode.mp4 -ac 1 -ar 16000 ep.wav
    .venv/bin/python transcribe.py ep.wav ep.words.json
    .venv/bin/python speakers.py ep.wav ep.words.json ep.lines.json      # [start, 'n'|'y', text, end]; n = higher voice

Then by hand (Claude): fix speaker boundaries the pitch split got wrong, correct medical terms and names
(D-dimer, Wells, Goroll, קריש not כריש...), add `segs` [[sec, id, title]], a pause line [sec, 'pause', secs, 'עצרו וענו']
after each "stop and think" question, and `hosts` {n: {name, role}, y: {...}}. Save the result in
`podcast/transcripts/<doc id>.json` and merge it into the episode's `podcasts` document with ArtifactData `update`.
