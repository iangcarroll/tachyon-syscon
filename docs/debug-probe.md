# Debug probe preparation

User reports a Geehy APM32/F103-based probe labeled `CMSIS_DAPLINK V2.0 f103ret5`.
That label does not establish its board pinout, CMSIS-DAP protocol version, voltage
reference handling, or whether its power pin is an output. USB enumeration on
2026-11-07 did not show a CMSIS-DAP probe. No probe was attached to the target.

TI documents CMSIS-DAP support for MSPM0 and current OpenOCD includes MSPM0 support:

- https://software-dl.ti.com/msp430/esd/MSPM0-SDK/latest/docs/english/tools/doc_guide/doc_guide-srcs/debug_program.html
- https://software-dl.ti.com/msp430/esd/MSPM0-SDK/2_08_00_03/docs/english/tools/keil_ide_guide/doc_guide/doc_guide-srcs/keil_ide_guide.html
- https://github.com/openocd-org/openocd/blob/master/tcl/target/ti/mspm0.cfg

Particle's debug adapter schematic has a J-Link-labeled connector and a TXS0108E
level translator between the 3.3 V probe side and 1.8 V target side. A compatible
CMSIS-DAP SWD probe can potentially use that interface after confirming wiring;
the connector name does not make the SWD transport specific to J-Link. The raw
Tachyon debug connector uses a different pin assignment and is not a substitute
for the adapter's probe connector. The adapter does not power Tachyon.

- https://developer.particle.io/tachyon/accessories/debug-board
- [Downloaded adapter schematic](../references/developer.particle.io/tachyon/debug-adapter-schematic.png)

The user has ordered the Particle adapter. Before connecting, verify probe
pinout, actual signal voltages, reference pin behavior, orientation, common ground,
and target power. Do not connect an unverified 3.3 V probe directly to the 1.8 V
target pins or join two power outputs.

## Attachment is not necessarily passive

The examined upstream OpenOCD `mspm0.cfg` installs an `examine-start` event invoking
`_mspm0_enable_low_power_mode`. That routine writes the power access port and
requests a system reset (`PWR_AP::SPREC = 1`). Therefore a stock configuration
cannot be described as a purely passive readback operation, even without a flash
command. Audit the exact installed configuration and connection behavior before
using it on the board. Halting the power controller can also affect normal board
operation. A custom connection sequence requires validation, not just removing
the reset hook and assuming success.

The same upstream script exposes explicit mass-erase and factory-reset commands.
Do not use either to solve a connection failure: they can destroy the very
configuration being preserved. Do not run a generic flashing example as a probe
test. Initially inspect the USB probe alone, then plan target identification and
repeatable MAIN/NONMAIN/factory/configuration readbacks with all writes audited.
