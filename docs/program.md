**The goals: Conduit with zero local patches; BitterClip (private) with zero check errors.**

Roundhouse turns Rails applications into code that Spinel can compile to native executables. The program uses app behavior to identify gaps, contributes fixes upstream and rebuilds on pinned upstream revisions. A clean `check` is a milestone; running the app correctly remains a separate test.

## Records and conditions

A Conduit record fixes the app source, Roundhouse and Spinel revisions, local patch series, Ruby version, build recipe and checks. It preserves patch manifests, source and binary identities, results and known limits. Each rebuild receives a new label. Earlier records and the measured agent build stay unchanged. Source: `results/ruby-compile/roundhouse-spinel-conduit-pg-20261030/README.md`.

The table gives whole local compiler patches for each published PostgreSQL record. Pins are abbreviated; full revisions and manifests are in each record. Counts can rise when upstream changes expose regressions. They do not measure patch size or general compiler coverage.

| Record, 2026 | Roundhouse: pin / patches | Spinel: pin / patches |
| --- | --- | --- |
| Sep 30, v4 | `25609ca3` / 17 | `813def1f` / 2 |
| Oct 02, v5 | `5bbc4765` / 11 | `d2c20df0` / 0 |
| Oct 04, v6 | `ac1fa43e` / 12 | `b7d04a903` / 0 |
| Oct 05, v7 | `2b2deff7` / 11 | `c1d108abe` / 0 |
| Oct 09, v8 | `ea4d3e68` / 10 | `f85f04b3a` / 0 |
| Oct 21, v9 | `1c84d346` / 11 | `6ca6d451b` / 1 |
| Oct 22, v10 | `0f6fb0c7` / 11 | `ca9717054` / 2 |
| Oct 28, v11 | `295abf08` / 10 | `3b397d7bc` / 1 |
| Oct 29, v12 | `4036ea9c5` / 8 | `d4e804c62` / 0 |
| Oct 30, v13 | `75672b31ef` / 8 | `97cea860aa` / 0 |

Sources: `results/ruby-compile/roundhouse-spinel-conduit-pg-YYYYMMDD/README.md`, using each row's date. The earlier `roundhouse-spinel-v2026.9.18/README.md` records a failed strict compilation, with no compiled server or comparable patch count.

In [v13](../results/ruby-compile/roundhouse-spinel-conduit-pg-20261030/README.md), the full series passes the production gate and every single-patch omission fails build, gate or boot recovery. The app still has documented substitutions. This does not prove every patch hunk necessary or general Rails parity. No v13 performance benchmark ran; the older v4 throughput result belongs to v4 alone.

For BitterClip (private), the October 31 count on Roundhouse main `690596f83` is **689 analyzer errors** on a pinned October 28 copy of the app, down from 720 on main `10d3a9ff0`. With the gem-declarations stack ([#1570](https://github.com/rubys/roundhouse/pull/1570), [#1580](https://github.com/rubys/roundhouse/pull/1580)), the count is **288**. The stack is an opt-in input for `check`, and emit refuses it. These are diagnostic counts, not execution results.

## Contributions and reproduction

Contributions go to [Roundhouse](https://github.com/rubys/roundhouse), [Spinel](https://github.com/matz/spinel) or [spinel-pg](https://github.com/rubys/spinel-pg), according to the defect. Check existing work, coordinate with its owner and credit the public handles and changes being built on. Use a synthetic repro, focused tests and independent review. Answer review findings with evidence. Follow each upstream repository's contribution rules. The [Conduit worklist](https://github.com/bunnykong/roundhouse/issues/1) connects the work, and its patch-retirement tables preserve credit.

To reproduce, choose one record and follow its `Reproduce` section from the AgentMVC root. For v13, use Docker with BuildKit, Git, Bash and Python; share the host's canonical Docker lock, use fresh build directories and the documented resource prefix. Prepare the pinned toolchain, verify manifests, build images, run compiled and Rails production gates, then the HTTP, edge and boot-recovery probes. The record supplies exact commands. Apt layers are not bit-reproducible across hosts. Record changed inputs as a new condition; do not replace the original evidence.
