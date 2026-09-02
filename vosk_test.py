#!/usr/bin/env python3
"""
Does grammar-constrained Vosk recognise Qaida items spoken by your students?

Throwaway diagnostic. Answers three questions, cheapest first, and STOPS as soon
as one of them is fatal - so you don't run a recording session to discover the
model was never going to work.

  1. check   Is the model grammar-capable, and does its lexicon even contain our
             items? (no recording needed - run this first)
  2. record  Capture student attempts as 16kHz wav
  3. score   Recognise them, open-vocabulary vs grammar-constrained, and report

Usage:
    python3 vosk_test.py check
    python3 vosk_test.py record --n 20
    python3 vosk_test.py score
    python3 vosk_test.py score --dir some/other/folder
"""
import argparse, json, os, re, sys, wave
from pathlib import Path

MODEL = Path(os.environ.get('VOSK_MODEL', 'vosk-model-ar-mgb2-0.4'))
CLIPS = Path('clips')
SR    = 16000

# ---------------------------------------------------------------- items
# Mirrors the LEVELS data in index.html. Duplicated deliberately: this file is a
# throwaway, and coupling it to the game would outlive its usefulness.
F, K, D   = 'َ', 'ِ', 'ُ'
FN, DN, KN= 'ً', 'ٌ', 'ٍ'
SH, SK    = 'ّ', 'ْ'
BASE = list('ابتثجحخدذرزسش'
            'صضطظعغفقكلمنو'
            'هءي')
CONS = [l for l in BASE if l not in ('ا', 'ء')]

LEVELS = {
    1: BASE,
    2: [l + F for l in BASE],
    3: [l + K for l in BASE],
    4: [l + D for l in BASE],
    5: [l + m for l in BASE for m in (FN, KN, DN)],
    6: ['أ' + F + l + SK for l in CONS],
    7: ['أ' + F + l + SH + F for l in CONS],
    8: [l + v for l in 'بتجدرسكلمن'
        for v in (F + 'ا', K + 'ي', D + 'و')],
    10: ['كَتَبَ', 'ذَهَبَ',
         'نَصَرَ', 'فَتَحَ',
         'عَلِمَ', 'سَمِعَ'],
}
ALL = [it for lv in sorted(LEVELS) for it in LEVELS[lv]]

# Names are real Arabic words, unlike the bare letters - the lexicon check below
# is expected to treat these very differently, and that contrast is the point.
NAMES = {'ا':'ألف','ب':'باء','ت':'تاء',
         'ج':'جيم','ح':'حاء','ص':'صاد',
         'ع':'عين','ق':'قاف','ه':'هاء'}

strip = lambda s: re.sub('[ً-ْٰـ]', '', s)

