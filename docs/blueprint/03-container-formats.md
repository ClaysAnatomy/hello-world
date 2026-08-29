# Container Memory Card Formats

This is reference material for Milestone 1 (`memcard-ps1`, the gate) and for
the later PS2/GameCube milestones. Byte layouts below are enough to start
from; verify against a real card image and the reference implementations
named in each section before trusting an edge case.

## PS1 memory card — 128 KB, the Milestone 1 target

Total size: exactly 131,072 bytes (128 KB). Structure: 16 blocks of 8,192
bytes each. Block 0 is the directory/system block; blocks 1–15 are data
blocks, each either free or holding (part of) one save.

### Block 0 layout (the directory)

Block 0 is itself divided into 8,192 / 128 = 64 "frames" of 128 bytes:

- **Frame 0**: header frame. Bytes `0x00-0x01` = magic `"MC"` (0x4D 0x43).
  Byte `0x7F` = XOR checksum of bytes 0x00–0x7E.
- **Frames 1–15**: one directory entry per data block (block 1 through 15
  map 1:1 to frames 1 through 15 — frame N describes block N).
- **Frames 16–35**: broken sector list (rarely relevant; treat as opaque
  and preserve on write, do not attempt to interpret for v1).
- **Frames 20+**: unused/reserved in most implementations — again, preserve
  verbatim, don't zero them.

### Directory entry (128 bytes, one per frame 1–15)

| Offset | Size | Field |
|---|---|---|
| 0x00 | 1 | Status byte — see table below |
| 0x04 | 4 | Size in bytes (little-endian u32) — always a multiple of 8192 |
| 0x08 | 2 | Next block number (little-endian u16); `0xFFFF` = end of chain, only meaningful for the *first* block of a multi-block save |
| 0x0A | 20 | Save name — see format below |
| 0x7F | 1 | XOR checksum of bytes 0x00–0x7E |

Status byte values:

| Value | Meaning |
|---|---|
| `0xA0` | Free block |
| `0x51` | In-use, **first** block of a save |
| `0x52` | In-use, **middle** block of a multi-block save |
| `0x53` | In-use, **last** block of a multi-block save |
| `0xA1` | Free, was previously first block (deleted) |
| `0xA2` | Free, was previously middle block (deleted) |
| `0xA3` | Free, was previously last block (deleted) |

A single-block save uses status `0x51` directly with no `0x52`/`0x53`
continuation. A save is never larger than the block count implied by its
size field; **the size field is the authoritative source of truth for how
many blocks to follow**, not just walking status bytes.

### Save name field (20 bytes at offset 0x0A of the directory entry)

ASCII, typically of the form:

```
BASCUS-94163TEST
```

— a 4-letter region/publisher prefix (`BASCUS`, `BASLUS`, `BESCES`, `BISLPS`
etc. depending on region/publisher), a hyphen, a 5-digit product code, then
a free-form save identifier the game itself chose. **The product code
portion (before the free-form suffix) is the game identity** — this is why
PS1 needs no ROM hashing for identity resolution (see `02-data-schemas.md`).
Split on the pattern `^[A-Z]{4}-\d{5}` to separate product code from the
game-chosen save label; treat anything that doesn't match as an
unrecognized/legacy format and fall back to filename-based identity.

### Save data blocks (blocks 1–15, 8192 bytes each)

Each data block also starts with its own small header (varies by game/tool
convention; treat the full 8192 bytes as opaque payload for extraction
purposes — do not attempt to interpret game-internal structure). For a
multi-block save, blocks are chained via the `next block number` field in
the *first* block's directory entry only; subsequent blocks' directory
entries are marked `0x52`/`0x53` but a full chain-walk requires reading
each block's own internal continuation pointer at a fixed offset within
the block (implementations vary — cross-check against a working reference
like `mymc` before finalizing this for multi-block saves).

### Extraction algorithm

1. Parse block 0, frames 1–15, into 15 directory entries.
2. For each entry with status `0x51` (first block, single- or multi-block):
   - Read `size` and compute block count = `size / 8192`.
   - Collect the data from this block plus any chained blocks.
   - Parse the 20-byte name into `(product_code, save_label)`.
   - Emit `SaveUnit { product_code, save_label, block_indices: [...], data: bytes }`.
3. Blocks with status `0xA0`/`0xA1`/`0xA2`/`0xA3` are free — not part of any
   `SaveUnit`.

### Reassembly / merge algorithm

Given a target card and a list of `SaveUnit`s to add (from a merge — see
`01-architecture.md` §Conflict resolution):

1. For each incoming `SaveUnit`, first check whether a unit with the same
   `product_code` + `save_label` already exists on the target with
   byte-identical data — if so, skip (already present).
