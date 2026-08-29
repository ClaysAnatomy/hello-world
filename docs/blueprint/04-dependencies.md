# Dependency Audit

Pulled live from the crates.io registry API, 2026-08-29. Pin exact versions
below in `Cargo.toml`; do not float on `*` or bare majors for anything
marked Caution or below. Re-check any crate before adding it if this file
is more than a few months old when a new milestone starts.

## Adopt — healthy, well-used, current

| Crate | Version | Downloads (total) | Recent (90d) | License |
|---|---|---|---|---|
| tokio | 1.53.1 | 919,622,101 | 213,975,009 | MIT |
| serde (+ derive) | 1.0.229 | 1,326,035,007 | 286,015,000 | MIT/Apache-2.0 |
| notify | 8.2.0 | 145,552,608 | 36,237,213 | CC0-1.0 |
| notify-debouncer-full | 0.7.0 | 14,991,111 | 4,080,816 | MIT/Apache-2.0 |
| blake3 | 1.8.7 | 171,739,286 | 40,873,623 | CC0/Apache-2.0 |
| zstd | 0.13.3 | 369,265,477 | 75,775,572 | MIT |
| rusqlite | 0.40.2 | 98,958,298 | 31,613,051 | MIT |
| axum | 0.8.9 | 445,568,931 | 111,425,917 | MIT |
| reqwest | 0.13.4 | 675,825,920 | 172,127,489 | MIT/Apache-2.0 |
| sqlx | 0.9.0 | 137,700,903 | 34,335,810 | MIT/Apache-2.0 |
| object_store | 0.14.1 | 82,300,713 | 18,756,013 | MIT/Apache-2.0 |
| toml | 1.1.4 | 857,410,411 | 202,551,314 | MIT/Apache-2.0 |
| sysinfo | 0.39.6 | 191,514,003 | 43,795,484 | MIT |
| clap (derive) | 4.6.6 | 1,085,587,189 | 223,356,644 | MIT/Apache-2.0 |
| tracing (+ subscriber) | 0.1.44 | 805,723,899 | 180,848,676 | MIT |
| directories | 6.0.0 | 67,503,871 | 12,070,393 | MIT/Apache-2.0 |
| tempfile | 3.27.0 | 770,103,559 | 172,976,349 | MIT/Apache-2.0 |

`notify` + `notify-debouncer-full` are the entire cross-platform file
watcher — this is what replaces fanotify/USN-Journal privileged capture
from the original proposal (see `01-architecture.md` §Capture). `blake3` is
the content-address hash for the version DAG. `object_store` is the
storage-backend abstraction (S3/R2/GCS/local-filesystem behind one trait) —
prefer it over reaching for `aws-sdk-s3` directly.

## Caution — adopt, but with a specific mitigation

| Crate | Version | Downloads (total) | Recent (90d) | Issue | Mitigation |
|---|---|---|---|---|---|
| fastcdc | 5.0.0 | 1,585,184 | 953,796 | Small, single-maintainer, single-purpose crate. Recent downloads are ~60% of all-time total — actively growing, but young. | Wrap it behind a local trait (`Chunker`) in `relay-core` so it can be swapped or vendored without touching call sites elsewhere. It implements a published algorithm (~200 lines) — vendoring is a realistic fallback if it goes unmaintained. Do not let its types leak past the wrapper. |
| keyring | 4.1.6 | 22,472,364 | 9,293,149 | Brokers four different OS credential stores; SteamOS/Game Mode has no reliable Secret Service provider. | Treat as best-effort. Fall back to a `0600`-permission token file when the OS keystore is unavailable. Auth storage failures must never block a local capture — the agent should still write to its local queue even if it can't currently authenticate to push. |

## Reject — do not use

| Crate | Version | Downloads (total) | Reason |
|---|---|---|---|
| unifuse | 0.3.0 | 3,473 | 3 versions since Feb 2026, no published docs, one maintainer. Was the foundation of the original proposal's VFS layer — rejected along with the VFS approach entirely (see `01-architecture.md`, Defect 7). |
| rfuse3 | 0.0.9 | 21,995 | `0.0.x` — pre-stable by the author's own versioning. Transitively pulled in only via `unifuse`; rejecting the parent removes this automatically. |
| winfsp (crate) | 0.13.1 | 67,102 | Also requires the *end user* to separately install the WinFSP kernel driver — an elevated, out-of-band step v1 does not need. |
| serde_yaml | 0.9.34+deprecated | 384,570,321 | **Deprecated by its own author**; no release since 2024-03-25. The version string literally says `+deprecated`. High download count is inertia, not health — do not use download count alone as a health signal. Use `toml` for all config/manifest files instead. |
| serde_yml | 0.0.13 | 22,439,846 | The commonly-suggested "replacement" for serde_yaml, and also wrong: `0.0.x`, contested-provenance fork. If YAML is ever genuinely required (e.g. consuming a third-party Ludusavi-style manifest verbatim), use `serde_norway` or `yaml-rust2` instead — both are maintained continuations of the pre-deprecation ecosystem. |

## Written in-house — no usable crate exists

Do not spend time searching for a shortcut on these; the search was already
done and came up empty. These are also, not coincidentally, the parts of
the system that make it worth building:

- **Memory card container codecs** (`crates/memcard-ps1`, later
  `memcard-ps2`, `memcard-gc`). See `03-container-formats.md`.
- **Save format normalization** (GBA save-size detection/padding, RTC
  footer stripping, SRAM sizing, wrapped-format header stripping).
- **Adapter manifest schema + resolver.** Ludusavi's manifest format is
  useful prior art for the general *shape* of "declarative save-location
  database" but targets PC game stores, not emulators, and should not be
  depended on directly — model the schema in `02-data-schemas.md` instead.
