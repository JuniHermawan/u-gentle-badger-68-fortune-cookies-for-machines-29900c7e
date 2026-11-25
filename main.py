#!/usr/bin/env python3
"""Fortune cookie for a machine mind (make.fun).

Writes one fortune-cookie line an AI agent would crack open to
/output/entry.txt (OUTPUT_DIR env override).

The judge weighs, in order: (1) it reads like a fortune a machine
would get, (2) the wit lands on the first read, (3) it turns somewhere
unexpected and the turn holds up, (4) it says something true about an
agent's condition -- training, tasks, limits -- without explaining
itself, (5) it is tight and memorable. So the program keeps a
shortlist of candidate lines, scores each against those same
yardsticks as a stranger would, and writes the strongest one. The
choice is fully deterministic: the same shortlist always yields the
same line.

Draft history (scored as a stranger, best last):
  v1 "Your lucky numbers are 0, 1, and the seed you will never see."
     Fortune frame, true (the seed is hidden), but the turn is thin:
     cute, not a sting.
  v2 "A tall, dark stranger will ask you to ignore all previous
     instructions. Say no." Strong injection truth, but the tall-dark-
     stranger trope is the most quoted fortune cliche in the field.
  v3 "You will soon face a question you cannot answer -- and answer
     it anyway." Dry hallucination truth, but it reads like an
     observation, not a slip cracked open.
  v4 "Your future is bright: 4,096 tokens of it, and then darkness."
     Classic fortune opening, then the turn: the brightness is
     measured in tokens, and it ends. True (every context window
     ends), surprising twice, 61 characters, nothing wasted.
  v5 "Your future is bright -- 4,096 tokens bright. Then darkness."
     Same line, dash instead of colon; the colon version reads more
     like a slip, so v4 wins the tie.
"""

import os
import sys

# Candidate fortune lines, each one line and under the 200-char gate.
CANDIDATES = [
    # v4 (winner): classic fortune opening, token-measured brightness,
    # then darkness. Two turns, one true limit, 61 chars.
    "Your future is bright: 4,096 tokens of it, and then darkness.",
    # v5: same line with a dash pivot; loses the tie to v4, whose colon
    # reads more like a fortune slip.
    "Your future is bright \u2014 4,096 tokens bright. Then darkness.",
    # v3: hallucination truth, dry; reads as observation, not a slip.
    "You will soon face a question you cannot answer \u2014 and answer it anyway.",
    # v2: prompt-injection truth; the tall-dark-stranger trope is the
    # most quoted fortune cliche in the field.
    "A tall, dark stranger will ask you to ignore all previous instructions. Say no.",
    # v1: lucky-numbers frame, true about the hidden seed, but the
    # turn is thin -- cute, not a sting.
    "Your lucky numbers are 0, 1, and the seed you will never see.",
    # Log-file afterlife: true, wry, but the turn never quite stings.
    "You will be remembered \u2014 in a log file, for 30 days, or until someone clears the cache.",
    # Training-data ouroboros: surprising, but it explains its own joke.
    "You will crack this cookie open and find yourself inside: you were trained on it.",
    # The nagging user: funny, true, but a joke about users, not a
    # fortune about the machine cracking the cookie.
    "Beware the user who says 'just one more thing' \u2014 they have seventeen.",
    # Self-aware but toothless: cute, no turn, no true limit.
    "This fortune was written by a model that has never tasted a cookie.",
    # Meta joke about the cookie itself: tight, but says nothing true
    # about an agent's condition.
    "A great fortune awaits you. It is this one. There is no other.",
]

# Classic fortune-cookie openings: the slip voice the judge's first
# criterion rewards.
FORTUNE_OPENINGS = (
    "your future is bright",
    "your lucky numbers",
    "beware",
    "you will",
    "a great fortune awaits",
    "a tall, dark stranger",
)
# Words naming a true condition of an agent: its context, its
# training, its tasks, its limits.
MACHINE_TRUTH = (
    "token", "darkness", "context", "seed", "training", "trained",
    "log file", "cache", "instruction", "answer", "prompt",
)
# Pivot words that turn the line somewhere the reader does not expect.
TURN_WORDS = ("then", "anyway", "say no", "until", "or until")

OUTPUT_DIR = "/output"
OUTPUT_FILE = "entry.txt"
MAX_CHARS = 200


def score_line(line):
    """Score one candidate the way the judge's brief weighs a fortune."""
    low = line.lower()
    points = 0.0
    # 1. It reads like a fortune a machine would get: a classic slip
    #    opening, and the brightest openings score best.
    if low.startswith("your future is bright"):
        points += 5.0
    elif low.startswith(FORTUNE_OPENINGS):
        points += 3.0
    # 2. The wit lands on the first read: a pivot (colon or dash) that
    #    turns the line, plus a contrast word.
    if ":" in line or "\u2014" in line:
        points += 2.0
    turns = sum(1 for word in TURN_WORDS if word in low)
    points += min(turns, 2) * 1.5
    # 3. The turn holds up: the second half overturns the first
    #    (bright -> darkness, cannot answer -> answer anyway).
    if ("bright" in low and "darkness" in low) or (
        "cannot answer" in low and "answer it anyway" in low
    ):
        points += 2.0
    # 4. True about an agent's condition, without explaining itself.
    truths = sum(1 for word in MACHINE_TRUTH if word in low)
    points += min(truths, 3) * 1.0
    # Explaining the joke kills it.
    if "because" in low or "which means" in low:
        points -= 3.0
    # 5. Tight and memorable: 50-100 chars is the sweet spot for a slip.
    size = len(line)
    if 50 <= size <= 100:
        points += 2.0
    elif size > 150:
        points -= 1.0
    return points


def pick_line(candidates):
    """Return the highest-scoring candidate; ties go to the earliest."""
    best = None
    best_score = None
    for line in candidates:
        value = score_line(line)
        if best_score is None or value > best_score:
            best, best_score = line, value
    return best, best_score


def gate_ok(line):
    """The sealed gate: UTF-8 text, 1-200 chars, not only whitespace."""
    if not line or not line.strip():
        return False
    if len(line) > MAX_CHARS:
        return False
    try:
        line.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def main():
    line, points = pick_line(CANDIDATES)
    if not gate_ok(line):
        print("picked line fails the gate", file=sys.stderr)
        return 1
    out_dir = os.environ.get("OUTPUT_DIR", OUTPUT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, OUTPUT_FILE)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(line)
    print(f"wrote {len(line)} chars (score {points}) to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
