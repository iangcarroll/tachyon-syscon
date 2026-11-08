# Direct target assertion and retained breadcrumbs

`target/fault_control_target.c` supplies original ARM interfaces for assertion
`0x2678`, stage set/get/name `0x7b78/0x7b88/0x7b9c`, MFTICK enable `0x7be0`, and
cached reset reason `0x7bfc`. These are target code, not host context adapters.

The assertion calls the variadic logger with the original format/tag contents
and argument order, executes CPSID, clears the SysTick interrupt bit,
configures pins 2/1/3, and performs the original 20-attempt toggle/delay/feed/read
sequence. Both reset paths execute DSB before and after AIRCR SYSRESETREQ and
then wait indefinitely. No reset-request sentinel or normal return replaces
that behavior. The reset controller is responsible for ending execution.

Stage names are an ordinary C string table. The reset-cause cache is a named
volatile byte shared with the GPIO/core module; PMU registers remain hardware
addresses. The stage getter
truncates the volatile register value to a byte; the setter writes its complete
input word, allowing the MCU model to apply hardware field semantics.

Target differential tests compare full ordered dependency/MMIO/barrier
traces, both button-reset branches, timeout, bounce, nonzero signed inputs,
PRIMASK, cached byte values and breadcrumb string contents. The tests continue
past the reset write to check the second DSB and nonreturning wait, rather than
counting the reset write alone as completed behavior.

GPIO, logger, delay and watchdog implementations are explicit linked dependencies.
The unit tests bind those boundaries to matching AAPCS callbacks; they do not
claim that delay timing or entire assertion-to-reboot integration is proven.
Private stack placement and fault frames are not compared. The complete-image relocation test injects an I2C NACK and checks the real
assertion path with the reconstructed GPIO/core and logger modules. Original-ROM
poisoning separately checks that diagnostics do not depend on their old addresses.
