# Original-ABI command parser

`target/protocol/protocol_target.c` implements the entire UART polling/parser body. Its
context has named volatile fields for port, buffer pointer, used count,
echo/enabled bytes and print callback. The twenty-byte ARM calling layout is
preserved; production globals are being migrated separately. `target/protocol/command_table_target.c`
owns the command names, help strings and handler pointers as ordinary C data.
The parser and HELP handler derive their count from this array, so adding a
record does not require changing a private address or a second count. The
linker places the table; fourteen-byte records remain the internal ARM layout.
Control/parser text and the debug flag also resolve through linker symbols.

The parser retains byte filtering, raw-value assertions, diagnostic/debug
logging, echo sequencing, count-before-buffer writes, overflow behavior, space
replacement, suffix quirks, case-insensitive prefix matching, required/optional
argument policies, uppercase argument copying and PASS/FAIL callbacks. Unknown
commands and argument errors run the actual reconstructed failure callback.
String operations, case conversion and scan support are source linked.

Differential tests compare original ARM and compiled parser across every
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

A source-edited whole-image fixture adds BUILD_INFO, moves the descriptor
table and text, and checks its UART response and HELP listing. Unit tests
poison the removed original command-data block before exercising every
command. Comparisons validate linked text contents, while preserving exact
non-text callback arguments and context/buffer access order.
