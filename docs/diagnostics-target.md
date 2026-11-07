# Target diagnostics and configuration accessors

`target/diagnostics_target.c` implements eleven original entries with the
firmware's fixed RAM layout and ARM argument ABI. It includes the complete
periodic diagnostic body, not just its side effects with log calls omitted.

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

The tests are bounded comparisons. They do not prove arbitrary interrupt
interleavings, private-stack aliasing, every call input, or a whole physical
image. Original-address constant strings remain a layout dependency. These
entries are not permission to flash a reconstructed image.
