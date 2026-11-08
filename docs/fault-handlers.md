# Nonreturning exception handlers

`src/drivers/fault_handlers.c` is Cortex-M0+ target code, kept outside the native-host
source directory. Never call these functions directly in a host process: they
write a physical MCU register and spin forever.

| Original entry | C function | Stage written to `0x400b040c` |
| --- | --- | --- |
| `0x79e4` | `syscon_default_exception` | 20 |
| `0x7bb8` | `syscon_hardfault` | 18 |
| `0x7bcc` | `syscon_nmi` | 19 |

The original handlers record the stage and then remain in an unconditional loop.
They do not reset the board directly. Any later watchdog reset is a separate
hardware behavior and has not been asserted by these tests.

`tests/test_fault_handlers.py` compiles the C for Cortex-M0+ with the ARM GCC
toolchain, links each entry into its own small ELF, extracts its bytes, and runs
those actual ARM bytes in Unicorn. It also runs the corresponding original
firmware entry. The explicitly initialized register trace and resulting value
match. Both original and rebuilt code remain at their respective loop address
for two bounded 100-instruction runs, issue no additional register accesses, and
never reach the supplied return address.

All three cases pass. The evidence establishes matching register-write/spin
behavior for these isolated handlers. It does not establish identical machine
bytes, exception stacking/unstacking, interrupt priority, the watchdog reset
deadline, or safety of a complete replacement firmware image. No hardware was
accessed or programmed.

Run:

```sh
SYSCON_COVERAGE_OUTPUT=syscon-re/analysis/fault-test-instruction-coverage.json \
  syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_fault_handlers.py
```
