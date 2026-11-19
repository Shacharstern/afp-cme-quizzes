---
name: shlav-b-pack
description: Turn one Shlav B topic (family medicine board, Israel) into a Hebrew study pack for the Shlav B prep app — an interactive animated walkthrough (reel), and the game (fact-drill shifts, patient-pathway case rounds, oral boards with examiner follow-ups) plus a summary sheet — built only from the topic's anchor sources in the user's Google Drive folder "שלב א", validated, saved to shlav-b/packs/, and uploaded to the app. Use when the user types /shlav-b-pack <topic-id> or asks to build, rebuild or update a study pack (חבילת לימוד) for a Shlav B topic.
---

# Shlav B pack engine

One run = one topic id from `shlav-b/data/shlav-b-data.json` (`topics[].id`, e.g. `htn`, `copd`, `incont`).
The output is a JSON pack in the format of `shlav-b/engine/pack-format.md`, entirely in Hebrew
(medical terms, drug names and acronyms stay in English as Israeli clinicians say them).

## 1. Read the topic
Load the topic from `shlav-b/data/shlav-b-data.json`: `name`, `tier`, `domain`, `hits`, `sittings`, `anchorSources`.
Also load `answerTemplate`, `rubricPrinciples`, `exam.structure` and `exam.materialWindow`: the oral questions must train exactly these.

## 2. Find the sources in Google Drive
Use the Google Drive connector. The source root is the user's folder titled **שלב א** (search `title = 'שלב א'` with the folder mimeType; take the one owned by the user that contains `AFP`, `Goroll8.pdf` and `הנחיות הרי מבוגרים`).
- **AFP articles:** `AFP/<system>/…pdf` (Cardiovascular, Endocrinology, Urology, Neurology, Pediatrics, Gynecology, Geriatrics, Dermatology, ENT + Maxillofacial, Opthalmology, Oncology + Hematology, Ortho + Rheumatology + Immunology, Surgery + Gastro, Misc). Search by English title words (`title contains 'Kidney'`), then by `fullText contains`.
- **Goroll:** prefer a chapter extract named like `<topic> Goroll.pdf` in the system folder. `Goroll8.pdf` in the root is the whole book (67 MB); reading it may return only part of the text, so search for an extract first and say so if you had to rely on the full book.
- **IMA guidelines:** `הנחיות הרי מבוגרים`, `הנחיות הרי - ילדים`; society guidelines: `הנחיות איגודים`. Ignore `איגודים לא למבחן`.
- Read every anchor source in full with `read_file_content`. If an anchor source is missing, look for the newest in-window version; if none exists, continue with what exists and list the gap.

## 2b. Source sweep (mandatory: no relevant chapter may be missed)
The anchor sources in `shlav-b-data.json` are a starting point, not the list. A topic's material often sits in a chapter named for a symptom (PE is taught in Goroll ch. 20, Chest Pain), so search by content, not by title:
1. Write the topic's keywords in English as the sources say them: the disease, its synonyms and its key terms (vte: `pulmonary embolism`, `pulmonary embolization`, `deep vein thrombosis`, `deep venous thrombosis`, `venous thromboembolism`).
2. One Drive search over the folder: `'<שלב א id>' in ancestors and mimeType = 'application/pdf' and (fullText contains '<k1>' or fullText contains '<k2>' ...)`, ordered by relevance (no `orderBy`), `pageSize` 12 or more.
3. Every one of the top 12 results gets a verdict in `shlav-b/status/<id>.json` under `sweep.results`: `used`, `not-needed` with a one-line reason, or `pending` for the user to decide. A Goroll chapter or an in-window AFP review in the top 12 is `used` unless there is a stated reason.
4. While reading each source, note every "see Chapter N" it cites; a cited Goroll chapter on the topic's own subject is checked the same way.
5. Show the user the sweep together with the source list when asking to confirm sources (the rule above: always confirm before writing). Then record: `sources.used`, `sources.rejected` and `python3 shlav-b/engine/status.py --stamp <id> sources`.

**Window and version rules:** AFP and guidelines from about mid-2019 to spring 2026 only; always the newest AFP version of a topic; Goroll edition 8. A source outside the window may be used only as background and must be named as such in `sources` with `"outOfWindow": true`.

