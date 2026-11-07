# SG560D original-ABI reconstruction

`target/sg560d_target.c` implements the 38 modem entry points listed in
`analysis/sg560d-target-mapping.json`, including the main poll routine at `0x6a68`.
The separate logger reconstruction implements `0x5edc`; it is not duplicated here.
The reference is the pinned 1.0.52 image (SHA-256
`5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6`).
Instruction listings and decompilations were compared with the earlier host
reconstruction; the target implementation additionally preserves diagnostic
calls and uses actual rebuilt function pointers in submitted task records.
`include/sg560d_literals.h` contains decoded literal **data**, not copied opcodes.

The implementation covers power routing and voltage checks, normal/EDL/FCT/
fastboot preparation and action sequences, UART setup and buffering state,
retry backoff and thermal limits, timed wakeup, shutdown/reboot detection,
transition deadlines, RGB sampling and debounce, USB boot debounce, and the
power-key pulse callbacks. It reads and writes the original 32-bit RAM layout.
The retry counter and 64-bit clocks retain unsigned wrap behavior; signed
voltage and temperature comparisons retain the original thresholds.

## Validation and boundaries

`tests/test_sg560d_target.py` compiles freestanding Cortex-M0+ C and executes it
against the original ARM code with Unicorn. It compares returned values where
specified, low 2 KiB state, ordered state writes (including access widths),
ordered external calls and argument payloads, emitted diagnostic UART bytes,
and normalized task callback pointers. Source-backed logger, formatter,
integer arithmetic, memory routines and UART descriptor lookup execute in the
candidate; internal modem calls execute reconstructed C. No candidate fetch
from the original firmware code is permitted by the harness mapping.

The existing 1,200-scenario poll corpus supplies inputs only. Its native host
implementation is not used as an expected result in target tests. Cases cover
power loss, transition timeout, FCT recovery, cold and hot retry behavior,
64-bit clock wrap, three-high/eight-low RGB debounce, five-second USB debounce,
and repeated polling. Additional cases cover clock changes at **each** read,
all submitted boot callback sequences, returned driver errors, and actual
fatal-assertion entry stops. A negative control replaces the reconstructed
`off()` body with an incorrect result and requires comparison failure.

External power, ADC, GPIO, expander, UART hardware, task scheduling, retained
state, protocol polling, clock and assertion endpoints are scripted ports in
this isolated test. Task records are compared and their callbacks are executed,
but this fixture is not an integrated scheduler/peripheral simulation. A
separate assertion-returning test mode checks paths beyond the endpoint; the
fatal mode verifies neither side continues past it. Neither mode claims to
reproduce the assertion handler/reset hardware itself. Callback addresses are
relocated and compared through an explicit address map, not forced to the
original executable addresses.

The standalone function calls do not prove interrupt interleaving, real modem
responses, arbitrary corrupt-pointer behavior, arbitrary aliasing into changed
private C stack frames, full-system boot correctness, or physical timing.
Instruction exercise is reported separately and is not path completeness or
an equivalence proof. In particular, the UART descriptor-null branch cannot
occur with the immutable valid descriptor table; the three boot-preparation
failure arms depend on `power_check()` returning zero, whereas its current
original body returns one or terminates at an assertion. No false-return hook
is inserted just to inflate integrated instruction coverage.

All work and tests are offline. This file does not authorize flashing and does
not establish that a source image is safe to install.

## Recorded checkpoint

The standalone target suite passed **15 tests in 16.51s**. Its report is
`analysis/sg560d-target-direct-instruction-coverage.json`: **2,041 of 2,079**
discovered instructions in the 38 mapped bodies were exercised. The 38
unexercised instructions are the unreachable branches described above; this
count does not include separately owned `0x5edc`. All five SG implementation,
header and fixture/test inputs remained unchanged during this run. The broader
modem host and logger regression selection passed **37 tests in 22.30s**; its
coverage is kept separately because endpoint-hook cases can exercise branches
that the real internal call graph cannot reach.
