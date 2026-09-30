# Sequential reference 1

An unscored revision of the preserved [eight-step final](../../../../../stacks/clojure/8-live-editing/). The measured source, effort and failed reviewer results remain unchanged.

| Observed defect | Repair |
| --- | --- |
| An owner's `article: []` update returned 200 and incremented the revision. | Check for a map after visibility and ownership checks, before any mutation. |
| An oversized comment ID produced 500. | Use non-throwing `parse-long`; an unrepresentable ID cannot match a stored comment and returns the existing 404 envelope. |
| All 25 concurrent bad logins bypassed a ten-attempt counter. | Reserve admission with `AtomicInteger.getAndIncrement` before password work. Successful authentication resets the existing bounded, expiring counter. |
| An extra field outside the shared `article` object was accepted and changed the article. | Pass the full envelope to the share service and check both outer and inner field sets after capability authorization. |

The first two are failures of the common contract probes. The concurrent login and outer shared-envelope cases are supplemental quality diagnostics. This revision makes no changes to the database, dependencies, runtime configuration or socket coordination. Additional source-inferred risks remain in the [expert review](../../EXPERT-REVIEW.md).

The published snapshot `94de69bcd802935a011c2072054ce4ceee79aea8b6b840aaa58874a376a9f961` passed both [independent development and production gates](verification.json), [21/21 HTTP contract cases, 3/3 quality cases and 48/48 favorites cases](reviewer-parity/results.json), and [3/3 shared contract cases plus the outer-envelope quality diagnostic](reviewer-parity/share-boundary.json). Repeated reference runtime is recorded separately.
