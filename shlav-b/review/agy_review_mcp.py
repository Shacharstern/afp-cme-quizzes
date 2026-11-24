#!/usr/bin/env python3
"""Reviewer bridge: one model writes, a second model (Gemini through the Antigravity CLI) critiques.

A tiny MCP server over stdio, standard library only. It runs `agy` (signed in to a Google account, no API key):

    agy -p "<prompt>" --model <model> --output-format json [--conversation <id>]

and takes `response` and `conversation_id` from the JSON. The id is kept per session in
shlav-b/review/sessions/<session>.json so every reply continues the same conversation.

Tools
  review(files, instructions, session)  opens a new review (a new conversation)
  reply(message, files, session)        continues the discussion in that session's conversation

Files are paths relative to the project root; the reviewer reads them itself. The reviewer only reads and comments:
headless `agy` blocks writing, shell and any tool not approved in advance, and the prompt forbids it as well.

Run as an MCP server (registered in .mcp.json):   python3 shlav-b/review/agy_review_mcp.py
Run once from a shell, for testing:               python3 shlav-b/review/agy_review_mcp.py --cli review SESSION "instructions" file1 file2
                                                  python3 shlav-b/review/agy_review_mcp.py --cli reply SESSION "message" [files...]
Settings (environment): AGY_BIN (default agy), AGY_MODEL (required; `agy models` lists the names),
AGY_TIMEOUT seconds (default 900).
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SESSIONS = os.path.join(HERE, 'sessions')
AGY_BIN = os.environ.get('AGY_BIN', 'agy')
AGY_TIMEOUT = int(os.environ.get('AGY_TIMEOUT', '900'))

REVIEWER_RULES = """You are the second model in a writer/critic pair. You are the CRITIC.
Rules:
- You only read and comment. Do NOT write, edit, create or delete any file, and do NOT run shell commands or any tool
  other than reading the files named below. The writer alone edits files.
- Check every claim against the SOURCE files you were given, not from memory. If a claim is not in the sources,
  say so; that is a finding even if you believe the claim is true.
- Return numbered findings. Each finding has exactly these fields:
    N. Location: <file and the exact item: e.g. pack drills[12], reel chapter "ch3" point 2, summary section "...">
       Severity: critical | major | minor
       Problem: <what is wrong>
       Evidence: <quote from the source file, with the file name and page/section if available>
       Suggested fix: <the corrected text or action>
- critical = medically wrong or unsafe; major = contradicts or is missing from the sources, misleading for the exam;
  minor = wording that changes meaning. Do not invent small stylistic comments. No findings is a valid answer.
