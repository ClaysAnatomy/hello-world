# Data Schemas

## Version DAG node (metadata service, e.g. Postgres)

```
Version {
  version_id    : UUID (primary key)
  asset_id      : UUID            // stable per (platform, game, save-class)
  content_ref   : BlobRef | ChunkListRef | TreeManifestRef
  parents       : [version_id]    // 0 = genesis, 1 = linear edit, 2+ = merge
  device_id     : UUID
  wall_clock    : timestamp       // display only — never used for ordering/causality
  vector_clock  : map<device_id, u64>  // cheap domination check without full DAG fetch
  origin        : {
    emulator         : string
    emulator_version : string
    core             : string?      // null for standalone emulators
    core_version     : string?
    host_arch        : string       // "x86_64" | "aarch64"
  }
  save_class    : "battery" | "state" | "container_unit" | "tree"
  created_at    : timestamp
}
```

Rules an implementation must enforce:
- `content_ref` objects are immutable once written. Never mutate a blob in
  place; a change is always a new `Version`.
- A `Version` is never deleted while any other `Version` or lease references
  its `content_ref` (garbage collection walks reachability from all heads).
- `asset_id` identity resolution is described below — it is intentionally
  decoupled from `Version` so identity can be corrected later without
  rewriting history.

## Asset identity

```
Asset {
  asset_id       : UUID
  platform       : string           // "psx" | "gba" | "snes" | ...
  canonical_id   : string           // serial/product code when known,
                                     // else normalized-title hash
  save_class     : "battery" | "state" | "container_unit" | "tree"
  container_of   : asset_id?        // set only for container_unit: the
                                     // parent memory-card asset this was
                                     // extracted from
  user_confirmed : bool             // true once a human has confirmed identity
}
```

Resolution order (cheapest/most-certain first — implement as a chain of
resolvers, each allowed to defer to the next):

1. Container-derived: PS1/PS2/GC product code is inside the save container
   itself (see `03-container-formats.md`). No ROM hashing needed.
2. ROM hash → DAT lookup (No-Intro / Redump / RetroAchievements sets).
   Hash the ROM both with and without a common copier header (iNES, SMC) to
   absorb headered/unheadered variance.
3. Filename normalization (strip region/rev/dump tags, lowercase, collapse
   punctuation) — fallback only, lowest confidence.
4. User override, stored and synced across devices once set.

Cache resolved identity locally (SQLite) keyed by ROM hash — this is a
one-time cost per ROM, not a per-launch cost.

## Adapter manifest (TOML, one file per emulator, lives in `adapters/`)

```toml
id = "retroarch"

[[detect]]
kind   = "flatpak"
app_id = "org.libretro.RetroArch"
root   = "~/.var/app/org.libretro.RetroArch/config/retroarch"

[[detect]]
kind = "path"
os   = "windows"
root = "%APPDATA%/RetroArch"

[[detect]]
kind = "path"
os   = "macos"
root = "~/Library/Application Support/RetroArch"

[[detect]]
kind = "path"
os   = "linux"
root = "~/.config/retroarch"

[[saves]]
class    = "battery"
glob     = "saves/*.srm"
identity = { from = "filename", strip_tags = true }

[[saves]]
class       = "state"
glob        = "states/*.state*"
identity    = { from = "filename", strip_tags = true }
arch_locked = true

[[saves]]
class    = "container"
glob     = "saves/*.mcr"       # or .mcd, matches the emulator's card extension
platform = "psx"
codec    = "ps1_memcard"        # names a codec implemented in crates/memcard-ps1
```

`detect` entries are tried in order; first match wins per-OS. `saves`
entries describe glob patterns relative to the resolved root, their save
class, and (for `container` class) which codec crate parses them.

## Local agent state (SQLite, one file per device)

Tables an implementation needs at minimum:

- `outbound_queue(version_id, asset_id, content_path, attempted_at, status)`
  — captures waiting to upload, survives restarts.
- `identity_cache(rom_hash, asset_id, resolved_at, source)`
- `known_heads(asset_id, version_id, fetched_at)` — local cache of the last
  metadata-service answer, used when offline.
- `leases_seen(asset_id, device_id, started_at, last_heartbeat, ttl)` —
  local cache for display; the metadata service is authoritative.

## Metadata service tables (Postgres — outline, not exhaustive DDL)

- `assets` — per `Asset` struct above.
- `versions` — per `Version` struct above.
- `version_parents(version_id, parent_id)` — edge table for the DAG.
- `devices(device_id, display_name, platform, registered_at)`.
- `leases(asset_id, device_id, started_at, last_heartbeat, ttl)`.
- `blob_refs(hash, size, chunk_of)` — for GC accounting; the object store
  itself is the source of truth for content, this table is for reachability
  bookkeeping only.
