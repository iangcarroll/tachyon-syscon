# MSPM0 system emulator

`tools/emulate.py` executes the original syscon image from its reset vector at
its physical addresses. It models the MCU's address space, exception machinery,
and the digital peripherals needed by the firmware. No firmware functions are
hooked out in this mode. FLASHCTL's copied SRAM routine, interrupt handlers,
startup, configuration initialization, and command parser execute as Thumb code.

This is separate from `tools/oracle.py` (isolated function comparisons) and
`tools/arm_rebuild_oracle.py` (relocated reconstructed-C test images). Those
harnesses deliberately have extra test memory; the system emulator has exactly
4 KiB of SRAM and no executable return sentinel or substitute firmware code.

## Run a complete command session

From `/Users/ian/tachyon`:

```sh
syscon-re/.venv/bin/python syscon-re/tools/emulate.py \
  --scenario syscon-re/fixtures/emulator/tachyon-synthetic.json \
  --instructions 1000000 --stop-at 0x3c9a \
  --command VERSION \
  --command 'CONFIG_SET emu.key alpha' \
  --command 'CONFIG_GET emu.key' \
  --report syscon-re/analysis/emulation-session.json
```

`0x3c9a` is the application loop in the pinned 1.0.52 image. UART bytes enter a
finite FIFO and trigger real firmware IRQ handling. Commands are paced in
virtual instruction ticks. JSON records execution addresses, exception events,
recent MMIO transactions, input hashes, UART bytes and final memory hashes.
The adjacent `.uart0.bin` and `.uart1.bin` files preserve binary output.

The supplied scenario is explicitly synthetic. It supplies zero-filled factory
and NONMAIN bytes, ADC input samples, GPIO levels, and one write-only readback
fixture. It is not a dump of this board. Omit those images and any access to
missing contents fails with `MissingImage`; the model never quietly supplies
factory calibration. JSON fields `factory_image`, `nonmain_image`, and
`sram_image` accept files relative to the scenario, with exact size checking.
`*_hex` supplies bytes inline; `*_fill` explicitly creates a synthetic fixture.

The original GPIO setup reads the write-only ICLR register at `0x400a1048`.
Its electrical readback has not been measured. The named scenario explicitly
assumes zero and records `fixture-wo-read` events. Without that fixture, the
emulator stops at the read. This assumption must be replaced with evidence
before claiming board correspondence.

## Physical memory and provenance

