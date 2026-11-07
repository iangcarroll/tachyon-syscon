# Timer and retained-state reconstruction

This module is a functional C reconstruction of selected routines in the pinned
1.0.52 image. It is not a complete firmware image and is not a flash candidate.
The public C entry points accept explicit state and hardware callbacks so the
same logic can run in native differential tests. Their calling conventions are
therefore not yet the original fixed-address firmware ABI, and whole-function
machine-code equivalence has not been established.

## Recovered timer state

The original state occupies 112 bytes beginning at `0x20000610`:

| Offset | Meaning |
| --- | --- |
| 0..95 | Four 24-byte timer slots |
| 96 | Initialization flag |
| 97..103 | Unmodified padding/unused bytes |
| 104..111 | Unsigned 64-bit tick count |

Each slot contains a 64-bit start tick, 32-bit interval, byte one-shot flag,
three preserved padding bytes, 32-bit callback address, and 32-bit callback
argument. Static assertions check these offsets in the C reconstruction.

| Original entry | Reconstructed entry |
| --- | --- |
| `0x76f8` | `syscon_timer_tick` (SysTick interrupt body) |
| `0x776c` | `syscon_timer_init` |
| `0x77b4` | `syscon_timer_now` |
| `0x77c0` | `syscon_timer_delay` |
| `0x77fc` | `syscon_timer_wait_countflags` |
| `0x781c` | `syscon_timer_register` |
| `0x7880` | `syscon_timer_unregister` |

The tick routine increments time first and visits slots in index order. A timer
is due when the unsigned 64-bit difference reaches its 32-bit interval. Every
nonzero one-shot byte is true. The callback runs before the one-shot flag is
checked again: callbacks can replace themselves, cancel timers, arm later slots,
or change the clock. Those changes affect the current dispatch pass.

Registration replaces the first matching callback address, or chooses the first
empty slot, and fails when neither exists. A zero callback is accepted and
updates an empty slot while leaving it inactive. Unregistering clears every
matching callback and argument, including arguments in empty slots when the
requested callback is zero. Other slot bytes are retained.

Initialization runs only when its flag is zero. It writes SysTick LOAD `0x7cff`,
updates the upper SHPR3 priority byte to `0xc0` while preserving the low 24 bits,
clears VAL, writes CTRL `7`, zeroes only the 96 slot bytes, and sets the flag.
It does not reset the software clock. The COUNTFLAG wait explicitly performs
one initial CTRL read even for a requested count of zero.

## Retained state

RAM at `0x200000da` holds three bytes: magic, packed mode nibbles, and a saturating
counter. These are mirrored into three 32-bit registers at `0x400b0400`,
`0x400b0404`, and `0x400b0408`. The byte names follow the existing reverse-engineering
notes; the physical reset/power retention behavior is not inferred from emulation.

| Original entry | Reconstructed entry |
| --- | --- |
| `0x59a0` | `syscon_retained_commit` |
| `0x59d8` | `syscon_retained_load` |
| `0x5a88` | `syscon_retained_clear_registers` |
| `0x5aa8` | `syscon_retained_set_modem` |
| `0x5ac4` | `syscon_retained_modem` |
| `0x5ad4` | `syscon_retained_set_battery` |
| `0x5af0` | `syscon_retained_battery` |
| `0x5afc` | `syscon_retained_increment_boots` |
| `0x5b14` | `syscon_retained_boots` |

Loading uses only each register's low byte. A magic byte other than `0x5b` causes
the three bytes to be reset to `{0x5b, 0, 0}` and written back. The low and high
nibble setters mask the supplied value and always commit all three registers.
The counter saturates at 255, but an increment still commits at saturation.
The register-clear function clears hardware registers without changing RAM;
a subsequent load sees invalid magic and performs the normal initialization.

## Differential evidence

`tests/test_timers.py` and `tests/test_retained.py` execute the original Thumb
instructions through `tools/timer_oracle.py` and compare the C reconstruction.
The six tests passed on 2026-11-07. They cover:

- 2,400 seeded mixed registration, replacement, cancellation, and tick operations,
  comparing all 112 state bytes and ordered callback traces after every operation.
  Starting clocks include the 32-bit boundary and the 64-bit wrap boundary.
- Callback-driven self cancellation/replacement, activation of later slots in
  the same tick, and changes to the clock during dispatch.
- Initialization with zero and nonzero flags, repeat initialization, preservation
  of padding and clock, and exact ordered 32-bit register reads/writes.
- Both delay loops with explicitly scripted external time/COUNTFLAG progress,
  including zero duration and counter wrap. Watchdog call counts are compared.
- All 256 low/high nibble input values, counter saturation, low-byte extraction
  from registers containing nonzero upper bits, invalid-magic reset, repeat loads,
  and clearing registers without altering the RAM copy. Register traces and all
  three RAM bytes are compared after each operation.
- A retained-state mutation injected on the first register write verifies that
  commit snapshots all three RAM bytes before issuing any register writes.

Run with:

```sh
.venv/bin/python -m pytest -q tests/test_timers.py tests/test_retained.py
```

## Explicit substitutions and remaining limits

The oracle maps only the relevant SCS and SYSCTL pages as passive register
storage, records accesses, and hooks diagnostic logging at `0x8f88`. Test callback
addresses are hooks instead of real application callbacks. Delay tests hook
watchdog feeding and script time progression; COUNTFLAG progression is scripted.
The production C reconstruction exposes these dependencies as callbacks and
omits the original diagnostic log text.

These tests establish function-level equivalence for the exercised inputs and
external events. They do not validate interrupt entry/exit, preemption, torn
64-bit accesses, physical clock rate, voltage/reset domains, watchdog timing,
the electrical persistence of retained registers, or complete power sequencing.
No hardware was connected, read, erased, or programmed by this work.
