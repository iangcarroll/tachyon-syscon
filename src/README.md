# Firmware source guide

This is the firmware source tree. The physical image links these implementations and the pinned soft-float sources under `vendor/`. `tools/build_target_interfaces.py` lists the production inputs; `tools/build_physical_firmware.py` adds reset/vector code and the linker script. `make` builds the complete image. Nothing in the build flashes hardware.

Legacy host-side models live in `tests/models/`; ARM test fixtures and test linker scripts live in `tests/fixtures/target/`. The physical builder rejects both directories. Tests also compile the production memory, arithmetic, formatting and flash-controller implementations directly, so those have only one maintained copy.

| Directory | Responsibility |
| --- | --- |
| `app/` | Initialization, main loop, event queue and diagnostics |
| `config/` | Persistent slots, configuration values and compaction |
| `protocol/` | UART parser, command descriptors and handlers |
| `modem/` | SG560D boot actions, power transitions, RGB feedback and automatic retry |
| `power/` | Supply routing, shutdown policy, button handling, retained state and LED policy |
| `drivers/` | MCU registers, GPIO, ADC, I2C, UART, PWM and flash programming |
| `scheduling/` | Millisecond timer and sequential action tasks |
| `logging/` | Diagnostic formatting and ARM variadic-call adapters |
| `runtime/` | Freestanding memory/stdio/parsing support and compiler ABI helpers |
| `physical/` | Reset, vectors, version slot and MCU-region linker layout |

Shared declarations and named state types are in `include/`. All private text, objects and callbacks use C/assembly symbols. The linker may move them. Hardware registers, MCU memory geometry, the updater version slot and persistent sectors are the explicit fixed-address contracts. Original addresses in tests select oracle functions; they do not constrain this image.

For a first edit, change an RGB preset in `include/rgb_data.h`. For a command, add its descriptor in `protocol/command_table_target.c`; the command count is computed from the array. For modem policy, start at `syscon_target_modem_poll`: it calls power-transition handling, RGB feedback, UART polling and automatic start/retry in that order. Retry delays and state live in `modem/modem_state.c` and `include/modem_state.h`.

Run `make quick-test` during development, then `make test` before proposing a firmware change. The full suite includes real reset, dirty/warm-reset state, source edits, relocated code/data, persistent flash writes and fault cases. Expected deliberate behavior changes need their own tests; unchanged behavior continues to use the original Thumb image as the oracle.

The assembly wrappers preserve documented legacy formatter/frame behavior. Do not replace those with a host libc or "simplify" argument layouts without running the relevant differential tests. All build outputs and generated evidence go under `build/`; historical analysis files are not a substitute for current tests.