The selected profile is MSPM0L1306: Cortex-M0+, 64 KiB flash, 4 KiB SRAM.
The firmware is consistent with this profile; exact part and silicon revision
still need identification. Addresses and sizes come from the
[TI datasheet](https://www.ti.com/lit/ds/symlink/mspm0l1306.pdf), its memory map
and interrupt tables, and the pinned
[TI device header](https://github.com/TexasInstruments/mspm0-sdk/blob/e6793f41ce464fe78f03f100e715d5e30b43f25a/source/ti/devices/msp/m0p/mspm0l130x.h).
The official TI CMSIS device pack, SVD, SDK headers and licenses are retained
under `references/ti-mspm0/`, with source URLs and SHA-256 manifests.

| Region | Address / size | Enforced behavior |
| --- | --- | --- |
| MAIN flash | `0x00000000`, 64 KiB | CPU read/execute; CPU stores fault; final eight bytes excluded from CPU access per TI prefetch restriction |
| MAIN alias | `0x00400000`, same image | Coherent with controller programming/erase; instruction cache invalidated |
| SRAM | `0x20000000`, 4 KiB | Read/write/execute; no extra harness stack or RAM |
| NONMAIN | `0x41c00000`, 512 bytes | Explicit image required on access, read-only; alias `0x41c10000` |
| Factory data | `0x41c40000`, 128 bytes | Explicit image required on access, read-only; alias `0x41c50000` |
| Peripherals | Exact SVD register addresses | Register access/width/reset metadata; reserved/unimplemented accesses fail; non-executable |
| ADC SVT | `0x4055a000` region | Conversion result aliases coherent with ADC ULL view |
| CPU PPB | `0xe000e000` page | Implemented NVIC, SCB and SysTick registers only; no MPU |
| ROM / holes | Unmapped | Fail, rather than inventing boot ROM or undocumented data |

Unicorn maps memory in pages. Sub-page guards independently enforce the smaller
NONMAIN/factory sizes and inaccessible holes. The model rejects wrapping,
misaligned, protected and unsupported transactions. Peripheral pages cannot
execute, and flash programming is available only through modeled controller
commands or explicit host fixture mutation.

The TI pack contains metadata errors. The reviewed profile overrides its MPU
and priority-bit settings using the device header (no MPU, two priority bits,
VTOR present), corrects double-added ADC SVT offsets, and adds the omitted ULL
view of four ADC result registers. It also fixes the interrupt-event cluster
stride from 44 to 48 bytes for TIMG0/1/2/4, DMA and COMP0, cross-checked against
the TI peripheral structs. These corrections are visible in
`tools/mspm0/profile.py`, rather than silently altering downloaded references.
The [profile audit](mspm0-profile-audit.md) records independent checks and the
limits of SVD-derived reset values.

## CPU and digital peripherals

The CPU model handles vector relocation, MSP/PSP selection, aligned exception
frames, nested priorities, PRIMASK, level IRQs, exception return, SVC, SysTick,
and sleep/wake. The explicit ARMv6-M instruction gate rejects instructions that
Unicorn incorrectly accepts for its Cortex-M0 model. See
[mspm0-core-emulation.md](mspm0-core-emulation.md) for detailed boundaries and tests.

The default fault policy stops with an inspectable model error. Python callers
can select `MCU(..., fault_policy='hardfault')` to exercise architectural fault
entry and lockup. Missing inputs and unsupported peripherals remain model
errors; they are not evidence of a hardware fault. `reset_system()` resets CPU
and peripheral state while preserving flash/SRAM and the applicable retained
register domain. It does not simulate the unavailable factory ROM.

Digital models include UART RX FIFO/IRQ and TX capture, GPIO edges and output
aliases, shared interrupt groups, I2C transactions to the expander with NACK
injection, ADC sample/sequence completion, FLASHCTL keyed programming/erase and
completion IRQ, watchdog configuration/feed/reset, and retained reset cause.
See [mspm0-peripherals.md](mspm0-peripherals.md) for supported modes and deliberate
stops. SVD presence supplies metadata, not a behavioral implementation of every
peripheral. SPI, DMA, unmodeled I2C1 paths, and unsupported ADC modes do not gain
behavior merely because their registers appear in the SVD.

Time is deterministic virtual instruction quanta, not physical CPU cycles.
Peripheral delays can be advanced explicitly. UART output is an immediate
external sink; analog settling, actual oscillator rates, PWM waveforms, power
rails, modem responses, and all sleep-clock domains are not electrically
simulated. This emulator is useful for firmware behavior and fault scenarios,
not a timing or board-safety proof.

## Verification

The `test_mspm0_*` suites test memory guards and aliases, metadata consistency,
CPU exceptions, reset, peripheral state machines and deliberate failure cases.
Full original-image tests boot from reset, execute the copied SRAM flash
routine, send VERSION through a real UART interrupt, write/read configuration,
and read it again after a fresh boot from mutated emulated flash. A NACK
negative control changes the firmware's failure path; missing factory data and
unspecified write-only reads fail explicitly.

`analysis/emulation-boot-version.json` is the standalone original-image run.
`analysis/full-suite-checkpoint.json` records the combined test outcome and
source hashes. Neither report means the reconstructed C has been linked into a
physical-layout replacement image. No hardware was attached, erased or flashed.

## Complete rebuilt-image comparison

`make rebuilt-system` first creates the strict source-only physical image and
then runs `tools/rebuilt_system.py`. Both binaries use this same MCU model and
the explicit synthetic scenario. The observer stops at the first application
stage-2 write, without replacing a firmware body. It then sends VERSION,
configuration set/get, and repeats configuration readback after a fresh CPU boot
with the resulting flash contents.

The initial integrated run matched command output after normalizing only the
leading logger timestamps, and matched both persistent sectors byte-for-byte.
Its evidence is `analysis/rebuilt-system-session.json`. Different compiled
instruction counts produce different virtual elapsed times and interrupt counts;
this comparison does not assert cycle equivalence. The reference executed
1,107,734 instructions and the rebuilt image 1,392,151 through the first command
session. Their boot-only minimum MSP values were `0x20000c98` and `0x20000c80`.
Those observed peaks are not maximum stack bounds. During the current command
session, minimum MSP was `0x20000b58` for the original and `0x20000b48` for the
source image; commands wait for an actual PASS/FAIL reply, not a fixed delay.

The current session runner also watches MSP throughout commands and fails if it
enters fixed globals below `0x20000820` or leaves physical SRAM. The full source
image regression is `tests/test_rebuilt_system.py`; its second scenario injects
four I2C NACKs and compares actual assertion output and interrupt-disable state
against the original. No firmware function is stubbed in these system tests.

Physical layout and source provenance are documented in
[physical-firmware-build.md](physical-firmware-build.md). The static stack audit
in [physical-stack-audit.md](physical-stack-audit.md) independently records
unresolved indirect calls, recursion and exception nesting. Successful sessions
cannot replace those missing proof obligations.
