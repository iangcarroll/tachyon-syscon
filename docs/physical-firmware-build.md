# Source-only physical-layout experiment

`tools/build_physical_firmware.py` now links a complete experimental image from reconstructed source with **zero unresolved symbols**. It performs no hardware operation. The physical profile remains unconfirmed, whole-image stack use is not bounded, and neither a successful link nor these startup tests establish firmware equivalence or flash readiness.

The builder uses `target/physical/firmware.ld` and follows the emulator's MSPM0L1306 profile: 65536 bytes MAIN flash and 4096 bytes SRAM. Missing symbols fail the link; test fixtures, endpoint stubs, installed runtime archives and original executable payloads are not production inputs. Rebuilds first remove old image outputs. Compilation/link/audit failures or input changes during the build prevent a current binary from being emitted. A manifest records source/header/linker/builder hashes, exact unresolved symbols, layout, load segments and compiler stack reports.

| Region | Placement and purpose |
|---|---|
| Flash `0x0000..0x00bf` | 48 source-defined vectors, initial MSP `0x20001000` |
| Flash `0x00c0..0x00ef` | Load image for the new source-built RAM executor, padded to its original 48-byte slot |
| Flash after the RAM executor load image, through `0xab1f` | Linker-sized code, constants and initialized-data load image; actual sizes/headroom are in the build manifest |
| Flash `0xab20..0xc418` | Data-only recovered actions/configuration constants/strings, with explicit source-symbol pointer relocations |
| Flash `0xc419..0xc61e` | Source-defined 37×14-byte command descriptors |
| Flash `0xc61f..0xe2d7` | Remaining recovered strings and immutable data |
| Flash `0xe2d8..0xe2df` | Relocated timestamp and queue constructor pointers |
| Flash `0xe2e0..0xe2e7` | Original code-relative unwind entry excluded |
| Flash `0xe2e8..0xe577` | 656-byte initialized SRAM image, with relocated printer pointers |
| Flash `0xe578..0xf7f7` | Linker-resolved configuration constants; code does not silently spill here |
| Flash `0xf7f8..0xf7fe` | Original version string retained as a comparison-data dependency |
| Flash `0xf800..0xffff` | Identity/config sectors excluded from emitted binary |
| SRAM `0x20000000..0x2000002f` | New 36-byte original-ABI flash executor, padded to 48 bytes and copied at reset |
| SRAM `0x20000030..0x200002bf` | Remaining legacy initialized globals; the old configuration-cache bytes are unused |
| SRAM `0x200002c0..0x20000533` | Remaining original zeroed globals and vacant migrated locations |
| SRAM `0x20000534..0x2000067f` | Reclaimed task/timer storage; linker-allocated scheduling/retained objects in `.state_bss` |
| SRAM `0x20000680..0x2000081f` | Remaining original zeroed globals and vacant migrated ADC storage |
| SRAM `0x20000820..0x20000fff` | Linker-allocated `.data`/BSS, followed by available stack space |

These region boundaries describe the transitional layout; the manifest records actual section sizes on every link. The emitted binary is 63487 bytes because fixed-address constants and version data retain their original addresses; this length is not the amount of executable code. No factory/NONMAIN contents or persistent identity/configuration are invented.

## Reset and original-ABI flash execution

`target/physical/startup.c` copies initialized globals, copies the new RAM executor, clears exactly the original BSS range, and initializes linker-allocated `.data`, `.state_bss` and auxiliary BSS. It calls reconstructed `syscon_target_runtime_init`, which performs the original no-op init hook and timestamp/queue constructors in order, then enters `syscon_target_main`. UART vector wrappers call source UART IRQ code with original bases `0x40108000` and `0x40100000`. Other populated vectors preserve their roles; originally null vectors remain null.

The production builder defines `SYSCON_DIRECT_FLASH_ABI` for `target/config_storage.c`. That narrow binding routes erase, program, blank and protection operations to `target/flash_abi_target.c`. Its helpers call `syscon_target_flash_ram_execute` through a linker-resolved reference. The RAM body performs direct volatile FLASHCTL accesses and has no callback or flash-resident data dependency. The generic callback controller remains available for existing standalone tests but is garbage-collected from the physical image. The callback API is not silently changed or implemented by ignoring an arbitrary callback argument.

