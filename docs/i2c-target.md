# I2C master transfers and fault handling

`target/drivers/i2c_target.c` reconstructs five original entries as directly compiled Cortex-M0+ functions. `include/i2c_target.h` defines their target ABI. These functions use real 32-bit target pointers and volatile accesses, without the host environment argument used by the older adapter.

| Original | Symbol | Contract |
|---|---|---|
| `0x82b4` | `syscon_target_i2c_error` | Log stage name, clear MCTR, flush TX then reload descriptor and flush RX, return -1 |
| `0x82f0` | `syscon_target_i2c_init` | Lookup/assert, power/reset, actual delay, GPIO mux/pullups, clocks, FIFO/interrupt configuration; return R0=0 and R1=bus |
| `0x844c` | `syscon_target_i2c_transmit` | FIFO-driven master write, interrupt error flag and timeout recovery; return count or -1 |
| `0x860c` | `syscon_target_i2c_receive` | FIFO-driven master read; return result in R0 and original count in R1 |
| `0x8798` | `syscon_target_i2c_irq` | Low-byte interrupt reasons 8/11 set the error flag and log NACK/arbitration loss |

Only bus zero resolves through the board descriptor; high bits are not truncated. Initialization rejects a null configuration after validating the bus. Transfer routines validate the saved mode byte, but do not add buffer validation absent from the original. Filename/expression contents and assertion line numbers are preserved.

`include/i2c_state.h` declares the typed bus descriptor and error/mode state.
`target/drivers/hal_helpers.c` defines Tachyon's SCL/SDA routing, peripheral base and IRQ;
`target/drivers/i2c_target.c` owns transfer state. These objects and diagnostic strings
are linker resolved. Only differential fixtures use their former placements.
The fault-stage names are editable C strings in `target/drivers/fault_control_target.c`.

Initialization preserves the ordering of descriptor, GPIO, configuration and MMIO reads. A nonzero configuration mode does **not** overwrite the saved mode byte. Signed IRQ numbers suppress NVIC accesses when bit 7 is set; nonnegative IRQ numbers retain ARM's masked shift behavior. The actual 1000-count cycle loop runs.

Transfer stage codes are 9–12 for transmit and 13–16 for receive. Status waits allow exactly 10000 failed reads/delays of 32; FIFO wait ordering has its own original checks. The implementation keeps repeated descriptor loads, the base captured by a successful status read, exact address/control masks, and 32-bit shift wrap. A zero base is not conflated with timeout. TX clears the error byte only when starting a nonempty transfer. RX does not clear it, so stale error state remains observable. Recovery flush loops have no invented timeout.

Progress counters wrap at eight bits even though lengths are 32-bit. Counts of 256 or more can therefore fail to finish. The comparison suite interrupts matching observable trace prefixes for those inputs rather than silently repairing the original behavior or claiming termination. A stuck flush similarly remains a wait until an explicit test boundary interrupts it.

## Dependencies and validation

`tools/i2c_pwm_target_oracle.py` builds this source with `target/drivers/pwm_target.c`, `target/drivers/hal_helpers.c`, `target/drivers/mspm0_core_target.c`, `target/drivers/gpio_state.c`, `target/drivers/core_helpers.c`, `target/drivers/fault_control_target.c` and `src/runtime_memory.c`. It links no installed libc/libgcc. FIFO helpers, descriptor lookup, stage set/name and actual cycle-delay instructions execute on both sides. Direct tests trap only logger `0x8f88` and nonreturning assertion `0x2678`; the linked full assertion body is not executed by these tests. Logger arguments are compared at the variadic call boundary, not substituted with an invented hardware result.

`tests/test_i2c_target.py` compares original and recompiled ARM return values, ordered RAM/MMIO reads and writes, logs, assertions, and RAM effects under the same scripted register environment. Cases include each IRQ reason byte, valid/invalid modes and buses, signed IRQ boundaries, all timeout stages, last-iteration readiness, dynamic descriptor replacement during actual delay execution, FIFO stalls, asynchronous/stale errors, payload/configuration aliases, invalid pointers, every initialization bus-fault prefix, and nontermination controls. Scripts describe external register inputs; these tests do not claim full I2C silicon or expander behavior. Higher-level device integration is a separate checkpoint.

Original-ROM poisoning checks reject old assertion, IRQ-message and stage-name
dependencies. Whole-image relocation tests move the bus/error objects and inject
an expander NACK at boot: both images must reach the same real assertion output,
interrupt-disabled state and SysTick state. Warm-reset tests compare data/BSS
initialization after poisoning the named objects. These remain finite emulator
checks, not physical electrical or timing validation.
