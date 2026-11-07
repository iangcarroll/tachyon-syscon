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
make test
make physical-firmware
make rebuilt-system
```

`make inputs` fetches hash-pinned TI emulator inputs and the original firmware
oracle. It does not install packages or run a device updater. Optional CAD and
schematics are fetched separately; see [references](references/README.md).

`make arm` builds a static archive. `make physical-firmware` links the complete
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

This linked implementation is the starting point for consolidation into one
maintainable tree. Duplicate host adapters in `src/` are test scaffolding, not a
second product implementation to evolve independently. Consolidation must keep
behavior tests working, replace fixed string/data addresses with named objects,
and preserve addresses only where a hardware, boot/update or persistent-data
contract requires them. That migration is not complete yet.

Private code, strings, tables and global state must use linker-resolved symbols,
not numeric original-image addresses. Fixed addresses are reserved for documented
hardware, MCU memory-region and persistent-storage contracts. Layout-change tests
must exercise moved data/code and changed string lengths. The current numeric
return-address workaround for malformed legacy format data, fixed global state
and remaining recovered data blocks still need migration; they are not approved
exceptions to this requirement.

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
outcome so two stuck images cannot pass. Broader stateful UART/ADC/I2C/button
fuzzing remains work to do. See the [scenario commands](docs/mcu-emulator.md#replayable-cold-start-scenarios).

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

## Hardware gates

Before considering a replacement flash, identify the actual MCU, obtain
repeatable MAIN/NONMAIN/factory/configuration readbacks, and demonstrate recovery
independent of the firmware being replaced. Linux-based updating is not sufficient
if broken syscon power control prevents Linux from running.

The [debug and recovery notes](docs/debug-probe.md) describe the probe constraints
and offline audit of Particle's packaged UART bootloader updater. Its behavior
must not be assumed identical to public upstream tools. Hardware identification,
readback permissions, security configuration and independent recovery remain open.

The oracle is the 63,487-byte packaged `tachyon_syscon.dvt.bin`, embedded version
`1.0.52`, from `particle-tachyon-syscon_1.1.1-1_arm64`. Its SHA-256 is
`5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6`.
It is not a live MCU readback and omits the board's actual NONMAIN/factory data.
The firmware fetch manifest pins the upstream package and extracted members.

Source and pull requests: [iangcarroll/tachyon-syscon](https://github.com/iangcarroll/tachyon-syscon).