The linker explicitly retains the RAM input section with `KEEP`, asserts that it is nonempty and no larger than 48 bytes, then pads the original reserved slot. This transitional slot still cannot overlap unmigrated globals. The audit verifies that the executor is a Thumb entry inside the copied executable SRAM section, rejects accidental retention of the generic executor, checks executable/load address ranges and excludes identity/config sectors. Tests check actual SRAM-only instruction execution and data reads throughout the flash-busy interval; the only external accesses there are FLASHCTL MMIO reads/writes.

A regression moves the executor eight bytes within its reserved SRAM region, executes reset and the copy, and verifies that its busy loop executes only from SRAM. The complete-image layout variant also moves that executor before exercising UART configuration writes and persistence. Stack headroom depends on the current named globals and is recorded in the build manifest.

## Data provenance and relocation

`target/physical/constants.S` is a textual data-only source artifact derived from the pinned firmware. It excludes original vectors, executable code, copied RAM machine code, old command descriptors and old unwind metadata. `analysis/physical-data-manifest.json` records the reference hash, data ranges and every reviewed relocation:

- Fifteen action callback fields in `0xab20..0xabdf`.
- Constructor fields at `0xe2d8` and `0xe2dc`.
- Printer fields at flash `0xe310` and `0xe3a8`, copied to SRAM `0x20000058` and `0x200000f0`.

Command descriptors come from reconstructed C and relocate their handlers. SG callback names use the owning module's canonical source symbols. No heuristic rewriting of arbitrary odd values is used. Tests scan imported bytes for all currently identified original function pointers and confirm that every match is explicitly relocated; this does not prove the static inventory is exhaustive.

The raw disassembler listing contains false instruction interpretations inside strings such as `DIAG` and diagnostic messages. Data-boundary checks use identified function-owned ranges rather than falsely classifying every raw listing line as executable code. Imported data has non-executable ELF section flags; this MCU has no MPU enforcing flash data nonexecution in hardware.

## Literal legacy configuration values

Configuration compaction now copies stored keys and values literally. The original used stored text as a printf format with omitted arguments, corrupting legacy values such as `%s` and `%u`. Public configuration commands already reject `%`; retaining existing legacy text is the approved correction to that bug.

The old assembly argument-frame adapter, numeric return address and reserved flash byte are removed. Code can grow across the former `0x2919` hole without a private format-string data dependency. Slot bounds, NUL termination, erased padding, checksums and flash operation ordering remain tested against the original for ordinary values. Candidate regressions cover format metacharacters as literal data, including `%n`, and whole-image UART compaction, readback and persistence across a fresh boot. Those legacy cases intentionally differ from the executed original and are tested as corrections, not declared equivalent.

## Stack and validation boundaries

The manifest reports `stack_headroom_bytes` after all fixed and linker-allocated globals. This is available space, not a proven maximum stack allowance. Compiler reports identify a 680-byte `syscon_rt_vfscanf` frame, a 584-byte `syscon_cfg_compact_body` frame and a 184-byte protocol poll frame. They must be composed with call chains, assembly ABI frames, interrupt stacking/nesting and callback paths. The builder records `.su` evidence and lists assembly sources without compiler frame bounds. It does not present these numbers as a whole-image bound. A linker minimum-headroom assertion is a rejection guard, not a stack-safety proof.

`tests/test_physical_firmware.py` uses a separate, plainly labelled test-only fixture. It verifies reset from dirty SRAM, initialized-global/BSS effects, constructor order, vectors and relocated data pointers, actual SRAM polling through nonterminal statuses, wrong-entry audit rejection and deliberate RAM-slot overflow rejection. The original reset comparison traps constructors/main at declared fixture boundaries and normalizes only the two relocated printer pointers. UART wrappers directly compare their dependency arguments with original instructions.

The original reset routine at `0x79f0` already copies initialized SRAM and clears
the ordinary BSS range on each reset. The retained three-byte SRAM mirror is
subsequently restored by `syscon_target_retained_load` from PMU scratch registers
at `0x400b0400..0x400b0408`; it does not survive through uninitialized `.bss`.
`tests/test_warm_reset.py` boots both complete images, dirties the SRAM mirror and
configuration cache, requests SYSRESETREQ, executes reset through the application
loop, and checks VERSION afterward. Read-only instruction observers verify the
valid retained values survive startup exactly, while invalid magic is cleared
according to the original behavior. Ordinary configuration data is reinitialized
in both images. This exercises the modeled warm-reset domain, not physical PMU
retention or ROM boot behavior on the attached MCU.

