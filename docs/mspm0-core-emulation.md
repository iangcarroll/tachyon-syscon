# ARMv6-M core emulator audit

`tools/mspm0/core.py` executes guest instructions at physical addresses using
Unicorn plus an explicit exception, interrupt-controller and memory model.
`tests/test_mspm0_core_exceptions.py` independently exercises transitions with
small instruction fixtures; it does not replace firmware functions with hooks.
The existing emulator and original-firmware end-to-end tests remain separate.

The architecture reference for this audit is Arm's
[ARMv6-M Architecture Reference Manual, DDI 0419E](https://documentation-service.arm.com/static/5f8ff05ef86e16515cdbf826):
B1.5.5–B1.5.14 for reset, exception stacking/return and faults; B1.5.16 for sleep;
B2.3 for memory access; B3.2–B3.4 for system registers, SysTick and NVIC.
Useful normative distinctions are that WFI wake eligibility differs from
PRIMASK-controlled exception delivery; exception hardware accesses banked
stacks independently of guest privilege; SVC can escalate; and NVIC input
levels and latched pending state are distinct. The implementation's behavior
and tests below are local evidence, not a claim of architectural certification.

## Implemented and tested changes

- WFI wakes for an enabled, sufficiently high-priority pending interrupt even
  when PRIMASK blocks handler activation. Disabled and insufficient-priority
  interrupts do not wake it. SLEEPONEXIT provides a deterministic virtual halt.
- Exception entry stacks the interrupted register state on MSP or PSP, records
  alignment padding, selects privileged Handler mode/MSP, and installs the
  appropriate EXC_RETURN. Return restores the selected bank and CONTROL.SPSEL.
  Nested return mode, active IPSR, stacked IPSR and return-PC consistency are
  checked. Missing stacked Thumb state faults after restoration.
- Unprivileged Thread mode is covered explicitly. Unicorn's public special-
  register accessors apply guest MRS privilege rules, returning zero for MSP,
  PSP and PRIMASK in this mode. The model temporarily selects a privileged
  register-access context to implement hardware stacking and scheduling; no
  guest instruction executes in that context. Guest accesses retain their
  privilege restrictions.
- `set_irq_line(irq_number, asserted)` tracks 32 external line levels separately
  from pending bits. A rising edge latches pending, deassertion leaves the latch,
  and an asserted source re-pends on exception return. ICPR only clears a pending
  source after its physical line is low. Priority byte lanes, SHPR byte writes,
  enable/disable, coalescing, NMI/HardFault priority and ICSR state are tested.
- SysTick uses deterministic instruction quanta. NOREF is asserted, so the
  clock-source bit reads as one. Changing RELOAD to zero does not discard an
  already running countdown; subsequent zero reloads do not fabricate count
  events. COUNTFLAG read/clear behavior and interrupt masking are covered.
- Halfword/word unaligned data transactions fault. CPU flash stores and
  execution from non-executable regions cannot silently succeed. Missing
  factory images and unsupported peripheral semantics still stop explicitly.
- The configured Unicorn Cortex-M0 engine was observed accepting MOVW, which
  is outside ARMv6-M. The model therefore checks 32-bit instructions against
  the ARMv6-M BL, MRS/MSR and barrier forms, rejects unsupported special-register
  operands, and rejects ARMv7-only IT/CBZ forms. Regressions exercise MOVW,
  BASEPRI access, IT, CBZ and an undefined instruction.

## Fault and reset interfaces

`MCU(..., fault_policy='stop')` remains the default: a precise CPU memory or
instruction fault stops with `BusFault`. With `fault_policy='hardfault'`, known
CPU faults enter exception 3 with a stacked faulting PC. SVC escalation stacks
its following instruction. A vector-read bus fault can use a derived HardFault
entry with the already-stacked frame. A fault while executing NMI/HardFault or
failure entering HardFault yields explicit `Lockup`, with PC at `0xfffffffe`.
Unmodeled registers and missing fixture images are model errors, not fabricated
hardware-fault results. Unknown behavior must remain distinguishable from an
implemented bus response.

`request_reset(cause)` queues a transition. A CPU-originated request stops the
current emulator slice; reset occurs before another guest instruction.
`reset_system(reason)` clears CPU, NVIC and SysTick state, then invokes
`Devices.reset_system(reason)` for the TI-specific peripheral domains. It
preserves modeled SRAM, flash, factory and NONMAIN contents. AIRCR accepts
SYSRESETREQ only with the `0x05fa` write key. Wrong-key writes are ignored by
this deterministic model policy. Peripheral retained-register/reset-cause
behavior belongs to `peripherals.py` and its tests.

Reset initializes architecturally unknown general registers, APSR and PSP to
zero and LR to `0xffffffff` for reproducibility; these are fixture choices,
not captured silicon reset values. Instruction/tick counters and event history
continue across resets, and `reset_count` records transitions.

## Supported boundary and remaining limitations

This is not complete or cycle-accurate MCU emulation. Interrupt recognition
occurs between guest instructions; late-arrival timing and tail-chaining cycle
optimizations are not simulated. Electrical sleep/clock-domain behavior is
outside this core model. Complex partially completed LDM/STM/PUSH/POP fault
replay is not exhaustively validated. Invalid exception-return combinations
that the architecture classifies as unpredictable stop conservatively with
`Lockup`; this is an explicit model choice.

WFE and SEV currently stop with a specific `ModelError`; the event-register
protocol is not silently approximated. Debug halt, trace and NMI escape from
lockup are not modeled; reset clears modeled lockup. The instruction checks
close demonstrated Unicorn gaps, but do not establish complete ISA conformance.
MPU/FPU functionality is not present in the selected device profile. Undefined
or unsupported peripheral behavior remains fail-closed.

The full firmware scenarios use an explicitly synthetic board fixture and
start from the available application reset vector, not an unavailable boot ROM.
Passing them does not validate a particular physical board's identity,
calibration, electrical timing, or flash safety. No hardware was accessed.
