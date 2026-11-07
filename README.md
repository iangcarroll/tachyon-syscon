# Tachyon syscon reconstruction

Work in progress. A complete source image now links and boots in the local MCU
emulator. Universal equivalence and hardware safety are not established; do not
flash this experimental image.

The reference is the 63,487-byte `tachyon_syscon.dvt.bin` distributed in
`particle-tachyon-syscon_1.1.1-1_arm64`, whose embedded version is `1.0.52`.
SHA-256: `5bf027f9655bdabb4870eccee5a39e005a08ce70b8337613672081feecef03f6`.
It is a packaged firmware image, not a readback of the MCU. The image omits live
configuration, factory data, NONMAIN, and the chip's ROM.

The target is consistent with the TI MSPM0 family and 4 KiB SRAM. The exact part
and silicon revision still require physical identification or debug readback.

## Layout

- `src/`, `include/`: reviewed C reconstruction, developed subsystem by subsystem.
- `tests/`: differential tests comparing C with the original Thumb instructions.
- `tools/oracle.py`: original ARM execution under Unicorn; unmapped peripherals fail.
- `analysis/decompiled/`: **unreviewed**, automatically generated Ghidra output.
- `analysis/listing.txt`, `functions.tsv`, `function-ranges.tsv`: static analysis.
- `analysis/manifest.json`: firmware hash, vectors, segments, and 37 command records.
- [Reference collection](references/README.md): public Particle schematics, CAD and datasheets.
- [Debug probe notes](docs/debug-probe.md): connection constraints and pending readback.
- [Reconstruction ledger](docs/reconstruction-ledger.md): per-function source,
  testing, byte-match evidence, and remaining gaps.
- [MCU emulator](docs/mcu-emulator.md): physical address map, real reset/interrupts,
  UART command sessions, persistence and fault injection.
- [Equivalence proof](docs/equivalence-proof.md): the first solver-checked module
  theorem, negative control, and concrete whole-image gaps.
- [Target interface link](docs/target-interfaces.md): combined source link and
  explicit remaining dependencies.
- [ARM execution](docs/arm-rebuild.md): freshly compiled Cortex-M0+ comparisons.

## Verification

From this repository, with Python, Clang, ARM GNU tools and the Z3 CLI installed:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make inventory test binary-check
make emulate
make rebuilt-system
```

The validated compiler is [Arm GNU Toolchain 13.3.Rel1](https://gitlab.arm.com/tooling/gnu-toolchains-for-arm/-/tree/releases/13.3.rel1). CI pins and verifies its Linux archive; build manifests record the compiler and flags.

Unicorn needs executable memory for its JIT. The macOS restricted execution
environment may terminate it; the tests have been run with local execution
permission. They do not access the Tachyon hardware.

The reconstructed modules cover application/control state machines, all command
handler groups, configuration stores, scheduler/timers, retained state, power
policy/button control, GPIO/expander, RGB/PWM, ADC, I2C, UART, FLASHCTL, formatting,
fault/reset helpers, and all currently identified arithmetic, memory, support,
heap, stdio, scanning and printf runtime entries. These are scoped
implementations with explicit dependencies and unsupported domains; coverage of
the module names does not establish complete behavior or original binary ABI.

`analysis/full-suite-checkpoint.json` pins the latest combined test invocation,
outcome counts, original instruction addresses, replaced dependency endpoints,
and source/test/tool hashes. It verifies whether those inputs remained unchanged
during the run. `analysis/test-instruction-coverage.json` may instead represent a
later partial invocation; each run also has a unique archived report.

Integration tests include UART IRQ through real VERSION/HELP responses and
formatted UART output; power routing through GPIO expander, I2C IRQ and MMIO;
power measurement through ADC; configuration updates through FLASHCTL and its
copied SRAM executor; application power flows; and SysTick through RGB/PWM.
Negative controls and injected faults test termination, timeouts, stuck outputs,
and rejection of unsupported emulator operations. These modeled flows are not
physical end-to-end validation. The system emulator additionally boots both the original and the complete
source-only physical image from reset. VERSION, configuration set/get, and
readback after a fresh boot match after timestamp normalization, with identical
persistent sectors and no firmware-function replacements. Injected I2C NACKs
also reach matching assertion output and interrupt-disable behavior.

`make arm` cross-compiles all current reconstructed modules for
Cortex-M0+ into a static archive. This does not link a complete firmware image.

The original parser-only tests intercept command handlers; separate handler and
integration suites execute their bodies. Hooks and command-triggered register
models are not complete physical peripheral models. Differential tests prove
agreement for exercised inputs, not every possible execution. Successful Ghidra
decompilation is not evidence of semantic reconstruction or full function discovery.

The ledger now maps 389 identified entries to scoped source implementations.
All 27 previously caller-folded helpers have standalone target interfaces.
Direct target interfaces now cover the application, modem, commands, power,
peripherals, helpers and runtime. The ledger records each mapping separately. No identified runtime entry remains
unmapped. These mappings do not establish universal equivalence. Nine isolated rebuilt bodies match the reference bytes exactly; the
binary reports distinguish these from behavioral agreement. This is not a
100% reconstruction claim: discovery, complete input domains, full observable
ABIs, worst-case stack bounds and hardware correspondence remain open.

The system emulator's original reset → main loop → UART VERSION session passes
with the named synthetic board inputs. Configuration set/get persists across a
fresh emulated boot. The older `tools/boot_probe.py` is a deliberately minimal
fail-closed probe, not the new system emulator; its first unsupported watchdog
write is a historical boundary, not the current system-model result.

## Completion requirements still open

1. Account for all executable/data regions, indirect call targets, interrupt
   handlers, startup and linked runtime code; review every function.
2. Reconstruct all application state machines, HAL drivers, protocol handlers,
   persistent storage, failure paths and timing behavior.
3. Build an explicit peripheral/environment model and exercise full boot, command
   sessions, shutdown/wake, battery/USB transitions, resets and injected faults.
4. Reproduce ARM ABI, image layout, vectors and immutable tables; measure and
   explain binary differences, including compiler/runtime differences.
5. Acquire repeatable, hashed live MAIN/NONMAIN/factory/configuration readbacks
   after identifying the hardware and validating voltage and debug access.
6. Establish a recovery path and compare real hardware traces before any
   replacement firmware is considered a flash candidate.

No device flashing, erase, factory reset, or debug attachment is performed by the
offline tools in this directory. Source, references, and verification evidence
are published at [iangcarroll/tachyon-syscon](https://github.com/iangcarroll/tachyon-syscon).
Publication is an experimental checkpoint, not completion of the equivalence
or hardware validation requirements above.
