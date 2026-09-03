# Qaidah — Arabic reading game

A game built directly on *Qaidah — تعليم القرآن، الجزء الاول* (Imaani Schools,
Aljamea-tus-Saifiyah). **Every item comes from the book**, and every level names the
page it came from, so the screen matches the page open in front of the child.

**Play:** https://aliumaini-prog.github.io/arabic-alphabet-game/

## Levels (Lessons 1–3, book pages 1–35)

| Level | Book | What it tests |
|---|---|---|
| 1a | p1 | Name each of the 28 letters. ق is *qaaf*, ك is *kaaf*. |
| 2a | p3–5 | **Letter forms** — the same letter alone, at the start, in the middle, at the end. No harakat. Self-scoring. |
| 2b | p6–10 | Two letters joining, shown apart → pale → joined, as the book prints it. |
| 2c | p11–16 | Three-letter words; the target letter is red so its position is what's tested. |
| 2d | p17–18 | **حروف القطع** — ا د ذ ر ز و join to the letter before, never the one after. |
| 3a / 3c / 3e | p20 / 25 / 30 | Every letter with zabar / zer / pesh. The 8 letters the book stars (خ ر ص ض ط ظ غ ق) carry a **جاڑو** badge. |
| 3b | p21–24 | Words where every mark is zabar. |
| 3d | p26–29 | Zabar and zer together, **zer in red**. |
| 3f | p31–35 | Pesh in red, including the two-word items from p35. |

509 items in total.

## Using it in a lesson

- Type the **student's name** — score and missed items are kept per student.
- Pick the lesson and level; the yellow badge shows the **book page**.
- Balloon levels: child says it aloud, you tap to pop. Spacebar pauses.
- **Report** lists what each student missed, grouped by level, with the page to reopen.

## Editing content

One file, `index.html`. The content block at the top is separated from the engine —
letters, pairs, words and the lesson table are all there, each labelled with its book
page. Nothing else needs touching to add or correct an item.

## Checking your edits

Open `index.html#test` — 39 checks on the content: 28 letters, correct harakat
codepoints, zabar words containing no zer or pesh, قطع words that really break where
they claim to, no duplicates. Run it after any content change.

## Not included yet

Lessons 4–7 (madd, sukoon, qalqalah, tanween, tashdeed — book pages 36–110) drop into
the same table when wanted. The microphone experiments live in `vosk_test.py` and
`mic-test.html`; auto-pop is currently switched off.
