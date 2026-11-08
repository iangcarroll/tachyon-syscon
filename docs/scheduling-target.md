# Original-ABI scheduler, timers, and retained state

The C in `src/scheduling/tasks_target.c`, `src/scheduling/timers_target.c`, and
`src/power/retained_target.c` uses named linker-allocated state and source text.
Only SysTick/NVIC and PMU scratch accesses use fixed hardware addresses.
Its public functions in `include/scheduling_target.h` take the original ARM
arguments, without a RAM or environment pointer. Callback words are actual
Thumb function pointers and execute through indirect calls. No original
instructions are copied into these implementations.

| Original entry | Target symbol suffix (all prefixed `syscon_target_`) |
| --- | --- |
| 7540 / 7554 / 75d8 / 76d8 | tasks_init / tasks_submit / tasks_poll / tasks_active |
| 76f8 / 776c / 77b4 | timer_tick / timer_init / now |
| 77c0 / 77fc / 781c / 7880 | timer_delay / timer_wait_countflags / timer_register / timer_unregister |
| 59a0 / 59d8 / 5a88 | retained_commit / retained_load / retained_clear_registers |
| 5aa8 / 5ac4 / 5ad4 / 5af0 | retained_set_modem / retained_modem / retained_set_battery / retained_battery |
| 5afc / 5b14 | retained_increment_boots / retained_boots |

In the original image and isolated differential fixtures, the two task records occupy 216 bytes at `0x20000534`. Four 24-byte timer
records start at `0x20000610`; the initialized byte is at `0x20000670` and
the clock is at `0x20000678`. Three retained bytes occupy `0x200000da` and
are copied to/from SYSCTL scratch registers `0x400b0400`, `404`, and `408`.
Existing `syscon.h` / `timers.h` layout assertions also apply to target builds.
Production objects are allocated by the linker through `scheduling_state.h`;
these private fixture addresses are not production placement requirements.

`syscon_target_now` deliberately reads the low word before the high word,
without masking interrupts or retrying. The original can return a torn value
at rollover; the reconstruction preserves that behavior. Callback slot writes
are likewise unprotected and ordered, not converted into atomic transactions.
Callbacks can modify their slot, later slots, the scheduler, or clock, and the
post-callback reads observe those modifications. Task start times retain their
32-bit width, zero sentinel, and unsigned 64-bit elapsed-time comparison.

The logger is an external link dependency with original arguments. Its tag and
format strings resolve from ordinary C data. Differential fixtures compare
text contents and consumed arguments, and poison obsolete text locations.
The physical linker can move these strings independently of their callers.
`syscon_target_watchdog_feed` is the
other external dependency. Byte copies/clears link our `src/runtime/runtime_memory.c`.

## Validation

`tools/build_scheduling_target.py` compiles the three modules, recovered memory
helpers, and explicitly test-only `tests/fixtures/target/scheduling_test_fixture.c` with GCC
for Cortex-M0+, `-Os -ffreestanding -fno-builtin -fno-jump-tables -nostdlib`.
There are no installed runtime library dependencies. It emits source hashes,
compiler flags/version, entry mappings, and the ELF hash beside the ELF.

`tests/test_scheduling_target.py` exercises all 20 entries with compiled ARM
instructions. The function tests compare all persistent RAM through
`0x20000cff`, the exact ordered persistent-RAM writes, ordered MMIO accesses,
logger arguments/pointers/order, defined returns, R4-R11, and PRIMASK.
Different stack scratch layouts are excluded. On the reference side only
logger/watchdog entry routing is redirected to the compiled test environment;
timer/task callbacks and byte copies execute instructions directly. The
candidate has no original executable fallback.

Cases include full/duplicate/zero timer registration, arbitrary once-word
truncation, mutable callbacks, later-slot activation, 64-bit wrap, torn reads,
SysTick initialization and idempotence, COUNTFLAG initial clearing, watchdog
delay progression, overlapping scheduler copy, invalid kinds/counts, callback
failure/nonboolean return, timestamp wrap, nibble truncation, saturated reboot
counts, retained snapshot mutation, logging-triggered state mutation, invalid
source/callback faults, and untouched guard RAM.

Two additional tests compile an upper-flash fixture using
`tests/fixtures/target/scheduling_test.ld`. They run our MCU exception model with no function
hooks: SysTick is pended while PRIMASK is set, delivered after unmasking, and
executes the real rebuilt handler plus compiled callback. The callback observes
IPSR=15, one-shot state clears, registers restore, and execution returns to
the preempted thread with either MSP or PSP. A bad-vector negative control
faults. The candidate physical-address fixture has no original firmware bytes.

The scoped run reports **33 passing tests and 488/488 identified original
instructions** across these entries in
`analysis/scheduling-target-test-instruction-coverage.json`. Coverage is finite
execution evidence, not a universal equivalence proof. The tests do not cover
every possible asynchronous interleaving or prove cycle timing; the MCU model
uses explicit virtual instruction time. Neither ELF is a production flash
image: the exception fixture uses a synthetic vector table and reserved test
RAM, and does not boot the complete application.

## Editable power-button implementation

`src/power/power_key_target.c` owns the production button state and timing ranges.
Its declarations are in `include/power_key_state.h`, and its editable log text
is in `include/power_key_text.h`. No private numeric address remains in this
module. The physical linker places the objects normally; only the differential
fixture linker places them at the original addresses to compare ordered writes.

GPIO input is active low. An edge schedules a one-shot 10 ms debounce callback;
a held button then polls every 10 ms. The default press intervals are
[50, 3000), [3000, 8000), and [8000, UINT32_MAX) ms. Starting a new press replaces
the two higher boundaries using the configured long/extra timer and a 5000 ms
extension. Even-numbered events describe a press; the next odd-numbered event
confirms release after more than 200 ms of released input. In passthrough mode,
the modem key is forcibly released once the held duration reaches 6000 ms.
These are original behaviors, including unsigned timer wrap.

The callback may mutate button state. Polling reads volatile state in the
original order and preserves the completion decision made before invoking the
callback. Named constants and comments explain these constraints without
preserving compiler register choices or private code addresses.

`test_power_key_target.py` compares all six entry points against original ARM
instructions, including threshold boundaries, overflow, callback mutations,
invalid callback faults, both modes and a complete long-press/release sequence.
Logger comparisons use string contents; pointer-like integer arguments are not
normalized. `test_firmware_relocation.py` additionally moves code and initialized
RAM, poisons the obsolete button RAM, then drives GPIO edges through the full
image's interrupt/timer/main-loop path. It requires press and release events,
application consumption, matching UART messages and ordered power transitions.
Its external clock advancement is synthetic, not a silicon cycle model.
`test_warm_reset.py` poisons the new state before SYSRESETREQ and compares its
restored initial contents with the original image.
