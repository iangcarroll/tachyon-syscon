# Original-ABI scheduler, timers, and retained state

The C in `target/tasks_target.c`, `target/timers_target.c`, and
`target/retained_target.c` accesses the firmware 1.0.52 addresses directly.
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

The two task records occupy 216 bytes at `0x20000534`. Four 24-byte timer
records start at `0x20000610`; the initialized byte is at `0x20000670` and
the clock is at `0x20000678`. Three retained bytes occupy `0x200000da` and
are copied to/from SYSCTL scratch registers `0x400b0400`, `404`, and `408`.
Existing `syscon.h` / `timers.h` layout assertions also apply to target builds.

`syscon_target_now` deliberately reads the low word before the high word,
without masking interrupts or retrying. The original can return a torn value
at rollover; the reconstruction preserves that behavior. Callback slot writes
are likewise unprotected and ordered, not converted into atomic transactions.
Callbacks can modify their slot, later slots, the scheduler, or clock, and the
post-callback reads observe those modifications. Task start times retain their
32-bit width, zero sentinel, and unsigned 64-bit elapsed-time comparison.

The logger is an external link dependency with original arguments. Its tag and
format pointers still refer to original-address rodata (`0xcdab..0xcdd2` and
`0xdbf6..0xdd00`). Integrating a production image requires source-defined strings
at those addresses or a coordinated pointer/layout translation. The isolated
function tests map the original image read-only for rodata compatibility;
candidate execution there is prohibited. `syscon_target_watchdog_feed` is the
other external dependency. Byte copies/clears link our `src/runtime_memory.c`.

## Validation

`tools/build_scheduling_target.py` compiles the three modules, recovered memory
helpers, and explicitly test-only `target/scheduling_test_fixture.c` with GCC
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
`target/scheduling_test.ld`. They run our MCU exception model with no function
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
