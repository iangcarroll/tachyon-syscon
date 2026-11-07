# Original-ABI command parser

`target/protocol_target.c` implements the entire UART polling/parser body. Its
context is the original twenty-byte layout, with port, buffer pointer, used
count, echo/enabled bytes and print callback. `target/command_table_target.c`
is a source-defined packed fourteen-byte table for all thirty-seven commands;
its function pointers resolve to reconstructed handler symbols. Names/help
retain original constant addresses and handler pointers relocate explicitly.

The parser retains byte filtering, raw-value assertions, diagnostic/debug
logging, echo sequencing, count-before-buffer writes, overflow behavior, space
replacement, suffix quirks, case-insensitive prefix matching, required/optional
argument policies, uppercase argument copying and PASS/FAIL callbacks. Unknown
commands and argument errors run the actual reconstructed failure callback.
String operations, case conversion and scan support are source linked.

Six differential groups compare original ARM and compiled parser across every
command, policy variants, return statuses, raw UART values, enabled/echo/debug
flags, chunk boundaries, overflow/suffix edges, live callback changes and
context/buffer aliasing. Ordered context/buffer memory accesses are compared.
The default manufacturing-printer pointer relation is checked separately.

These fixtures substitute UART, diagnostic sinks, fatal assertion and command
handlers. They prove neither complete command behavior nor all private-stack
states. The 132-byte uppercase temporary has a different compiled frame;
ordinary parser limits keep accepted command arguments within its copied range,
but corrupted contexts and arbitrary callbacks require broader proof. The
production table has no fallback to original executable code.
