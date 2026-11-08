# Periodic diagnostics and runtime accessors

`tests/models/diagnostics.c` reconstructs diagnostic enable `0x347c`, polling `0x3488`,
the eight packed runtime configuration accessors `0x3114..0x3178`, and hardware
revision parsing `0x3194`.

The poll counts loops in 64 bits but stores its sampling timestamps in 32 bits.
It samples after strictly more than 5000 ms, resets the counters even when output
is disabled, preserves the voltage-read order, and formats signed temperatures
with the original 12-byte truncation. The 64/32-bit timestamp mismatch causes
repeated sampling after the 32-bit clock wraps. The original unsigned 64-bit
divider returns all ones for nonzero divided by zero (zero for0/0); the C code
handles this explicitly when the measured interval rounds down to zero seconds.

Hardware revision accepts the original `%u.%u.%u` grammar, including signs,
whitespace and trailing characters. It selects the newer hardware path only when
the parsed major is1 and the unsigned minor exceeds1. This preserves unusual
cases such as a negative minor becoming a large unsigned value.

Two differential groups compare persistent RAM, dependency order, parsed results,
formatted temperature strings and diagnostic arguments across clock wrap,
integer extremes, invalid-temperature sentinel and revision syntax. ADC/GPIO,
clock, power state and logging remain explicit dependencies. The logger calls are
compared as typed arguments; full transport composition is separate. This is not
proof of physical measurement accuracy or complete firmware behavior.
