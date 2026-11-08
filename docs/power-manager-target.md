# Power routing and battery detection

`src/power/power_manager_target.c` implements measurements, power-route selection,
USB reattachment and battery detection. `src/power/power_policy_target.c` handles
reports, initialization, minimum voltage and shutdown-reason expiry. Both use
ordinary source strings and the linker-allocated objects in
`include/power_state.h` / `src/power/power_state.c`. Neither module depends on
original private RAM or ROM addresses. The older `tests/models/` implementations are
host test scaffolding, not a second production implementation.

## Measurements and switching

Measurement retries a zero ADC sample once. It truncates the ADC pin argument to
16 bits, but selects a scale using the full original pin value. The six source
scale factors correspond to VPH, header, battery, 1v8, USB and NTC; multiplication
retains 32-bit wrap. Tests rebuild a variant with a changed VPH factor and require
only that channel's result to change.

Routing getters read both selector pins in order and reject contradictory or
nonboolean combinations. Setters preserve the order of disconnect, NTC/battery-ID
selection, reconnect, voltage checks and final route verification. GPIO write
failures remain visible to callers and diagnostics. The USB isolation setter
performs both writes and returns their wrapped sum.

Header routing enables the booster, delays, measures output and performs the
requested direction change. Low voltage produces a diagnostic; it does not
skip the requested switch. A mismatched final route reaches the real assertion
path. Battery detection keeps the signed 3000 mV test and the unsigned NTC
window calculation, then restores the battery NTC source and commits the detected
battery type through retained-state code.

Some original interfaces expose an R0/R1 pair. Their `uint64_t` signatures retain
that behavior: the low word is the status, and the high word may be a selector
or a linked diagnostic-name pointer. Private pointer values can change when
source moves; their string contents and the resulting diagnostics are compared.

## USB reattachment

`syscon_usb_reattach_state` names the active flag and split timestamp words.
The busy check preserves the original read order, including rereading the time
after the clock call, and checks a 2000 ms cooldown with unsigned wraparound.
A request validates busy state, USB voltage and booster state, then schedules
isolation, a 250 ms delay and release. Callback addresses come from C symbols.
Submission failure clears the active flag after logging the error.

## Validation and limits

Differential tests compare ordered pin/ADC/clock/task effects, volatile accesses,
returns, log contents and terminal faults. The scheduler integration executes
actual task submission, polling and callback dispatch. ROM-poisoning checks
ensure migrated strings/scales do not fall back to original data. The name-table
comparison validates each linked string before normalizing pointers; it does
not replace guest functions or manufacture successful outcomes.

Whole-image relocation sends BATCHECK, PWRSTATUS and shutdown commands through
UART while varying external ADC samples across battery and NTC thresholds.
Warm-reset tests poison the new state and name tables and require startup to
restore them. Other integration cases cover configuration compaction, stuck
outputs, task exhaustion and voltage/thermal curves.

The synthetic curves exercise firmware decisions, not battery chemistry or
charger regulation. Physical voltage settling, charge current, cell temperature
and charging safety require hardware measurements. The README identifies the
separate hardware-tested revision; local source validation is not a claim that
this revision has been flashed.
