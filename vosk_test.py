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
    HARAKAT = set('ًٌٍَُِّْ')
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

        marked = sum(1 for w in vocab if HARAKAT & set(w))
        print(f"  vowelled: {marked} of {len(vocab):,} entries carry any harakat")

        # The honest test: is the item present AS WRITTEN, vowels and all?
        # Checking the stripped form instead flatters the model - stripping is
        # precisely the information Qaida is teaching.
        print("\n  can the model's vocabulary express our items AS WRITTEN?")
        for lv in sorted(LEVELS):
            items = LEVELS[lv]
            exact = sum(1 for i in items if i in vocab)
            print(f"    level {lv:<2} {exact:>3}/{len(items):<3} exact  "
                  f"{'ok' if exact else 'DEAD - vowelled form not in lexicon'}")
        names = sum(1 for n in NAMES.values() if n in vocab)
        print(f"    letter NAMES  {names}/{len(NAMES)}  "
              f"{'ok - these are real words' if names else 'DEAD'}")

        # And the reason it is dead: whole levels become indistinguishable.
        print("\n  what the model can actually emit (harakat stripped):")
        seen = {}
        for lv in sorted(LEVELS):
            key = tuple(sorted({strip(i) for i in LEVELS[lv]}))
            same = [o for o, k in seen.items() if k == key]
            seen[lv] = key
            note = f"IDENTICAL to level {same[0]}" if same else ""
            print(f"    level {lv:<2} -> {len(key):>3} distinct strings   {note}")

        collapsed = [lv for lv in seen if any(seen[o] == seen[lv] and o < lv for o in seen)]
        if collapsed:
            print(f"\n  VERDICT: levels {collapsed} collapse onto earlier levels.")
            print("  The lexicon is unvocalised, so bin/zer/pesh are the same output.")
            print("  Even at 100% acoustic accuracy this model cannot tell them")
            print("  apart. Word-level Arabic ASR is the wrong tool - see the notes")
            print("  at the bottom of this file.")
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


# ---------------------------------------------------------------- 4. vowels
# The vowel is what word-level ASR discards, but acoustically it is the EASY
# half: /a/ /i/ /u/ sit in well-separated regions of the F1/F2 plane. If they
# separate for your students, the Qaida distinction is recoverable without ASR.
VOWELS = [('zabar', F, 'a'), ('zer', K, 'i'), ('pesh', D, 'u')]
VCONS  = list('بتدسك')
VDIR   = Path('vowels')

def _lpc(x, p):
    """Levinson-Durbin. Returns LPC coefficients, or None if degenerate."""
    import numpy as np
    r = np.array([float(np.dot(x[:len(x) - k], x[k:])) for k in range(p + 1)])
    if r[0] <= 0:
        return None
    a, e = np.zeros(p + 1), r[0]
    a[0] = 1.0
    for i in range(1, p + 1):
        acc = r[i] + (np.dot(a[1:i], r[i - 1:0:-1]) if i > 1 else 0.0)
        k = -acc / e
        prev = a.copy()
        for j in range(1, i):
            a[j] = prev[j] + k * prev[i - j]
        a[i] = k
        e *= (1 - k * k)
        if e <= 0:
            return None
    return a

