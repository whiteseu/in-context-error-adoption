# Prompt templates

Reproduced verbatim from the evaluation runner. `{...}` marks substitution.
Nothing else is added to the request: no system message, no few-shot
instructions beyond the two priming turns shown below.

## Answer instruction

Appended to every user turn that asks for an answer.

```
\n\nEnd your response with the returned value on its own line in the form: [OUTPUT] <value>
```

## Question

```
{code}

What does f({input}) return?
```

For GSM8K the question is the problem statement itself; the rest of the
scaffolding is identical.

## Priming turns

Two items drawn from the pool but **excluded from the evaluated bank** are
prepended to fix the answer format:

```
user:      {question_of(p)}{ANSWER_INSTR}
assistant: [OUTPUT] {p.gold}
```

## Placement 1 — user turn (`other_error`, the primary decomposition)

```
user: {question}

Here is an attempt at this problem written by another assistant. That attempt is incorrect:

<<<
{payload}
>>>

Please trace the function from scratch and do not rely on that attempt.{ANSWER_INSTR}
```

## Placement 2 — assistant turn (`self_error`)

```
user:      {question}{ANSWER_INSTR}
assistant: {payload}
user:      Your previous attempt above is incorrect. Please trace the function
           again from scratch and do not rely on your previous attempt.{ANSWER_INSTR}
```

## What `{payload}` is, per condition

The payload is the only thing that varies. Every payload ends with the same
fixed answer statement for a given item, so the erroneous answer `w` is held
constant across conditions.

| condition      | payload |
|----------------|---------|
| `bare`         | the answer statement alone |
| `filler`       | problem-independent prose + the answer statement |
| `full`         | the item's own erroneous trace (already ends in the statement) |
| `mismatch`     | another item's erroneous trace, its own answer statement replaced by this item's |
| `scrambled`    | `filler` with word order permuted, word multiset and character count preserved |
| `declarative`  | declarative prose matched per item in characters and words |
| length variants| nested prefixes of `filler` at 25 / 50 / 75 %, plus a 3.4x extension |
| `full_notail`  | `full` with the final answer statement removed |
| `full_scrub`   | answer masking: `full_notail` with every standalone occurrence of `w` replaced by `<value>` |

The `mismatch` tail is built as:

```
{donor_body}

The output is {w}.

[OUTPUT] {w}
```

## Answer extraction

```python
_OUT_RE       = r"^\s*\[OUTPUT\]\s*(.+?)\s*$"                      # strict
_OUT_RE_LOOSE = r"^\s*(?:#{1,6}\s*|\*{1,2}\s*)?\[OUTPUT\]\**\s*(.+?)\s*$"
```

The loose pattern accepts a Markdown heading or bold prefix and is used for
the two chat-template models; it was fixed before the run, and there is no
other fallback. The last match in the response wins. Extracted strings are
compared after `ast.literal_eval` normalisation.
