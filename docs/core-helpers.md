# Target sleep and cycle-delay helpers

`target/core_helpers.c` supplies target-only implementations for MCU sleep
(`0x74f8`) and the busy delay (`0x7ae8`). The tests compile Cortex-M0+ code and
execute it alongside the original image in separate Unicorn instances.

The sleep helper logs `Going to sleep`, disables interrupts, clears SysTick's
interrupt-enable bit, executes DSB and ISB, then WFI. Upon wake it unconditionally
enables interrupts, reads SysTick control again and sets bit 1, and logs
`Waking up`. It does not restore the caller's initial interrupt mask: a caller
entering with interrupts disabled leaves with them enabled. The second SysTick
read preserves register changes made while asleep.

Logging is an explicit `syscon_core_log` link boundary. The helper currently
uses the original image's three string addresses, so it belongs to the pinned
image's address space rather than a standalone relocated firmware image. The
emulator test hooks logging and models an immediate external wake at WFI,
including a scripted change to SysTick control. It compares ordered logs,
register reads/writes, IRQ mask transitions and barriers for both initial IRQ
masks and varying register contents. It does not emulate a real sleeping core,
pending-interrupt arbitration, wake latency or clock gating.

The delay uses a five-instruction naked assembly body embedded in C. A normal
C loop would not guarantee the original instruction shape. It subtracts two
from the input, then repeatedly subtracts four, executes the original `mov r8,r8`
NOP and branches while carry is set. There is no watchdog feed. Inputs 0 and 1
underflow and request approximately a billion loop iterations; they are not
clamped to zero. The caller's r0 remains unchanged, and arithmetic flags and r3
follow the original sequence.

Three test groups in `tests/test_core_helpers.py` passed. Delay tests compare
complete instruction-offset traces, final r3 and APSR for short and medium
inputs, and bounded prefixes for underflow and very large inputs to establish
that they do not falsely return. The compiled delay has an exact **10-byte**
match to the original, recorded in `analysis/core-helper-binary-comparison.json`.
That small byte match does not prove physical timing: oscillator frequency,
flash wait states, interrupts and pipeline behavior remain outside the tests.
The sleep body is semantically compared and is not claimed byte-identical.

No target helper was executed on physical hardware. These files are excluded
from the host shared-library build; they require target compilation and explicit
link integration before use in a firmware image.
