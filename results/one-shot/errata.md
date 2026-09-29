# Phoenix source-size measurement correction

The first one-shot result originally reported Phoenix as 4,938 owned backend tokens / 515 nonblank, noncomment lines and 9,084 whole-backend tokens. Those values were too low. The corrected values are **8,734 owned tokens / 948 lines** and **13,093 whole-backend tokens**.

The Phoenix agent created a root `conduit/` directory of symlinks so its container toolchain could work in `/work/app/conduit`. The publisher added `conduit` to a list of directory **names** to exclude. That also excluded the real `lib/conduit/` directory, which contains domain schemas and contexts. The frozen [measurement boundary](frozen-measurement.md) calls for those files to count. The corrected measurement skips only the root alias path and counts all `lib/conduit/` source.

The original [size record](phoenix/size-before-erratum.json) is retained. The corrected [size record](phoenix/size.json) was recomputed from the unchanged first-run workdir and its untouched `.scaffold/` baseline using the same `o200k_base` tokenizer. No backend code, agent transcript, acceptance gate, or runtime measurement changed. Rails and Loco did not use this path exclusion and their source counts are unchanged.

The corrected owned-source ratios relative to Rails are 1.57× for Phoenix and 1.66× for Loco. The previous Phoenix number suggested it was smaller than Rails; that conclusion was an artifact of the measurement bug. The eight-step history uses a separate measurement path and is unchanged by this correction.
