# I2C HAL reconstruction

`src/i2c.c` reconstructs the only configured I2C controller from syscon 1.0.52. The host interface preserves its RAM mapping at offset `0x13c`, GPIO mapping at `0x16c`, sticky interrupt-error byte at `0x760`, and transfer-mode byte at `0x761`.

| Entry | Operation |
| --- | --- |
| `0x82b4` | Error cleanup: clear transaction control, flush TX and RX FIFOs |
| `0x82f0` | Controller, pinmux, interrupt, and clock setup |
| `0x844c` | Synchronous write |
| `0x860c` | Synchronous read |
| `0x8798` | I2C interrupt handler |

The reconstruction includes the register effects of helpers `0x934c`, `0x9374`, `0x93a0`, and `0x93d0`; it does not substitute high-level fake successful transfers. Every MMIO read/write and delay is visible through the environment. The original instructions execute in `tools/i2c_oracle.py` with exactly the same explicit register inputs and read-response scripts. Diagnostic UART formatting is omitted; stage writes at `0x400b040c` are retained and compared.

## Preserved behavior and quirks

- Only bus zero is valid. Invalid bus, a null initialization configuration, and an unsupported transfer mode reach explicit original assertion boundaries.
- Initialization uses only the first of the eight configuration bytes and ignores the remaining fields. Its configuration of pins, register masks, and NVIC clear/enable ordering is preserved. A negative signed IRQ number suppresses NVIC writes; nonnegative values use the low five bits for the mask.
- Transaction address fields preserve all unrelated register bits and mask the shifted address to eleven bits. Length programming preserves the original twelve-bit field mask.
- Idle, transaction-start, RX FIFO, and completion waits perform up to 10000 failed polls, each followed by a 32-cycle delay. TX FIFO availability has a separate counter that permits 10000 empty delays and fails on the next empty check.
- Writes clear the sticky IRQ error only when beginning the transaction; reads do not clear it. IRQ status values 8 and 11 set the sticky byte, while other values leave it unchanged. The tests include error injection at specific register reads to represent an interrupt between instructions.
- The inner TX helper rechecks FIFO availability for each byte, but the outer function advances its intended byte count even if the helper writes fewer bytes. A differential case demonstrates returning eight after a status change prevents all eight actual writes.
- Both transfer counters wrap at eight bits. Lengths at or above 256 can fail to progress until an interrupt error occurs. Tests execute 256, 257, and 65536-byte requests with IRQ termination; a separate instruction-budget test confirms repeated nonprogress in the original 256-byte TX path without transmitting bytes.
- FIFO flush loops have no software timeout. The C reconstruction retains this behavior and therefore must only be called with a model or hardware environment that can make the flush condition progress. No timeout success is fabricated.
- Error cleanup leaves earlier received bytes and transmitted effects intact. Sticky errors are not automatically cleared by cleanup.

## Test boundary

Tests compare low-32-bit returned values, the full global RAM region through offset `0x7ff`, received buffer bytes, ordered MMIO/delay traces, final modeled registers, and remaining scripted responses. Register reset side effects, electrical signaling, real interrupt timing, physical FIFO occupancy, and actual silicon recovery are outside this deterministic register model. Arbitrary corrupt GPIO metadata or missing buffer memory is not a validated firmware-compatible domain; such host inputs can return `UINT64_MAX` at the explicit unsupported boundary.

Validation checkpoint: the sixteen I2C groups and six ADC groups passed together: **22 passed in 2.19 seconds**. The I2C groups include large-length counter wrap and original-code nonprogress. Run:

```sh
.venv/bin/python -m pytest -q tests/test_i2c.py
```

This module is not a flashable replacement and does not establish complete board emulation.
