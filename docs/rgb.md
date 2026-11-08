# RGB LED reconstruction

The RGB subsystem in the pinned syscon 1.0.52 image has been reconstructed in
`tests/models/rgb.c`. It is host-testable C and cross-compiles for Cortex-M0+. No complete
firmware image or byte-for-byte match is claimed.

| Original entry | Reconstructed operation |
| --- | --- |
| `0x5b20` | Brightness scaling and output polarity |
| `0x5b48` | Flush R/G/B PWM channels in order 3/2/1 |
| `0x5b7c` | Initialize PWM and register a 20 ms timer |
| `0x5bd4` | Set brightness, optionally flush |
| `0x5bfc` | Set pattern, optionally flush |
| `0x5c38` | Apply a five-byte color/brightness/pattern configuration |
| `0x5c68` | Select one of ten state presets and optional timeout |
| `0x5cac` | Timer callback: restoration, breathing, blinking, rainbow |
| `0x5dbc` | Read current state |
| `0x5dc8` | Read six-byte state and color configuration |
| `0x5df4` | State name lookup |
| `0x5e0c` | Pattern name lookup |
| `0x5e24` | Select transient state for 40 ms |

## State and behavior

`syscon_rgb_state` preserves the 28-byte RAM span at `0x200003a8`:

| Offset | Meaning |
| --- | --- |
| 0 | Pattern |
| 1–3 | Red, green, blue |
| 4 | Configured brightness, clamped to 100 |
| 5–7 | Padding, preserved outside initialization |
| 8–11 | Current brightness as binary32 float |
| 12 | Breathing increasing flag |
| 13 | Pattern tick counter |
| 14–15 | Blink interval in milliseconds |
| 16 | Active-high polarity byte |
| 17–19 | Padding |
| 20 | Rainbow palette index |
| 21 | Current state |
| 22 | Previous state |
| 23 | Padding |
| 24–27 | Temporary-state duration in 20 ms ticks |

Initialization clears only the first 20 bytes. It preserves the adjacent
palette index, current/previous state, and timeout. It initializes PWM channels
3, 2, and 1 in that order, registers the callback, logs a registration failure
without propagating failure, and calls timer initialization.

The scaling operation first converts the current floating-point brightness to
an integer and truncates it to eight bits, then multiplies the color channel,
divides by 100, and truncates the result to eight bits. A zero active-high byte
complements that byte. It does not multiply the color directly by fractional
brightness. The C reconstruction explicitly reproduces the image's saturating
soft-float integer conversion, including its results for non-finite inputs,
without undefined out-of-range C casts.

Pattern 1 breathes by `configured_brightness / 100.0f` per callback, starting by
decreasing the current level. Pattern 2 toggles every 500 ms; pattern 3 every
100 ms. Pattern 5 advances a ten-color palette every three callbacks (60 ms).
Other patterns do not update on the timer callback. Pattern changes reset the
counter only when the incoming full-width value differs from the stored byte;
the value is stored as a byte but compared against 1/2/3 before truncation when
selecting initialization behavior. This matters for out-of-range values.

The timeout truncates milliseconds by integer division by 20. On expiry it
restores the previous state with duration zero, using the normal preset setter.
Temporary states therefore have one level of previous-state storage, not a
stack. The restored state's animation can also advance in the same callback.

Preset configurations and palette bytes are recovered from flash `0xcf18` and
`0xcf4a`, respectively. State names come from the pointer table at `0xced8`;
pattern names from `0xcf00`. The preset named `off` is preserved exactly as
encoded, including its red color, brightness 20, and solid pattern; this code
does not infer different behavior from the name.

## Differential evidence

`tests/test_rgb.py` runs the original Thumb RGB code and its original software
floating-point helpers. It compares all 28 state bytes and the ordered PWM and
timer callback traces against the native C reconstruction after each operation.
It includes:

- All ten presets over complete animation cycles, under both output polarity
  configurations across the suite.
- Temporary durations around tick boundaries, nested temporary states, and the
  transient helper.
- Randomized color, brightness, pattern, and state changes, including invalid
  values and null configuration pointers.
- Every integer brightness 0–100 with all 256 color channels, plus fractional,
  negative, subnormal, NaN, infinity, out-of-range, and randomized binary32 bit
  patterns for the conversion/scaling operation.
- Initialization with preexisting state, timer-registration success/failure,
  getters, and names.

17 RGB tests passed. The IO-expander module separately has 36 passing tests.
Both modules also compile with `arm-none-eabi-gcc -mcpu=cortex-m0plus -mthumb
-Os -ffreestanding -Wall -Wextra -Werror`.

## Limits

The oracle replaces PWM initialization `0x87dc`, PWM writes `0x88c0`, timer
registration `0x781c`, timer initialization `0x776c`, and logging `0x8f88` with
trace hooks. It does not replace float arithmetic or conversions. These tests
therefore establish subsystem behavior at the HAL boundary, not physical LED
output or end-to-end timer-interrupt operation.

The C interface adds explicit state and I/O-context pointers. It retains the
observed RAM layout but is not yet linked with the original function ABI or
fixed addresses. Binary32 arithmetic is used without fast-math; the tested
normal operating sequences match the original level bits exactly. Arbitrary
corrupted float state during animation, interrupt reentrancy, electrical PWM
behavior, and a full-board boot have not been validated by this suite. No live
board access occurred.

Run from `syscon-re`:

```sh
.venv/bin/python -m pytest -q tests/test_rgb.py tests/test_ioexpander.py
```
