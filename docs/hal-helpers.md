# Original-ABI HAL helpers

`target/hal_helpers.c` reconstructs twelve complete leaf functions from the pinned image. `include/hal_helpers.h` exposes their original 32-bit argument/pointer ABI. These implementations directly access volatile memory and MMIO; they do not call the existing host adapters, TI DriverLib, libc, libgcc, or replacement function hooks. `analysis/hal-helper-mapping.json` records the entries.

| Original entry | Reconstructed symbol | Behavior |
|---|---|---|
| `0x7a68` | `syscon_hal_adc_lookup` | Scan the six linker-allocated `syscon_adc_channels` descriptors by byte identifier; first match wins. |
| `0x7a90` | `syscon_hal_pwm_lookup` | Scan three linker-allocated `syscon_pwm_channels` descriptors; first match wins. |
| `0x7ac0` | `syscon_hal_uart_lookup` | Return a linker-allocated `syscon_uart_ports` descriptor for unsigned indices 0 and 1, otherwise null. |
| `0x7ad4` | `syscon_hal_i2c_lookup` | Return the linker-allocated `syscon_i2c_bus` only for index 0. |
| `0x930c` | `syscon_hal_adc_clock` | Keyed source-field update, divider-field update, then frequency byte write. |
| `0x934c` | `syscon_hal_i2c_clock` | Masked source and divider updates, preserving unrelated register bits. |
| `0x9374` | `syscon_hal_i2c_fill_tx` | Write source bytes while count comparison and FIFO availability permit. |
| `0x93a0` | `syscon_hal_i2c_flush_tx` | Set flush bit, poll TX availability until exactly eight, reread control and clear flush bit. |
| `0x93d0` | `syscon_hal_i2c_flush_rx` | Set flush bit, poll RX count until zero, reread control and clear flush bit. |
| `0x964c` | `syscon_hal_uart_put_blocking` | Poll TX-full bit until clear, then write the full 32-bit argument. |
| `0x9664` | `syscon_hal_vref_config` | Ordered byte/halfword/word configuration reads and two VREF register writes. |
| `0x9688` | `syscon_hal_vref_clock` | Write source byte then divider byte to their clock registers. |

The descriptor identifiers are compared against the **full 32-bit** input; an input above 255 does not wrap into a valid byte identifier. Descriptor memory stays mutable and is read at each call. The direct UART/I2C lookups do not dereference their returned address.

The I2C fill helper has a significant original edge case: the comparison truncates its incrementing index to 16 bits, but the source address uses the full 32-bit index. A count greater than 65535 therefore cannot end by the count comparison; a full FIFO or memory fault must end the operation. This behavior is preserved, including data accesses beyond source offset 65535. No invented length cap or timeout was added.

Configuration memory access ordering was recovered from the actual instructions, not Ghidra's expression formatting. For example, ADC clock configuration reads the old divider register **before** the configuration word. VREF configuration reads byte 1, byte 0, and halfword 2 in that order, writes CTL0, then reads word 8 before word 4. All accesses retain their original byte/halfword/word width. All MMIO read-modify-write operations read the register once per specified operation; flush helpers reread control after polling so asynchronously changed unrelated bits survive.

## Validation

`tests/test_hal_helpers.py` independently compiles this source for Cortex-M0+ using `arm-none-eabi-gcc -Os`, links it without any external library, and executes both original and rebuilt instructions under Unicorn's Cortex-M0 model. The oracle replaces **no original functions**. The environment supplies explicit MMIO values and scripted status changes at the register boundary.

Tests compare returned lookup pointers and the ordered sequence of MMIO/configuration/table/data memory accesses, including widths and values. They also check AAPCS callee-saved registers and stack restoration on normal return. Coverage includes every byte identifier, duplicate descriptor precedence, unsigned index boundaries, all configuration byte values, every input/old-register bit and its complement, randomized combined fields, all relevant polling status bit combinations, delayed completion, stuck polling, and I2C index rollover.

The final scoped run passed **34 test groups in 3.57 seconds**, with unchanged tracked inputs during the run. `analysis/hal-helper-reference-coverage.json` records all **185/185 identified original instructions** for these twelve entries exercised and no replaced endpoints. Instruction exercise is reported separately from equivalence proof. Configuration/MMIO overlap tests also preserve later reads of fields changed by an earlier write.

Negative controls inject a bus fault at every configuration/table access boundary and compare the exact preceding observable accesses. Unmapped configuration/base/data pointers exercise real Unicorn memory faults. Stuck polling is stopped only by the test's explicit access budget; no helper returns success or emits a post-poll write. The access-budget stop is test infrastructure, not part of the reconstructed function.

These tests establish the observed ABI and register/data access contract for the exercised cases. They do not establish physical peripheral timing, exact emitted bytes, instruction-count equality, identical scratch registers/flags at a void return, or identical exception frames/program counters at a fault. Full-address-space formal equivalence and silicon validation are separate claims. Unaligned-access behavior is subject to the MCU bus model, not established by this function-level harness. The source adds no pointer validation, bounds check, alignment fixup, polling timeout, or hardware success assumption absent from the original.
