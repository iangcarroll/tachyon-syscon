# tachyon-syscon

Particle seems to have abandoned Tachyon, leaving parts of the platform without promised source code. I started this project to help keep the hardware maintainable by reconstructing and open-sourcing the missing syscon firmware.

The reconstruction was written by **GPT-6 Astra**, with human direction and hardware testing. It aims to preserve the original functionality while making the source understandable and editable. See the [source guide](src/README.md) to get started.

Project-authored code is available under the [MIT License](LICENSE). Bundled third-party code retains its existing licenses.

**Experimental: use at your own risk.** This reconstructed firmware has been tested on real Tachyon hardware, including a full cold boot. Automated differential tests compare its behavior with the original Particle firmware, and MCU emulation exercises complete images. These tests do not prove complete equivalence or safety. We recommend having a [Tachyon debug board and compatible SWD probe](docs/debug-probe.md) available for recovery: the syscon controls board power, and a bad image can prevent Linux from booting.

## Build and installation

Install Python, Clang and [Arm GNU Toolchain 13.3.Rel1](https://gitlab.arm.com/tooling/gnu-toolchains-for-arm/-/tree/releases/13.3.rel1), with `arm-none-eabi-gcc` on your PATH:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make
make quick-test
```

The image is `build/physical-firmware/firmware.bin`. Tests fetch hash-pinned reference inputs automatically. Building and testing do not access the board.

Follow the [short flashing guide](docs/flashing.md) to install the image through Tachyon’s Linux updater.

## Validation

**Software:** The original Thumb binary runs under Unicorn as an oracle. We compare reconstructed functions and complete images in an MCU emulator with modeled memory, interrupts and peripherals. Tests cover boot/reset, UART, persistent configuration, source/layout changes, battery ADC curves, power actions, injected faults and recovery at flash-write boundaries. `make quick-test` is the short development loop; `make test` and CI run the full suite. See [emulator details](docs/mcu-emulator.md).

**Hardware:** On 2026-11-08, rebuilt firmware passed a flash/restore round trip and a full cold boot on a real Tachyon. Configuration and identity data were preserved, Linux booted after complete power removal, and a device-side CRC verified the rebuilt image. Recovery from a broken image without Linux, independent SWD recovery and sustained charging remain unverified. See the [hardware record and recovery limits](docs/debug-probe.md#controlled-replacement-round-trip).

## Configuration options

Use Particle's installed Linux helper to inspect or change persistent settings:

```sh
sudo /usr/bin/particle-tachyon-syscon.sh list_config
sudo /usr/bin/particle-tachyon-syscon.sh get_config sys.auto_boot
sudo /usr/bin/particle-tachyon-syscon.sh set_config sys.auto_boot:true
```

These are the eight behavioral settings consumed by the reconstructed 1.0.52 firmware. Defaults below apply when no valid stored value exists; your board may already have different settings. Booleans accept lowercase `true`/`false` or `1`/`0`. Timer values are decimal seconds, clamped to 3–30 when loaded. Changes reload the configuration cache, but boot and power-transition settings take effect when their corresponding event next occurs. Use `list_config` to check effective values after writing; a stored value alone does not establish that it was accepted as a boolean or timer.

| Option | Default | What it does |
| --- | --- | --- |
| `sys.auto_boot` | `false` | Automatically starts the main processor after a cold power-on. A retained deliberate shutdown can keep it off across an MCU reset. Particle recommends connecting the battery before USB/5V. |
| `sys.wake_pin_enable` | `false` | Enables external wake-pin power-on while the main processor is off. Particle documents a low-to-high transition on a 0–3.3 V input; lowering it does not power the board off. See the polarity caveat below. |
| `sys.fastboot_enabled` | `false` | Adds fastboot selection to the power button when starting from off. Release after `sys.edl_timer` seconds for EDL, or after that threshold plus 5 seconds for fastboot (8 seconds with defaults). |
| `sys.color_debug_enable` | `false` | Adds ANSI color escape sequences to emitted debug logs. Does not enable logging itself or change the RGB status LED. |
| `sys.demo_enabled` | `false` | On cold startup, selects the cyan breathing LED preset instead of the normal auto-boot action. Suppresses the application's normal power-button event actions while enabled; UART handling and other main-loop work continue. This is not a normal operating mode. |
| `sys.enable_5v_when_off` | `false` | Keeps the 5 V header supplied when the main processor is off, unless the header is already configured as an external power input. It does not keep Linux running and can continue consuming battery power. |
| `sys.edl_timer` | `3` seconds | Button-hold threshold for EDL when starting from off. With fastboot enabled, the longer fastboot threshold is this value plus 5 seconds; otherwise EDL is requested at the threshold. |
| `sys.shutdown_timer` | `3` seconds | Button-hold threshold for requesting shutdown while the main processor is on. With fastboot selection enabled, the application acts on release. This is not a shutdown countdown or a timeout waiting for Linux to halt. |

The first three options are [documented by Particle](https://developer.particle.io/tachyon/device-details/syscon); the remaining five are recovered from the firmware. The table describes source behavior, not a hardware test of every setting. In particular, the recovered wake handler checks an active-low MCU input, while Particle describes a rising edge at the external pin; connector polarity has not yet been verified on hardware. See the [configuration loader](src/config/config_storage.c), [application actions](src/app/application_target.c), [button timing](src/power/power_key_target.c) and [power sequencing](src/modem/sg560d_target.c) for implementation details.

`hw_revision` belongs to the separate factory identity store and selects board-revision-dependent power sequencing. `confVersion` is internal storage metadata. Neither is an ordinary runtime setting; preserve factory identity and metadata. Other stored keys do not acquire behavior just because the configuration writer accepts them.
