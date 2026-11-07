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

## Linux updater and recovery transport (offline audit)

The locally retained Particle packages use a Linux UART connection to the MSPM0 bootloader, with GPIO-controlled invocation and reset. This is separate from SWD/J-Link/CMSIS-DAP. No device connection, GPIO operation, unlock, erase, or programming was performed in this audit. Package provenance below identifies the exact local archives; it does not independently authenticate their publisher or establish the firmware currently installed on the board.

Audited files are under `../re/pkg/particle-tachyon-syscon_1.1.1-1_arm64/` relative to this repository. Their bytes were checked against the corresponding retained `.deb` archive.

- `data/usr/bin/particle-tachyon-syscon.sh:12-14` selects `/dev/ttyHS1`, 115200 baud, and `/usr/lib/firmware/tachyon_syscon.dvt.bin`. Line322 runs `MSPM0FLASH_CTRL=/usr/bin/mspm0flash_ctrl.sh mspm0flash -S "$COM_PORT" -b "$BAUD_RATE" -s -v -v -v -v prog "$SYSCON_BIN"`.
- `data/usr/bin/mspm0flash_ctrl.sh:6-12` uses TLMM offsets63 for BSL invoke and46 for reset. Lines17-26 assert invoke, pulse reset low, and release reset, with100ms waits. Lines28-36 release invoke and pulse reset to resume normal operation. Lines39-49 also manipulate both GPIOs before dispatch. Even the tool's `info` operation normally invokes this control script: it is not a passive inspection command.
- `data/lib/systemd/system/particle-tachyon-syscon.service:7` runs upgrade and identity backup; `control/postinst:21-29` starts/restarts that service during package configuration. Installing the package can initiate an update.
- `particle-tachyon-syscon.sh:277-289` skips the ordinary upgrade if the running application cannot answer its version query; `--force` bypasses that gate. That option does not prove that recovery will work. Lines319-330 retry the programmer up to10 times.

### Exact packaged erase/program boundary

The packaged executable identifies itself as `0.4.2-0-g20a0bb62`. Both retained package versions contain the same executable. Its corresponding fork source was not located; the conclusions here come from the actual AArch64 binary, not an assumed upstream implementation.

Relevant ELF virtual addresses:

| Operation | Evidence |
| --- | --- |
| Load and pad image | `0x2fa0`; `0x305c-0x3068` computes `(length+1023)&~1023`, and `0x3084-0x308c` fills padding with `0xff` |
| Program dispatcher | `0x3458`; unlock at`0x34b4`, then range erase at`0x34dc-0x34e8` with start0 and padded length |
| Range erase packet | `0x26f0-0x2740` encodes command`0x23`, start, and inclusive end`start+length-1` |
| Program packets | `0x3524-0x3574` starts at0 and sends at most256bytes per call to`0x2998` |
| Verification | `0x3614-0x3650` compares device CRC over the padded region against the local image CRC |
| Start application | `0x368c-0x36a4` invokes the start command when`-s` is selected |

Both packaged BIN files contain63487bytes. They are padded to63488(`0xf800`), so the intended erase/program interval is`0x0000..0xf7ff`. Both HEX files likewise contain only addresses below`0xf800`, and no NONMAIN records. Thus these particular update inputs preserve the MAIN configuration/identity sectors at`0xf800` and`0xfc00`; they do not program NONMAIN. This is conditional on the input size: the binary does not impose a hard-coded protection boundary at`0xf800`.

An independent offline Unicorn AArch64 execution of the actual range-packet routine confirmed command`0x23`, start`0`, inclusive end`0xf7ff`, and a16-byte packet for length`0xf800`. Only logging was skipped and the serial/I2C boundary trapped; no operating-system/device calls occurred. The reproducible offline audit is `tools/audit_packaged_updater.py`; it verifies the exact executable hash and stops before the transport implementation.

