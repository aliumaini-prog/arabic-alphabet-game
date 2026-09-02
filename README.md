# Balloon Qaida — Arabic alphabet game

A balloon game for teaching the Arabic alphabet and Qaida reading. Balloons rise
at a speed you control; the student sounds out what's on the balloon **before it
escapes**. The teacher is the judge: click a balloon to pop it (+1), let it reach
the top and it counts as a miss.

**Play:** https://aliumaini-prog.github.io/arabic-alphabet-game/

## How to use in a lesson

- Pick a level, set **Rise time** (difficulty) and **Spawn gap** (how busy the sky gets).
- Student says the letter/sound aloud → click the balloon.
- **Spacebar** pauses. Pause or Reset shows **"Missed — drill these"**, sorted by
  how often each item was fumbled — that's your list for next lesson.

## Levels

1. Huroof (letter names)
2. Zabar (Fatha) · 3. Zer (Kasra) · 4. Pesh (Damma)
5. **Mixed harakat** — zabar/zer/pesh interleaved. The only level with mic auto-pop.
6. Tanween · 7. Jazm (Sukoon) · 8. Tashdeed (Shadda) · 9. Madd
10. Two-letter joins · 11. Three-letter joins · 12. Four-letter joins

## Mic auto-pop (level 5 only)

Turn on **Mic**, say the vowel, and the balloon pops by itself. It calibrates to
whoever is speaking first — six prompts, hands-free — so it works for a child's
voice as well as an adult's. Audio never leaves the device; there is no model and
no network call, just an FFT.

It judges the **vowel**, not the letter. That is why it runs on level 5 and
nowhere else: every other level has a single vowel throughout, so listening for
one would pop any balloon regardless of the letter shown. It also cannot catch a
wrong consonant — a child saying "tu" at بُ will pop it.

Requires **https** (or localhost), so use the GitHub Pages link, not a local file.
Recalibrate for a new student by clicking Mic while it is already on.

## Editing the content

Everything lives in one file, `index.html`. The `LEVELS` array sits at the very
top of the `<script>` block — add, remove or reorder items there without touching
any game code. Levels 2–5 are generated from the 29 huroof; 6–11 are written out.

## Checking your edits

Open `index.html#test` — it verifies the level data (correct harakat codepoints,
no duplicates, expected item counts) and prints pass/fail.

## Running locally

No build, no dependencies. Open `index.html` in a browser.
