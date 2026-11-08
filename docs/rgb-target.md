# RGB animation and editable presets

`src/power/rgb_target.c` provides all thirteen identified RGB entries using the
linker-allocated `syscon_rgb_runtime` object in `include/rgb_state.h`. It includes source callback registration, color
scaling, PWM output order, initialization, brightness/pattern configuration,
presets, timer expiry, state/configuration queries and key feedback.

Change colors, brightness, animation patterns and palette entries in
`include/rgb_data.h`. Names and messages are ordinary C strings. Code and data
can move without updating private numeric addresses. The enum names in
`include/rgb_state.h` identify the existing command-visible preset/pattern IDs;
changing those IDs would change the protocol. The preset named `off` retains
the original solid-red setting; the name is not a reason to change its behavior.

PWM pin/timer routing is a separate board description in
`src/drivers/hal_helpers.c`, declared by `include/pwm_state.h`. The physical linker
temporarily places LED state and PWM descriptors in reclaimed SRAM to avoid
duplicating old reservations. See [memory layout](physical-firmware-build.md#reclaiming-sram-during-source-migration).

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

`tests/test_rgb_target.py` compares register results,
ordered state reads/writes, output dependency arguments and resulting RAM.
Cases include all floating-point classes plus deterministic random raw bits,
unsigned channel wrap, configuration aliases, PWM callbacks changing later
colors, every pattern, invalid patterns/presets, duration expiry, long animation
sequences and restoration after transient key feedback. The timer callback
pointer relation is checked against the precise original and rebuilt symbols.
PWM, timer registration/init and logger are explicit endpoints in this fixture.
String arguments and name returns are compared by content, not private address.
Negative controls poison the original strings/tables. A source-edit test changes
a preset brightness, rebuilds, and requires an actual PWM output change.

`tests/test_firmware_relocation.py` also exercises real UART commands, the timer
interrupt and ordered red/green/blue compare writes in both complete images.
It moves code and peripheral data and poisons the old LED/PWM locations.
Animation must progress, so two stuck outputs cannot pass by equality alone.
Warm-reset tests poison the new objects and compare their initialization with
the original. These finite emulator tests do not validate physical PWM timing.
