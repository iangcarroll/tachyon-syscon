# Original-ABI PWM target drivers

`target/pwm_target.c` and `include/pwm_target.h` reconstruct eight entries with direct target memory/MMIO operations.

| Original | Symbol | Behavior |
|---|---|---|
| `0x87dc` | `syscon_target_pwm_init` | Descriptor/GPIO lookup, assertion order, GPIO power/mux, conditional timer power/clock/configuration |
| `0x88c0` | `syscon_target_pwm_write` | Disable timer, write compare value, reload descriptor base, enable timer |
| `0x9400` | `syscon_target_pwm_clock` | Three byte configuration reads and ordered clock register writes |
| `0x941c` | `syscon_target_pwm_compare` | Full-width compare value and wrapping index offset |
| `0x942c` | `syscon_target_pwm_capture` | Read/modify/write mask `0x27777` |
| `0x9450` | `syscon_target_pwm_action` | Read/modify/write mask `0xffc1b6db` |
| `0x9470` | `syscon_target_pwm_output` | Read/modify/write mask `0x8f` |
| `0x948c` | `syscon_target_pwm_configure` | Optional channels 2/3, period/mode/action setup, channels 0/1 and final control merge |

Initialization performs both lookups before validating either result. The PWM lookup uses the full pin argument; no new low-byte truncation is added. Timer initialization is skipped when the single power-register read already has bit zero set. GPIO mux and timer descriptor data are loaded in original order. Compare writes do not clamp duty cycle or validate channel index; full-width index multiplication and address addition wrap as ARM32 operations.

Configuration preserves all three mode classes: zero, `0x20`, and every other byte. The first two use period minus one with unsigned wrap; other modes use period shifted right one. Extra-channel setup reads mode before its writes; main setup rereads mode afterward, so aliasing configuration memory with affected registers is observable. It reads control byte 6, mode byte 4 and period word in original order. Final control uses mask `0x3000ffbf`. Return R0 is the input base and R1 is the captured control byte, represented by a `uint64_t` target return.

The descriptor table at `0x20000148`, GPIO table and original assertion strings are fixed-layout data dependencies. These bodies call source-reconstructed descriptor lookup and string helpers. Assertions are explicit nonreturning dependency boundaries in direct tests. There is no original executable fallback or installed runtime library.

`tests/test_pwm_target.py` compares original versus source-compiled ARM with the shared builder in `tools/i2c_pwm_target_oracle.py`. It covers every mode byte and every control byte, extra channels, period underflow/high-bit boundaries, each register-mask bit, full-width/wrapping channel indices, changing register read values, register/configuration aliases, every descriptor, timer-already-powered paths, invalid mappings and injected bus faults. All RAM/MMIO access widths, ordering and values are compared alongside returns and RAM effects.

The combined checkpoint is **24 passing groups, 833/833 identified original instructions across 13 I2C/PWM entries**. See `analysis/i2c-pwm-target-reference-coverage.json`, `analysis/i2c-pwm-target-mapping.json`, and [I2C target dependencies](i2c-target.md). This does not establish universal equivalence, exact code bytes, hardware PWM waveforms, private stack-alias behavior, or flash readiness.
