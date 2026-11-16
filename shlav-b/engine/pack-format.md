# Pack format (schema 1)

A pack is one JSON object per topic. All user-facing text is Hebrew. The app renders whatever modes a pack contains; every mode is optional, but a pack needs at least one.

```jsonc
{
  "id": "stones",              // topic id from shlav-b-data.json
  "schema": 1,
  "title": "אבנים בכליות: טיפול ומניעה",
  "updated": "2026-11-16",     // YYYY-MM-DD
  "sources": [ { "label": "full citation", "kind": "AFP|Goroll|IMA|Society|Nelson|TaskForce", "year": 2019, "outOfWindow": false } ],

  "summary": {                 // mode: סיכום
    "oneLiner": "the whole topic in one or two sentences",
    "sections": [ { "h": "heading", "points": ["..."], "pearl": "one board pearl (optional)" } ]
  },

  "drillSections": [ { "id": "dx", "label": "אבחנה" } ],
  "decks": { "mf": ["מיתוס", "עובדה"], "rf": ["אפשר בקהילה", "הפניה מיידית"] },   // two labels: [answer 0, answer 1]
  "drills": [                  // mode: תרגול עובדות (no timer, streaks, repeat of misses)
    { "id": "s1", "sec": "dx", "k": "pick", "q": "question", "o": ["a", "b", "c"], "a": 0, "w": "why", "fixed": false },
    { "id": "s2", "sec": "dx", "k": "swipe", "d": "rf", "q": "statement", "a": 1, "w": "why" },
    { "id": "s3", "sec": "dx", "k": "num", "q": "question", "min": 0, "max": 20, "step": 1, "lo": 10, "hi": 10, "near": 2, "u": " מ״מ", "start": 4, "w": "why" }
  ],
  // pick: options are shuffled unless "fixed": true (use fixed for category lists the learner should see in a stable order)
  // num: correct when lo ≤ value ≤ hi; "close" (half credit) within `near`; `start` must sit outside lo..hi

  "pathway": {                 // mode: מסלול מקרים (walk patients through the algorithm, then rebuild it from memory)
    "name": "מסלול …",
    "stations": [ { "k": "urgent", "t": "short name", "sb": "subtitle", "rule": "what this station always involves" } ],
    "cases": [ { "id": "k1", "name": "first name", "age": 34, "story": "vignette", "out": "outcome",
                 "steps": [ { "st": "urgent", "q": "decision", "o": ["right", "wrong", "wrong"], "a": 0, "w": "why" } ] } ]
  },

  "oral": [                    // mode: בחינה בעל פה (answer aloud, flip key points: said / partial / missed)
    { "id": "so1", "t": "station name", "d": "subtitle",
      "q": [ { "id": "so1a", "k": "בוחן | ייעוץ · שיחה עם …", "q": "examiner question",
               "f": "structure line to open the answer",
               "p": ["key point", "..."],
               "fu": { "q": "follow-up twist", "f": "structure line", "p": ["..."] } } ] }
  ]
}
```

IDs must be unique within a pack (drills, oral questions). Oral question ids feed spaced repetition: changing an id resets that question's history, so keep ids stable when updating a pack.

Validate with `python3 shlav-b/engine/validate_pack.py <pack.json>`.
