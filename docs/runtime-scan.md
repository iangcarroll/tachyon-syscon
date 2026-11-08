# ARM32 runtime scanning and formatting

The runtime parser reconstruction executes as compiled Cortex-M0+ C in the
relocated, nonflashable test image. It never calls the host's libc or executes
original firmware instructions in the candidate. `tools/build_runtime_scan_image.py`
links the rebuilt scanner, formatter parser, stream helpers, allocator, memory
helpers, and reentrancy accessors together, including source-backed integer
arithmetic and jump-table ABI helpers; no `libgcc` archive is linked. Original code remains executable only
in the separate reference CPU.

| Original | Reconstructed entry |
|---|---|
| `0x976c` | `syscon_rt_snprintf` |
| `0x97d4` | `syscon_rt_sscanf` |
| `0x9844` | `syscon_rt_strncasecmp` |
| `0x9904` | `syscon_rt_strtol_core` |
| `0x9a20` | `syscon_rt_strtol_r` |
| `0x9a28` | `syscon_rt_strtol` |
| `0x9b24` | `syscon_rt_vfprintf` (ARM ABI glue plus seeded C core) |
| `0x9ddc` | `syscon_rt_vfscanf` |
| `0xa3d8` | `syscon_scan_chars` |
| `0xa494` | `syscon_scan_integer` |
| `0xa69c` | `syscon_scan_sccl` |

These are the image's Newlib nano routines. They are separate from the custom
formatter at `0x9038`; in particular nano printf supports width and precision.
The source is in `target/runtime/runtime_scan.c`, `target/runtime/runtime_scan_wrappers.c`, and
`target/runtime/runtime_scan_printf.c`, plus `target/runtime/runtime_scan_abi.S` for the original
stack-dependent entry frames, with declarations in `include/runtime_scan.h`.

## Source provenance and license

