# UART initialization and deinitialization

This page describes historical host test scaffolding. Production firmware uses
[the UART driver](uart-hal-target.md) and [receive rings](uart-ring-target.md).

`tests/models/uart_hal.c` reconstructs interrupt masking (`0x891c`/`0x8938`),
initialization (`0x8954`), deinitialization (`0x8b50`), line configuration
(`0x95f0`), and clock selection (`0x9638`). Transmit, receive, and ring-buffer
operations are in the separate `tests/models/uart.c` module.

The two original 16-byte descriptors select UART bases `0x40108000` and
`0x40100000`, logical TX/RX pins 4/5 and 6/7, and IRQs 15 and 13. Descriptor
mux and idle-mux fields are preserved separately. IRQ fields are signed bytes;
negative values suppress NVIC writes, while nonnegative values use their low
five bits for the mask shift.

Initialization preserves the exact sequence of pin mux, peripheral reset/power,
clock, line format, baud registers, interrupt state, peripheral enable, saved
configuration, and receive-buffer clearing. Deinitialization reverses the
interrupt and power operations and restores idle pin muxes; it does not clear
the saved configuration or ring itself.

The caller configuration is a nine-byte packed object: two bytes of header,
two-byte copy size, four-byte baud, and a byte controlling interrupt/polling
mode. Initialization reads the baud and mode before copying only
`min(copy_size, 9)` bytes into the saved configuration. A short copy therefore
can retain the previous saved mode even though interrupt setup used the new
argument's mode. The host adapter mirrors the saved mode into `syscon_uart`'s
separate disabled bytes and clears only the selected 76-byte ring.

The original baud calculation first performs unsigned integer division
`2000000 / baud`, then converts that integer to float. It does not compute a
fractional quotient. The low 16 bits become the integer baud divider; the
subsequent float/double arithmetic yields zero in the low six fractional bits
for every 32-bit baud value. The firmware's divide-by-zero helper returns zero,
so a zero baud also produces zero dividers. The C reconstruction preserves this
behavior instead of replacing it with a more accurate fractional calculation.

One read/modify/write in initialization reads the same register twice. Those
reads are preserved separately: the written value combines bit zero from the
first read with all other bits from the second. A scripted-changing-register
test checks this detail rather than assuming the register is constant.

## Validation boundary

The original code oracle executes all lookup, driver, integer, float, and
double helper instructions. Only passive MMIO values and terminal assertions
are supplied externally. Tests compare the entire ordered register trace,
register results, both packed saved configurations, and both receive rings.
Cases include standard and random 32-bit baud rates, zero and very low baud,
both ports, polling/interrupt mode, partial copy sizes, invalid index/null
config assertions, signed IRQ boundaries, random register masks, and changing
consecutive register reads.

The mask/unmask functions in the original do not validate the port index. The
reconstruction retains their valid-index precondition; arbitrary corrupted
board descriptors and out-of-range mask/unmask calls are not established safe.
The original memory barriers in deinitialization have no electrical effect in
the host model and are not represented as register operations. They must be
restored when integrating target firmware.

These are register-level software comparisons, not UART waveform or physical
baud-rate validation. The register model does not simulate reset-domain effects
or asynchronous RX/TX hardware. The portable interfaces are harness interfaces,
not the original target ABI or matching machine code. No board was accessed.

Run from `syscon-re`:

```sh
.venv/bin/python -m pytest -q tests/test_uart_hal.py
```