Historical startup and flash-ABI reports under `analysis/` describe their recorded revisions. Current validation comes from the tests and CI artifacts; obsolete compatibility-byte checks are no longer part of the layout contract. Whole-image emulator reset/CLI comparisons remain separate from hardware evidence.

The production artifact paths are `build/physical-firmware/firmware.elf`, `firmware.bin`, `firmware.map` and `manifest.json`. The manifest deliberately retains `flash_candidate=false` and `whole_firmware_equivalence=false`. The [README](../README.md) identifies the earlier source revision tested on hardware; that result does not automatically validate later builds.

The complete-image regression now exists in `tests/test_rebuilt_system.py`.
`make rebuilt-system` reproduces reset, real UART IRQ/command handling and
persistent configuration readback across a fresh boot for both the original and
source image. The named synthetic scenario passes with matching normalized
command output and persistent sectors. A separate I2C failure injection reaches
matching assertion output. See `build/rebuilt-system-session.json` and
[the emulator documentation](mcu-emulator.md) for the observation limits.


## Reclaiming SRAM during source migration

Keeping both every old state reservation and every new C object eventually
exhausted stack space: a relocated ADC build collided with live BSS during
configuration-compaction logging. The prior fixed `0x20000820` emulator guard
could not detect that collision with newer objects above its boundary.

The linker now allocates scheduler/retained objects in the freed task/timer
region instead of reserving a second copy in auxiliary RAM. Object addresses
remain linker-resolved, and the whole-image regression changes their order.
LED state, PWM/GPIO/I2C/UART descriptors and reset-cause cache now share reclaimed
peripheral-table storage; GPIO callbacks and I2C state reuse the former ADC
scratch/callback region, extended through the freed UART receive-buffer region.
UART configuration and rings are now allocated in the same arena.
The relocation test shifts these arenas by eight bytes. Startup copies this initialized
data and clears its BSS before constructors. Its 64 bytes of reclaimed storage
matter: keeping a duplicate raised the stack floor to `0x2000094c`, and the
compaction test caught an actual stack descent to `0x20000944`.
This split SRAM layout is transitional while other modules still depend on
legacy locations; it must not become a permanent private-address ABI. Remaining
migration should converge on ordinary contiguous data/BSS allocation.

The build manifest supplies `stack_floor_address`, the highest allocated state
end. `make rebuilt-system` reads it from a manifest whose binary hash must match
the image. A raw image without a manifest requires an explicit `--stack-floor`.
Full-image relocation and compaction tests pass this bound to the emulator
and check startup and later stack use against it. Only vacant legacy locations
are poisoned: reclaimed arenas are now live storage. Negative controls relink
the same objects with duplicate scheduler or LED allocation restored,
boots successfully and must hit the allocation guard during compaction. These dynamic
checks establish the exercised paths, not a maximum over all possible paths.

## Configuration data migration

Configuration messages, keys, command formats and default values now come from
ordinary C constants in `include/config_text.h` and `target/config_storage.c`.
The linker collects configuration objects' read-only data into `.config_data`
within the spare application-flash region. Code references compiler/linker
symbols rather than original string addresses; identity/configuration sectors
remain excluded from the load image.

`tests/test_config_relocation.py` poisons the original configuration text in the
isolated oracle, edits a diagnostic to a longer string and checks its real UART
output. `tests/test_firmware_relocation.py` builds a shared whole-image variant
with early/late code shifted by 16/32 bytes
configuration constants shifted by 256 bytes and initialized SRAM shifted by 64
bytes, exercising reset, UART commands and persistence. The configuration cache
is now a named `syscon_configuration_state` object whose load/runtime addresses
come from the linker. Reset copies the ordinary `.data` range before constructors.
A dirty-SRAM startup test checks the copy against the ELF load image, including
a build with no initialized data. The whole-image variant poisons the old cache
location and compares CONFIG_INTERNAL, a timer update and persistent flash with
the original. Per-function oracle fixtures deliberately retain the old cache
location only in the test linker; the physical linker has no such constraint.
Other fixed global state and recovered constants remain outstanding. New private fixed addresses are
not part of the intended source architecture.
