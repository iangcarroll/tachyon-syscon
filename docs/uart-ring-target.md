# Original-ABI UART ring implementation

`target/uart_ring.c` implements seven direct ARM interfaces with the original
RAM descriptors and state locations. It supplements, rather than silently
relabels, the higher-level `src/uart.c` host adapter.

| Original | Target symbol |
| --- | --- |
| `0x891c` | `syscon_target_uart_rx_disable` |
| `0x8938` | `syscon_target_uart_rx_enable` |
| `0x8c34` | `syscon_target_uart_put` |
| `0x8c8c` | `syscon_target_uart_write_buffer` |
| `0x8cf0` | `syscon_target_uart_available` |
| `0x8d70` | `syscon_target_uart_irq` |
| `0x8de4` | `syscon_target_uart_read` |

State is accessed directly at the original 32-bit addresses; no host-owned ring
struct, environment callback or port-array substitute is used. The implementation
links the reconstructed descriptor lookup and blocking UART transmitter from
`target/hal_helpers.c`, plus source runtime string functions for the invalid-port
assertion path. Invalid public port indices invoke the original assertion
interface with the same file pointer, line number and expression. Assertion
behavior is an explicit unresolved link dependency of this module, not replaced
with a normal error return. Tests stop and compare that boundary.

Unsigned ring counts, nonzero full/disabled bytes, and the signed available-count
test in read are preserved. The receive handler prefers descriptor 1 when both
descriptors point to the same base. It consumes RXDATA before checking ring
capacity, and retains the original behavior when a disabled port is nevertheless
passed to the receive handler. Corrupt indices are not normalized before access:
the byte write may overwrite a ring metadata byte, after which the original
reloads the write index before incrementing it. Volatile operations preserve
these read/write dependencies and MMIO ordering.

Eight test groups execute original and freshly compiled ARM implementations,
linking the actual reconstructed dependencies without libc or libgcc. They compare
complete non-stack RAM and ordered RAM/MMIO transactions, including 600 mixed
receive/read operations, full-ring drops, corrupt/self-aliasing indices, mutated
descriptor bases, unsigned count wrap, signed availability, busy TX polls,
source-buffer faults after partial transmission, invalid ports, and suppression
of invalid-buffer reads when disabled or size is zero. Transaction values are
masked to the transfer width: Unicorn's byte-write hook reports the whole source
register, while only its low byte is transferred.

This is executable integration evidence for these original interfaces, not a
whole-firmware proof. The tests retain separate harness stacks and do not prove
cycle timing, all interrupt interleavings, assertion/reset completion, or a
physical-layout replacement image.

## Caller-saved register correction

A real parser→SET_RGB→logger→UART execution exposed behavior beyond the public C return value. The original `0x8c8c` returns R0=0, R1=input port, R2=input size, R3=input size. These outputs feed a later variadic callback when SET_RGB supplies too few arguments. The previous C-only transmitter preserved R0 but left different R1–R3 values.

`target/uart_ring_abi.S` now owns the public entry, using the original 32-byte push layout, length store at SP+4, and pop into R1/R2/R3. It calls the source transmitter body in `target/uart_ring.c`. The signature remains `uint32_t(port,data,size)`; the additional register effects are explicit target ABI behavior. Tests compare all four output registers for both ports, enabled/disabled state, and zero/nonzero sizes. A buffer aliasing the outer entry frame verifies that its original saved words are transmitted. The C body's deeper private stack remains distinct and is not claimed byte-identical.

Both standalone and combined target builders include the assembly adapter. The source-built full MCU UART regression now matches original SET_RGB tokens `0`, `%u`, `%s`, `%p`, `%d`, `%x`, `%c`, and `%3u` through the real parser/logger/peripheral path. These finite cases resolve the demonstrated discrepancy; arbitrary missing arguments remain a wider proof obligation.
