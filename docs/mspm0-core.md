# MSPM0 core, watchdog and GPIO reconstruction

`src/mspm0_core.c` reconstructs register-access and RAM-initialization behavior
from the pinned syscon firmware. Its native-test entry points take explicit RAM,
register read/write functions, and a callback dispatcher. They are not a binary
replacement ABI. No physical peripheral simulator or flash image is provided.

Implemented original entry points:

| Entry | Behavior |
| --- | --- |
| `0x798c` | Watchdog initialization: five ordered 32-bit writes |
| `0x79d0` | Watchdog feed write |
| `0x79f0` | Both initialized-data copies, BSS clear, constructor/main/fault call order |
| `0x7a50` | Empty routine |
| `0x7a54` | 25-entry logical-pin descriptor lookup |
| `0x7be0`, `0x7bfc` | SYSCTL register initialization and raw cached reset-cause getter |
| `0x7c08` | Cached reset-reason register decode |
| `0x7c3c` | Reset-reason name-pointer lookup |
| `0x7f58` | GPIO direction, pull, initial level and IOMUX configuration |
| `0x8054`, `0x80ac`, `0x80f8` | GPIO output set/clear, toggle and input read |
| `0x8148`, `0x81f8` | GPIO interrupt setup and removal |
| `0x8258` | GPIO interrupt dispatch |

Reset initialization copies `0xe2e8..0xe578` to RAM `0x20000030..0x200002c0`,
then copies `0xaaf0..0xab20` to RAM `0x20000000..0x20000030`, then clears
`0x200002c0..0x20000820`. Other RAM bytes are preserved. The constructor runner,
main, and fault path are explicit dependencies in that order; their bodies are
not substituted with fictional hardware initialization.

GPIO pin descriptors are read from their actual initialized RAM table at
`0x2000016c`, including physical port, bit and IOMUX index. Interrupt callback and
argument records are stored at `0x20000698`. IRQ setup preserves the original
read/modify/write sequence, including separate reads before clearing and setting
the edge configuration and the final NVIC enable write. IRQ dispatch checks the
group pending source, resolves the physical pin back to the first matching
logical descriptor, then invokes that record's callback if nonzero.

## Validation

Six tests in `tests/test_mspm0_core.py` pass against the original ARM code:

- Exact watchdog initialization/feed register traces, including repeated calls.
- Reset with randomized initial RAM: copies, zeroing, preserved memory, and
  constructor/main/fault dispatch order all match.
- Every logical pin with input/output/ignored direction configurations, four
  pull values, initial-level flags, set/clear/toggle and sampled inputs.
- Every pin with interrupt modes, zero/nonzero callbacks, matching and unmatched
  pending sources, callback arguments and repeated disable operations.
- All 256 cached reset-reason values and name/descriptor lookup boundaries.
- A negative control proves that an unspecified register read fails rather than
  supplying an invented zero value.

The oracle permits access only to explicitly mapped pages and requires an
explicit initial value for each accessed register. Register operations are
traced in order and compared with the C callbacks. RAM is compared through
offset `0xeff`, excluding only the test function call's stack/config scratch.

## Limits and remaining work

This is a register-access model. It does not simulate watchdog countdown/reset,
clock readiness, GPIO electrical levels, IOMUX electrical effects, IRQ priority,
interrupt preemption, read-to-clear peripheral behavior, or W1C hardware effects.
The supplied register storage follows the test's declared values and records the
firmware's access sequence. A full-board model must supply actual peripheral
semantics instead of treating this storage as a working board.

Invalid GPIO pins or null configuration pointers cause a nonreturning assertion
in the original. The native analysis entry currently returns `UINT64_MAX` for
those invalid calls; that is an explicit host API limitation, not a faithful
reimplementation of the fault/reset machinery. Exception loops have separate
target-code tests in [fault-handlers.md](fault-handlers.md). The constructor/main
bodies have separate orchestration tests in [application.md](application.md).

No hardware was accessed or programmed. Run:

```sh
.venv/bin/python -m pytest -q tests/test_mspm0_core.py
```