2. If it exists but differs — this is a same-slot conflict; do not
   auto-merge this one unit, escalate it to the launch-time picker
   (per-unit, not per-card).
3. Otherwise, find `block_count` contiguous or non-contiguous free blocks
   (status `0xA0` or later) on the target card. PS1 does not require
   contiguity — chaining handles fragmentation.
4. Write the data into those physical block slots.
5. Write a new directory entry: status `0x51` for the first block used
   (`0x52`/`0x53` for continuation blocks if more than one), correct `size`,
   correct `next block` chain, the original name bytes, and a freshly
   computed XOR checksum over bytes 0x00–0x7E.
6. Recompute and write the header frame checksum if the format/tooling you
   validate against expects it to reflect directory changes (verify against
   a real emulator load — some emulators don't check it, some do).

### Wrapped/exported single-save formats — normalize on ingest, not storage

These are common export formats for a *single* save (already extracted from
a card by some tool) and should be normalized to the raw 128-block payload
on ingest so the rest of the system only ever deals with one internal
representation:

| Extension | Header size | Notes |
|---|---|---|
| `.mcs`, `.mcr`, `.mcd`, `.mc`, `.mem`, `.vmc`, `.vgs` | 0 or small fixed offset | Varies by tool; `.vgs` has a 64-byte header |
| `.gme` (DexDrive) | 3904 bytes | Strip header, remainder is raw card/save data |
| `.psv` (PS3/Vita) | variable, has its own container format | Out of scope for v1 — flag and skip rather than guess |
| `.vmp` (PSP) | 128-byte header | Strip header |

### Validation targets for Milestone 1's acceptance tests

- Round-trip a real, non-trivial card (multiple games, at least one
  multi-block save) through parse → extract all units → reassemble
  identical card → byte-compare to original.
- Merge test: two different real cards, each with saves the other lacks,
  merge to the union, load the result in DuckStation without corruption
  and confirm each game reads its own save correctly in-emulator.
- Conflict test: two cards with the *same* product code + label but
  different data — confirm this is detected and NOT silently merged.

### Reference implementations to cross-check against

- `mymc` (Python, PS1/PS2) — the most complete open reference for the
  directory/frame layout and checksum behavior.
- Dolphin's memory card code is PS1-adjacent reading material for the
  general "block directory + chained blocks" pattern even though Dolphin
  targets GameCube, not PS1.

---

## PS2 memory card — 8 MB, later milestone

Real FAT-like filesystem, not just a flat directory-of-blocks like PS1.

- Superblock at offset 0, magic string `"Sony PS2 Memory Card Format "`.
- Cluster-based allocation (cluster size defined in the superblock, commonly
  1024 bytes), with an allocation table and an indirect FAT layer for larger
  cards.
- Directory entries live in a real directory tree (not a flat 15-slot list
  like PS1), named like `BASLUS-20488SYSTEM` — same product-code-prefix
  convention as PS1 for identity purposes.
- A "save" is a directory plus the files inside it, not a single block
  chain — extraction/merge is the same conceptual algorithm as PS1
  (identify the unit by product code, extract as a self-contained tree,
  reassemble by allocating free clusters) but implemented against a real
  filesystem structure rather than a 15-entry table.
- **Reference implementation**: `mymc` again covers PS2 as well as PS1 and
  is the primary source to validate cluster/FAT parsing against.
- Do not start this until Milestone 1 (PS1) has passed its acceptance
  tests — the algorithms are structurally similar, so PS1 working correctly
  substantially de-risks this one.

---

## GameCube memory card — `.raw` / `.gci`, later milestone

- Header block (block 0) with card size, encoding, serial etc.
- **Two redundant directory blocks** and **two redundant block-allocation
  maps** (BAT) — GameCube cards keep duplicate copies of both with a
  sequence/update counter to determine which copy is current; an
  implementation must read the counter and pick the newer copy, not assume
  block 1 vs block 2.
- 8 KB data blocks, same general chained-block shape as PS1.
- Directory entries carry `gamecode` (4 chars, e.g. `GALE` for a Zelda
  title) and `makercode` (2 chars) as identity — again, no ROM hashing
  needed for identity on this platform.
- `.gci` is already a single exported save entry (Dolphin's native export
  format) — effectively GameCube ships a per-save file format already,
  which makes this the easiest of the three to support once the raw
  `.raw` full-card format is handled.
- **Reference implementation**: Dolphin's `Source/Core/Core/HW/GCMemcard/
  GCMemcard.cpp` is a complete, readable, actively-maintained parser/writer
  for this exact format — treat it as ground truth over this document for
  any discrepancy.
