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

## 4. Validate
`python3 shlav-b/engine/validate_pack.py shlav-b/packs/<id>.json` must print OK. Fix every ERROR; fix warnings unless there is a reason.

## 5. Save and upload
1. Save to `shlav-b/packs/<id>.json`.
2. Upload to the app's database with the `ArtifactData` tool: `action: "set"`, `url: "https://claude.ai/artifact/QmSkYmiFQTpwUvm1omtrGb"`, `collection: "packs"`, `doc_id: "<id>"`, `file_path: "shlav-b/packs/<id>.json"`. If the document exists, `get` it first and pass its `version` as `if_version`. The app picks the pack up live; no republish needed.
3. Commit the pack on the working branch.

## 6. Report to the user (in Hebrew)
Which sources were read (title, year, Drive folder), what is missing or out of window, the conflicts found, and the pack size (drills, cases, oral questions). Name anything in the pack that rests on clinical reasoning rather than an explicit source statement.
