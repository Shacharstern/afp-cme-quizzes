---
name: shlav-b-pack
description: Turn one Shlav B topic (family medicine board, Israel) into a Hebrew study pack for the Shlav B prep app — summary, fact drills, a patient pathway with cases, and oral-exam questions with examiner follow-ups — built only from the topic's anchor sources in the user's Google Drive folder "שלב א", validated, saved to shlav-b/packs/, and uploaded to the app. Use when the user types /shlav-b-pack <topic-id> or asks to build, rebuild or update a study pack (חבילת לימוד) for a Shlav B topic.
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
- **Sizes:** summary 8–12 sections; drills 25–60 with mixed `pick`/`swipe`/`num`, every one with a `w` (why); 3–6 cases; oral 2–4 stations × 2–4 questions, each with a follow-up. Keep the pack under 240 KB.
- **Hebrew style:** short sentences, no filler, the way a senior family physician would explain it. Quote-like marks inside strings: use ״ and ׳, not ASCII double quotes.

## 4. Validate
`python3 shlav-b/engine/validate_pack.py shlav-b/packs/<id>.json` must print OK. Fix every ERROR; fix warnings unless there is a reason.

## 5. Save and upload
1. Save to `shlav-b/packs/<id>.json`.
2. Upload to the app's database with the `ArtifactData` tool: `action: "set"`, `url: "https://claude.ai/artifact/QmSkYmiFQTpwUvm1omtrGb"`, `collection: "packs"`, `doc_id: "<id>"`, `file_path: "shlav-b/packs/<id>.json"`. If the document exists, `get` it first and pass its `version` as `if_version`. The app picks the pack up live; no republish needed.
3. Commit the pack on the working branch.

## 6. Report to the user (in Hebrew)
Which sources were read (title, year, Drive folder), what is missing or out of window, the conflicts found, and the pack size (drills, cases, oral questions). Name anything in the pack that rests on clinical reasoning rather than an explicit source statement.
