# Source-only physical-layout experiment

`tools/build_physical_firmware.py` now links a complete experimental image from reconstructed source with **zero unresolved symbols**. It performs no hardware operation. The physical profile remains unconfirmed, whole-image stack use is not bounded, and neither a successful link nor these startup tests establish firmware equivalence or flash readiness.

The builder uses `target/physical/firmware.ld` and follows the emulator's MSPM0L1306 profile: 65536 bytes MAIN flash and 4096 bytes SRAM. Missing symbols fail the link; test fixtures, endpoint stubs, installed runtime archives and original executable payloads are not production inputs. Rebuilds first remove old image outputs. Compilation/link/audit failures or input changes during the build prevent a current binary from being emitted. A manifest records source/header/linker/builder hashes, exact unresolved symbols, layout, load segments and compiler stack reports.

| Region | Placement and purpose |
|---|---|
| Flash `0x0000..0x00bf` | 48 source-defined vectors, initial MSP `0x20001000` |
| Flash `0x00c0..0x00ef` | Load image for the new source-built RAM executor, padded to its original 48-byte slot |
| Flash below `0x2919` | Linker-sized early reconstructed code, after the RAM executor load image |
| Flash `0x2919` | Source-defined zero byte for the original missing `%s` argument; read-only and non-executable ELF section/load segment |
| Flash `0x291c..0xab1f` | Remaining code, constants and initialized-data load image; actual sizes/headroom are in the build manifest |
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
| SRAM `0x200002c0..0x2000081f` | Original zeroed-global ABI |
| SRAM `0x20000820..0x20000fff` | Linker-allocated `.data`/BSS, followed by available stack space |

These region boundaries describe the transitional layout; the manifest records actual section sizes on every link. The emitted binary is 63487 bytes because fixed-address constants and version data retain their original addresses; this length is not the amount of executable code. No factory/NONMAIN contents or persistent identity/configuration are invented.

## Reset and original-ABI flash execution

`target/physical/startup.c` copies initialized globals, copies the new RAM executor, clears exactly the original BSS range, and initializes any explicitly allocated auxiliary SRAM. It calls reconstructed `syscon_target_runtime_init`, which performs the original no-op init hook and timestamp/queue constructors in order, then enters `syscon_target_main`. UART vector wrappers call source UART IRQ code with original bases `0x40108000` and `0x40100000`. Other populated vectors preserve their roles; originally null vectors remain null.

The production builder defines `SYSCON_DIRECT_FLASH_ABI` for `target/config_storage.c`. That narrow binding routes erase, program, blank and protection operations to `target/flash_abi_target.c`. Its original-ABI helpers call the fixed Thumb RAM entry `0x20000001`. The RAM body performs direct volatile FLASHCTL accesses and has no callback or flash-resident data dependency. The generic callback controller remains available for existing standalone tests but is garbage-collected from the physical image. The callback API is not silently changed or implemented by ignoring an arbitrary callback argument.

The linker explicitly retains the RAM input section with `KEEP`, asserts that it is nonempty and no larger than 48 bytes, then pads the original reserved slot. This matters because a fixed numerical call target creates no linker relocation to retain the routine automatically. The audit verifies the source executor symbol is exactly `0x20000001`, rejects accidental retention of the generic executor, checks executable/load address ranges and excludes identity/config sectors. Tests check actual SRAM-only instruction execution and data reads throughout the flash-busy interval; the only external accesses there are FLASHCTL MMIO reads/writes.

This reviewed direct binding supersedes the earlier experimental layout that placed the generic 48-byte callback executor plus 20 bytes of callbacks/table in SRAM. Those additional 20 bytes are no longer allocated; headroom is restored from 1996 to 2016 bytes.

## Data provenance and relocation

`target/physical/constants.S` is a textual data-only source artifact derived from the pinned firmware. It excludes original vectors, executable code, copied RAM machine code, old command descriptors and old unwind metadata. `analysis/physical-data-manifest.json` records the reference hash, data ranges and every reviewed relocation:

- Fifteen action callback fields in `0xab20..0xabdf`.
- Constructor fields at `0xe2d8` and `0xe2dc`.
- Printer fields at flash `0xe310` and `0xe3a8`, copied to SRAM `0x20000058` and `0x200000f0`.

Command descriptors come from reconstructed C and relocate their handlers. SG callback names use the owning module's canonical source symbols. No heuristic rewriting of arbitrary odd values is used. Tests scan imported bytes for all currently identified original function pointers and confirm that every match is explicitly relocated; this does not prove the static inventory is exhaustive.

