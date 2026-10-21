# In-context error adoption

Prompts and core code for *Presence or Content? Decomposing In-Context Error
Adoption in LLM Cascades*.

Excerpts, not a runnable pipeline.

| file | contents |
|---|---|
| `prompts.md` | prompt templates, both placements, answer extraction |
| `conditions.py` | how each control condition is built |
| `analysis.py` | estimand, item-clustered bootstrap, odds scale, Holm |

Each item pairs a problem with an erroneous solution whose final answer `w`
differs from gold. Every condition ends with the same fixed answer statement
and differs only in the text before it, so `filler − bare` isolates the
effect of additional text and `full − mismatch` that of problem-specific
content.

Licence: MIT, see `LICENSE`.