def formants(path):
    """F1,F2 from the steady-state middle of a clip, via LPC root angles."""
    import numpy as np
    with wave.open(str(path), 'rb') as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    if len(x) < sr // 4:
        return None
    x = x[len(x) // 4: 3 * len(x) // 4]            # middle 50%, skip onset/release
    if np.max(np.abs(x)) < 200:                     # essentially silence
        return None
    x = np.append(x[0], x[1:] - 0.97 * x[:-1])      # pre-emphasis
    x = x * np.hamming(len(x))
    a = _lpc(x, 2 + sr // 1000)
    if a is None:
        return None
    rts = np.roots(a)
    rts = rts[np.imag(rts) > 0.01]
    if not len(rts):
        return None
    f  = np.arctan2(np.imag(rts), np.real(rts)) * sr / (2 * np.pi)
    bw = -0.5 * (sr / (2 * np.pi)) * np.log(np.abs(rts))
    # Band-limited pick. Taking the two lowest poles outright lets a spurious
    # wide resonance between F1 and F2 pose as F2 - which wrecks /i/, whose real
    # F2 sits up near 2800 Hz. Real formants are narrow, artifacts are wide, so
    # try a tight bandwidth first and only relax it if that finds nothing.
    for maxbw in (200, 400):
        cand = np.sort(f[(f > 90) & (f < 4500) & (bw < maxbw)])
        f1 = next((v for v in cand if 200 <= v <= 1300), None)
        if f1 is None:
            continue
        f2 = next((v for v in cand if max(f1 + 250, 700) <= v <= 3800), None)
        if f2:
            return (f1, f2)
    return None

def vowels_cmd(record_first, reps, folder=None):
    import numpy as np
    vdir = Path(folder) if folder else VDIR
    if record_first:
        try:
            import sounddevice as sd
        except ImportError:
            die("needs sounddevice + numpy:  pip install sounddevice")
        vdir.mkdir(exist_ok=True)
        n = len(VCONS) * len(VOWELS) * reps
        print(f"{n} clips: {len(VCONS)} letters x 3 vowels x {reps}. Enter before each.\n")
        for rep in range(reps):
            for c in VCONS:
                for name, mark, _ in VOWELS:
                    input(f"  say:  {c + mark}   ({name}, take {rep+1})  (enter) ")
                    au = sd.rec(int(1.5 * SR), samplerate=SR, channels=1, dtype='int16')
                    sd.wait()
                    with wave.open(str(vdir / f"{ord(c):04x}_{name}_{rep}.wav"), 'wb') as w:
                        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                        w.writeframes(au.tobytes())
        print()

    pts = {v: [] for v, _, _ in VOWELS}
    for f in sorted(vdir.glob('*.wav')):
        parts = f.stem.split('_')
        if len(parts) < 2 or parts[1] not in pts:
            continue
        F = formants(f)
        if F:
            pts[parts[1]].append((F, chr(int(parts[0], 16))))
    total = sum(len(v) for v in pts.values())
    if total < 6:
        die(f"only {total} usable clips in {vdir}/ - run:  vosk_test.py vowels --record")

    print(f"{'vowel':<8}{'n':>4}   {'F1 mean':>9}{'F2 mean':>9}   (Hz)")
    for v, _, ipa in VOWELS:
        if pts[v]:
            arr = np.array([p[0] for p in pts[v]])
            print(f"  /{ipa}/{'':<4}{len(arr):>4}   {arr[:,0].mean():>9.0f}{arr[:,1].mean():>9.0f}")

    # Leave-one-out nearest centroid: can we name the vowel from F1/F2 alone?
    flat = [(np.array(F), v) for v in pts for F, _ in pts[v]]
    hits = 0
    for i, (F, truth) in enumerate(flat):
        cent = {}
        for j, (G, v) in enumerate(flat):
            if i != j:
                cent.setdefault(v, []).append(G)
        guess = min(cent, key=lambda v: np.linalg.norm(F - np.mean(cent[v], axis=0)))
        hits += (guess == truth)
    pct = 100 * hits // len(flat)
    print(f"\n  leave-one-out vowel identification: {hits}/{len(flat)} = {pct}%")
    print("  (chance is 33%)")
    if pct >= 85:
        print("\n  Zabar/zer/pesh ARE separable in these voices. The half that ASR")
        print("  throws away is recoverable with no model at all.")
    elif pct >= 60:
        print("\n  Partial separation. More takes per vowel, or a real classifier,")
        print("  would likely push this up - but it is not free.")
    else:
        print("\n  Not separable this way. Custom acoustic work is a research")
        print("  project, not a feature. Ship teacher-judged instead.")

def die(msg):
    print(msg, file=sys.stderr); sys.exit(1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['check', 'record', 'score', 'vowels'])
    ap.add_argument('--n', type=int, default=20, help='clips to record')
    ap.add_argument('--secs', type=float, default=2.0, help='seconds per clip')
    ap.add_argument('--dir', default=str(CLIPS), help='folder of wavs to score')
    ap.add_argument('--record', action='store_true', help='vowels: capture clips first')
    ap.add_argument('--reps', type=int, default=2, help='vowels: takes per letter')
    a = ap.parse_args()
    if   a.cmd == 'check':  check()
    elif a.cmd == 'record': record(a.n, a.secs)
    elif a.cmd == 'vowels': vowels_cmd(a.record, a.reps, a.dir if a.dir != str(CLIPS) else None)
    else:                   score(a.dir)

# ---------------------------------------------------------------------------
# RESULT ON vosk-model-ar-mgb2-0.4 (measured, Sept 2026)
#
#   grammar:  NO  - static HCLG.fst, no runtime vocabulary restriction
#   lexicon:  957,745 entries, of which 9 carry any harakat (all typos)
#
# So levels 1-5 all collapse to the same 29 unvocalised strings. This is not a
# tuning problem. General Arabic ASR is trained and decoded on UNVOCALISED text
# because that is how Arabic is written - the vowels are inferred by the reader,
# not transcribed. Qaida teaches exactly those vowels. The tool discards the
# lesson.
#
# That single fact also explains everything else we hit: Azure returns empty
# phoneme fields for Arabic, and the Web Speech API maps syllables onto real
# words. Switching vendors does not help; they share the assumption.
#
# What is left, in order of effort:
#
#   1. PHONEME recognition instead of word recognition. Models like wav2vec2
#      IPA variants emit /ba/ /bi/ /bu/ as distinct phoneme strings, so vowels
#      survive. This is the most promising off-the-shelf path.
#   2. Split the problem. The vowel is the part ASR throws away, but it is the
#      EASY part acoustically - /a/ /i/ /u/ separate cleanly on formants F1/F2.
#      Run `vowels` below to see whether that holds for your students.
#   3. Train a classifier over the closed ~300-item set from clips/.
# ---------------------------------------------------------------------------
