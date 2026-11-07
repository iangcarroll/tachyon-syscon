# FLASHCTL reconstruction and configuration integration

`src/flash_controller.c` reconstructs the hardware-facing erase (`0x7af4`),
program (`0x7b10`), protection-mask clear (`0x7b44`), blank verify (`0x7b60`),
and command executor routines. The executor is copied from image bytes
`0xaaf0..0xab1b` into SRAM at `0x20000000`; veneer `0xaae0` branches to it.
The controller base used by the image is `0x400cd000`.

| Offset | Role in the original transactions |
| --- | --- |
| `0x1100` | CMDEXEC, written 1 to start the staged command |
| `0x1104` | CMDTYPE: program 1, sector erase `0x42`, blank verify 6 |
| `0x1120` | CMDADDR |
| `0x1124` | Byte write mask, written `0xff` for eight-byte programming |
| `0x1130/0x1134` | The two little-endian data words |
| `0x11d0/0x11d4/0x11d8` | CMDWEPROTA/B/C |
| `0x13d0` | STATCMD |

**`0x7b44` clears write/erase protection masks, not status flags.** It writes
zero to all three MAIN protection registers. It does not touch the separate
NONMAIN protection register. This is confirmed by the
[TI register definitions](https://github.com/TexasInstruments/mspm0-sdk/blob/main/source/ti/devices/msp/peripherals/hw_flashctl.h),
saved in `analysis/ti-hw-flashctl.h`.

The copied-RAM executor writes CMDEXEC, then repeatedly reads `STATCMD & 7`.
Only values 1 (done, failure) and 3 (done, pass) return. Values 0, 2, 4, 5, 6,
and 7 all keep polling. There is no timeout or watchdog feed in this loop.
Higher error bits are discarded by the return value. A permanently stuck
controller can therefore hang the original firmware here.

## Register-level model

`tools/flash_controller_oracle.py` provides an explicit model for the image's
64 KiB MAIN region, eight-byte programming, and 1 KiB erase sectors. Register
setup alone does not alter flash. A CMDEXEC write stages the operation, scripted
busy states are returned, and successful mutation occurs only when the terminal
status is read. Protection failures, attempted zero-to-one programming,
nonblank verification, injected failure, unsupported commands, and out-of-model
addresses return terminal failure with corresponding status bits.

Protection uses individual CMDWEPROTA bits for the first 32 sectors and grouped
CMDWEPROTB bits thereafter, following TI's single-bank implementation in
[DL_FlashCTL_unprotectSector](https://github.com/TexasInstruments/mspm0-sdk/blob/e6793f41ce464fe78f03f100e715d5e30b43f25a/source/ti/driverlib/dl_flashctl.c).
The exact target part is still unconfirmed. The model does not claim support
for multibank remapping, NONMAIN writes, larger devices, ECC behavior, endurance,
partial programming pulses, voltage failures, or real completion timing.
Out-of-scope operations are rejected explicitly.

## Differential evidence

Eight test groups in `tests/test_flash_controller.py` pass. They compare the
complete ordered register trace, final controller registers, flash contents,
and operation results against original driver instructions and the original
RAM polling code. They include protection failures, clearing MAIN protection
without altering NONMAIN protection, busy states with misleading DONE/PASS
bits, retries after injected errors, illegal addresses, and setup/execute/
completion mutation boundaries.

The integrated configuration test performs 100 updates across successful and
injected-failure scenarios, including compaction. Original configuration
algorithms call the actual `0x7af4`/`0x7b10`/`0x7b44`/`0x7b60` functions and RAM
executor without hooks. Native configuration algorithms use the reconstructed
controller routines. Their full register traces and resulting sectors match.
The original status diagnostic at `0x2738` also runs and its logging calls match
the reconstruction. It masks STATCMD with `0x10f0` and recognizes only exact
single-error combinations; combined bits produce the unknown-failure message.
The mask excludes invalid-data bit `0x100`, so that failure can misleadingly
produce the original success message; this behavior is preserved. Diagnostic
UART transport, the logger endpoint, watchdog feeding, and the high-level
fatal-assertion boundary remain explicit hooks in this integration; the
assertion body has a separate reconstruction and test suite.

Both flash-controller and fault-control modules compile for Cortex-M0+ with
warnings treated as errors. Their context-injected interfaces are not yet the
original target ABI or exact machine code. No live flash access occurred.

```sh
.venv/bin/python -m pytest -q tests/test_flash_controller.py
```