**Do not substitute public upstream mspm0flash without auditing it.** At [Kontron commit60593696](https://github.com/kontron/mspm0flash/blob/60593696a35bc310d43b5b293dd1b70dde51b455/main.c), `load_fw_image` pads to4KiB and `cmd_prog` calls mass erase. This differs materially from the retained Particle executable and would threaten the preserved MAIN configuration sectors.

### Readback, authentication, and NONMAIN

The packaged CLI exposes `prog`, `info`, `erase`, and `crc`, with no raw-memory dump command. Its ELF contains a memory-readback packet routine at`0x28b0` (command`0x29`), but no direct caller or CLI dispatch to it was found. A CRC result is not a restorable backup. `backup_identity` in the shell script reads four logical identity keys after upgrade (`CONFIG_ID_GET`, lines379 and407-450); it is not a pre-update raw MAIN/NONMAIN backup.

The unlock routine at`0x25f0` sends the public TI factory-default BSL password; no password-selection CLI option was found. This does not establish the attached board's configured password or security policy. Repeated automatic retries must not be used to discover them.

TI documents ROM BSL for the MSPM0L family. Memory readback requires authentication and a configuration flag disabled by default. Range erase affects MAIN only; factory reset erases MAIN and NONMAIN. Three incorrect passwords trigger the configured security response, which can erase both regions, disable BSL, or do nothing. Erased NONMAIN can lock access if not restored before reset. These are reasons to preserve and inspect the actual configuration before any unlocking or recovery attempt, not instructions to change it. [TI BSL guide, sections2,4.3.6-4.3.9,4.5](https://www.ti.com/lit/ug/slau887a/slau887a.pdf)

### Recovery boundaries still unverified

The GPIO/reset sequence is consistent with the MSPM0L1306 hardware BSL entry path, which does not require a functioning application, provided BSL and GPIO invocation remain enabled. Fast boot or changed NONMAIN settings can prevent that entry. [TI datasheet, section8.27](https://www.ti.com/lit/ds/symlink/mspm0l1306.pdf) Whether the actual board uses ROM BSL directly, a registered plugin, or an alternate flash BSL has not been established from its NONMAIN configuration.

The packaged updater keeps executing on Linux while the syscon is in BSL and its application region is erased and reprogrammed. A successful official update therefore implies that Linux and board power survive that interval. This is an inference from the update mechanism, not a captured recovery test on this board. It substantially narrows the remaining questions: whether Linux can start after a power cycle with a broken syscon application, and whether recovery remains possible after that application actively cuts SoC power. Neither follows from a successful ordinary update.

Linux-based recovery needs Linux, its UART, the two GPIOs and board power. The independent SWD path remains necessary for the two failure cases above. The exact MCU identity, probe electrical compatibility, SWD protection state, repeatable MAIN/NONMAIN/factory readback and recovery without the replaced application remain unverified. The existing attachment/reset caveats above still apply. Particle's adapter does not power the board. [Particle debug-board documentation](https://developer.particle.io/tachyon/accessories/debug-board)

### First replacement round trip (planned, not executed)

0. **Original-only rehearsal:** before introducing a candidate, stage and hash-check the original firmware already intended for this board and the exact packaged updater/control script. Confirm the currently installed versions, a working Linux console, stable power and a padded programming interval below `0xf800`. Reflash that original image through Particle's existing update path, require successful verification and the original VERSION reply, and compare configuration/identity before and after. This rehearses staging and the vendor procedure without requiring candidate-image SWD/readback gates first. It is still a flash operation; do not use retries to discover an unknown BSL authentication policy. This rehearsal has not been executed.

After identifying the MCU, preserving repeatable device readbacks and validating the independent SWD connection and restore procedure:

1. Connect the verified SWD probe before programming. Keep stable board power and a Linux console available. Save the running application's VERSION reply and configuration/identity contents for comparison.
2. Stage the original restore image and the tested source-built image locally on the board. Check their hashes and ensure each padded programming interval ends before `0xf800`. Use the exact hash-verified Particle `mspm0flash` executable and audited control script; do not substitute upstream mass-erase tooling or install a package to launch the experiment.
3. Program the initially equivalent candidate through the packaged BSL path. Record updater verification, Linux availability and the resumed application's VERSION reply. If a step fails, stop normal testing and use the prepared restore path; do not power-cycle to troubleshoot or repeatedly guess authentication.
4. While Linux is still running, reflash the original with the same updater. Require successful verification, its VERSION reply and unchanged configuration/identity. This round trip tests the Linux restore path before relying on it.
5. Only after the original restore succeeds consider a separate power-cycle test with the independent recovery path ready. Record power-cycle recovery and recovery from an app-driven power cut as separate outcomes; the BSL round trip alone proves neither.

The candidate still needs the private-address migration and broader stateful input/fault tests. This protocol records the hardware experiment to perform when those prerequisites and the physical recovery gates are met; no replacement has been flashed.

### Immutable audit inputs

| Retained input | SHA256 |
| --- | --- |
| `../re/debs/particle-tachyon-syscon_1.0.19-1_arm64.deb` | `b53c3cad2e9ab468e6f388756522fdaf0701b56d9972aa9b1a2bc7a24e1f2910` |
| `../re/debs/particle-tachyon-syscon_1.1.1-1_arm64.deb` | `626394bdecf470d20336a1abd5d18d477da4d36a252144a4d024903f33573358` |
| `data/usr/bin/mspm0flash` in both archives | `a64185e0623d773c51fa933f82e394375801bd2cfd3a8d49606c3708ec0d48de` |

The ELF build ID is`5038235d84359270b2719edcc91e9bb9ac4a4173`. The package version and embedded revision string do not substitute for these hashes. The Kontron source comparison was fetched at the pinned commit above and matched the inspected files; it is comparison evidence, not the source of the Particle fork.

To reproduce without connecting a device, fetch the hash-pinned package and
extract its executable as inert test data. No package scripts are executed:

```sh
.venv/bin/python tools/fetch_firmware.py --with-updater
.venv/bin/python tools/audit_packaged_updater.py --binary build/reference-tools/mspm0flash --output build/updater-audit.json
SYSCON_UPDATER_BINARY=build/reference-tools/mspm0flash PYTHONPATH=tools .venv/bin/python -m pytest -q tools/tests/test_audit_packaged_updater.py
```

These optional tests execute the padding and packet code under AArch64 emulation,
including boundary inputs and corrupted-instruction/packet controls. They do not
run the native updater or discover serial devices. The ordinary firmware test
suite does not require this external executable.
