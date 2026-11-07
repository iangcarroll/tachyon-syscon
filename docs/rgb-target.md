# Original-ABI RGB state machine

`target/rgb_target.c` provides all thirteen identified RGB entries with their
fixed state at `0x200003a8`. It includes source callback registration, color
scaling, PWM output order, initialization, brightness/pattern configuration,
presets, timer expiry, state/configuration queries and key feedback.

The original clears only the first twenty state bytes during initialization.
It leaves the palette/current/previous preset and duration tail intact. Byte
wraparound, volatile reloads, overlapping input/output configuration buffers,
and low-byte conversions are retained. `syscon_target_rgb_tick` preserves the
observed R0/R1 pair, including the breathing branch replacing the saved R1 word
with the target-brightness float bits. Other incidental caller-saved registers
and exact private frame layout remain outside the function test contract.

Floating operations link the pinned GCC soft-float reconstruction and our
arithmetic ABI adapters. Scale conversion calls the explicit bit-based helper
so NaNs, infinities and out-of-range values follow the original conversion
policy rather than an undefined C float-to-integer cast. No installed libgcc
archive is linked.

The six test groups in `tests/test_rgb_target.py` compare register results,
ordered state reads/writes, output dependency arguments and resulting RAM.
Cases include all floating-point classes plus deterministic random raw bits,
unsigned channel wrap, configuration aliases, PWM callbacks changing later
colors, every pattern, invalid patterns/presets, duration expiry, long animation
sequences and restoration after transient key feedback. The timer callback
pointer relation is checked against the precise original and rebuilt symbols.
PWM, timer registration/init and logger are explicit endpoints in this fixture.
This is not an exhaustive theorem or physical-image verification; fixed rodata
pointers and relocated code pointers still require whole-image integration.
