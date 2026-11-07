# Original-ABI configuration commands

`target/config_commands_target.c` implements the eleven configuration command
handlers and shared dump routine, using original signatures and source-backed
scan/printf, namespace storage and flash operations. It retains password
parsing, partial scanset conversions, getter mutation of keys, exact return
values, failure text, dump blank/rejected distinctions and watchdog writes.
Internal-config reporting snapshots all eight getters before printing.

The integration tests compare original and rebuilt commands through the actual
FLASHCTL model: setting/getting/indexed lookup, duplicate keys, repeated
compactions, record rejection, blank records, erase passwords, malformed and
31-byte-boundary inputs, and legacy format-bearing values during compaction.
They compare printed formats and consumed arguments, full flash/controller
traces, runtime RAM and watchdog MMIO. Getter leaves for CONFIG_INTERNAL are
explicit endpoints; the compiler fixture watchdog executes a direct MMIO write.

The test printer reads strings bytewise to the terminator and does not require
unrelated stack pages to be mapped. Private temporary pointer addresses are
compared by consumed contents. Whole-machine equality for arbitrary private
stack aliases, missing printf arguments, self-modifying callbacks and all
interrupt schedules is not established by these bounded comparisons.
