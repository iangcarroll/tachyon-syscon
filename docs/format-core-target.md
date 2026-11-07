# Direct target formatter core

`target/format_core_target.c` and `include/format_core_target.h` expose three
original ABI entries without host context or memory-access arguments:

| Original | Target | Result |
| --- | --- | --- |
| 8fcc | syscon_target_format_digits | R0 reversed-digit count; R1 original output pointer |
| 9028 | syscon_target_format_forward | Actual callback R0 |
| 9038 | syscon_target_vformat_callback | Emitted byte count |

The digit helper accepts a 64-bit value in R0/R1, buffer in R2, radix in R3,
and alphabet offset on the stack. It writes digits in reverse order without
a trailing terminator. Alphabet addition truncates to a byte, and its
remainder comparison is signed on the low 32-bit word, preserving behavior
even for radices above `INT32_MAX`. The low result word is the digit count and
the high result word is the original buffer pointer.

The original calls the EABI division wrapper rather than the raw unsigned
division algorithm. This matters for radix zero: the wrapper yields quotient
zero/max and zero remainder. The digit loop continues writing zero digits,
rather than validating the radix or returning an error. An initial differential
test caught the difference from calling the raw recovered division algorithm;
the target now explicitly preserves the wrapper's zero-divisor branch. Radix
one with a positive value also continues until an external fault. Tests compare
the written prefix before the output crosses mapped SRAM.

The forwarding adapter uses actual volatile 32-bit context words: increment
the wrapping count at offset8, then read the callback and user context at
offset0/4, then call the real function pointer. It preserves the full 32-bit
character argument and callback result. This last behavior was absent from
the native host API's void return, so the target uses a dedicated adapter.

The callback formatter delegates to the recovered shared formatter with
`memory=NULL`, which selects actual volatile target byte/word loads, and a
direct callback invocation adapter. No host reader substitutes for ARM memory.
This retains the original restricted format grammar, embedded NUL output,
32/64-bit argument alignment, `%hhd` zero-extension quirk, string-length
prescan, and callback-visible future format/argument/string mutation. It adds
no terminator and does not suppress invalid target-memory faults.

## Executable tests

`tools/build_format_core_target.py` builds a relocated test ELF with these
adapters, `src/format.c`, our recovered arithmetic C/ABI source, and explicitly
test-only callbacks/memory helpers. It links no installed runtime archive and
records source/compiler/ELF hashes and entry mappings. Shared formatter source
was not modified for this checkpoint.

`tests/test_format_core_target.py` executes both original and compiled ARM
instructions. The user callbacks are compiled C functions at identical
function-pointer addresses on both sides, not Python substitutes. The
candidate's original-image mapping is read-only and non-executable.

The **10 passing tests** cover values from zero through `UINT64_MAX`, random
64-bit values, ten radices including extreme unsigned values, four alphabet
offsets, the zero/one-radix fault prefixes, wrapping callback counts, callback
function/context mutation, callback return values, exact forwarding read/write
order, malformed context fault after increment, the full format/length/flag
matrix, native variadic-word widths and eight-byte alignment, mutable strings,
future format/argument mutation, binary NUL output, and invalid callback or
argument/string-memory faults. Empty format text does not invoke an invalid
callback or read the variadic memory.

Comparisons check returning R0 (and R1 for8fcc), callee-saved registers,
unchanged PRIMASK, persistent RAM through `0x20000cff`, exact persistent-RAM
write traces, and actual callback records. Stack scratch is excluded. A
dedicated trace confirms `%u/%llu` reads the three required variadic words at
the original widths and alignment.

The scoped report
`analysis/format-core-target-test-instruction-coverage.json` records **319/319
identified original instructions** across the three entries. ELF and manifest
are under `build/format-core-target/`. This is finite executable evidence,
not universal equivalence, a cycle-timing proof, or a production flash image.
Arbitrary aliases into changed private stack frames and callbacks that inspect
or corrupt those frames remain outside this checkpoint's evidence.