# ---------------------------------------------------------------- 1. check
def check():
    if not MODEL.is_dir():
        die(f"Model not found at ./{MODEL}\n\n"
            "  curl -LO https://alphacephei.com/vosk/models/vosk-model-ar-mgb2-0.4.zip\n"
            "  unzip vosk-model-ar-mgb2-0.4.zip\n\n"
            "  318MB. That is the smallest Modern Standard Arabic model there is;\n"
            "  the only smaller Arabic model is Tunisian dialect, wrong for Qaida.")

    print(f"model: {MODEL}")
    g = MODEL / 'graph'

    # (a) grammar capability - static HCLG means no runtime grammar, full stop
    if (g / 'HCLG.fst').exists():
        gram = False
        print("  grammar:  NO - static HCLG.fst, vocabulary is fixed at build time")
    elif (g / 'HCLr.fst').exists() and (g / 'Gr.fst').exists():
        gram = True
        print("  grammar:  YES - dynamic graph (HCLr.fst + Gr.fst)")
    else:
        gram = None
        print("  grammar:  UNKNOWN - unexpected graph layout, try score anyway")

    # (b) lexicon coverage - the check that usually decides it.
    # A grammar can only be built from words the model already knows. Bare
    # letters and vowelled syllables are very unlikely to be lexicon entries.
    words = g / 'words.txt'
    if not words.exists():
        words = MODEL / 'words.txt'
    if words.exists():
        vocab = set()
        with open(words, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                p = line.split()
                if p:
                    vocab.add(p[0])
        print(f"  lexicon:  {len(vocab):,} entries ({words.relative_to(MODEL)})")

        def cover(label, items):
            hit = [i for i in items if strip(i) in vocab]
            pct = 100 * len(hit) // max(1, len(items))
            mark = 'ok' if pct >= 70 else 'DEAD' if pct == 0 else 'weak'
            print(f"    {label:<22} {len(hit):>3}/{len(items):<3} in lexicon  {pct:>3}%  {mark}")
            return pct

        print("\n  can the model's vocabulary even express our items?")
        pcts = {lv: cover(f"level {lv}", LEVELS[lv]) for lv in sorted(LEVELS)}
        cover("letter NAMES (words)", list(NAMES.values()))

        if all(p == 0 for lv, p in pcts.items() if lv <= 8):
            print("\n  VERDICT: levels 1-8 are entirely out-of-vocabulary.")
            print("  A grammar cannot contain words the model has never seen, so")
            print("  constrained recognition of bare letters/syllables is not")
            print("  possible with this model. Only whole-word levels can work.")
            print("  Don't bother recording - see notes at the bottom of this file.")
    else:
        print("  lexicon:  words.txt not found - skipping coverage check")

    print(f"\n  items total: {len(ALL)}  (grammar would hold this many phrases)")
    return gram

# ---------------------------------------------------------------- 2. record
def record(n, secs):
    try:
        import sounddevice as sd
    except ImportError:
        die("needs sounddevice:  pip install sounddevice")
    import random
    CLIPS.mkdir(exist_ok=True)
    picks = random.sample(ALL, min(n, len(ALL)))
    print(f"Recording {len(picks)} items, {secs}s each. Enter to start each one.\n")
    for idx, item in enumerate(picks):
        input(f"  [{idx+1}/{len(picks)}]  say:  {item}   (enter) ")
        audio = sd.rec(int(secs * SR), samplerate=SR, channels=1, dtype='int16')
        sd.wait()
        path = CLIPS / f"{idx:03d}_{'-'.join('%04x' % ord(c) for c in item)}.wav"
        with wave.open(str(path), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(audio.tobytes())
    print(f"\nsaved {len(picks)} clips to {CLIPS}/ - keep them, they are a training set")

def item_of(path):
    """Recover the item from the filename's codepoint encoding."""
    stem = Path(path).stem
    try:
        return ''.join(chr(int(h, 16)) for h in stem.split('_', 1)[1].split('-'))
    except Exception:
        return None

# ---------------------------------------------------------------- 3. score
def score(folder):
    try:
        from vosk import Model, KaldiRecognizer, SetLogLevel
    except ImportError:
        die("needs vosk:  pip install vosk")
    SetLogLevel(-1)
    clips = sorted(Path(folder).glob('*.wav'))
    if not clips:
        die(f"no wav files in {folder}/ - run:  python3 vosk_test.py record")

    model = Model(str(MODEL))
    grammar = json.dumps(sorted({strip(i) for i in ALL}) + ['[unk]'], ensure_ascii=False)
    modes = [('open', None)]
    try:
        KaldiRecognizer(model, SR, grammar)
        modes.append(('grammar', grammar))
    except Exception as e:
        print(f"grammar rejected by this model: {e}\nfalling back to open vocabulary only\n")

    rows, tally = [], {m: 0 for m, _ in modes}
    for c in clips:
        want = item_of(c)
        if not want:
            continue
        heard = {}
        for mode, gram in modes:
            rec = KaldiRecognizer(model, SR, gram) if gram else KaldiRecognizer(model, SR)
            with wave.open(str(c), 'rb') as w:
                while True:
                    data = w.readframes(4000)
                    if not data:
                        break
                    rec.AcceptWaveform(data)
            txt = json.loads(rec.FinalResult()).get('text', '').strip()
            heard[mode] = txt
            if txt and strip(txt) == strip(want):
                tally[mode] += 1
        rows.append((want, heard))

    w1 = max((len(r[0]) for r in rows), default=8) + 2
    print(f"\n{'shown':<{w1}}" + ''.join(f"{m+' heard':<28}" for m, _ in modes))
    print('-' * (w1 + 28 * len(modes)))
    for want, heard in rows:
        line = f"{want:<{w1}}"
        for mode, _ in modes:
            got = heard[mode] or '(nothing)'
            mark = 'Y' if got and strip(got) == strip(want) else 'n'
            line += f"{mark} {got:<26}"
        print(line)

    n = len(rows)
    print(f"\n{n} clips")
    for mode, _ in modes:
        print(f"  {mode:<8} {tally[mode]}/{n} = {100*tally[mode]//max(1,n)}%")
    print("\n  Under ~70% on the grammar column means this path is not worth")
    print("  rebuilding the app around. See notes at the bottom of this file.")

def die(msg):
    print(msg, file=sys.stderr); sys.exit(1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['check', 'record', 'score'])
    ap.add_argument('--n', type=int, default=20, help='clips to record')
    ap.add_argument('--secs', type=float, default=2.0, help='seconds per clip')
    ap.add_argument('--dir', default=str(CLIPS), help='folder of wavs to score')
    a = ap.parse_args()
    if   a.cmd == 'check':  check()
    elif a.cmd == 'record': record(a.n, a.secs)
    else:                   score(a.dir)

# ---------------------------------------------------------------------------
# IF THE LEXICON CHECK COMES BACK DEAD
#
# It means the model's vocabulary has no entry for a bare letter or a vowelled
# syllable - only for real words. A Vosk grammar is assembled from known words,
# so it cannot be built for levels 1-8. Options, in order of effort:
#
#   1. Teach letter NAMES instead of sounds at level 1 (الف, باء) - those ARE
#      words, and the lexicon check prints their coverage separately so you can
#      see it. Doesn't help levels 2-8.
#   2. Extend the lexicon: Vosk/Kaldi models can be rebuilt with added
#      pronunciations, mapping each Qaida item to its phoneme sequence. Real
#      work, but it is the standard fix and it is well documented.
#   3. Drop ASR entirely and train a small classifier over the ~300-item closed
#      set from your own recordings. The clips/ folder from `record` is exactly
#      that dataset - which is why this script keeps them.
# ---------------------------------------------------------------------------
