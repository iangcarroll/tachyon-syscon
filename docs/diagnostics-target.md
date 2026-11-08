# Target diagnostics and configuration accessors

`src/app/diagnostics_target.c` implements eleven original entries with the
ARM argument ABI, including the complete periodic diagnostic body. Enable
state and loop/rate counters are named linker-allocated objects declared in
`include/diagnostics_state.h` and defined in `src/app/diagnostics_state.c`. The
application timestamp constructor uses that same state. All text is ordinary C
data; the module has no original private RAM or ROM address dependencies.

The six flags remain full byte values. The unaligned timing words use four
byte reads in the original order (second, first, third, fourth). Revision
classification executes the rebuilt scan runtime with the original format.
The loop counter is 64-bit; timestamps retained in RAM are 32-bit. Elapsed
checks, rollover, repeated time reads, unsigned division, and truncation of
the modem-state byte are preserved. A zero loop-rate divisor uses the original
unsigned divide helper's result rather than C undefined division.

`tests/test_diagnostics_target.py` compares original ARM and newly compiled C.
It exercises parsing without a parser hook, formatting through the rebuilt
logger formatter, boundary timestamps, counter overflow, negative and sentinel
temperatures, zero-divisor cases, and dependency-call/log-argument order.
Persistent RAM access widths/order are compared, including a mutation between
low/high counter reads. Clock, power measurements, GPIO, temperature, modem
state, minimum voltage and the final logger sink are explicit test endpoints.
Private buffer pointers are compared by their consumed string contents.

ROM-poisoning tests check string independence. Whole-image relocation exercises
DIAG commands and main-loop counter progress with old storage poisoned, while
warm reset verifies that the enable byte returns to its original initial value
of one and that the counters are reinitialized. The freed power-string ROM
block now holds linker-allocated constants; it is no longer an imported blob.

These are bounded comparisons, not proofs of every interrupt interleaving or
private-stack alias. Synthetic MCU temperature inputs do not establish sensor
accuracy or physical battery thermal behavior.
