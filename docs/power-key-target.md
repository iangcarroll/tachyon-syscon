# Original-ABI power-key implementation

`target/power/power_key_target.c` implements the six power-key entries against the
original split SRAM layout. Public declarations are in
`include/power_key_target.h`.

| Original entry | Target symbol |
| --- | --- |
| 570c | syscon_target_powerkey_edge |
| 5740 | syscon_target_powerkey_poll |
| 5844 | syscon_target_powerkey_debounce |
| 5908 | syscon_target_powerkey_callback |
| 591c | syscon_target_powerkey_mode |
| 5970 | syscon_target_powerkey_init |

The range table occupies `0x200000b4..0x200000d7`; mode and current event are
at `0x200000d8` and `d9`. Counters, callback, pending/forced flags, callback
context, and pin occupy `0x20000390..0x200003a5`. Volatile byte/halfword/word
accesses retain the original write widths and order. Registration retains
the exact 32-bit callback/context pointers; callbacks execute as ARM code.

This implementation calls the real target timer implementation, not the
host context-based timer model. It preserves 10ms debounce/poll scheduling,
the four-slot timer failure behavior, pressed/released counter wrap, the
strict greater-than-5999ms forced modem-key release, and greater-than-200ms
release completion. It rereads mode after modem-key dependencies and retains
the local completion decision across a user callback. Consequently a callback
that changes the pending/event fields still receives the original subsequent
cleanup. Mode's stored byte and its diagnostic choice intentionally differ
for a nonzero input whose low byte is zero, matching the original.

External link dependencies are GPIO config/read/attach/detach from
`mspm0_core_target.h`, the canonical logger, configured long/extra hold
durations from `diagnostics_target.h`, and modem-off/key-assert/key-release
helpers. `syscon_target_modem_off` is the original 6690 predicate (positive
means off); its positive branch selects 315c, not 3178. These helpers remain
independent modules rather than duplicated inline hardware logic.

Production integration still needs the initial source-defined range table
and the mode-log string addresses `0xcd7b`, `0xcd84`, `0xcd8b`, `0xcda6`.
The key initializer configures GPIO and mode but does not initialize all
range-table/counter fields; the original depends on reset data/BSS contents.

## Executable validation

`tools/build_power_key_target.py` builds the target key module, target timer
module, our C memory routines, and a clearly separate compiled test fixture.
It uses Cortex-M0+ GCC, `-Os -ffreestanding -fno-builtin -fno-jump-tables
-nostdlib`, no libraries, and emits a source/compiler/ELF hash manifest.
The ELF is relocated to the test address space and is not a flash image.

`tests/test_power_key_target.py` compares original ARM instructions against
the rebuilt ARM functions. GPIO, modem, configuration getters, and logger
use compiled fixture code; reference entries are redirected to those fixture
functions only. The timers, power-key functions, byte-memory helpers, and
mutable user callbacks execute directly. Target execution cannot enter the
read-only original-image mapping.

The three internal edge/poll/debounce function pointers necessarily move in
this isolated ELF. Tests translate only those known pointer values in timer
callback fields and GPIO attach records. Caller-provided callback/context
values are identical on both sides and never translated. The comparisons
cover persistent SRAM through `0x20000cff`, exact persistent-RAM write order,
ordered MMIO effects, dependency/logger/callback records, defined returns,
callee-saved registers, and unchanged PRIMASK. Stack scratch is excluded.

The suite covers initialization, mode truncation, null registration,
nonboolean GPIO/modem values, all debounce branches, dependency mutation,
threshold and multiply/add overflow, all range boundaries, mutable user
callbacks, timer capacity failure, and invalid callback faults. An end-to-end
case executes over six seconds of virtual timer ticks through edge, debounce,
repeating hold polling, forced modem-key release, GPIO release, callback
delivery, timer removal, and GPIO rearming. It compares both sides at every
tick; no host key or timer model stands in for the target code.

The scoped checkpoint has **18 passing tests and 230/230 identified original
instructions** across the six entries, recorded in
`analysis/power-key-target-test-instruction-coverage.json`. These are finite
instruction-execution comparisons, not proof for every asynchronous
interleaving, GPIO electrical behavior, or whole-firmware equivalence.
