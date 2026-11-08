# Tachyon syscon reconstruction

The goal is maintainable source that can be modified while initially preserving
the original firmware's functional behavior. A source-built image already boots
in the local MCU emulator. It is experimental and is not yet a hardware-validated
flash candidate.

Compatibility covers command/protocol behavior, persistent configuration and
identity, power sequencing, watchdog/reset behavior and externally visible
peripheral effects. Timing-sensitive behavior needs an explicit timing contract.
Private instruction addresses, scratch registers and identical compiler output
are not the acceptance goal. Intentional functional changes need documented
expectations and regression tests.

## Build and test

Install Python, Clang and the pinned
[Arm GNU Toolchain 13.3.Rel1](https://gitlab.arm.com/tooling/gnu-toolchains-for-arm/-/tree/releases/13.3.rel1), then run:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make inputs
make quick-test
make test
make physical-firmware
make rebuilt-system
```

`make inputs` fetches hash-pinned TI emulator inputs and the original firmware
oracle. It does not install packages or run a device updater. Optional CAD and
schematics are fetched separately; see [references](references/README.md).

Use `make quick-test` for daily feedback after setup. It runs helper and ARM
differential tests for UART parsing, configuration writes, ADC conversion,
time-varying power inputs, RGB/PWM and runtime memory, plus input-fetch and
build-tool validation. Elapsed time depends on the host. Compiler launches on
macOS avoid copying accumulated emulator mappings when no inheritable private
descriptors need closing.
It writes a separate partial-coverage report under `build/`. `make test` retains
the full suite, including complete-image cold starts and extensive fault cases;
CI runs that complete suite in parallel core, integration, cold-start, stateful and flash-recovery jobs. The quick
selection is not a replacement for whole-image validation before a firmware PR.

`make`, `make arm` and `make physical-firmware` link the complete
experimental image under `build/physical-firmware/`. `make rebuilt-system` runs
both images from reset, exercises UART/configuration commands and checks
persistence across a fresh emulated boot. No hardware is accessed.

Unicorn needs executable memory for its JIT; restricted macOS execution can
block it. The tests compare the original Thumb instructions with reconstructed
source and run both complete images in the same MCU model. Protocol output,
persistent data, power actions and failure outcomes are functional observations;
finite scenarios do not establish every possible behavior.

## Production source and test scaffolding

The current physical build is defined by
[build_physical_firmware.py](tools/build_physical_firmware.py). It links production
code from `target/`, shared implementations from `src/`, headers, linker data and
the retained runtime source. It includes no original executable payload or
firmware-function replacement hooks.

Production modules are organized by subsystem under `target/`; isolated fixtures
live under `target/testing/` and are rejected by the physical builder. The four
shared `src/` implementations listed by the build are used directly; the other
host adapters are test scaffolding, not a second product to edit independently.
`make host-models` builds that legacy test archive explicitly.

Private code, strings, tables and global state must use linker-resolved symbols,
not numeric original-image addresses. Fixed addresses are reserved for documented
hardware, MCU memory-region and persistent-storage contracts. Layout-change tests
must exercise moved data/code and changed string lengths. Configuration storage
now preserves legacy values literally, including `%` characters, instead of
interpreting them as printf formats. This approved bug fix removes the private
return-address dependency; normal commands still reject `%`. All private globals, strings, tables and callbacks now use source objects.
Startup initializes only linker-defined objects, and the physical linker uses
MCU regions rather than original private addresses.

Start with these production source groups when making a change:

| Behavior | Implementation | State and data |
| --- | --- | --- |
| Configuration and persistent slots | `target/config/` | `include/config_state.h`, `include/config_text.h` |
| Power-button debounce and press/release events | `target/power/power_key_target.c` | `include/power_key_state.h`, `include/power_key_text.h` |
| Timers, scheduled tasks and retained boot state | `target/scheduling/timers_target.c`, `target/scheduling/tasks_target.c`, `target/power/retained_target.c` | `include/scheduling_state.h` |
| Diagnostic reporting and loop-rate tracking | `target/app/diagnostics_target.c`, `target/app/diagnostics_state.c` | `include/diagnostics_state.h` |
| UART command parsing and control handlers | `target/protocol/protocol_target.c`, `target/protocol/control_commands_target.c` | Editable `target/protocol/command_table_target.c`; named parser fields/debug flag in `include/protocol_state.h` |
| Main loop, key-event queue and wakeup | `target/app/application_target.c`, `target/app/application_state.c` | `include/application_state.h`; named state and source strings |
| ADC conversion and calibration | `target/drivers/adc_target.c`, ADC lookup in `target/drivers/hal_helpers.c` | `include/adc_state.h` |
| RGB animation and PWM | `target/power/rgb_target.c`, `target/drivers/pwm_target.c`, PWM routing in `target/drivers/hal_helpers.c` | `include/rgb_state.h`, editable presets/palette in `include/rgb_data.h`, `include/pwm_state.h` |
| Power routing, battery detection and shutdown policy | `target/power/power_policy_target.c`, `target/power/power_manager_target.c`, `target/power/power_state.c` | `include/power_state.h`; source voltage scales and diagnostic strings |
| Modem state machine | `target/modem/sg560d_target.c` | `include/modem_state.h`; named boot/runtime/parser state and source retry table |
| GPIO, reset causes and watchdog | `target/drivers/mspm0_core_target.c`, `target/drivers/gpio_state.c` | `include/gpio_state.h` |
| I2C and fault diagnostics | `target/drivers/i2c_target.c`, `target/drivers/fault_control_target.c` | `include/i2c_state.h`, bus routing in `target/drivers/hal_helpers.c` |
| UART initialization and receive buffering | `target/drivers/uart_hal_target.c`, `target/drivers/uart_ring.c`, `target/drivers/uart_state.c` | `include/uart_state.h`, port routing in `target/drivers/hal_helpers.c` |
| Logging and ARM variadic calls | `target/logging/logger_target.c`, `target/logging/logger_target_abi.S`, `target/logging/logger_state.c` | `include/logger_state.h` |
| Runtime context, heap and character rules | `target/runtime/` | `include/runtime_state.h`; linker-resolved state and ASCII rules |
| Reset, vectors and memory layout | `target/physical/` | `target/physical/firmware.ld` |

Files named `*_test_fixture.c`, `emulation_runtime.c` and `emulation.ld` provide
isolated test environments and are excluded from the physical image. The build
script's source list is authoritative; see [the module guide](target/README.md).
The original addresses in differential tests identify oracle inputs; they are
not a requirement on production object placement.

For a first edit, change a preset's color or brightness in `include/rgb_data.h`.
Run `make quick-test`, then `make physical-firmware`. The RGB tests include a
source-edit example that rebuilds a changed preset and checks its PWM output.
Intentional behavior changes need explicit new expectations; unchanged paths
should continue to match the original oracle. Run
`python -m pytest -q tests/test_firmware_relocation.py tests/test_warm_reset.py`
to exercise the complete image with moved objects, UART input and reset. Build
artifacts live under `build/`; generated reports and binaries do not belong in
source commits. Hardware validation is a separate step described below.

The [function ledger](docs/reconstruction-ledger.md) maps implementations and
tests; it is an inventory, not a completion percentage. The [MCU emulator
notes](docs/mcu-emulator.md) describe modeled regions, interrupts and peripherals.
Older analysis reports are historical snapshots, not assertions about every
later source revision. Current CI runs upload their test reports, updater audit
and physical-build artifacts instead of rewriting those reports in Git.

## Validation priorities

The current whole-image corpus exercises command and persistent-configuration
cold starts, missing-rail failures and UART readiness, with reproducible mutations
of rail delay, UART spacing and USB ADC input. It compares ordered power outputs,
protocol replies and persistent flash, and requires an independent expected
outcome so two stuck images cannot pass. Seeded stateful sessions now interleave
configuration commands and rejected inputs, battery ADC curves, fresh boots,
button presses and recoverable I2C NACKs. They compare intermediate flash and
power effects as well as protocol output. This is a bounded seed grammar, not
arbitrary input-stream or exhaustive fault fuzzing. See the
[scenario commands](docs/mcu-emulator.md#replayable-cold-start-scenarios) and
[stateful replays](docs/mcu-emulator.md#stateful-whole-image-replays).
Flash-recovery tests also compare every committed prefix of a normal append and
a full compaction, then boot fresh CPUs from every distinct persisted image.
They preserve the original's nontransactional recovery behavior; they do not
model torn programming cells. See [interrupted writes](docs/mcu-emulator.md#interrupted-configuration-writes).

Battery and power tests must include time-varying supply inputs, routing changes,
brownout/recovery paths, thermal behavior and externally reported shutdowns.
Synthetic ADC curves test firmware responses; they are not a validated charging
or battery-chemistry model. Charging responsibilities outside the syscon need
separate evidence.

Formal methods remain available for targeted invariants, especially protected
flash, power safety and watchdog behavior. Existing checksum proofs are optional
developer checks (`make proof-test`, requires Z3) rather than the default
functional test suite. Their explicit contracts are documented in
[the proof notes](docs/equivalence-proof.md).

## Hardware validation

A controlled Linux-only round trip on 2026-11-07 flashed rebuilt commit
`295015f0f4cada173339aa97291fcb0aa979e8a7`, verified its programmed CRC, obtained
VERSION/configuration/identity/rail responses, and restored the original 1.0.52
image with CRC verification. Linux kept the same boot ID throughout. The owner
explicitly authorized testing without SWD after local validation. The board is
back on the original firmware; later source revisions are not covered by that
hardware observation.

This proves the ordinary Linux update-and-restore path on the attached board.
It does not prove recovery after the app cuts Linux power, after a power cycle
with a broken app, or without functioning UART/GPIO access. Exact MCU identity,
raw MAIN/NONMAIN/factory readbacks, security configuration and independent SWD
recovery remain unverified. These are open evidence gaps, not a requirement to
re-request the owner's authorization for the agreed Linux-only experiment.

The [debug and recovery notes](docs/debug-probe.md) record the tested artifact,
checks, updater limits and remaining recovery boundaries. Further experimental
updates retain the known original image, verify hashes and padded flash bounds,
and avoid power-cycling before the intended restore/checks finish. Never assume
public upstream programmers behave like Particle's packaged executable.

The oracle is the 63,487-byte packaged `tachyon_syscon.dvt.bin`, embedded version
`1.0.52`, from `particle-tachyon-syscon_1.1.1-1_arm64`. Its SHA-256 is
`5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6`.
It is not a live MCU readback and omits the board's actual NONMAIN/factory data.
The firmware fetch manifest pins the upstream package and extracted members.

Source and pull requests: [iangcarroll/tachyon-syscon](https://github.com/iangcarroll/tachyon-syscon).
