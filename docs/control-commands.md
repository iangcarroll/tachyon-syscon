# Control CLI handlers

`tests/models/control_commands.c` reconstructs the 26 command-table records outside the
configuration subsystem: 23 unique handler entry points, plus the POWER,
REBOOT, and STATUS aliases. The other 11 records, including CONFIG_INTERNAL,
belong to the separate configuration reconstruction.

| Entry | Commands |
| --- | --- |
| `0x3ef0` | VERSION |
| `0x3f24` | HELP |
| `0x3f80` | IOEXP_READ |
| `0x3fd0` | PWRSTATUS, STATUS |
| `0x40a0` | WAKE_AFTER |
| `0x40fc` | MCU_SLEEP |
| `0x4110` | MCU_REBOOT, REBOOT |
| `0x41a4` | SHUTDOWN_REASON |
| `0x422c` | 560D_DIRECT |
| `0x4258` | 560D_ON, POWER |
| `0x42c8` | LEDSTATUS |
| `0x4320` | SET_PATTERN |
| `0x4364` | SET_RGB |
| `0x4420` | READ_PWR |
| `0x47b0` | BATCHECK |
| `0x47bc` | GPIO_READ |
| `0x47fc` | 560D_DBG |
| `0x4850` | KEYS |
| `0x48a4` | 560D_OFF |
| `0x48e0` | DIAG |
| `0x4904` | ERROR |
| `0x4970` | KEY_MODE |
| `0x49ac` | LOG |

Each handler's argument interpretation, output-format calls, dependency order,
and return value are compared against the original Thumb code. The original
string and integer library routines execute in the oracle. HAL and other
subsystems use explicit scripted callbacks rather than fabricated success.
Both successful and unsuccessful dependency return values are exercised.

## Notable preserved behavior

- HELP uses the exact 37 command names and descriptions recovered from the
  packed table at `0xc419`. VERSION identifies the pinned image as 1.0.52.
- Numeric parsing accepts a numeric prefix and ignores trailing text. The
  decimal conversion follows the firmware's signed 32-bit saturation at
  overflow. SET_PATTERN uses atoi-like conversion, so nonnumeric strings can
  select state zero. GPIO_READ truncates the parsed pin to 16 bits, and
  IOEXP_READ truncates it to eight bits, while printing the original number.
- WAKE_AFTER accepts 0 through 259200 seconds. A negative parsed integer is
  rejected by an unsigned comparison. With no argument it prints the result of
  the timed-wake query.
- DIAG and LOG inspect only the first byte of the argument. Thus `1junk` and
  `10` both enable the setting.
- SET_RGB requires five colon-terminated tokens no longer than three bytes.
  Empty or nonnumeric tokens convert to zero; converted values truncate to
  eight bits. Pattern validation occurs after truncation and allows 0–4.
  Partial token echoes occur before later-token validation fails.
- SET_RGB passes each echoed token directly as a printf format string with no
  arguments. The reconstruction deliberately records this original call
  boundary. A token containing `%s`, `%d`, or similar conversions can cause
  undefined variadic behavior in the real firmware. The tests compare the raw
  format invocation without inventing the missing arguments. They do not prove
  the resulting UART bytes or safety of those inputs.
- 560D_DIRECT removes the final two suffix bytes and sends the remaining
  argument, then CR/LF as a separate write. Its handler assumes the parser's
  suffix contract; arbitrary shorter direct-handler inputs are outside that
  contract. The existing parser performs its original uppercase conversion.
- A missing reboot argument selects soft reboot. Hard reboot resets the
  expander and retained state before the 500 ms delay and AIRCR reset write.
- ERROR 0 and nonnumeric ERROR arguments enter the fatal assertion; ERROR 1
  succeeds silently, ERROR 2 emits an error log and succeeds, and other values
  emit an invalid-command log and fail.
- 560D_OFF returns the shutdown dependency's result directly. It is not
  normalized to a boolean success value like 560D_ON.

## Non-returning commands and parser integration

The original reboot handler writes `0x05fa0004` to AIRCR `0xe000ed0c` and then
does not return. The assertion handler also does not return. The original-code
oracle stops at these boundaries; it never accesses a live device.

The reconstructed handler returns host sentinel `SYSCON_CONTROL_TERMINATED`
after recording the boundary. `syscon_control_feed` is host harness machinery
that uses setjmp/longjmp to stop the reconstructed parser before PASS/FAIL or
any later command. It is not reconstructed target code. Unknown handlers
similarly stop with `SYSCON_CONTROL_UNHANDLED` unless an explicit fallback
dispatcher is supplied. The fallback is the integration point for the separate
configuration handlers. A caller must never treat either sentinel as ordinary
nonzero command success.

## Evidence and limits

14 differential test groups pass in `tests/test_control_commands.py`, covering
all listed handlers, dependency results -1/0/1/5, aliases, parser input split
into three-byte chunks, lowercase commands and parser uppercasing, malformed
arguments, numeric overflow, randomized RGB tokens, terminal-command stopping,
unknown-handler stopping, and explicit configuration fallback routing. The
terminal tests append VERSION after reset/assertion and establish that neither
the command's PASS nor the later VERSION is emitted. The source also compiles
for Cortex-M0+ with warnings treated as errors.

The oracle executes the real parser and command handlers. Hooked dependencies
include GPIO/expander reads, ADC/power functions, SG560D control, LED settings,
logging, sleep, reset delay, and the assertion boundary. Their results and side
effects are test fixtures.
This work does not establish that those hardware actions succeed on a board.
`PWRSTATUS` is tested with a callback fixture supplying diagnostic output; its
power-diagnostic implementation is not reconstructed here.

Print callbacks expose the original printf format plus typed argument values.
For ordinary defined formatting these establish the text to be rendered, but
the actual UART formatter and serial transport are outside this suite. Parser
diagnostic logging is separately excluded, consistent with the parser's
existing tests. The native interfaces use context pointers and callback
injection, so they are not a drop-in original binary ABI. No byte-for-byte
firmware equivalence, complete hardware emulation, or flashable image is
claimed.

Run from `syscon-re`:

```sh
.venv/bin/python -m pytest -q tests/test_control_commands.py
```
