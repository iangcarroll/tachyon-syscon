# Formatting and UART logging

`src/runtime/format.c` reconstructs the formatter at `0x9038`, integer conversion at
`0x8fcc`, and bounded-output semantics of `0x92ac`. The interface takes a virtual
32-bit ARM format-string pointer and va_list pointer. A checked target-memory
reader preserves pointer width, 8-byte alignment for 64-bit arguments, and access
to strings in the original image/RAM. It does not substitute the host libc printf.

Recovered behavior includes `%c`, `%s`, signed/unsigned decimal, octal, hex,
pointers, `%%`, length modifiers and the `+`, space and `#` flags. Width, precision,
floating-point formats and left justification are not supported by the original;
they are emitted as literal text. `%hhd` zero-extends its byte even though the
conversion is signed. `%p` always emits a lowercase `0x` prefix, including zero.
Output length counts bytes that would have been emitted, while buffers are
terminated and truncated exactly as in the original.

`tests/models/logging.c` implements:

- `0x5edc`: SG560D UART1 formatting into a zeroed 128-byte buffer, sending only
  through the first NUL and then a separate CRLF.
- `0x8e8c`: optional colored UART0 diagnostic logging, signed 64-bit timestamp
  prefix, first a 32-byte message attempt and then a 256-byte attempt, adding
  `...` at bytes 252–254 when the message exceeds 255 bytes. The color setting is
  sampled twice, so opening/closing color sequences can differ if it changes.

Six differential groups passed. The scoped report
`analysis/format-test-instruction-coverage.json` records all 268 discovered
instructions in the main formatter exercised, all 34 in the SG560D wrapper, and
all discovered instructions in its integer/output helpers. This is an instruction
exercise count, not a proof of every format/path combination.

The native interfaces expose va_list explicitly rather than relying on a 64-bit
host's variadic calling convention. Tests execute the original wrapper with real
ARM register/stack argument placement, compare complete output buffers including
untouched bytes, and compare ordered UART writes, timestamp/color reads and binary
output. Tests include null destination, zero/one-byte capacities, truncation,
embedded NULs, integer extremes, and arguments aligned at offsets zero and four.

## Remaining boundaries

The original diagnostic logger passes the full required prefix length to UART
even if its 32-byte prefix buffer truncated. A sufficiently long tag/timestamp
combination therefore reads beyond that buffer into the original stack. The
native adapter returns `-2` at this boundary instead of reading outside its host
buffer. Missing variadic arguments also require the original caller's exact
stack contents; the memory reader can represent supplied target bytes, but the
reconstructed callers do not yet reproduce all such stack layouts. In particular,
corrupt configuration values and user-supplied SET_RGB format tokens are not
claimed fully equivalent for missing arguments.

The [UART HAL](uart-hal.md) reconstructs transport initialization.
[Target wrappers](arm-rebuild.md) now use real compiler-generated ARM variadic
argument handling and are differentially executed. Their code layout and full
image linking remain unverified. No logging test touches physical UART hardware.

## Runtime provenance candidates

`tools/fingerprint_runtime.py` searches the installed ARM toolchain's `libgcc.a`
and `libc_nano.a` using exact bytes or explicitly masked relocation fields. The
initial result has 70 candidates at 39 original addresses, including 13 exact
matches without ignored relocations. `analysis/runtime-fingerprints.json` records
archive hashes and every ignored-byte count. Short generic wrappers can match
multiple unrelated symbols; masked matches remain candidates until their branch
and data targets are resolved. This does not establish a fully rebuilt runtime.

## Generic callback output and independent review

`syscon_format_forward` reconstructs `0x9028` with the original three-word target
context: callback address, callback context, and wrapping 32-bit count. It
increments the count before invoking the callback and forwards the entire 32-bit
character argument. The callback return value is ignored. The host bridge takes
the target callback address explicitly rather than treating it as a host pointer.
`syscon_vformat_callback` exposes `0x9038` directly: every emitted byte reaches the
sink, including embedded NUL, with no trailing terminator.

The original `%s` conversion measures the entire string before the first output
callback and then rereads exactly that many bytes. The shared C core now does the
same. A differential test changes `ABCDE` to `A\0XDEmore` during its first
callback: both implementations emit precisely `A\0XDE`, including the new NUL
and excluding the extension. Further tests change a future format specifier and
argument during output, proving those reads remain live rather than snapshotted.

`tests/test_format_callback.py` compares the original callback instruction paths
with the native C implementation. Coverage includes callback-visible counter
preincrement/wrap, callback modifications of future callback address/context/count, full-width
forwarded characters, target argument alignment, flags and integer sizes, and
binary output. A missing format/argument/string byte makes the checked host
interface return `complete=0`; it does not invent data or claim equivalence to a
target memory fault. Arbitrary callbacks can be represented by the bridge, but
these tests do not emulate every callback implementation, recursive callback
stack shape, or deliberate corruption of the formatter's private stack.

The review also identified an off-by-one in the reconstructed diagnostic logger's
unsupported boundary. A required prefix length of exactly 32 does not overread:
the original sends 32 bytes, including the forced NUL at byte 31. Only required
lengths greater than 32 cross the local prefix buffer. The regression compares
31- and 32-byte prefix output against the original and checks that the host
explicitly rejects a 33-byte prefix. The original's stack-dependent overread
remains unimplemented.
