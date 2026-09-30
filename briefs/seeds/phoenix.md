# Phoenix brief

## Rule ownership

- Let feature contexts own product decisions behind thin controllers. Split a context by rule or aggregate as it grows.
- Give slug generation, visibility, edit authority, stale revision, publication and share-key validation one named owner each. Define direct-read and discovery policies together as named query and decision functions.
- Enter one content commit from explicit author and keyed entrances, keeping capability checks distinct. Recheck revocation inside its transaction, guard the revision atomically, and publish updates after commit.
- Let the database enforce uniqueness, references, valid states and revision lower bounds.
- Let supervised per-room processes own admission, presence and the cap. Deliver committed updates through Phoenix.PubSub, and keep socket sends out of the admission process.

## Use what the framework provides

- Sign and verify the JWT with Joken, and hash passwords with Bcrypt. Do not implement crypto.
- Use Ecto changesets for persistence validation and constraint errors.
- Insert the export row and its Oban job in one Ecto transaction, and make completion idempotent.
- Route the raw socket through Phoenix and Bandit with WebSockAdapter, not Phoenix Channels, whose envelope the client does not speak. Monitor members and clean up empty rooms.

## Bounded queries

- Page in SQL first, then preload and batch author, follow, favorite and count data for that page. An Ecto page projection cut one anonymous list from 42 statements to four.
- Share one Ecto filter between the count and the page.
- Filter tags with array containment so the GIN index can apply, and add `id` to the ordering index for the tie-break. Check plans; this did not bound every tag page.

## Boundaries

- Authenticate, then resolve visibility and ownership or share capability before decoding the envelope. Check revision next, then fields.
- `cast/4` ignores unpermitted fields. Check exact wire shape and JSON types separately where the contract rejects them.
- Tag the caller as anonymous or a user, never a fake user ID.
- Return tagged domain results and render them with Phoenix JSON renderers.

## Production

- Build a compiled Mix release and copy only the release into a small runtime image. This cut one image from 1,673 MB to 165 MB.
- Run migrations through the release entry point, then start Phoenix and Oban in one container.
- Document the process-local room cap as a one-instance limit.

## Known traps

- Ecto's `validate_length` counts graphemes by default, while PostgreSQL's `varchar` limit counts characters. Size each column for every accepted value, including derived slugs.
- Elixir integers are unbounded, so a path ID can exceed `bigint` and fail when sent to PostgreSQL. Treat out-of-range IDs as missing.
- A throttle that reads a count and increments it later lets a concurrent burst through. Reserve each attempt per email before password verification, and release on finish, cancel or caller death.
- A delayed revocation for an old share generation must not evict members of a newly rotated link.

## Source

Distilled from `one-shot-v2-phoenix-expert/ENVIRONMENT.md`, `docs/phoenix-expert-track.md`, `results/one-shot-v2-phoenix-expert/pilot-1/README.md`, `results/one-shot-v2-phoenix-expert/reference-1/README.md`, `results/one-shot-v2-phoenix-expert/reference-2/README.md` and `results/v2-expert-symmetry/README.md`.

Draft seed for practitioner review. Not a frozen experiment input.
