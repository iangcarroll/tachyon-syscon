# Original-ABI ADC target drivers

`target/adc_target.c` implements `0x7c54`, `0x7d54`, `0x7e7c`, and `0x7f24` through the interfaces in `include/adc_target.h`. These are direct target functions, not wrappers around the host ADC environment. The source uses the reconstructed lookup/clock/VREF helpers, memory routines, signed division, and actual cycle-delay instructions.

| Entry | Target symbol | Behavior retained |
|---|---|---|
| `0x7c54` | `syscon_target_adc_init` | Truncated pin lookup, assertion order, reset/power/clock sequence, manual conversion fields, seven-byte config copy and separate byte scale writes |
| `0x7d54` | `syscon_target_adc_temperature` | Lazy VREF initialization, bounded readiness polling plus final reread, sampling, factory access mode, calibration arithmetic |
| `0x7e7c` | `syscon_target_adc_raw` | Manual sample/conversion sequence, delay-separated descriptor reloads, SVT result read and 16-bit mask |
| `0x7f24` | `syscon_target_adc_millivolts` | Bytewise scale reload, wrapping 32-bit product and signed truncation toward zero |

Pin lookup uses the low byte of its argument and the mutable original ADC descriptor table. Missing descriptors assert before null configuration is checked during initialization. Assertions preserve the original filename/expression addresses and line numbers. Initialization's R0 is zero and R1 is the copied first clock-configuration word; a `uint64_t` return explicitly preserves both.

The raw conversion does not cache its port across delay calls. It reloads the descriptor's base after the 32000-count delay, then reloads the slot and base after the 3200-count delay. The target implementation and tests preserve these reads, including descriptor changes during actual delay execution. It does not invent a conversion-complete poll or timeout absent from the original.

Temperature readiness performs up to 100 loop reads and delays of 320, followed by a separate final read. Readiness may disappear between the loop read and final read, or appear only at that final read; both cases retain their original behavior. The cached VREF-initialized flag is set after initialization even if subsequent readiness times out.

Temperature conversion masks the ADC result to 16 bits, reads the CPUSS factory access mode, writes mode 5, reads factory word `0x41c4003c`, and restores only the old mode's low three bits. Calibration values zero and `0xfff` return `0x80000000`. Other values use the exact wrapping subtraction/multiply, reconstructed signed division by -7168, and wrapping addition of 300. A bus fault during the calibration read leaves access mode 5 because the original has no recovery cleanup; the negative test preserves that prefix.

The scale conversion keeps the original byte read order and defined ARM32 wrap semantics. It performs signed division by 4096 toward zero, including products with bit 31 set. It does not replace that operation with unsigned division or saturate the result.

## Dependencies and evidence

The standalone builder `tools/adc_uart_target_oracle.py` links `target/hal_helpers.c`, `target/mspm0_core_target.c`, `target/core_helpers.c`, `src/runtime_memory.c`, `src/runtime_arithmetic.c`, the reconstructed arithmetic ABI/adapters, and pinned GCC soft-float source. No installed libc/libgcc is linked. `syscon_target_assert` is the one trapped nonreturning dependency in the direct tests; the full target assertion can be linked by the final image builder. Unused sleep/logging code is garbage-collected, so this ADC test does not supply a fake logger.

Fixed data-layout dependencies include ADC descriptors at `0x200000f4`, saved configuration/scale at `0x20000681`, the VREF flag at `0x20000694`, clock bytes at `0xabe0`, and original assertion strings. The factory word is explicit register-environment input, never an invented board calibration. Original bytes are readable data only in the candidate process; original executable code is not a fallback.

`tests/test_adc_target.py` compares actual original and recompiled ARM instructions, ordered RAM/MMIO accesses, return bits, and RAM effects. It exercises every descriptor, high-bit pin aliases, overlapping forward config copies, invalid mappings, null/config-pointer faults, channel/slot extremes, real delay execution, temperature readiness transitions, calibration sentinel/overflow cases, and faults at every initialization access boundary. Delay observation hooks record calls and optionally change explicit environment inputs; they do not bypass delay instructions.

The shared ADC/UART checkpoint passed **29 test groups in 15.11 seconds**, exercising **605/605 identified instructions across all eight driver entries**. `analysis/adc-uart-target-reference-coverage.json` records this run. Its global input-stability flag is false because unrelated scheduling files changed during the run; linked driver sources and tests were unchanged. This is differential test evidence, not full-domain formal proof, exact-binary equivalence, physical ADC timing/calibration validation, or a flash-ready image. Private stack-layout aliasing and silicon-specific unaligned-access behavior are not established by this relocated function harness.
