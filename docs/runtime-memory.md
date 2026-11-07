# Memory and string runtime reconstruction

`src/runtime_memory.c` reconstructs ten routines directly from the original
instructions, with fixed 32-bit length arguments and unsigned-byte comparisons:

| Original entry | Replacement |
| --- | --- |
| `0x263c` | `syscon_rt_strcmp` |
| `0x2650` | `syscon_rt_strlen` |
| `0x972c` | `syscon_rt_memcmp` |
| `0x9748` | `syscon_rt_memcpy` |
| `0x975a` | `syscon_rt_memset` |
| `0x9828` | `syscon_rt_strchr` |
| `0x9890` | `syscon_rt_strncmp` |
| `0x98b4` | `syscon_rt_strncpy` |
| `0x98dc` | `syscon_rt_strrchr` |
| `0xa8b0` | `syscon_rt_memchr` |

Four test groups compile the replacements to Cortex-M0+ instructions and compare
return registers and complete memory regions with original execution. Cases cover
zero lengths, byte truncation, unaligned pointers, comparison differences, early
NULs, strncpy padding, and the original memcpy's forward-copy overlap behavior.
No host libc implementation supplies the compared result.

An original strrchr quirk is intentionally preserved: its initial zero test uses
the entire int, but strchr subsequently truncates it to a byte. A nonzero multiple
of 256 repeatedly searches for NULs beyond the string. A negative test confirms
that both original and rebuilt ARM eventually fault at the mapped SRAM boundary.
Such invalid memory access is exercised only in the emulator, not native C.

Ordinary calls require accessible memory for all reads/writes. These routines
do not add memory validation, model wrapping address-space accesses, or prove
all possible corrupt-pointer behavior. Native host pointer width differs; ARM
tests use the actual 32-bit pointer ABI. Incidental scratch-register values are
not part of the comparison. Soft-float, division, scanning, allocation and
other runtime bodies have separate implementations and evidence in the runtime
module documents and reconstruction ledger.

`tools/verify_runtime_binary.py` separately records exact emitted bytes for each
routine. Functions containing unresolved relocations cannot receive an exact
linked-body match. These measurements are not a complete linked firmware image.
