# Power reports and shutdown policy

`target/power/power_policy_target.c` implements the report callback, ADC/expander
initialization, minimum VPH tracking and shutdown reason/time/staleness logic.
Its globals and diagnostic tables are named C objects in `target/power/power_state.c`.
All seven shutdown names, including BROWNOUT, are source strings. The physical
linker allocates them; only the isolated differential fixture uses old locations.

The setter logs before writing the reason and timestamp. Elapsed-time querying
reloads the timestamp after reading the clock. Expiry polling uses the initial
timestamp/reason and reloads the reason for its diagnostic. These different
orders, zero-time behavior, unsigned rollover and the five-minute stale boundary
are preserved. The minimum tracks signed measurements; INT32_MAX means no sample
and the getter exposes that sentinel as UINT32_MAX.

Initialization reuses configuration buffers across ADC and expander calls, so a
dependency's buffer mutation is still observed by later calls. Report fields
retain their order and voltage thresholds. Named tables retain volatile reads
and unsigned index arithmetic. Valid enum values are the interface contract;
incidental bytes reached by invalid indices are not a promise about a relocated
image's private layout.

Tests compare actual original and rebuilt ARM execution, consumed variadic
arguments, state changes, read order and fault prefixes. Poisoned-ROM tests cover
the report and every shutdown name. Whole-image battery/NTC curves, real UART
commands, moved data and warm resets complement those isolated comparisons.
See [power manager](power-manager-target.md) for source organization and the
boundary between synthetic power tests and physical charging behavior.
