# Loco list-query reference: verification checkpoint

This isolated copy changes list pagination to run in PostgreSQL and shares the article projection between list and single-record responses. The original scored Loco source and eight-step history are unchanged.

The final [development](development.json) and [fresh-production](production.json) gates passed, including API, direct socket, browser, security, formatting, and Clippy checks. The first development attempt lacked the scaffold's Cargo alias in the copied workdir; the second passed product checks but Clippy rejected an eight-argument function. The final source uses a named `ArticlePage` input. All attempts are retained.

The paired [runtime attempt](runtime-run.json) was stopped during its first round to return the workstation to an idle state. No Loco throughput result or before/after speed claim is published from it. A later measurement should start from the same source and run two complete rounds under the recorded resource limits.
