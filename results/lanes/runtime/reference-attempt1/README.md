# Preserved reference runtime attempt 1

The coordinator stopped this attempt after diagnosing a benchmark container-name
bug. The Go eight-step reference's database hostname was 64 characters long,
which exceeds the DNS label limit of 63. Its HTTP process could not resolve the
database and never reached a timed workload. Its separate socket round passed.
The Python eight-step HTTP startup was interrupted before measurement.

The original summary, failed HTTP result/log and completed socket evidence are
retained here. [Diagnosis and original-summary hash](diagnosis.json).

The corrected reference run uses a deterministic short hash in container names.
Full session, source and image identities remain in the result records. No
application, frozen coding input, workload, timing window or resource limit was
changed. The measured originals used shorter names and are unaffected.

The later complete reference measurements are in [reference](../reference/).