The retained upstream reference is Newlib tag `newlib-4.3.0`, commit
`9e09d6ed83cce4777a5950412647ccc603040409`, from the
[Newlib source repository](https://sourceware.org/git/newlib-cygwin.git).
`vendor/newlib-4.3.0/manifest.json` pins each downloaded file's path, immutable
mirror URL, and SHA-256; bytes fetched through the tag and immutable commit were
compared. Original ARM disassembly confirms the field offsets, parser flags,
conversion dispatch, prefixes, 350-byte scan buffer, and absent weak float
handlers. This establishes the source family and tested behavior, not the exact
version or compiler flags used to build Particle's binary. The existing runtime
fingerprint report independently matches the `nano-svfscanf` helper family.

The scanner, scanset builder, and strtol implementation adapt upstream code.
BSD/University of California and ARM notices are retained in the adapted files
and unmodified references. This software includes code developed by the
University of California, Berkeley. The printf parser is rewritten around the
recovered state layout and retains the upstream notices as well.

## Recovered ABI and observable quirks

The original uses the small-reentrancy variant of Newlib's 104-byte `FILE`.
The installed toolchain's default `FILE` differs, so the reconstruction defines
and statically checks the target layout: pointer at 0, remaining read/write
counts at 4/8, flags at 12, main buffer at 16, reent pointer at 28, pushback buffer
at 52, saved position/count at 60/64, and inline pushback bytes at 68. The scan
state is 388 bytes: seven 32-bit fields, a 350-byte conversion buffer, then
ungetc/refill pointers at 380/384. Both target pointers and `long` are 32 bits.
The build uses `-fwrapv`; output count and width wrap are not host 64-bit math.

The wrappers use real ARM variadic argument placement. They call the reconstructed
parsers, which call reconstructed pushback/refill, signed/unsigned conversion,
padding, writer, and allocator functions. Input/output bytes, errno, end pointers,
stream state, scan state, character tables, and argument-list advancement are
compared against the original. The character classification table is still read
from the pinned image at `0xe127`; it is data, not executable original code.

Strtol saturates to signed 32-bit limits on overflow and sets errno 34 in the
explicit reent object. An invalid base sets errno 22 in the global reent object
and leaves the end pointer untouched, even when the explicit reent differs.
The scanner recognizes only a single `h`, `l`, or `L` length modifier; repeated
modifiers follow the original fallback behavior. Integer scanning supports
prefix rollback through real ungetc, zero skipping beyond the temporary buffer,
assignment suppression, and the original width bookkeeping. Scansets preserve
inversion, literal `]`/`-`, chained ranges, and malformed termination behavior.
Absent scanf floating support performs no float conversion or argument consumption.

## Original stack-dependent printf behavior

The original nano printf float handler is absent. A float conversion consumes an
8-byte aligned argument, emits nothing, and adds a stale conversion-length word
to the result. Before any integer conversion that word is uninitialized at
original entry SP minus 136. After an integer conversion it holds that conversion's
length. The original machine code also bypasses the `n == -1` check in the absent
float branch: a seed of `0xffffffff` is added to the result and parsing continues.
A straightforward adaptation of upstream C missed that compiler-produced detail;
the original ARM differential test exposed it.

`syscon_rt_vfprintf_seeded` accepts this original conversion-length word and the initial size word explicitly and matches
the tested original behavior for arbitrary seeds, including signed extremes.
`syscon_rt_snprintf_seeded` provides a variadic wrapper with an explicit seed;
its extra named parameters change argument placement, so callers must use its own
AAPCS signature. A second stale field affects alternate octal: the integer helper checks precision
against the previous `print_state.size` before assigning the current digit count.
Before any integer conversion this size word is uninitialized at incoming SP minus
104; later conversions reuse the prior field size. Tests vary that initial word
through signed extremes for `%#o`, precision/width combinations, preceding strings,
integers, and absent floats. The ABI shim captures this second word as well.

The ordinary original-ABI entry `syscon_rt_vfprintf` now samples incoming SP minus
136 (and initial size at SP minus 104) in a small ARM assembly shim before any reconstructed C prologue can overwrite
it. The original's earlier callees use frames below its SP; its seed remains above
those frames until an integer conversion replaces it. `syscon_rt_snprintf`
reproduces the original 136-byte wrapper frame, saved registers, and saved
variadic arguments, so the nested seed is read from its caller's SP minus 272, with initial size at caller SP minus 240.
Tests seed both incoming stacks independently and compare the ordinary ABI entries
for first/repeated floats, preceding literals/integers, signed extreme seeds,
output bytes, return counts, and errno. This closes the previously identified
first-float gap for those tested ABI entry conditions without inventing a seed.

The explicitly named convenience APIs `syscon_rt_vfprintf_checked` and
`syscon_rt_snprintf_checked` retain an `INT_MIN` failure boundary when a first float or alternate-octal conversion
requires unavailable stack state. They are not the mapped original ABI entries.
The seeded and checked convenience APIs are auxiliary interfaces; the mapped ARM
entries preserve the original stack-seed behavior. Full equality of all private
stack bytes/register scratch values remains outside the current comparison;
public state and both observed stack-dependent reads are covered.

## Validation and limits

The final parser/stdio/heap run passed **22 groups in 28.47 seconds**, including
13 parser groups. `tests/test_runtime_scan.py` exercises all eleven mapped entries, including both
variadic wrappers and direct helper state. It covers every base 2–36 and invalid
bases, signed limits and overflow, end-pointer/errno separation, all byte values
in case-insensitive comparison, numeric prefixes and widths, literal matching,
whitespace, suppression, `%n`, scansets, EOF/read-error behavior, output widths,
precision, truncation, NULs, allocation failure, and the stack-seeded float branch.
A deliberate corruption of the rebuilt strtol routine makes the integrated scanf
comparison fail, verifying that the flow uses the actual reconstructed converter.
Normal integration comparisons replace no dependency endpoints with hooks.

Direct helper tests place the 388-byte state and 256-byte table in an additional
local test RAM page to keep them separate from the original stack. This is a test
fixture, not a claim that the MCU has that extra RAM. String wrapper tests use the
ordinary 4 KiB target RAM. Parser tests also exercise allocation success from an initialized free list and
literal-output growth failure with no allocator hooks. Further heap growth paths
are covered by
`tests/test_runtime_heap.py` and `tests/test_runtime_stdio.py`; the original stock
sbrk endpoint always fails. Arbitrary callbacks that change scanner suppression
flags halfway through a conversion can expose original uninitialized registers;
that corrupted-state behavior is not claimed equivalent. Unterminated format or
input buffers can still fault or exhaust an instruction budget, as on the
reference CPU. No firmware was flashed and no physical I/O was performed.

The dedicated passing run exercises 1214 of 1228 currently identified instructions
in these eleven entries. The remaining 14 are the absent weak printf/scanf float
handler branches and the scanner helper return-2 dispatch, which neither linked
integer nor character helper can return. This is instruction reachability for the
pinned image and tested state domain, not proof over all possible memory corruption.
`analysis/runtime-scan-test-instruction-coverage.json` records the exact addresses;
`analysis/runtime-scan-mapping.json` supplies the entry-to-source mapping.
