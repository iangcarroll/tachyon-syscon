# Source-only physical-layout experiment

`tools/build_physical_firmware.py` now links a complete experimental image from reconstructed source with **zero unresolved symbols**. It performs no hardware operation. The physical profile remains unconfirmed, whole-image stack use is not bounded, and neither a successful link nor these startup tests establish firmware equivalence or flash readiness.

The builder uses `src/physical/firmware.ld` and follows the emulator's MSPM0L1306 profile: 65536 bytes MAIN flash and 4096 bytes SRAM. Missing symbols fail the link; test fixtures, endpoint stubs, installed runtime archives and original executable payloads are not production inputs. Rebuilds first remove old image outputs. Compilation/link/audit failures or input changes during the build prevent a current binary from being emitted. A manifest records source/header/linker/builder hashes, exact unresolved symbols, layout, load segments and compiler stack reports.

| Region | Contract |
|---|---|
| Flash `0x0000..0xf7f7` | Source vectors, code, read-only objects and initialized-data load images; allocated by the linker |
| Flash `0xf7f8..0xf7ff` | Eight-byte firmware-version slot required by the packaged updater |
| Flash `0xf800..0xfbff` | Persistent identity sector; excluded from the emitted image |
| Flash `0xfc00..0xffff` | Persistent configuration sector; excluded from the emitted image |
| SRAM `0x20000000..0x20000fff` | Copied flash executor, initialized objects, BSS and downward-growing stack |

The linker owns every private object's placement. There are no original-ROM
payloads, fixed constructor tables, legacy SRAM initialization copies or private
allocation arenas. Named output sections group modules for inspection and
relocation tests; they share the real MCU regions rather than reproducing the
original map. The manifest records their actual addresses and sizes on each
build. The version slot keeps the emitted image length independent of used code
size. Factory/NONMAIN contents are never invented.

## Reset and flash execution

`src/physical/startup.c` copies each linker-defined initialized section and
clears each allocated BSS section. It leaves unallocated SRAM alone. Runtime
initialization calls the timestamp and queue constructors in their original
order before main. Warm-reset tests corrupt ordinary objects and verify their
restoration, including parser callbacks, runtime pointers and modem state. PMU
retained values are restored through their explicit hardware-backed path.

The flash executor is source-built, copied into SRAM and called through its
linked symbol. Its reserved 48-byte capacity is a size guard, not a call-address
contract: relocation tests move the entry and poison the former entry. While
flash is busy, both instruction fetches and data reads must stay in SRAM except
for FLASHCTL accesses. Negative controls check stale calls and slot overflow.

The builder rejects unresolved symbols, test fixtures, original executable
payloads, sections outside the MCU regions, and load data entering the persistent
sectors. It also rejects a misplaced flash executor and an image whose inputs
changed while building. `analysis/physical-data-manifest.json` records that no
imported data segment remains; the old assembly constants file is removed.

## Relocation and editable source

The complete-image variant shifts code and data, reorders runtime/modem objects,
adds a UART command and lengthens configuration text. It executes actual reset,
UART commands, battery input curves, GPIO/button events, I2C faults and persistent
configuration compaction. Obsolete RAM is poisoned only where no live linked
object has reclaimed it. Unit fixtures may keep original addresses to compare
individual functions; those placements never enter production.

`tools/audit_source_addresses.py` rejects common private RAM/ROM literal patterns
in production C, assembly and headers. It is a regression lint, not an alias
analysis or whole-program proof; executable relocation tests remain necessary.

## Literal legacy configuration values

Configuration compaction now copies stored keys and values literally. The original used stored text as a printf format with omitted arguments, corrupting legacy values such as `%s` and `%u`. Public configuration commands already reject `%`; retaining existing legacy text is the approved correction to that bug.

The old assembly argument-frame adapter, numeric return address and reserved flash byte are removed. Code can grow across the former `0x2919` hole without a private format-string data dependency. Slot bounds, NUL termination, erased padding, checksums and flash operation ordering remain tested against the original for ordinary values. Candidate regressions cover format metacharacters as literal data, including `%n`, and whole-image UART compaction, readback and persistence across a fresh boot. Those legacy cases intentionally differ from the executed original and are tested as corrections, not declared equivalent.

## Stack and validation boundaries

The manifest reports `stack_headroom_bytes` after all fixed and linker-allocated globals. This is available space, not a proven maximum stack allowance. Compiler `.su` reports give the current frames for functions such as `syscon_rt_vfscanf`, `syscon_cfg_compact` and protocol polling; these sizes may change when source is edited. They must be composed with call chains, assembly ABI frames, interrupt stacking/nesting and callback paths. The builder records `.su` evidence and lists assembly sources without compiler frame bounds. It does not present these numbers as a whole-image bound. A linker minimum-headroom assertion is a rejection guard, not a stack-safety proof.

`tests/test_physical_firmware.py` uses a separate test-only fixture for dirty-SRAM
startup, initialized/BSS objects, constructor order, vectors, SRAM-only execution
through flash-busy statuses, wrong-entry audit rejection, RAM-slot overflow and
load-image alignment. Complete-image tests provide the application-level checks.