The raw disassembler listing contains false instruction interpretations inside strings such as `DIAG` and diagnostic messages. Data-boundary checks use identified function-owned ranges rather than falsely classifying every raw listing line as executable code. Imported data has non-executable ELF section flags; this MCU has no MPU enforcing flash data nonexecution in hardware.

## Legacy format-string compatibility byte

Whole-image boot and UART compaction exposed a concrete mismatch for a valid-checksum legacy configuration value `%s`. The original missing variadic argument is logical `R3=0x2919`; reading that address yields a NUL. Newly relocated code originally put nonzero instruction bytes there, which the formatter persisted and later returned through `CONFIG_GET`.

The linker now splits the source text before this address and defines exactly one `BYTE(0)` at `0x2919`, in its own read-only, non-executable section and `PF_R` load segment. This is a source-defined compatibility constant, not copied original instructions. The numeric argument remains `10521`, preserving `%u` behavior. The early text must fit before it; later code starts after it. Address, size, value, section flags, load flags and executable overlap are independently audited. The ELF flags describe the artifact and do not provide MCU memory protection.

Staged whole-image tests booted both original and rebuilt firmware, submitted `CONFIG_SET` through actual UART interrupts to compact a full legacy store, and compared the resulting persistent sector and `CONFIG_GET` value. Both `%s` and `%u` matched. Deliberately changing the compatibility byte to one changed both persistence and readback, establishing a behavioral negative control. These checks do not claim arbitrary malformed format strings or all diagnostic timing match. A separate eight-byte stack diagnostic difference was traced to an extra CONFIG_SET helper frame; original and rebuilt reset/main SP already matched. Inlining that helper restores the original call-path SP. The final canonical image probe matched persistent sectors and both command replies after removing timestamps only, including the original `1008 bytes of stack in use` diagnostic. Entry SP matched at main (`0x20000ff8`), CONFIG_SET (`0x20000ef8`), runtime update (`0x20000ea8`) and compaction (`0x20000e58`).

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

The latest direct-flash/startup checkpoint passed **24 tests in 1.11 seconds**: eight original flash-ABI groups and sixteen physical startup/placement groups, including wrong compatibility byte/address/flags, executable load segment and early-text overflow rejection. Reports are `analysis/flash-abi-target-reference-coverage.json`, `analysis/flash-abi-target-mapping.json` and `analysis/physical-startup-mapping.json`. Whole-image emulator reset/CLI comparisons are separate evidence managed by the parent task.

The production artifact paths are `build/physical-firmware/firmware.elf`, `firmware.bin`, `firmware.map` and `manifest.json`. The manifest deliberately retains `flash_candidate=false` and `whole_firmware_equivalence=false`. No device has been flashed.

The complete-image regression now exists in `tests/test_rebuilt_system.py`.
`make rebuilt-system` reproduces reset, real UART IRQ/command handling and
persistent configuration readback across a fresh boot for both the original and
source image. The named synthetic scenario passes with matching normalized
command output and persistent sectors. A separate I2C failure injection reaches
matching assertion output. See `analysis/rebuilt-system-session.json` and
[the emulator documentation](mcu-emulator.md) for the observation limits.


## Configuration data migration

Configuration messages, keys, command formats and default values now come from
ordinary C constants in `include/config_text.h` and `target/config_storage.c`.
The linker collects configuration objects' read-only data into `.config_data`
within the spare application-flash region. Code references compiler/linker
symbols rather than original string addresses; identity/configuration sectors
remain excluded from the load image.

`tests/test_config_relocation.py` poisons the original configuration text in the
isolated oracle, edits a diagnostic to a longer string and checks its real UART
output, then builds a whole-image variant with early/late code shifted by 16/32 bytes
configuration constants shifted by 256 bytes and initialized SRAM shifted by 64
bytes, exercising reset, UART commands and persistence. The configuration cache
is now a named `syscon_configuration_state` object whose load/runtime addresses
come from the linker. Reset copies the ordinary `.data` range before constructors.
A dirty-SRAM startup test checks the copy against the ELF load image, including
a build with no initialized data. The whole-image variant poisons the old cache
location and compares CONFIG_INTERNAL, a timer update and persistent flash with
the original. Per-function oracle fixtures deliberately retain the old cache
location only in the test linker; the physical linker has no such constraint.
Other fixed global state, recovered constants and the numeric legacy
return-address workaround remain outstanding. New private fixed addresses are
not part of the intended source architecture.
