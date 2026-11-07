# Original-ABI UART configuration target drivers

`target/uart_hal_target.c` implements the four interfaces in `include/uart_hal_target.h` without host-context callbacks:

| Original | Target symbol | Meaning |
|---|---|---|
| `0x8954` | `syscon_target_uart_init` | UART initialization |
| `0x8b50` | `syscon_target_uart_deinit` | UART deinitialization, not interrupt dispatch |
| `0x95f0` | `syscon_target_uart_line_config` | Module/control and line-format configuration |
| `0x9638` | `syscon_target_uart_clock_config` | Clock source/divider configuration |

Initialization retains the original mutable 16-byte UART descriptors at `0x20000234`, GPIO descriptor lookup, pin mux writes, protected reset/power writes, and default configuration bytes at `0xabe8`. Invalid port asserts before null config. Configuration inputs are read in their actual byte/halfword order, including bytewise reads of the packed baud field.

The baud path executes the complete reconstructed arithmetic chain: unsigned integer division of 2000000 by baud, unsigned-to-float conversion, float-to-unsigned conversion and 16-bit truncation, signed-to-float conversion, subtraction, multiplication by 64, float-to-double extension, addition of 0.5, and unsigned conversion before the six-bit fractional-field update. This source does not replace the chain with a precomputed fractional zero. The integer division's zero-denominator policy comes from the reconstructed arithmetic helper.

Line control is read twice during the final update: bit zero comes from the first read and the remaining bits from the second. RX interrupt enable tests the incoming configuration's disabled byte, while the subsequent persisted configuration copies only the caller-specified length, capped at nine bytes. Short copies therefore retain old bytes, including a potentially stale disabled flag. The ring's 76 bytes are then cleared. Overlapping configuration copies keep the original forward-byte-copy behavior.

Deinitialization tests the descriptor IRQ as a signed byte, writes the NVIC disable register when nonnegative, and executes actual DSB/ISB instructions. It reloads the IRQ byte after masking the peripheral interrupt before deciding whether to clear NVIC pending state. It then disables/resets/powers down the UART and restores the pin mux values. No barriers, volatile rereads, or signed-byte conditions were removed.

## Validation and integration boundaries

`tests/test_uart_hal_target.py` uses the standalone source-only builder and comparator in `tools/adc_uart_target_oracle.py`. Both original and reconstructed instructions run; no original executable fallback or installed libgcc/libc is available to the candidate. The only trapped nonreturning dependency is `syscon_target_assert`. All division and floating-point functions are source-linked from the reconstructed runtime and pinned soft-float implementation. The remaining source dependencies are the GPIO/lookup helpers and reconstructed memcpy/memset/strrchr; the precise list is in the builder.

Tests compare ordered RAM/MMIO accesses, barrier events, return values, and RAM effects. They cover signed IRQ bytes across all 256 values, IRQ index wrapping, every persisted config-copy length, all low-level config bytes and bit basis, config/MMIO aliases, forward-copy overlap, two-read line control, assertion ordering, invalid pointers, and faults at every visible memory access.

The baud regression partitions all nonzero 32-bit denominators by the distinct value of `2000000 / baud`, testing both endpoints of each nonzero-quotient interval and the endpoints of the final zero-quotient interval, plus denominator zero. It compares the complete original and rebuilt public initialization functions at those representatives. This checks every attainable integer quotient class; it is not a machine-checked theorem covering every driver input/environment/interruption state.

The shared final checkpoint passed **29 groups in 15.11 seconds** and exercised **605/605 identified original instructions for these four UART and four ADC entries**. Evidence is `analysis/adc-uart-target-reference-coverage.json`; mappings are `analysis/adc-uart-target-mapping.json`. The global run snapshot changed only in unrelated scheduling files, while linked sources/tests remained unchanged.

The target still requires original-address read-only tables/strings, descriptors, vectors/startup, the real assertion implementation, and integration with the rest of the firmware. Relocated test builds are not device-flash images. Physical UART timing, clock rates, baud electrical output, full-domain formal equivalence, exact binary identity, private stack-layout aliasing, and identical fault frames remain separate unverified claims.
