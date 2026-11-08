# Original-ABI I/O expander

`src/drivers/ioexpander_target.c` and `include/ioexpander_target.h` implement eleven
entries with their original arguments, direct pointers, SRAM initialized flag
at `0x200002d0`, target I²C calls, GPIO calls, logger, and assertion boundary.
There is no host context or private device-state copy in the implementation.

| Entry | Target symbol suffix, prefixed `syscon_target_` |
| --- | --- |
| 3620 / 364e | pin_read / pin_write |
| 3668 / 36bc / 374c | ioexpander_write16 / ioexpander_read8 / ioexpander_write8 |
| 379c / 37e4 / 3808 | ioexpander_write_unchecked / ioexpander_reset / ioexpander_init |
| 386c / 3940 / 39e8 | ioexpander_configure / ioexpander_write / ioexpander_read |

The low-level write16/read8/write8 routines preserve their original R0 result
(the full input register index, even though the transmitted register is a
byte). Reset consequently leaves R0=4. The GPIO wrapper forwards the HAL or
expander write result rather than substituting zero. The 3620 wrapper selects
HAL pins below 25 and otherwise truncates `pin-25` to a byte before expander
validation, matching the original.

Every returned I²C failure is retried up to four attempts. In particular,
`0xfffffffe` is an ordinary returned failure here, not the native host model's
terminal sentinel. When an I²C dependency does not return, no retry occurs.
After four failures the real target assertion dependency receives the original
filename pointer, line, and expression pointer. No host-only status return
replaces assertion behavior. The implementation also preserves configuration
read timing across bus calls, read-modify-write no-op suppression, the unusual
nonboolean-output clear operation, direction-based input versus output reads,
the output pointer store after bus reads, and the lack of early null-output
validation.

I²C dependencies use the canonical `i2c_target.h` API: init82f0 and receive860c
return 64-bit register pairs, with the lower word used for result checks;
transmit844c returns a word. GPIO80f8/8054, assertion2678, logger8f88, and our
C `runtime_memory.c` string/copy helpers are ordinary link dependencies.
The initialization flag, diagnostic basename and assertion/log strings are
linker-resolved objects. The removed `0xb2c7..0xb4ab` ROM block is poisoned in
a differential regression; input/read/write/error behavior still matches.

## Differential tests

`tools/build_ioexpander_target.py` produces a relocated, non-flashable ELF and
a source/compiler/ELF hash manifest. The target module and compiled test
environment use Cortex-M0+ GCC `-Os -ffreestanding -fno-builtin -nostdlib`.
The fixture's 64-bit return construction uses our recovered arithmetic runtime,
compiled with its established `-O2` flags, and its small ABI assembly. No
installed runtime libraries are linked.

`tools/ioexpander_target_oracle.py` and `tests/test_ioexpander_target.py`
execute the original and rebuilt ARM instructions. I²C/GPIO/logger/assert
reference endpoints redirect to separately compiled fixture bodies; all
expander and runtime-string logic executes directly. The fixture models a
byte register bank, scripted returned failures, a distinct terminal dependency
fault, and writes to supplied buffers. This tests the expander's bus contract;
it does not replace an electrical device validation or independently prove
the I²C HAL. The HAL has separate target tests.

Comparisons include persistent SRAM through `0x20000cff`, exact ordered
persistent-RAM writes, bus payloads/ordering, device-register contents,
logger/assert arguments, R0, callee-saved registers, and unchanged PRIMASK.
Stack scratch and incidental caller-saved register values are excluded.
The GPIO and I²C fixture functions themselves execute ARM code, including
the terminal assertion's nonreturning BKPT boundary.

The **18 tests pass**, including an init→configure→write→read→reset flow for
all sixteen pins; configuration flags and nonboolean values; every retry
position and exhaustion; null/invalid pin/config assertions; an I²C fault
that never returns; byte truncation/wrap; mutable configuration between bus
transactions; an output pointer aliasing the initialized flag; and a null
output whose store faults only after both bus reads.

Scoped instruction evidence is in
`analysis/ioexpander-target-test-instruction-coverage.json`: **437/450
identified instructions** across the eleven entries. The remaining thirteen
are unreachable for the pinned image and ordinary dependency contract:

* Ten filename fallback instructions require a filename without `/`, while
  the original filename at `0xb2c7` contains `/` (the rebuilt source uses its diagnostic basename directly): 369a/369c, 36ec/36ee,
  3728/372a, 377a/377c, 3838/383a.
* Three wrapper error instructions at 3648/364a/364c require 39e8 to return
  nonzero. Its successful path returns zero and its failure paths assert or
  fault without returning.

This is finite execution evidence, not universal equivalence or a complete
physical image. Arbitrary aliases into different compiler-generated stack
frames, all asynchronous interleavings, and physical bus timing are not proven.
