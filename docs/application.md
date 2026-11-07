# Application startup and bounded main-loop reconstruction

`src/application.c` reconstructs the main application orchestration around
`0x3b34`. The infinite loop is exposed as initialization plus a single bounded
tick, using the original RAM layout and explicit dependency calls. Constructors,
the four-byte power-key event queue, helper wrappers, boot decisions, event
dispatch and deferred shutdown are included.

The reset routine's constructor runner at `0x96d4` has an empty preinit array,
calls the empty `0x7a50` routine, then invokes `0x3610` and `0x3ec0` in that order.
The first stores the low 32 clock bits at RAM offset `0x2cc`. The second
initializes the queue at `0x2d8`, with its four-byte storage at `0x2d1`, then calls
the destructor-registration wrapper. Constructor/destructor ABI machinery
remains an explicit dependency; no destructor body is invented.

| Entry | Reconstructed behavior |
| --- | --- |
| `0x3610`, `0x3ec0`, `0x96d4` | Constructor state and order |
| `0x3a8c` | Enqueue one byte, dropping the new event when full |
| `0x3b0c` | Queue occupancy, including wrapped and full states |
| `0x3b34` | Initialization and one main-loop iteration |
| `0x3ad4` | Immediate or deferred power-off request |
| `0x3af4` | Set stage 17, then UART0 write with original pointer/length |
| `0x4c14` | Parser poll using context `0x20000048` |
| `0x78ac`, `0x7910`, `0x7928` | Wake IRQ debounce, input setup and configured enable/disable |
| `0x7974` | Consume the wake flag and request normal boot |

Initialization preserves the order of watchdog setup, stage/reset capture,
system and UART setup, retained-state load, timers/tasks/configuration, reset
reason, button callback registration, expander and power-manager initialization,
modem power discovery, and reset-dependent automatic/FCT boot handling. Calls
whose results are used only in diagnostic text are still made in their original
order. Diagnostic formatting/output itself is omitted from this module.

Each tick preserves stage markers 2 through 8 and calls diagnostics, event
processing, the user parser, SG560D poll, watchdog feed, task scheduler, deferred
shutdown processing and wake handling in the observed order. Events are consumed
even when FCT configuration suppresses their effects. A pending deferred shutdown
suppresses event consumption until tasks finish, then requests forced power-off.

## Validation

Six tests in `tests/test_application.py` pass. They compare the original ARM
instruction execution and the reconstructed C for all RAM below the test stack,
ordered dependency calls, and UART configuration payloads. They cover:

- Constructor order, timestamp truncation, queue wrap, full-buffer overflow,
  repeated enqueue/dequeue cycles and occupancy.
- Reset reason, automatic-boot and FCT configuration combinations, retained
  modes, initialization error returns and continued execution.
- All six recognized events plus unknown values, remembered off/on state,
  alternate-button configuration, immediate/deferred shutdown and task activity.
- Helper wrappers and wake-flag consumption.
- Wake interrupt configuration gating, ten COUNTFLAG waits followed by input
  sampling, and conditional flag setting only when the modem is off and the
  sampled wake pin remains low.
- A composed flow using the actual reconstructed C application, SG560D control
  routines and task scheduler: initialize, schedule normal boot, execute its
  callbacks/delays, observe a scripted power-good signal, process button events,
  request shutdown and observe scripted power-off confirmation. The original ARM
  executes those same internal components; only external dependencies are hooks.

The composed flow uses one active task slot and externally supplied clock and
power readings. It is a software integration flow, not complete board-level E2E.
The C scheduler currently receives time as an explicit argument; the test records
the corresponding original clock read for its one active delay action. It does
not claim to validate two asynchronously progressing slots in that integration.

Original initialization runs to `0x3c9a`, the first loop entry. Each tick executes
the body and the back-edge at `0x3da6`, stopping at the next loop entry. The scoped
report is `analysis/application-test-instruction-coverage.json`. Seven main-loop
instructions in the defensive second-empty-queue check remain unexercised: tests
do not mutate the queue to empty between its two occupancy checks. Five
constructor-runner instructions loop over the empty preinit array and therefore
do not execute for this pinned image.

## Limits

The native API changes the nonreturning main routine into init/tick functions.
It is not a binary/entry-point-compatible application image. Most hardware,
configuration, timer and retained-state calls remain environment boundaries in
application tests, although their implementations have separate differential
tests elsewhere. The composed flow integrates application, SG560D and scheduler
logic but continues to use explicit external driver/ADC/UART/parser/LED hooks.
Unknown MMIO has not been made permissive to claim a successful full boot.

Interrupt preemption, assertion/reset loops, physical power timing, real serial
traffic, and a complete linked MCU boot are not established. No hardware was
accessed or programmed.

Run:

```sh
SYSCON_COVERAGE_OUTPUT=analysis/application-test-instruction-coverage.json \
  .venv/bin/python -m pytest -q tests/test_application.py
```
