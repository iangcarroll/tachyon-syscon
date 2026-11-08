# Reconstructed FILE and integer formatting support

`target/runtime/runtime_stdio.c` implements these seven runtime helpers with original
32-bit target pointers. The interfaces in `include/runtime_stdio.h` use opaque
FILE/reentrancy pointers so the scanner can share its explicit target structures.

| Original | Replacement |
| --- | --- |
| `0x9a60` | `syscon_rt_swrite` |
| `0x9d24` | `syscon_rt_sungetc_r` |
| `0x9d9c` | `syscon_rt_ssrefill_r` |
| `0xa0d4` | `syscon_rt_printf_common` |
| `0xa1b4` | `syscon_rt_printf_integer` |
| `0xa714` | `syscon_rt_strtoul_r` |
| `0xa830` | `syscon_rt_submore` |

The FILE layout follows the image's small-reentrancy ABI: current pointer at
0, read/write counts at 4/8, 16-bit flags at 12, main buffer at 16/20,
pushback buffer at 52/56, saved pointer/count at 60/64, and inline three-byte
pushback storage at 68–70. It is not the host libc FILE structure.

The writer preserves fixed-buffer truncation, dynamic allocation versus
reallocation, 1.5-times growth, flags, and failure handling. Reallocation failure
frees the old dynamic buffer before marking the stream error. Pushback can reuse
a matching preceding byte, then uses inline storage, then allocates 1024 bytes,
and subsequently doubles the buffer. Refill frees dynamic pushback storage,
restores saved unread input when available, or marks EOF. Allocation follows the
exact heap model documented in `docs/runtime-heap.md`.

Integer formatting uses the recovered state offsets (flags 0, precision 4,
digit precision 8, width 12, size 16, cumulative count 20, conversion 24, blank/zero
25/26, digit buffer 27–66, sign/prefix bytes 67–69). It preserves signs, alternate
hex/octal prefixes, short/long interpretation on ARM32, precision and padding,
`%n` writes, strings, character conversions, unknown-code fallback, and callback
order including zero-length writes. Exactly `-1` from the output callback stops
formatting; another negative value does not automatically mean failure.

`syscon_rt_strtoul_r` follows the image's character table, sign/base/prefix
handling, end pointer and unsigned saturation behavior. Overflow sets the supplied
reentrant errno to 34. Tests include zero/invalid bases, incomplete prefixes,
large magnitudes and unsigned negation; no host strtoul supplies expectations.

Six stdio groups, together with three heap groups, passed against original ARM
instructions. They compare returned values, full FILE/format-state bytes,
argument-pointer advancement, output callback records, heap contents and errno. The dedicated report `analysis/heap-stdio-reference-coverage.json`
records instruction exercise separately from semantic validation.
The integrated flow executes original integer formatting → common padding → FILE
writer → allocator, compared with the reconstructed equivalents. Scripted output
failures exercise stopping at individual callback positions. A separate path
uses the image's real always-failing sbrk endpoint.

All tests are local CPU emulation. A scripted successful heap is a deliberately
supplied environment, not an invented success result for the original sbrk.
Malformed pointers or huge widths can still fault or run for a long time as in
the original; no complete corrupt-memory/path proof is claimed. The C bodies
preserve target interfaces but are not asserted byte-identical. The upper
snprintf/sscanf/vfprintf/vfscanf parsers and scanner token helpers are maintained
separately in the runtime-scan module.
