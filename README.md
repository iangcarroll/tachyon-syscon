# tachyon-syscon

Particle seems to have abandoned Tachyon, leaving parts of the platform without promised source code. I started this project to help keep the hardware maintainable by reconstructing and open-sourcing the missing syscon firmware.

The reconstruction was written by **GPT-6 Astra**, with human direction and hardware testing. It aims to preserve the original functionality while making the source understandable and editable. See the [source guide](src/README.md) to get started.

Project-authored code is available under the [MIT License](LICENSE), copyright Cautela LLC. Bundled third-party code retains its existing licenses.

**Experimental: use at your own risk.** This is reconstructed firmware. Differential testing and MCU emulation provide evidence of similar behavior, not proof of complete equivalence or safety. The syscon controls board power; a bad image can leave the board unable to boot or recover through Linux.

## Build and installation

Install Python, Clang and [Arm GNU Toolchain 13.3.Rel1](https://gitlab.arm.com/tooling/gnu-toolchains-for-arm/-/tree/releases/13.3.rel1), with `arm-none-eabi-gcc` on your PATH:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make
make quick-test
```

The image is `build/physical-firmware/firmware.bin`. Tests fetch hash-pinned reference inputs automatically. Building and testing do not access the board.

To install experimentally:

1. Run `make test` and retain the original firmware plus configuration/identity backups.
2. Copy the built image and original restore image to Tachyon. Follow the [Linux flash-and-restore procedure](docs/debug-probe.md#controlled-replacement-round-trip), including hash and programming-range checks, using **Particle's packaged updater**. Other `mspm0flash` versions can mass-erase protected data.
3. Verify the programmed image and UART responses, then demonstrate restoration of the original while Linux stays running. Keep power stable throughout; Linux-based recovery depends on Linux remaining available.

## Validation

**Software:** The original Thumb binary runs under Unicorn as an oracle. We compare reconstructed functions and complete images in an MCU emulator with modeled memory, interrupts and peripherals. Tests cover boot/reset, UART, persistent configuration, source/layout changes, battery ADC curves, power actions, injected faults and recovery at flash-write boundaries. `make quick-test` is the short development loop; `make test` and CI run the full suite. See [emulator details](docs/mcu-emulator.md).

**Hardware:** On 2026-11-08, the image built from `8ddf964` was flashed to a Tachyon, CRC-verified, and exercised through version, configuration, identity and rail-voltage queries. It is byte-identical to the CI image for merged source `ceeb1b3`. The original firmware was restored successfully without rebooting Linux; configuration and identity dumps were unchanged, and rail readings differed by at most 3 mV. This is a Linux-running flash/restore result, not a cold-boot test. Power-cycle recovery, independent SWD recovery and sustained battery charging remain unverified. See the [hardware record and recovery limits](docs/debug-probe.md#controlled-replacement-round-trip).
