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
5. Tanween · 6. Jazm (Sukoon) · 7. Tashdeed (Shadda) · 8. Madd
9. Two-letter joins · 10. Three-letter joins · 11. Four-letter joins

## Editing the content

Everything lives in one file, `index.html`. The `LEVELS` array sits at the very
top of the `<script>` block — add, remove or reorder items there without touching
any game code. Levels 2–5 are generated from the 29 huroof; 6–11 are written out.

## Checking your edits

Open `index.html#test` — it verifies the level data (correct harakat codepoints,
no duplicates, expected item counts) and prints pass/fail.

## Running locally

No build, no dependencies. Open `index.html` in a browser.
