# Assertion, fault vectors, and retained breadcrumbs

`tests/models/fault_control.c` reconstructs the body of the original fatal assertion
handler at `0x2678`, rather than treating the entire handler as immediate reset.

The recovered sequence is:

1. Log the expression, file, source line, and fixed error value 1.
2. Disable interrupts with CPSID and clear SysTick's interrupt-enable bit.
3. Configure logical GPIO pins 2, 1, and 3, in that order, using the recovered
   12-byte configuration.
4. Up to twenty times: toggle pin 3, delay 10,000,000 loop units, feed the
   watchdog, and read pin 0. If it reads zero, delay another 1,600,000 units and
   read it again. Two consecutive zero reads take the early-reset branch.
5. Issue DSB and write `0x05fa0004` to AIRCR `0xe000ed0c`.

Both reset branches execute another DSB and then loop forever in the original,
until hardware reset occurs. The host model stops at the reset write and returns
the explicit `SYSCON_FAULT_RESET_REQUESTED` sentinel. Delay arguments are
reported as the original loop counts, not inferred wall-clock milliseconds.

The small adjacent routines are also reconstructed:

| Entry | Recovered behavior |
| --- | --- |
| `0x7b78` | Write current breadcrumb to SYSCTL.SHUTDNSTORE3 |
| `0x7b88` | Read its low byte |
| `0x7b9c` | Name one of 21 breadcrumb values, or `BAD` |
| `0x7bb8` | HardFault vector: store 18 and halt forever |
| `0x7bcc` | NMI vector: store 19 and halt forever |
| `0x7be0` | Set SYSCTL.MCLKCFG.USEMFTICK |
| `0x7bfc` | Read the cached reason byte at original RAM `0x20000254` |

The breadcrumb write is **not** a GPIO/power-configuration operation. Register
`0x400b040c` is shutdown storage byte 3, confirmed by the
[TI MSPM0L11xx/L13xx SYSCTL definitions](https://github.com/TexasInstruments/mspm0-sdk/blob/e6793f41ce464fe78f03f100e715d5e30b43f25a/source/ti/devices/msp/peripherals/m0p/sysctl/hw_sysctl_mspm0l11xx_l13xx.h),
saved in `analysis/ti-hw-sysctl.h`. The table includes stages such as I2C waits,
UART_TX, HARD_FAULT, NMI, and BAD_IRQ. The reset/startup routine responsible for
caching or clearing a previous breadcrumb is outside this module.

## Validation

Nine test groups in `tests/test_fault_control.py` pass. They execute the
original assertion body and compare its entire ordered callback/register trace
with C, covering timeout after twenty toggles, immediate button reset, bounce
on every iteration, reset on the final iteration, signed/nonzero GPIO returns,
watchdog and delay ordering, PRIMASK becoming disabled, and both reset paths.
They also compare every breadcrumb name, invalid names, all cached-byte values,
raw breadcrumb writes, clock-mask preservation, and HardFault/NMI halts.

GPIO configuration/toggling/reads, delay loops, watchdog feeding, and logging
are explicit callback boundaries in the assertion tests. SysTick and AIRCR
accesses are passive emulated registers, not actual hardware. The tests stop
at the reset request or infinite-loop boundary and do not prove physical reset,
LED polarity, electrical debounce, or watchdog timing. Interfaces add a context
and callbacks; target linkage and exact machine-byte equivalence remain
integration work. No hardware was accessed.

```sh
.venv/bin/python -m pytest -q tests/test_fault_control.py
```
