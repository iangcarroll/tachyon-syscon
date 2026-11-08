# Recompiled ARM validation

This checkpoint executes the reconstructed C as Cortex-M0+ Thumb instructions
and compares it with the captured firmware in a separate Unicorn instance.
It supplements the native C differential tests by testing 32-bit pointers,
`size_t`, ARM soft-float behavior, stack arguments, and compiler-generated
`va_start`. It is not a bootable or flashable firmware image.

## Build and memory boundary

`tools/build_arm_test_image.py` compiles selected reconstruction sources with
Arm GNU GCC, `-mcpu=cortex-m0plus -mthumb -mfloat-abi=soft -Os`, freestanding,
and warnings treated as errors. Arithmetic and soft-float dependencies are built
from the reviewed runtime reconstruction and pinned GCC soft-fp sources at
`-O2`; no installed libc or `libgcc` archive is linked. `tests/fixtures/target/emulation_runtime.c`
supplies minimal byte-copy/fill/compare routines; these harness routines are
distinct from the separately reconstructed `src/runtime/runtime_memory.c` functions.

The linker script `tests/fixtures/target/emulation.ld` locates code at `0x01000000` and
candidate globals at `0x21000000`. `tools/arm_rebuild_oracle.py` maps the
original 4 KiB RAM at `0x20000000`, but uses separate 64 KiB harness RAM for
globals, scratch allocation, and the candidate stack. Thus passing tests do
not establish fit within the physical MCU's RAM or flash. The original image
is mapped read-only and **non-executable**, so existing recovered literal
pointers can be read without allowing fallback execution of original code.
A negative test attempts such execution and requires an emulator fault.

External dependencies are explicit callback traps. Unknown peripherals remain
unmapped. Target UART, clock, and color endpoints contain `BKPT` instructions
and require explicit test bindings; a negative test proves that an unbound
endpoint faults. Candidate callbacks use ARM registers and stack words, with
64-bit results returned through R0/R1. These are controlled test environments,
not peripheral or reset-sequence emulation.

Each build records compiler version, flags, source/header/linker hashes,
vendor provenance, and ELF hash in `manifest.json`, including
`"flash_candidate": false`. Pytest builds fresh sources in its temporary
directory, independently of the optional persistent build artifact.

## Validated behavior

`tests/test_arm_rebuild.py` contains 21 collected cases at this checkpoint:

- RGB scaling across all brightness percentages, random float representations,
  signed zeros, subnormals, infinities and NaNs; channel boundaries; ten preset
  waveforms over 240 timer ticks each; transient-state restoration. Raw RGB
  state and ordered PWM events are compared with original execution.
- SG560D 64-bit wake/deadline wraparound, retry/temperature policy, submitted
  task payloads, 100 seeded power-decision scenarios, and 180 seeded poll
  scenarios. Comparisons include the first 2 KiB of state RAM and ordered
  external dependency events. These target tests supplement the broader
  original-versus-native SG560D suite; they do not claim exhaustive poll
  instruction or state-space coverage by themselves.
- Timer registration with the fifth C argument on the stack, raw timer slots,
  clock overflow, and 64-bit return registers.
- Variadic formatting with register/stack arguments, 64-bit argument alignment,
  integer length modifiers, pointers, strings, truncation and null destinations.
  UART logging checks enable state, color decisions, binary NULs, and buffer
  boundaries through 300-byte inputs.

Target-only wrappers in `tests/fixtures/target/format_wrappers.c` use real compiler-generated
`va_start` and a direct memory adapter into the reconstructed format engine:

| Original entry | Recompiled target wrapper | Compared result |
| --- | --- | --- |
| `0x92f4` | `syscon_target_snprintf` | Return length and full output sentinel region |
| `0x8f88` | `syscon_target_logger` | Ordered clock/color calls and UART bytes |
| `0x8fa0` | `syscon_target_mfg_logger` | Ordered clock/color calls and UART bytes |
| `0x5edc` | `syscon_target_sg560d_printf` | UART bytes, truncation, and CRLF |

The tests feed identical raw AAPCS words to the original entry and recompiled
wrapper. Both caller stacks are eight-byte aligned. The adapters assert the
target's four-byte pointer and `va_list` representation at compile time. Logger
wrapper return values are analysis status codes; they do not preserve the
original's incidental return-register contents. Invalid memory and the
original logger's unsafe oversized-prefix behavior remain outside the matched
domain; the shared logger model reports incomplete handling for that prefix
case rather than claiming equivalence.

## Reproduction and limits

From `/Users/ian/tachyon`:

```sh
syscon-re/.venv/bin/python syscon-re/tools/build_arm_test_image.py
SYSCON_COVERAGE_OUTPUT=syscon-re/analysis/arm-rebuild-reference-coverage.json \
  syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_arm_rebuild.py
```

The source-only runtime integration checkpoint passed **21 tests**. This also
checks the new compiler-support logical 64-bit shift helper across word and
full-width boundaries; that helper is not counted as an original entry. The coverage report records
original instructions exercised by this suite; candidate execution uses a
separate loader and does not contaminate that report with relocated addresses.
It is not a whole-firmware coverage claim. The build includes additional modules
for linking dependencies; inclusion alone is not execution coverage.

No hardware was accessed or changed. These tests establish differential
behavior for the listed cases, not binary identity, full ABI compatibility,
physical board safety, complete peripheral timing, or complete firmware
reconstruction.
