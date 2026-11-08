# Logger output and ARM variadic adapters

`target/logger_target.c` formats timestamps, tags, colors, messages and truncation.
`target/logger_target_abi.S` collects ARM variadic arguments and preserves the
UART return-register effects used by the existing command parser. Enable state
and the manufacturing tag are named objects in `target/logger_state.c`, declared
by `include/logger_state.h`. Text and colors are ordinary C strings. `include/logger_frame.h` gives the
exposed stack buffers named fields and shares their layout with assembly.

| Original entry | Rebuilt symbol | Existing link alias |
| --- | --- | --- |
| 8e8c | syscon_logger_target_vlog | — |
| 8f88 | syscon_logger_target | syscon_target_logger |
| 8fa0 | syscon_logger_target_mfg | syscon_target_mfg_logger |
| 5edc | syscon_logger_target_sg560d | syscon_target_sg560d_printf |
| 92ac | syscon_logger_target_vformat | — |
| 92f4 | syscon_logger_target_snprintf | syscon_target_snprintf |

The physical linker allocates the enable byte in reclaimed SRAM. The isolated
oracle linker alone places it at the original address. `src/logging.c` is the
historical host scaffold; production does not call that adapter.

## Returns and legacy frame behavior

The original logger reserves 368 bytes including saved r4–r7 and LR. Its prefix
starts at offset 24, short message at 56, and 256-byte message at 88. Although
prefix formatting has a 32-byte buffer, the original sends its full formatted
length. An overlong tag can therefore expose stale buffers, saved registers or
caller memory, and eventually fault on an unmapped read. The current source
retains that behavior and the exposed buffer/argument layout.

Saved return addresses are now the actual linked call returns. There are no
original return-address literals or mappings back to a relocated continuation.
Normal stack return restores r4–r7 and PC while leaving UART R0–R3 unchanged.
An externally corrupted saved return still causes its native control-flow or
fault behavior. Raw private PC bytes exposed by malformed overlong tags change
when code moves; identical private addresses are outside the project's contract.

The logger writes time/tag at offsets 0/4/8 and the argument pointer at 16.
Messages of 1–31 bytes use the short buffer; other lengths trigger a second pass.
Signed nonpositive results send no message. Long positive messages truncate to
255 bytes ending in `...`, then a possible color reset and CRLF. SG560D uses a
separate cleared 128-byte buffer and UART port 1. These buffers and the runtime
formatter use native target memory accesses, not host substitutions.

## Validation

`tools/logger_target_oracle.py` compares original and compiled ARM execution with
explicit UART/time/color ports. It compares ordered output bytes, sizes, ports,
faults, preserved registers and stack restoration. Constant source pointers are
compared by their transmitted contents. When an overlong prefix exposes saved
LR, the oracle first checks that word against the real observed call return,
then normalizes only that word. A deliberately reinstated original-address
literal must fail this check; normalization cannot silently bless it.

Tests cover prefix overreads and RAM-boundary faults, formatting thresholds,
variadic alignment, buffer overlap, live format/argument mutations, changed
saved registers/returns, disabled logging and invalid pointers. Original-ROM
poisoning checks text/color/tag independence. The real-UART variant executes
actual register writes and checks R0–R3, allowing the validated manufacturing
tag object to move in disabled logging. Register values can become missing
variadic arguments in the original SET_RGB parser.

Whole-image relocation exercises LOG disable/re-enable and SET_RGB tokens through
real UART, protocol, logger and peripheral code, with the old enable byte
poisoned. Warm reset compares reinitialization. The source contains no original
executable fallback. Current run results are CI artifacts; the README identifies
the separate hardware-tested revision.

These finite tests do not establish every interrupt interleaving or arbitrary
pointers into deeper C frames. The logger still has the original overlong-prefix
bug; moving private code/data does not require preserving the private bytes it
can expose. Physical UART timing and silicon fault behavior need hardware tests.
