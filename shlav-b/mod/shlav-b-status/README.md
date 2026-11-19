# shlav-b-status

A pane beside the chat for the Shlav B study-pack pipeline. It lists every topic that has work in the repository
(pack, narration, podcast, status file), with a progress bar and each step's state: sources confirmed, the Drive
source sweep (every file the topic's keywords hit has a verdict), pack validation, visual check, narration per
chapter (stale when the text changed after recording), podcast script and recording, NotebookLM files, Spotify
episodes and transcripts, upload to the app, app publish, and uncommitted files. Long jobs that write to
/tmp/shlav-b-jobs/<topic>-<step>.log show live. The checks live in shlav-b/engine/status.py; the pane runs it every
6 seconds and after each file edit. Command: /shlav-b-status. Load from a checkout with
`claude --plugin-dir shlav-b/mod/shlav-b-status`.
