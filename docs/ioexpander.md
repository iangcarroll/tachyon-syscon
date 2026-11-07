# IO-expander reconstruction

This is a reviewed, host-testable C reconstruction of the IO-expander layer in
the pinned syscon 1.0.52 image. It is not a complete hardware emulator or a
flashable firmware replacement. The physical expander part number is not
established by this work.

| Original entry | Reconstructed operation |
| --- | --- |
| `0x3668` | Write a 16-bit register pair, little endian |
| `0x36bc` | Select and read an 8-bit register |
| `0x374c` | Write an 8-bit register |
| `0x379c` | Update an output latch bit without direction checking |
| `0x37e4` | Reset direction/output/polarity register pairs |
| `0x3808` | Initialize HAL I2C, optionally reset expander registers |
| `0x386c` | Configure one of 16 pins |
| `0x3940` | Write an output pin, reject input pins |
| `0x39e8` | Read input register or output latch according to direction |
| `0x3620` | Route a GPIO read to the MCU or expander |
| `0x364e` | Route a GPIO write to the MCU or expander |

The reconstructed layer uses I2C bus zero, address `0x26`. Register pairs are
input at 0/1, output latch at 2/3, polarity at 4/5, and direction at 6/7. A set
direction bit means input. Reset writes `ffff` to direction, then `ffff` to
output, then `0000` to polarity; this ordering is preserved.

Every HAL write/read has its own four-attempt budget. Only an exact byte-count
match succeeds. I2C initialization succeeds only on return zero. Exhausting a
budget enters the original fatal assertion handler. The native implementation
reports the assertion line through a callback and returns host-only sentinel
`-2`; the original assertion never returns. No subsequent expander operation is
performed after this boundary. Emulation stops at the same assertion boundary,
so the watchdog, LED, and reset behavior inside the assertion handler is not
covered here.

Observed compatibility details preserved:

- Only output value 1 sets a latch bit. Every other value clears it. A value
  other than 0 or 1 forces a write even if the latch bit was already clear.
- Output initialization happens before changing direction, and still happens
  when the pin is already configured as output. Direction is read back after
  a direction change, but the readback is not checked against the written value.
- Reads of output pins use the output latch, not the input sampling register.
- Writing an input pin logs an error and returns `-1` without changing a latch.
- Nonzero configuration mode and apply-initial-value bytes mean true. The
  recovered configuration prefix consists of three bytes: output mode, initial
  value, and apply-initial-value flag.
- Generic GPIO IDs below 25 route to the native MCU HAL. IDs at or above 25
  subtract 25 and then truncate to eight bits before expander validation.
  Consequently some large IDs wrap to valid expander pins.
- The generic GPIO write wrapper is void and discards expander status. The
  host adapter returns zero for its normal completion, including the logged
  input-pin case; this host result is not claimed as the original ABI.

## Differential validation

`tests/test_ioexpander.py` executes the original Thumb instructions using
`tools/ioexpander_oracle.py`, and compares them with the compiled C. It compares
the complete ordered I2C transaction trace, register storage, selected-register
pointer, assertion boundary, return values where defined, read outputs, and the
original initialized byte at `0x200002d0`.

Coverage includes all 16 pins, all combinations of four mode/value cases and
three initialization-flag cases, 500 further randomized operations, retry
success on attempts 1 through 4, short/oversized/negative HAL results, terminal
failure, independently exhausted read/write retry budgets, failed reset at each
register pair, invalid arguments, initialization preconditions, and generic
GPIO ID boundaries/wrapping.

The shared deterministic register-bus model implements full transfers and
leaves registers unchanged on short/failing transfers. This is an explicit
test-environment assumption; it does not establish what the real I2C controller
or expander does after a partially completed transaction. No electrical timing,
bus arbitration, clock stretching, interrupt concurrency, or MSPM0 peripheral
register implementation is modeled. HAL functions `0x82f0`, `0x844c`, and
`0x860c`, native GPIO functions `0x8054`/`0x80f8`, diagnostic logging `0x8f88`, and
fatal assertion `0x2678` are explicit oracle hooks. All intermediate expander
functions execute original instructions.

## ABI and build status

The portable C uses a context and injected callbacks instead of the original
fixed globals and HAL linkage. Its interfaces are therefore harness interfaces,
not a drop-in ARM binary ABI. `syscon_io_config` preserves the observed first
three configuration bytes. Restoring original linkage, register/stack calling
conventions, fixed addresses, and code-generation equivalence remains work for
the eventual firmware integration. No exact machine-byte match is claimed for
this module, and nothing in this work accessed or modified the board.

Run the differential suite from `syscon-re` with:

```sh
.venv/bin/python -m pytest -q tests/test_ioexpander.py
```

On the current macOS environment Unicorn requires permission to allocate JIT
memory outside the sandbox. This requirement concerns local emulation only.
