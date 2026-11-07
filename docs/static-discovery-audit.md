# Unassigned static listing audit

The audited listing originally contained 95 addresses outside every recorded function range.
All 95 are classified in `analysis/static-discovery-audit.json`: **2 instructions
belong to one uncatalogued function; 93 are string data misdecoded as Thumb
instructions; none are unresolved or padding.** This is complete classification
of that specific set, not proof that every possible entry in the binary has
been discovered.

## Actual missing entry: `0x9824`, string EOF reader

Bytes `00 20 70 47` decode as `movs r0,#0; bx lr`. The callback returns zero and
does not dereference its arguments or write memory. It is a separate four-byte
function, not an interior instruction of the adjacent sscanf or strchr bodies.

The reference at `0x981c` contains Thumb pointer `0x9825`. In sscanf:

- `0x97ee` loads that pointer; `0x97f2` stores it at `sp+0x2c`.
- `0x9804` passes `sp+8` as the FILE pointer to vfscanf at `0x980e`.
- Therefore the stored pointer occupies FILE offset `0x24`, the `_read` field.
- The pinned upstream `vendor/newlib-4.3.0/sscanf.c` assigns `_read=__seofread`
  at lines 434 and 464, supporting the recovered function identity.

At audit time `syscon_rt_sscanf` initialized the other original fields but
omitted `_read`. Its current string refill helper does not use this callback,
so ordinary input tests did not expose the omission. The omission nevertheless
changes an observable FILE field and leaves the standalone callback unimplemented.

The implemented fix adds `syscon_rt_seofread` and initializes `_read` with its rebuilt
address. It deliberately does not initialize other fields the original left
undefined. The original constructor initializes `_p`, `_r`, `_flags`, `_file`,
`_bf._base`, `_bf._size`, `_read`, `_ub._base` and `_lb._base`. In particular,
blanket zeroing the whole FILE would change original private-frame behavior.

Staged tests compare the emitted four-byte function and direct ABI behavior,
including invalid pointer arguments. An observer at the genuine vfscanf entry
compares all original initialized FILE fields, normalizing only the relocated
callback pointer. An alias case redirects `%n` to the live `_read` field, then
executes the actual scanner and checks the overwritten field and subsequent
integer conversion. Captured callback pointers are called on both CPUs.

The callback tests passed **7 tests in 0.40s**, including exact
four-byte symbol-size and byte comparison. The new tests plus the existing
scanner/formatter suite passed **20 tests in 9.46s**.

The fix, tests, function/range registration and source mapping are prepared in
`/tmp/syscon-scan-callback-stage/` while the full-suite sources remain frozen.
The patch is `/tmp/syscon-scan-callback-stage.patch`. The ledger should be
regenerated from the updated TSVs and runtime mapping after application; the
existing generated ledger is not silently edited during its frozen checkpoint.

## Data misclassified as instructions

| Listed addresses | Count | Actual bytes and references |
|---|---:|---|
| `0xb290`, `0xb292` | 2 | `DIAG` at `0xb290`, referenced by literal `0x35f4` and command descriptor `0xc451` |
| `0xb848`, `0xb84a` | 2 | End of `Reset MCU - %s`, then `MFGD` at `0xb849`; tag references include `0x8fbc` |
| `0xb896` through `0xb8fe`, every two bytes | 53 | CRLF terminator, `NORMAL:;`, `FASTBOOT:;`, `FCT:;`, `EDL:;`, LEDSTATUS format and RGB labels; references `0x42b4` through `0x42c0`, `0x431c`, `0x440c`, `0x4410` |
| `0xd084` through `0xd0ca`, every two bytes | 36 | `5V input OFF`, VUSB diagnostic and header-direction error format; references `0x6138`, `0x6114`, `0x6118` |

The JSON records every individual listed address, its raw two bytes, apparent
instruction, actual string spans (including shared terminators), and all
literal pointer fields found for those strings. The apparent loads, arithmetic
and branches are ASCII byte coincidences. Their preservation belongs to the
fixed data/string image; they require no additional executable implementation.

The fix is integrated into the current target source, and the inventory now contains 389 entries. The 93 remaining unowned listing addresses are classified string data.
