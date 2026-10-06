# Limitations

Findings are suggestions, not confirmed defects. Static rules cover a few syntactic patterns;
they miss most semantic threshold and None-handling bugs. Mutable defaults can be deliberate
state, built-ins may be shadowed, and guarded out-of-range loops can be safe. Static detection
does not prove reachability, infer types, analyze dataflow, or apply fixes.

LLMs can hallucinate explanations, miss bugs, choose wrong lines, or emit invalid JSON. Strict
schemas constrain format, not semantic truth. Prompt instructions cannot guarantee resistance to
malicious source comments. No tools are exposed to the model, and code is never automatically run.

The benchmark contains obvious, documented contracts and highly related template variants.
It lacks real-world distributions, large dependency context, concurrency, exception protocols,
complex object lifecycles, and independent annotation. Small reserved splits have high variance.
The dataset does not establish repository-level usefulness or statistically significant gains.

Review handles one file at a time, and diff review needs complete post-image files with matching
hunks. Dynamic definitions, notebook cells, quoted Git paths, binary patches, deleted functions,
and rename-only patches are unsupported. Functions over 200 lines are skipped. Bounded imports
are not a resolved dependency graph. Nested scopes can appear in LLM outer-function context, so
outer and inner review suggestions may overlap; evaluation cases deliberately contain one function.

Real LoRA training and a controlled reserved comparison were executed. Both the base and adapter
had recall zero; the adapter mostly abstained and reduced false positives. This does not
demonstrate effective bug detection or real-repository usefulness. The tiny fixture is
insufficient to learn reliable reviewing, and the 48-example training collection is also small.
GPU capacity checks do not establish that inference, full LoRA, or QLoRA fit a given configuration.
Optional dependencies have a constrained API range, but their whole cross-platform combination
is not a lockfile or a guarantee. Record versions for actual runs and use Python 3.11/3.12.

Artifacts are protected against accidental replacement. Multi-artifact creation is rolled back
on ordinary errors but is not crash-atomic. Host timeouts on Docker execution cannot guarantee
cleanup if Docker or the host fails; containers should be inspected after interrupted runs.
