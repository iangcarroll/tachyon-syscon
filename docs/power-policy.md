# Power report, initialization, and shutdown-reason policy

`tests/models/power_policy.c` reconstructs eleven entry points from syscon 1.0.52 using the original 4 KiB RAM layout. This is a host-test ABI, not a flashable replacement. `syscon_power_policy_execute` returns `UINT64_MAX` for unsupported entry points and report table indices outside the supplied RAM image. Void original functions return zero in this host adapter; tests do not compare their incidental register contents.

| Entry | Behavior |
| --- | --- |
| `0x5358` | Power status report |
| `0x54cc` | ADC configuration and optional I/O-expander initialization |
| `0x559c` | Update minimum observed VPH voltage |
| `0x55b4` | Reset minimum-voltage sentinel |
| `0x55c4` | Retrieve minimum voltage, mapping sentinel to `-1` |
| `0x55dc` | Record shutdown reason, clear stale flag, set timestamp |
| `0x562c` | Raw shutdown reason |
| `0x5638` | Elapsed time since recorded reason |
| `0x5670` | Stale flag |
| `0x567c` | Active reason, zero if stale |
| `0x5694` | Mark an old shutdown reason stale |

## Recovered behavior

Minimum voltage is a signed 32-bit comparison at RAM offset `0x5c`; `INT32_MAX` is the unset sentinel. Negative readings are not filtered. Shutdown reason is stored as one byte at `0x36f`, stale at `0x380`, and the full 64-bit timestamp at `0x388`. Setting a reason always clears stale. The timestamp is cleared only when the entire input argument is zero; an argument such as 256 stores a zero reason but still reads and stores the clock.

The stale threshold is **five minutes**, not five seconds. Literal `0x493df` at `0x56fc` is 299999; stale is set when unsigned 64-bit elapsed time is greater than that value. A zero timestamp suppresses expiration. The poll reads the clock even if reason is zero or already stale. The elapsed getter instead avoids a clock read for zero timestamps and returns zero when the clock is not later than the timestamp. Consequently, a backward clock can mark a reason stale through unsigned subtraction while the elapsed getter reports zero. The reconstruction preserves that discrepancy.

The report preserves ADC/helper read order and the exact original format-string and string-table pointers. USB is reported attached above 4499 mV, SG560D 1.8 V on strictly above 1700 mV, and VPH on strictly above 3000 mV. The report callback adapter receives the original format ROM address and packed 32-bit arguments; the tests compare these calls without pretending to implement the UART printf transport.

Initialization configures ADC pins 12, 13, 14, 15, 16, and 23 using the seven initialized bytes recovered from the stack. With a zero argument it produces a power report. Otherwise, it configures expander pins 8, 9, 10, 12, 13, 0, 15, 7, and 1 low, then 2, 3, and 11 high using the original three-byte payload. All dependency return values are ignored and the entry returns zero.

## Verification boundary

`tools/power_policy_oracle.py` executes the original functions and substitutes typed calls for power-routing/ADC helpers, retained battery state, I/O-expander access, the monotonic clock, ADC and expander configuration, and output callbacks. Diagnostic UART logging at `0x8f88` is omitted. Real ADC conversion, electrical rails, retained registers, printf bytes, and MCU timing are not proven by this module.

Five differential test groups passed in **1.15 seconds**, covering signed voltage limits, reason byte truncation, timestamp zero and wrap, 299999/300000 ms expiration boundaries, stale flags, report thresholds, dependency order, exact initialization payloads, and ignored dependency failures. Tests compare all global RAM in offsets `0x000..0x7ff` and ordered typed dependency traces; original stack scratch space is deliberately outside the comparison. Run from the workspace root:

```sh
syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_power_policy.py
```

Integration with the reconstructed power-routing helpers remains a separate step. This evidence does not establish full firmware or hardware end-to-end equivalence.
