# Original-ABI power policy

`target/power_policy_target.c` implements all eleven policy entries, including
the diagnostic report's variadic callback, ADC/expander initialization, signed
voltage minimum and shutdown reason/time/staleness tracking. Its fixed-memory
accesses and ROM pointers match firmware 1.0.52. The report performs unchecked
wrapping table indexing exactly as the target does; it does not adopt the
older host adapter's bounds guards.

The shutdown setter logs before writing state. Elapsed-time querying reloads
the timestamp after calling the clock, while expiry polling uses the initial
timestamp and reason, then reloads the reason for its diagnostic. Time checks
retain unsigned wraparound. Configuration structures are reused across the
initialization calls, so modifications through a dependency's pointer remain
observable by subsequent calls.

Seven test groups compare original and compiled ARM results, persistent RAM
read/write widths and order, dependency order, consumed log/callback arguments
and fault prefixes. They cover signed threshold boundaries, wrapped/out-of-range
table indices, live callback changes, ADC/expander config mutation, minimum
sentinels, arbitrary reason low bytes, clock rollover and stale-state checks.
An unmapped reason-table access must fault before the stored reason changes.

The fixture source-links the memory helper and explicitly substitutes power
measurements, route getters, clock, ADC, expander and output dependencies. It
does not establish universal interrupt equivalence, identical private stack,
a physical memory image, or complete peripheral behavior. Variadic callback
arguments are compared only where the format consumes them; incidental unused
argument registers are not a proof boundary.
