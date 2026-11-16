# Pack format (schema 1)

A pack is one JSON object per topic. All user-facing text is Hebrew. The app renders whatever modes a pack contains; every mode is optional, but a pack needs at least one.

```jsonc
{
  "id": "stones",              // topic id from shlav-b-data.json
  "schema": 1,
  "title": "אבנים בכליות: טיפול ומניעה",
  "updated": "2026-11-16",     // YYYY-MM-DD
  "sources": [ { "label": "full citation", "kind": "AFP|Goroll|IMA|Society|Nelson|TaskForce", "year": 2019, "outOfWindow": false } ],

  "reel": {                    // mode: סרטון אינטראקטיבי (scrubbable, animated, one chapter per key idea)
    "chapters": [ {
      "id": "burden", "label": "short tab label", "eyebrow": "section", "title": "headline that states the point",
      "lede": "one or two sentences", "cap": "caption under the visual",
      "points": [[0.04, "51%", "point text, may contain <b>bold</b>"]],   // [reveal at 0..1, key (number/term), text]
      "pearl": [0.9, "board pearl"],
      "scene": { "type": "stats", "...": "fields per type below" }
    } ]
  },

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

## Reel scene catalog

Each chapter's `scene.type` picks one animated template. Pick the one that shows the idea; never decorate.

| type | use it for | fields |
|---|---|---|
| `stats` | prevalence, burden, a headline percentage | `pct` (0–100, fills a 100-dot grid), `waffleLabel`, `pctLabel`, `stats:[{v,l,tone}]` (≤2), optional `ring:{n,label}` (a subset of the filled dots) |
| `cycle` | 3–6 types/classes that take turns | `items:[{name,short,tone,tag,text}]` (chips jump to each) |
| `map` | a questionnaire answer → category, optional score bar | `header`, `rows:[{k,l,to,tone}]` (≤5), optional `bar:{title,max,parts:[{n,label,sub,tone}],note}` |
| `tiles` | mnemonics, lists of 4–12 named items | `tiles:[{k,a,b,tone}]` (`k` big letter/word; Latin letters read left-to-right automatically) |
| `bins` | items that sort into 2–4 groups (drugs by mechanism, causes by system) | `bins:[{h,out,tone,items:[]}]`, `note` |
| `sort` | do vs don't (tests to order or skip, what helps or not) | `cols:[{label,tone},{label,tone}]`, `cards:[{c:0|1,t,s}]` (≤8) |
| `threshold` | numbers that decide management (sizes, volumes, angles, days, scores) | `rulers:[{title,min,max,unit,step,target,ticks:[],zones:[{from,to,label,tone,msg}]}]` (1–2) |
| `flow` | the algorithm: a chain of decisions with side exits | `nodes:[{t,exit,exitLabel,nextLabel}]` (≤7), `end` |
| `regimen` | a dosing or exercise rhythm plus key numbers | `title`, `pulses`, `pulseLabel`, `footer`, `chips:[{v,l,tone}]` (≤4), optional `nnt`, `nntLabel` |
| `ladder` | escalation of treatment | optional `block:{title,cross,lines}` (what not to do), `steps:[{t,lines}]` (≤5, bottom to top) |
| `timeline` | schedules and follow-up intervals | `span`, `unit`, `ticks`, `rows:[{label,tone,events:[],bar:[from,to],note}]` (≤5) |
| `bars` | ranges on one scale (cost, dose, rates) | `max`, `prefix`, `unit`, `ticks`, `rows:[{l,lo,hi,tone}]` (≤10), `legend:[[label,tone]]` |
| `flags` | red flags and referral, then next steps | `flags:[{t,s}]` (≤9), `banner`, `cards:[{h,lines}]` (≤3) |
| `recap` | the SORT recommendations with their grades | `cards:[{t,s,badge}]` (≤5) |

Tones: `teal`, `rose`, `amber`, `muted`, `ink`. Keep every label short: the visual is 600×440 and Hebrew text does not wrap except in `cycle`, `tiles` and `bins` headers.

## Game

The game is generated from `drills`, `pathway` and `oral`; there is nothing extra to write. `drillSections` become shifts (with hearts, combo, golden patients, stars and a final mixed round), `pathway` becomes case rounds with the rebuild-from-memory finale, and `oral` becomes the oral boards with follow-ups and spaced repetition. A `num` drill can show a visual dial with `"v": "gauge" | "angle" | "waffle"` (gauge for volumes, angle for degrees 0–90, waffle for a percentage 0–100).
