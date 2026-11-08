# Power routing, ADC scaling, and USB recovery

`tests/models/power_manager.c` reconstructs entry points from `0x4c50` through `0x5274`:
ADC scaling/retry, three two-GPIO selectors, rail/USB controls, selector changes,
USB isolation/recovery tasks and cooldown, and battery-type detection. The host
executor operates on a 4 KiB RAM image using original global offsets. Dependencies
are explicit ADC/GPIO/time/task/retained-state callbacks.

Preserved details include the zero ADC sample retry, a 16-bit ADC pin argument
followed by a full-width channel comparison, uint32 multiplication wrap, ordered
GPIO switching, selector assertions, USB task-submission failure rollback,
2000 ms recovery cooldown, and battery-ID thresholds. GPIO/ADC/time endpoints in
`tools/power_oracle.py` replace hardware only; internal original power-manager
functions and selector checks execute as real Thumb instructions.

Tests compare persistent RAM, GPIO states, ordered calls, return values and
assertion boundaries. Cases include stuck GPIO writes, contradictory selector
pins, voltage boundaries, timer wrap, rejected tasks and repeated routing changes.
An integration test also executes the original power manager through the original
two-slot scheduler and both USB recovery callbacks, comparing the reconstructed
pipeline at ordinary and 32-bit-wrap timestamps.

Limits: diagnostics are suppressed rather than reproduced. Assertion/reset is
represented by an explicit `UINT64_MAX` outcome and assertion event, not an actual
reset. Selector modes outside 0–2 and out-of-range diagnostic-table indexing are
unsupported. The hardware model does not establish voltage settling, current
limits, thermal behavior, physical power rails or brownout behavior. C callback
adapters are host interfaces, not final linked ARM call sites. These tests do not
make the replacement firmware safe to flash.

Integration fault injection found that a lower-level I2C assertion initially
returned a synthetic error to the host GPIO adapter and allowed power routing to
continue. The host power executor now unwinds immediately on the explicit
`SYSCON_POWER_IO_TERMINATED` GPIO sentinel, preserving state/effects up to the
assertion and emitting no later bus operations. Ordinary negative statuses are
kept distinct, and 64-bit clock values are never interpreted as termination.
