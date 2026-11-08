# Direct target control-command handlers

`target/control_commands_target.c` implements the 23 control handlers assigned
to this module. Each uses the original `(uint32_t arguments, uint32_t printer)`
ABI from `protocol_target.h`. The printer is an actual ARM variadic function
pointer. The source command table relocates function pointers to these bodies;
command names, help, tokens and output strings are ordinary C data. The
version remains at the packaged updater's documented flash boundary.

Implemented entries are 3ef0, 3f24, 3f80, 3fd0, 40a0, 40fc, 4110, 41a4, 422c,
4258, 42c8, 4320, 4364, 4420, 47b0, 47bc, 47fc, 4850, 48a4, 48e0, 4904, 4970,
49ac. Exact symbol mappings are in `tools/control_commands_target_oracle.py`
and the canonical `analysis/command-target-symbols.json`. Root's separate
configuration handlers are not replaced or stubbed in production code.

Numeric scanning uses the actual rebuilt `syscon_rt_sscanf`, `syscon_rt_atoi`,
and newlib-derived scan/runtime sources. Comparisons, searches, lengths, and
bounded copies use the recovered C string helpers. This preserves scanner
assignment counts, integer saturation/errno, whitespace/sign/trailing-text
behavior, and distinctions between scanf validation and permissive atoi.
There is no host decimal parser in the execution path.

The implementations retain output ordering, callback
arguments, nonboolean dependency results, pin truncation, direct modem-length
underflow, and terminal behavior. KEYS passes both SG key-pulse arguments
`(pin, 0)`. A hard reboot resets expander registers and clears retained
scratch registers before delaying, writing AIRCR.SYSRESETREQ with its key,
executing the post-write DSB, and waiting in an infinite loop. ERROR invokes
the actual assertion dependency rather than returning a host terminal sentinel.

SET_RGB intentionally forwards its short token as a format string, as the
original does. Callback mutation of that stack token is visible to the
subsequent atoi. No escaping or new rejection rule changes its behavior.
This leaves an important proof boundary: formats requesting missing arguments
may observe incidental register or stack contents. The tests preserve the
callback invocation and one actual missing-register-word observation for
`%d`; that fixture produced no counterexample. They do **not** prove arbitrary
missing-argument formatter behavior or stack corruption. The original and
rebuilt C stack layouts and incidental caller-saved registers are not generally
identical. This must remain part of the whole-image proof work.

## Executable checkpoint

`tools/control_commands_target_oracle.py` builds these handlers together with
the source-backed scanner, runtime, UART parser, packed command table, and
callback helpers. It uses the runtime builder's target compiler settings and
links no installed runtime archives. `target/control_commands_test_fixture.c`
implements real ARM variadic printer/logger consumers; their format pointer,
defined argument words, format bytes, and ordering are recorded. Local format
addresses are compared by bytes; fixed rodata and semantic argument pointers
retain their values.

Hardware/application dependencies are explicitly replaced at their entry
boundaries in the harness. Their arguments, payloads, returned values, and
terminal behavior are checked. Scanner/string/runtime/command/parser bodies
are never replaced by Python. A trap for an unlinked configuration handler
fails closed, so those handlers cannot silently pass through a test stub.
The candidate cannot execute the original image mapped for rodata access.

`tests/test_control_commands_target.py` has **27 passing test groups**, covering
all handlers, all exact-string alternatives, malformed/case-mismatched input,
numeric edge and overflow cases, RGB tokens and callback mutation, unsigned
raw-send length underflow, dependency failures, logger/error paths, terminal
reset/assertion behavior, invalid printer/argument faults, and chunked UART
input through the real source parser into real command handlers. The reset
loop test also executes the original post-request barrier and wait loop under
an explicitly passive reset-register environment.

Comparisons include R0, callee-saved registers on returning commands, ordered
dependency and callback records (text is compared by contents), persistent RAM and guard bytes through
`0x20000aff`, and ordered persistent-RAM writes. The original
parser→handler→sscanf stack reaches `0x20000b7c`, so higher stack scratch is
excluded. The rebuilt test stack resides in separate emulation memory.

The scoped report
`analysis/control-commands-target-test-instruction-coverage.json` records
**636/636 identified original instructions** across the 23 entries. This is
finite execution evidence; it does not prove universal equivalence, arbitrary
stack aliases, every asynchronous event, or a complete physical image.
Persistent ELF, source/compiler hashes, and mapping metadata are emitted under
`build/control-commands-target/`. The isolated ELF is not a flash image.