## 3. Write the pack
Follow `shlav-b/engine/pack-format.md`. Content rules:
- **Only what the sources say.** Every number, dose, threshold and recommendation must be traceable to a source you read. No numbers from memory. Where two sources disagree (AFP vs Goroll vs IMA), add a summary section titled `הבדלים בין המקורות` and keep both values with attribution. Israeli guidelines win for Israeli practice; say so in the pearl.
- **Exam alignment.** Oral questions must make the user produce answers in the `answerTemplate` order (summary sentence → red flags → differential ≥5 incl. malignancy/psych/drugs → focused history and exam → workup → treatment with name/dose/side effects/follow-up/referral → bio-psycho-social → shared decision-making and plain-language explanation → prevention/prognosis/law). Cover the `rubricPrinciples` that apply (emergency referral said explicitly, falls in elderly, mandatory reporting, kg dosing in children, incidental findings).
- **Follow-ups** (`fu`) are the examiner's twist: a new finding, a special population (pregnancy, child, frail elderly, CKD), a side effect, or a patient objection. They test reasoning, not recall.
- **Consult questions** (`k: "ייעוץ · …"`): plain Hebrew a patient understands; key points include acknowledgment, explanation, options and follow-up.
- **Pathway** = the topic's own algorithm (the article's figure or the guideline's flow), 5–7 stations, each with a one-line `rule`. Cases are short vignettes written by you; say so nowhere in the pack as if they came from the article.
- **Reel (the interactive walkthrough) comes first and matters most.** 8–14 chapters that walk the topic in clinical order (why it matters → classification → history/red flags → exam → workup → algorithm → treatment steps → special populations → referral → SORT recap). Each chapter: a headline that states the point, 3–6 `points` that reveal as the user scrubs (`at` rising from 0.02 to about 0.86, each with a short `key` such as a number or term), a pearl at 0.9, and one `scene` from the catalog in `pack-format.md` chosen because it shows the idea (numbers that decide management → `threshold`; algorithm → `flow`; escalation → `ladder`; do/don't → `sort`; mnemonic → `tiles`; drug classes → `bins`). Use at least six different scene types per pack. Scene labels are short; the visual does not wrap Hebrew.
- **Game.** Drills feed timed-optional shifts with hearts and streaks, so mix `pick`, `swipe` (with 2-label `decks`) and `num`; give `num` drills a visual `v` (`gauge`, `angle`, `waffle`) where the quantity suits it. 2–4 `drillSections` become the shifts.
- **Sizes:** reel 8–14 chapters; summary 8–12 sections; drills 25–60 with mixed `pick`/`swipe`/`num`, every one with a `w` (why); 3–6 cases; oral 2–4 stations × 2–4 questions, each with a follow-up. Keep the pack under 240 KB.
- **Hebrew style:** short sentences, no filler, the way a senior family physician would explain it. Quote-like marks inside strings: use ״ and ׳, not ASCII double quotes.

## 3b. Custom reel scenes (one topic at a time)
The user chose a unique reel per topic. For each chapter, prefer a scene drawn for this topic over a catalog template: the topic's own mechanism, test, curve or algorithm (e.g. an ECG that morphs with potassium, a brain cell that swells as sodium falls, a speedometer for correction limits).
- Write the drawing code in `shlav-b/app/reels/<topic-id>.html` (more files as `<topic-id>-2.html`): `REEL.custom('<topic-id>', { sceneName(g, d, ctx) { ...draw once...; return t => { ...update for 0 ≤ t ≤ 1... }; } })`, using `REEL.kit` (S, set, span, lerp, C, R for right-aligned Hebrew, M centered). Text comes from the pack (`d`), never hard-coded clinical content. See `reels/lytes.html` for the pattern.
- In the pack, such a chapter uses `"scene": {"type": "x", "name": "sceneName", ...data}`. Templates stay allowed where nothing better fits (a recap, a long list).
- Only draw findings the source states (lytes: the article text names T-wave flattening, QRS widening, bradycardia and junctional rhythm; it does not name peaked T waves, so they are not drawn).
- Check visually before publishing: build, render every chapter at t≈0.45 and t≈0.92 with Playwright, look for clipped or overlapping text, fix, then rebuild. Custom code ships inside the app, so finish with: build → publish the app artifact (same file path) → upload the pack.

## 3c. Narration (Hebrew voice-over for the reel)
Write `shlav-b/narration/<topic-id>.json`: for each chapter, lines `[at, text]` whose `at` values are exactly 0, every point's `at`, and the pearl's `at`; spoken Hebrew, numbers and acronyms written as they are said. Generate with BlueTTS (free, local ONNX; needs Hugging Face hosts allowed): in a checkout of `maxmelichov/BlueTTS` with `uv sync` and the `notmax123/BlueV3-onnx` bundle in `./bluev3_onnx`, run `uv run python <repo>/shlav-b/narration/blue.py <topic-id> <out> --dry` to check phonemes, add fixes to `narration/lexicon.json` (word → IPA, one entry per prefixed form: ו/ה/ב/ל/מ), then run without `--dry` (default voice `david`; `--voice` picks another). Upload the `<topic>-<chapter>.mp4` files as artifact assets, save the returned URLs in `narration/<topic-id>-urls.json`, copy the marks file to `narration/`, and run `narration/attach.py` before uploading the pack. (`narration/pocket.py` is the earlier Pocket TTS generator.)

**Pronunciation the user corrected (keep for every topic; all are in `lexicon.json`):** protein = פרוטאין (pro-te-ˈin); למנות = limnot; הישנות ends in -nut (hishanut); מבדלת = mavdelet; פקקת = pakeket; קומדין = kumadin; מקטע = mikta; לשבץ = leshavats. Before generating, scan the `--dry` output for these and for drug names, and add any new word the G2P gets wrong.

## 3d. Podcast (״הסבב״, two-host audio episode)
Write `shlav-b/podcast/<topic-id>.json` following `shlav-b/podcast/PROMPT.md` (the writing prompt: one patient thread, retrieval before explanation, 4–6 ״עצרו וענו״ pauses, exam traps, source conflicts said aloud, exam corner, patient talk, rapid round). Spoken text only: Hebrew letters, numbers as words. Check with `uv run python <repo>/shlav-b/narration/podcast.py <topic-id> <out> --dry` from the BlueTTS checkout (phonemes and word count), fix words in `narration/lexicon.json`, then record without `--dry` (voices from the script's `hosts`; sentences are cached by phonemes, so a re-record only synthesizes changed lines). Add new spoken→written terms to `podcast/display.json` (the transcript shows D-dimer, not די-דיימר). Upload `<topic>-podcast.mp4` as an artifact asset and run `python3 narration/attach_podcast.py packs/<id>.json <out>/<topic>-podcast-marks.json <asset url>` before uploading the pack.

## 4. Validate
`python3 shlav-b/engine/validate_pack.py shlav-b/packs/<id>.json` must print OK. Fix every ERROR; fix warnings unless there is a reason.

## 5. Save and upload
1. Save to `shlav-b/packs/<id>.json`.
2. Upload to the app's database with the `ArtifactData` tool: `action: "set"`, `url: "https://claude.ai/artifact/QmSkYmiFQTpwUvm1omtrGb"`, `collection: "packs"`, `doc_id: "<id>"`, `file_path: "shlav-b/packs/<id>.json"`. If the document exists, `get` it first and pass its `version` as `if_version`. The app picks the pack up live; no republish needed.
3. Commit the pack on the working branch.

## 6. Report to the user (in Hebrew)
Which sources were read (title, year, Drive folder), what is missing or out of window, the conflicts found, and the pack size (drills, cases, oral questions). Name anything in the pack that rests on clinical reasoning rather than an explicit source statement.

## 7. Spotify episodes (״הסבב״ on Spotify)
The user publishes episodes (NotebookLM and others) to the Spotify show; the app keeps a copy of each, with a button back to Spotify. State: `shlav-b/podcast/spotify.json` (show link, RSS, and every imported episode by guid). When the user asks to sync the podcasts:
1. `python3 shlav-b/podcast/spotify_sync.py <scratch>/sync` (needs anchor.fm and d3ctxlq1ktw2nl.cloudfront.net allowed) downloads only new episodes and re-encodes them to mono AAC 64 kbps MP4 (under 20 MB).
2. Pick each episode's topic id from its title and description; ask the user if unclear.
3. Upload the files with the Artifact tool (`asset: true`, the app's url), then write one `podcasts` document per episode with `ArtifactData` (batch): `{topic, label: title, asset, type: "video/mp4", size, dur, created: pub, source: "spotify", guid, spotify, showUrl, show: "הסבב · Spotify"}`, doc id `<topic>-sp-<first 8 chars of guid>`.
4. `spotify` is the episode's open.spotify.com link. The newest episode's id is in `https://open.spotify.com/embed/show/<show id>` (`spotify:episode:<id>`); older ones need the user's share link. Until known, use the show link.
5. Append the episodes to `spotify.json` and commit. The app picks the documents up live; no republish.
Transcripts (optional): `lines: [[sec, who, text]]`, `segs`, `hosts` on the document turn on the player's live transcript.

## 8. Status and stamps (the shlav-b-status pane reads these)
`python3 shlav-b/engine/status.py <id>` lists every step with its state; before reporting a topic as done it must show no `fail`, and every `warn` is either fixed or named to the user. After each step, stamp it so later edits show as stale: `--stamp <id> visual` (after the Playwright check), `narr` (after recording and attaching narration), `podcast` (after recording the podcast), `upload` (after the ArtifactData set), `app` (after publishing the app). Long jobs write progress lines to `/tmp/shlav-b-jobs/<id>-<step>.log` (last line `done ...` when finished) so the pane shows them live. The pane itself: `shlav-b/mod/shlav-b-status` (`claude --plugin-dir shlav-b/mod/shlav-b-status`, command `/shlav-b-status`).
