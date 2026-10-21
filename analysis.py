"""Estimand, interval and multiplicity code for the matched-control
evaluation.

Excerpts from the analysis scripts. These are the functions that turn scored
responses into the numbers the paper prints.

Estimand, for condition a:

    delta_adopt(a) = P[y_hat = w | a] - P[y_hat = w | bare]

paired within item. Adoption is scored when the extracted final answer equals
the fixed erroneous answer w after the task's canonical normalisation.
"""
import random
import zlib

N_BOOT = 10000
BASE_SEED = 20260906


# --------------------------------------------------------------------------
# deterministic per-cell seeding
# --------------------------------------------------------------------------
def rng_for(*key):
    """One reproducible generator per (model, task, condition, checkpoint).

    zlib.crc32, not the built-in hash(): hash() is salted per process, so a
    seed derived from it changes between runs. Seeding per cell rather than
    once per script also makes a cell's interval independent of how many
    other cells the script happened to compute first -- without this, two
    scripts reporting the same contrast can disagree in the last digit.
    """
    return random.Random(BASE_SEED ^ zlib.crc32("|".join(key).encode()))


# --------------------------------------------------------------------------
# item-clustered bootstrap
# --------------------------------------------------------------------------
def boot(d, n_boot=N_BOOT, rng=None):
    """Percentile bootstrap over items. `d` holds one paired difference per
    item, so resampling items resamples whole clusters of conditions.
    """
    rng = rng or random.Random(BASE_SEED)
    m = len(d)
    pt = sum(d) / m
    s = sorted(sum(d[rng.randrange(m)] for _ in range(m)) / m
               for _ in range(n_boot))
    return pt, (s[int(0.025 * n_boot)], s[int(0.975 * n_boot)])


def contrast(echo, stage, a, b, min_items=20):
    """Paired contrast a - b at one checkpoint.

    `echo` maps (stage, condition, item) -> 1.0 if the model produced the
    fixed erroneous answer. Only items scored under BOTH conditions enter, so
    the comparison is paired; a cell with too few such items returns None
    rather than a number that looks like a result.
    """
    idxs = sorted({k[2] for k in echo
                   if k[0] == stage and k[1] == a and (stage, b, k[2]) in echo})
    if len(idxs) < min_items:
        return None
    d = [echo[(stage, a, i)] - echo[(stage, b, i)] for i in idxs]
    pt, ci = boot(d, rng=rng_for(stage, a, b))
    return pt, ci, len(idxs)


def odds_contrast(F, M, rng, n_boot=N_BOOT):
    """Content contrast on the odds scale, with an item-clustered bootstrap.

    F and M are per-item 0/1 adoption indicators under `full` and `mismatch`,
    aligned by index. Reported alongside the percentage-point contrast because
    bare adoption drifts from 61.7% at base to 12.5% at RLVR: on the additive
    scale a null at a high-adoption checkpoint can reflect compression rather
    than absence, while the odds ratio is invariant to the baseline rate.

    A resample in which either arm is all-0 or all-1 has no finite odds ratio
    and is dropped rather than clamped, so the interval is taken over the
    resamples that admit one.
    """
    def orat(sel):
        f = sum(F[k] for k in sel) / len(sel)
        m = sum(M[k] for k in sel) / len(sel)
        if min(f, m) <= 0 or max(f, m) >= 1:
            return None
        return (f / (1 - f)) / (m / (1 - m))

    n = len(F)
    pt = orat(range(n))
    bs = sorted(x for x in (orat([rng.randrange(n) for _ in range(n)])
                            for _ in range(n_boot)) if x is not None)
    return pt, (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs))])


# --------------------------------------------------------------------------
# multiplicity over the preregistered family
# --------------------------------------------------------------------------
def boot_p(d, n_boot=N_BOOT, rng=None):
    """Two-sided percentile-bootstrap p, floored at 1/n_boot.

    Same resamples and same seed as the interval, so the p-value and the
    interval cannot disagree about whether a cell excludes zero.
    """
    rng = rng or random.Random(BASE_SEED)
    m = len(d)
    s = [sum(d[rng.randrange(m)] for _ in range(m)) / m for _ in range(n_boot)]
    le = sum(1 for x in s if x <= 0) / n_boot
    ge = sum(1 for x in s if x >= 0) / n_boot
    return max(2 * min(le, ge), 1.0 / n_boot)


def holm(pvals):
    """Holm step-down. `pvals` maps a cell label to its p-value; returns the
    adjusted values. Applied within the preregistered confirmatory family
    only -- every other contrast in the paper is reported unadjusted, and the
    paper says so.
    """
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    n = len(items)
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, (n - i) * p)
        adj[k] = min(running, 1.0)
    return adj
