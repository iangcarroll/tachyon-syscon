# Original-ABI application and main loop

`target/application_target.c` implements the complete non-returning `0x3b34`
entry in C, plus its event queue, constructors, shutdown request, diagnostic
UART wrapper, parser wrapper, wakeup handling, log-enable flag and board GPIO
setup. Unlike the older context-based application adapter, this body retains
boot/error/key/wakeup log calls and their original arguments.

The queue uses the original RAM at `0x200002d8`, four bytes at `0x200002d1`,
and wraparound unsigned indices. Volatile reloads and the divide-by-zero
remainder behavior are intentional. The shutdown and remembered key state are
bytes at `0x200002ec` and `0x200002ed`; wake state is `0x20000680`. In key event
3, the remembered state is sampled before the alternate-key callback; other
events reload at their own observed positions. The main loop is not split
into independently invoked test ticks.

`tests/test_application_target.py` runs original main and source main to an
explicit stage-2 boundary. It compares initialization under reset/factory/auto
boot combinations, initialization errors, log argument order, every key event,
unknown events, deferred shutdown, multiple successive loop iterations, queue
state disappearing between the two count checks, and state changed by a
callback. Separate helper tests cover corrupt/aliased queue fields, unsigned
index wrap, zero-sized queues, full-buffer drops, access ordering, wake
registration, and unmapped-buffer faults. A compiled request-off body patched
to return immediately is rejected by the complete-loop comparison.

External modules in `tools/application_target_oracle.py:DEPENDENCIES` are
explicit test endpoints. The test does not call an installed C runtime or
execute original instructions from a rebuilt function. Runtime helpers are
source linked; the original image is mapped non-executable in the candidate.

Callback addresses are deliberately relocated: the power-key registration
uses the source `syscon_target_queue_event` and wake registration uses the
source `syscon_target_wakeup_irq`. Tests check both exact original and rebuilt
addresses before comparing these two known relations. They do not erase
arbitrary pointer differences. The queue destructor is also a source symbol;
the original runtime's no-op exit registration does not retain it.

This is a tested implementation, not a universal equivalence proof. Private
stack layout and raw return registers of void functions differ; hardware
modules and log output are isolated by endpoints in these tests. Static string
pointers and retained battery-name tables still require placement in a full
physical image. The code is not yet a flash candidate.
