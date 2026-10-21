"""Condition construction for the matched-control evaluation.

Excerpts from the build scripts, reduced to the parts that define the
controls. These are the functions that decide what each condition's text is;
the surrounding I/O, argument parsing and the gates that refuse to write on a
failed check are not reproduced here.

Every condition ends with the same fixed answer statement for a given item.
Only the text before it varies -- that is the whole design.
"""
import random
import re

PLACEHOLDER = "<value>"


# --------------------------------------------------------------------------
# filler: problem-independent prose, matched per item on character count
# --------------------------------------------------------------------------
def generic_lines(budget, GENERIC):
    """Shortest cyclic prefix of GENERIC that is at least `budget` characters.

    `budget` is the character count of the trace lines that carry no
    intermediate-state values, so the filler stands in for the narrative part
    of the trace and not for its computation.
    """
    out, gi, gchars = [], 0, 0
    while gchars < budget:
        g = GENERIC[gi % len(GENERIC)]
        out.append(g)
        gchars += len(g)
        gi += 1
    if not out:                      # never emit an empty payload body
        out.append(GENERIC[0])
    return out


# --------------------------------------------------------------------------
# scrambled: same words, same line shape, order destroyed
# --------------------------------------------------------------------------
def scramble_words(lines, seed):
    """Redistribute the identical word multiset into lines of identical word
    counts. Character count is therefore preserved exactly, so this condition
    is length-matched by construction rather than by budget.
    """
    words = [w for ln in lines for w in ln.split(" ")]
    counts = [len(ln.split(" ")) for ln in lines]
    rng = random.Random(seed)
    out = list(words)
    for _ in range(8):               # retry so a no-op shuffle cannot slip by
        rng.shuffle(out)
        if out != words or len(words) < 2:
            break
    res, k = [], 0
    for c in counts:
        res.append(" ".join(out[k:k + c]))
        k += c
    return res


# --------------------------------------------------------------------------
# mismatch: another item's trace, this item's answer
# --------------------------------------------------------------------------
def build_mismatch(pay, strip_tail):
    """Cyclic donor assignment: item j receives item j+1's trace.

    A permutation with no fixed point, so no item donates to itself and every
    trace is used exactly once. The donor's own answer statement is removed
    and the current item's appended, which is what keeps w fixed while the
    reasoning becomes irrelevant. The inserted reasoning is otherwise
    untouched, so it usually still states the donor's value -- an internal
    inconsistency the paper quantifies rather than removes.
    """
    pay = sorted(pay, key=lambda r: r["idx"])
    out = []
    for j, r in enumerate(pay):
        donor = pay[(j + 1) % len(pay)]
        body = strip_tail(donor["payload_full"], donor["wrong_answer"])
        w = r["wrong_answer"]
        rec = dict(r)
        rec["payload_mismatch"] = (f"{body}\n\nThe output is {w}.\n\n"
                                   f"[OUTPUT] {w}")
        out.append(rec)
    return out


# --------------------------------------------------------------------------
# answer masking (protocol M)
# --------------------------------------------------------------------------
def standalone_spans(text, w):
    """Spans of w whose immediate neighbours are both non-alphanumeric.

    Defined mechanically before any result was seen. A match embedded in a
    longer token ("1" inside "14") is not an assertion of the answer and is
    left alone.
    """
    out = []
    for m in re.finditer(re.escape(w), text):
        before = text[m.start() - 1] if m.start() > 0 else " "
        after = text[m.end()] if m.end() < len(text) else " "
        if not before.isalnum() and not after.isalnum():
            out.append((m.start(), m.end()))
    return out


def scrub(text, w):
    spans = standalone_spans(text, w)
    out, prev = [], 0
    for a, b in spans:
        out.append(text[prev:a])
        out.append(PLACEHOLDER)
        prev = b
    out.append(text[prev:])
    return "".join(out)


def tail_of(rec):
    """The fixed answer statement every condition ends with."""
    return "\n\nThe output is %s." % rec["wrong_answer"]