- When the writer rejects a finding with evidence, re-check; concede when the evidence is against you, and say so.
- End with one line, exactly: VERDICT: SATISFIED   or   VERDICT: NOT SATISFIED
"""


def _session_path(session):
    safe = re.sub(r'[^A-Za-z0-9._-]', '_', session)
    return os.path.join(SESSIONS, safe + '.json')


def _load(session):
    try:
        return json.load(open(_session_path(session)))
    except Exception:
        return {'session': session, 'conversation_id': None, 'rounds': []}


def _save(session, data):
    os.makedirs(SESSIONS, exist_ok=True)
    json.dump(data, open(_session_path(session), 'w'), ensure_ascii=False, indent=1)


def _check_files(files):
    missing = [f for f in files or [] if not os.path.exists(os.path.join(REPO, f))]
    if missing:
        raise RuntimeError('files not found under the project root: ' + ', '.join(missing))


def _files_block(files):
    if not files:
        return ''
    return '\nFiles to read (paths relative to the project root ' + REPO + '):\n' + '\n'.join('- ' + f for f in files) + '\n'


def _run_agy(prompt, conversation_id=None):
    model = os.environ.get('AGY_MODEL')
    if not model:
        raise RuntimeError('AGY_MODEL is not set. Run `agy models` and set AGY_MODEL to the Gemini model to use.')
    cmd = [AGY_BIN, '-p', prompt, '--model', model, '--output-format', 'json']
    if conversation_id:
        cmd += ['--conversation', conversation_id]
    try:
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=AGY_TIMEOUT)
    except FileNotFoundError:
        raise RuntimeError(f'`{AGY_BIN}` was not found. Install the Antigravity CLI and sign in, or set AGY_BIN.')
    except subprocess.TimeoutExpired:
        raise RuntimeError(f'agy did not answer within {AGY_TIMEOUT} s')
    if p.returncode != 0:
        raise RuntimeError(f'agy exited with {p.returncode}: {(p.stderr or p.stdout).strip()[:2000]}')
    out = p.stdout.strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}\s*$', out, re.S)  # tolerate log lines before the JSON
        if not m:
            raise RuntimeError('agy did not return JSON: ' + out[:2000])
        data = json.loads(m.group(0))
    response = (data.get('response') or '').strip()
    if not response:
        raise RuntimeError('agy returned an empty response (the reviewer may have tried a blocked tool). Raw: ' + out[:2000])
    verdict = 'SATISFIED' if re.search(r'VERDICT:\s*SATISFIED\b', response) else (
        'NOT SATISFIED' if re.search(r'VERDICT:\s*NOT SATISFIED', response) else 'MISSING')
    return {'response': response, 'conversation_id': data.get('conversation_id') or conversation_id,
            'verdict': verdict, 'model': model}


def review(files, instructions, session):
    _check_files(files)
    prompt = REVIEWER_RULES + '\nTask from the writer:\n' + instructions.strip() + '\n' + _files_block(files)
    r = _run_agy(prompt)
    data = {'session': session, 'conversation_id': r['conversation_id'], 'model': r['model'], 'rounds': []}
    data['rounds'].append({'at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'kind': 'review', 'files': files,
                           'sent': instructions, 'response': r['response'], 'verdict': r['verdict']})
    _save(session, data)
    return r


def reply(message, files, session):
    data = _load(session)
    if not data.get('conversation_id'):
        raise RuntimeError(f'no open review for session {session!r}; call review first')
    _check_files(files)
    prompt = ('Reminder: you are the critic; read only, no file writes, no shell. Re-check against the sources and end with '
              'VERDICT: SATISFIED or VERDICT: NOT SATISFIED.\n\nWriter\'s reply:\n' + message.strip() + '\n' + _files_block(files))
    r = _run_agy(prompt, data['conversation_id'])
    data['conversation_id'] = r['conversation_id']
    data['rounds'].append({'at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'kind': 'reply', 'files': files or [],
                           'sent': message, 'response': r['response'], 'verdict': r['verdict']})
    _save(session, data)
    return r


# ---------------- MCP over stdio (JSON-RPC 2.0, one message per line) ----------------
TOOLS = [
    {'name': 'review', 'description': 'Open a new review by the critic model (Gemini via Antigravity CLI). '
     'The critic reads the given files itself and returns numbered findings ending in VERDICT: SATISFIED / NOT SATISFIED.',
     'inputSchema': {'type': 'object', 'required': ['files', 'instructions', 'session'], 'properties': {
         'files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Paths relative to the project root.'},
         'instructions': {'type': 'string', 'description': 'What to review and against which source files.'},
         'session': {'type': 'string', 'description': 'Session name, e.g. chestpain-pack. Reused by reply.'}}}},
    {'name': 'reply', 'description': 'Continue the same review conversation: answer findings point by point and ask for a re-check.',
     'inputSchema': {'type': 'object', 'required': ['message', 'session'], 'properties': {
         'message': {'type': 'string'},
         'files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Changed or new files to read.'},
         'session': {'type': 'string'}}}},
]


def _send(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def serve():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid, method, params = msg.get('id'), msg.get('method'), msg.get('params') or {}
        if mid is None:  # notification
            continue
        if method == 'initialize':
            _send({'jsonrpc': '2.0', 'id': mid, 'result': {
                'protocolVersion': params.get('protocolVersion', '2024-11-05'),
                'capabilities': {'tools': {}}, 'serverInfo': {'name': 'agy-review', 'version': '1.0'}}})
        elif method == 'tools/list':
            _send({'jsonrpc': '2.0', 'id': mid, 'result': {'tools': TOOLS}})
        elif method == 'tools/call':
            name, a = params.get('name'), params.get('arguments') or {}
            try:
                if name == 'review':
                    r = review(a.get('files') or [], a.get('instructions', ''), a['session'])
                elif name == 'reply':
                    r = reply(a.get('message', ''), a.get('files') or [], a['session'])
                else:
                    raise RuntimeError('unknown tool ' + str(name))
                text = f"[model {r['model']} · conversation {r['conversation_id']} · verdict {r['verdict']}]\n\n{r['response']}"
                _send({'jsonrpc': '2.0', 'id': mid, 'result': {'content': [{'type': 'text', 'text': text}]}})
            except Exception as e:
                _send({'jsonrpc': '2.0', 'id': mid, 'result': {
                    'content': [{'type': 'text', 'text': 'REVIEW FAILED: ' + str(e)}], 'isError': True}})
        elif method == 'ping':
            _send({'jsonrpc': '2.0', 'id': mid, 'result': {}})
        else:
            _send({'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': 'method not found: ' + str(method)}})


def cli(argv):
    kind, session, text, files = argv[0], argv[1], argv[2], argv[3:]
    r = review(files, text, session) if kind == 'review' else reply(text, files, session)
    print(f"[model {r['model']} · conversation {r['conversation_id']} · verdict {r['verdict']}]\n")
    print(r['response'])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        try:
            cli(sys.argv[2:])
        except Exception as e:
            print('REVIEW FAILED: ' + str(e), file=sys.stderr)
            sys.exit(1)
    else:
        serve()
