# PWM HAL and RGB integration

This page describes the historical host test scaffold. Editable production
firmware lives in [the target PWM driver](pwm-target.md) and [RGB module](rgb-target.md).

`tests/models/pwm.c` reconstructs the original PWM initialization (`0x87dc`) and value
write (`0x88c0`) paths, together with timer-driver helpers at `0x9400`, `0x941c`,
`0x942c`, `0x9450`, `0x9470`, and `0x948c`. It executes through explicit 32-bit
register-read/write callbacks. The original board mappings are retained in
12-byte PWM and 8-byte GPIO descriptors.

The image maps logical pin 1 to timer base `0x40088000`, compare index 1. Pins 2
and 3 share base `0x40084000`, compare indices 0 and 1. Initialization first
enables GPIO power and writes the pin mux. It initializes the timer only when
bit zero of its power register is clear. Consequently initialization of a
second color sharing the timer does not reset an already-powered timer.

The recovered default sequence uses period 256 and configures the compare and
output-action registers before enabling the clock and timer. Value writes clear
bit zero of timer control, write the full un-clamped 32-bit compare value, and
set bit zero again. Bit masks and register access order are preserved. The
general timer configuration helper includes its optional extra channels and all
three mode branches, not only the fixed configuration used by RGB startup.

Invalid PWM pins enter the original assertion at source line 13 for init or
43 for write. A matching PWM descriptor with no corresponding GPIO record
asserts at line 14. The host model stops at the assertion callback and returns
`-2`; it does not execute the reset sequence inside the assertion handler.

## Validation

Four test groups in `tests/test_pwm.py` compare every original MMIO read/write
with native C, including initial random register bits, all three channels,
shared-timer ordering, already-enabled timers, repeated initialization, invalid
pins, descriptor corruption, out-of-range compare values, all configuration
mode branches, and randomized low-level helper fields. The original mapping
lookup and register-driver instructions execute; only passive MMIO storage and
the fatal assertion boundary are supplied by the oracle.

`tests/test_led_integration.py` adds two integration cases. Original SysTick,
RGB callbacks, PWM HAL, timer driver, and soft-float routines all execute without
subsystem hooks, and are compared with the combined C modules. The only
external model is passive MMIO. It compares the complete 28-byte RGB state,
112-byte timer state, register values, and ordered register trace after each
operation over 1,000 SysTick calls per case.

The two cases check initialization both with and without prior timer setup.
They preserve an important order dependency: RGB initialization registers its
callback and then calls timer initialization. If timers were not initialized
beforehand, that initialization clears the newly registered slot. With prior
timer initialization, SysTick drives RGB animation and PWM writes normally.
The full application boot order must satisfy that dependency; this test does
not change it silently.

The passive model is not an MSPM0 timer simulation. It does not synthesize
clock edges, reset effects, counter motion, PWM waveforms, or real interrupt
delivery. SysTick is invoked explicitly. These tests establish software and
register-sequence equivalence for the tested paths, not physical timing or
board safety. Source interfaces add context and board pointers, so original
target function linkage and exact code generation remain integration work.

Run from `syscon-re`:

```sh
.venv/bin/python -m pytest -q tests/test_pwm.py tests/test_led_integration.py
```
