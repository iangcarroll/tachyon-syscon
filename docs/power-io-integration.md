# Power routing through the expander and I2C controller

`tests/test_power_io_integration.py` removes the previous GPIO/expander/I2C function substitutions along these paths:

```text
Original ARM power routing / reconstructed C power routing
  → GPIO routing (0x3620 / 0x364e)
  → expander configuration, read, and write logic
  → real I2C initialization / TX / RX / IRQ functions
  → modeled MMIO controller, FIFOs, and external register device

Power measurements
  → actual ADC HAL and fixed-point conversion
  → modeled ADC MMIO with explicitly supplied raw samples
```

The original path executes the firmware instructions for every module above the MMIO boundary. The C path calls the corresponding reconstructed modules. Neither ADC nor I2C HAL is substituted by a function-level success result. The external model starts transactions when software programs the controller's transaction register, consumes bytes actually written to the TX FIFO, supplies bytes through the RX FIFO, tracks busy/ready status, and implements the flush controls used by the firmware. It decodes the slave address from the programmed register and NACKs addresses other than `0x26`. ADC initialization and sampling also execute through their real register paths; raw readings are explicit test inputs rather than claimed electrical measurements.

The external device has an explicitly supplied eight-byte register bank representing sixteen GPIO pins: input, output-latch, polarity, and direction register pairs. Accesses use a register pointer, and multi-byte transfers advance within a pair. This models the register operations used by this firmware; it is not a claim that the exact board expander silicon has been identified. Inputs, initial latches, directions, polarity, and every initial MMIO value are provided by the test. The MMIO fixtures are not asserted to be hardware reset values.

## Interrupts and faults

A modeled NACK queues the I2C interrupt if its peripheral and NVIC masks are enabled. The ARM harness preserves the interrupted CPU context, executes the **actual original ISR at `0x8798`**, and restores the context afterward. The C path invokes the reconstructed ISR at the matching MMIO boundary. ISR MMIO reads and sticky-error RAM effects are compared. This is explicit interrupt scheduling, not a full model of Cortex-M exception stacking, priority, or electrical timing.

The scenarios include:

- I2C initialization, expander reset, configuring all sixteen outputs, and repeated battery, SG560D VBUS, and 5 V header routing changes.
- Input/output direction changes and external input changes across all sixteen pins.
- ADC scaling on every configured input, the zero-reading retry, and battery detection running through actual ADC and expander/I2C code.
- One to four NACKs during a write, successful retries, and terminal expander assertions.
- Read NACKs remaining sticky across subsequent read retries, matching the original behavior.
- An initial controller idle timeout followed by error cleanup and a successful retry.
- Invalid selector state detected after actual bus reads.
- A negative control that forces one output low only in the reconstructed path. The power manager's readback detects the mismatch and asserts; the differential comparison rejects that path while the original control succeeds.
- A terminal lower-layer assertion propagating through the power manager without follow-up bus operations. This integration exposed an error in the initial C power adapter: it continued after an expander `-2` assertion sentinel. The regression remains part of the suite so a host-only return sentinel cannot silently replace the original nonreturning reset boundary.
- A fatal I2C HAL precondition assertion being distinguished from recoverable controller errors. The original asserts once; interpreting its host sentinel as ordinary `-1` incorrectly retried it and generated additional assertions. This second boundary has its own regression.

Both assertion-propagation defects are now fixed. The integration adapter maps the I2C host assertion sentinel to terminal `-2`; expander retries propagate it immediately, and the power-manager host executor unwinds at that terminal dependency result. Recoverable controller failures remain `-1` and retain their original retry behavior. Clock and ordinary numeric return values are not treated as terminal GPIO results.

Comparisons cover every ordered MMIO, wire-transaction, IRQ, diagnostic-event, and retained dependency event; all global RAM through offset `0x7ff`; output and input register banks; register pointer; controller registers; FIFO contents; pending transactions and interrupts; and clock state. Tests also verify that critical original entries executed and were not present in the oracle's hook table.

## Remaining boundaries

Millisecond delays, retained battery-state updates, and task submission remain explicit external dependencies in this test. ADC register samples are supplied inputs; analog voltages are not modeled. Direct MCU GPIO pins below 25 are outside its exercised routing domain. The model does not simulate load switching, physical rise times, arbitration, complete register-reset side effects, or boot/reset recovery. It proves these power-to-I2C and power-to-ADC software flows against a defined peripheral model, not whole-board end-to-end equivalence or flash safety.

```sh
syscon-re/.venv/bin/python -m pytest -q syscon-re/tests/test_power_io_integration.py
```

Validation checkpoint: the integration suite and existing expander differential suite passed together: **53 passed in 2.35 seconds**. This includes the two fatal-boundary regressions and the deliberately mismatched stuck-output negative control.
