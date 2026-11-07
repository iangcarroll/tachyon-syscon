# UART receive/transmit reconstruction

Implemented original routines `0x8c34` (single transmit), `0x8c8c` (buffer transmit),
`0x8cf0` (available), `0x8d70` (receive IRQ), and `0x8de4` (read). Native source is
`src/uart.c`; the two 76-byte ring structures preserve the original byte layout.

Both channels have 64-byte rings. A full ring drops newly received bytes. The
available/read paths mask the RX interrupt and then unconditionally enable it;
they do not restore a previously disabled interrupt mask. The disabled-mode byte
prevents read/transmit but does not stop the IRQ routine from adding bytes, because
the availability check returns zero in this mode. Those behaviors are preserved.
Transmit polls the FIFO-full bit without a timeout, matching the original.

`tools/uart_oracle.py` maps only the two documented UART register windows and
rejects access to registers outside its explicit set. It supplies individual
IIDX/RXDATA events and scripted TX-full reads. It does not claim complete silicon
FIFO, interrupt, baud-rate, timing, or error-status behavior. The original UART
descriptors, ring algorithms, and interrupt-mask routines execute unmodified.

Differential tests compare ring RAM, ordered register accesses and TX values
across receive overflow, wrap, disabled modes, non-RX interrupt reasons, and busy
TX FIFOs. An integration test feeds simulated IRQ bytes through the original UART
ring and command parser, comparing the reconstructed UART/parser pipeline's
dispatch, response and echo behavior, including overflow and malformed input.
The command-handler bodies in that integration test are explicit stubs; separate
configuration protocol tests execute the recovered real CONFIG handlers.

`tests/test_uart_command_logging_integration.py` additionally compares RX IRQ,
ring, parser, real VERSION/HELP handlers, MFG logger, formatter, and UART transmit
register writes in one flow, for both echo and color settings. Command bodies
and response transport execute in that test; parser debug logging remains an
explicitly suppressed side channel. Four integration cases pass, including
malformed input and command-prefix behavior.

UART initialization/deinitialization and the clock/pin register sequence are now
reconstructed separately in [UART HAL](uart-hal.md); the vector wrappers are in
[application glue](application-glue.md). Automatic silicon IRQ delivery and real
baud timing remain outside these scripted environments.

Invalid port numbers in the host API return -1; the original enters its
assertion/reset path. Ring indices are
required to be in range; arbitrary corruption of the ring pointers is not covered.
