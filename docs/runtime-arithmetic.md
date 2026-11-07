# Arithmetic runtime source reconstruction

All 35 identified entries below `0x263c`, the switch helper at `0x2660`, and
ten additional comparison ABI entries missed by the initial function
inventory have direct reconstructed-source ARM differential tests. The exact
machine-readable mapping is `tools/runtime_arithmetic_mappings.py` (46 entries).
This is a source replacement checkpoint for this region, not a complete
firmware equivalence or flash-safety result.

## Source and ABI

`src/runtime_arithmetic.c` implements integer division, multiplication, leading
zero counts and float-bit comparisons in C. It avoids native floating point,
undefined shifts and signed overflow. The unsigned 64-bit division algorithm
is adapted from GCC's `TARGET_HAS_NO_HW_DIVIDE` implementation, with explicit
full-width-shift behavior for direct zero-divisor calls.

`target/runtime_arithmetic_abi.S` contains the small helpers whose interfaces
cannot be expressed as ordinary C functions: switch dispatch using the table
following LR, flag-producing float comparisons, the identity divide-by-zero
handler, and unsigned 64-bit division returning quotient in R0/R1 and remainder
in R2/R3. `target/runtime_arithmetic_float.c` preserves the original unsigned
float-to-integer conversion policy by composing reconstructed signed
conversion and subtraction.

Floating-point arithmetic and signed conversions compile the reviewed GNU
soft-fp source in `vendor/gcc-soft-fp`. The source was obtained from the
[official GCC mirror at GCC 13.3.0](https://github.com/gcc-mirror/gcc/tree/releases/gcc-13.3.0/libgcc/soft-fp),
using its [ARM machine definitions](https://github.com/gcc-mirror/gcc/blob/releases/gcc-13.3.0/libgcc/config/arm/sfp-machine.h).
Operation semantics were cross-checked against
[GCC's documented runtime interfaces](https://gcc.gnu.org/onlinedocs/gccint/Soft-float-library-routines.html)
and the captured instructions. Source identity is not inferred merely from
an installed archive fingerprint. The replacement compiler release is known;
the original compiler version remains unproven.

Each upstream file has its URL and content hash recorded in
`vendor/gcc-soft-fp/provenance.json`. Original license notices and license texts
are preserved; see the vendor README. The adapted division source carries the
GCC runtime exception notice. No installed runtime object is substituted for
these source implementations.

| Original entry | Source behavior |
| --- | --- |
| `0xc0`, `0xd4`, `0x2660` | Signed byte, unsigned byte, signed halfword switch dispatch |
| `0xe8`, `0x1f4` | Unsigned 32-bit quotient/remainder in R0/R1 |
| `0x1fc`, `0x3c8` | Signed 32-bit quotient/remainder in R0/R1 |
| `0x3d0` | Divide-by-zero hook, identity return |
| `0x448`, `0x550` | ARM 64-bit quotient/remainder wrapper and C pointer-result division |
| `0x488` | Low 64 bits of 64-bit multiplication |
| `0x23d0`, `0x240c` | Leading-zero counts, including zero input |
| `0x6e8`, `0xa24`, `0xdb4`, `0x1000` | Float32 add, divide, multiply, subtract |
| `0x14bc`, `0x1b34` | Float64 add and subtract |
| `0x135c`, `0x2258` | Float32/float64 to signed 32-bit integer |
| `0x4e4`, `0x514` | Float32/float64 to unsigned 32-bit integer, original composition |
| `0x139c`, `0x1438`, `0x22c4` | Signed/unsigned 32-bit integer to float32; float32 to float64 |
| `0xc54`, `0xca0`, `0xd2c` | Float32 inequality; ordered comparison with -2/+2 for unordered |
| `0x2424`, `0x24a8`, `0x2574` | Float64 equivalents |
| `0x3ec`, `0x3f8`, `0x40c`, `0x420`, `0x434` | Float32 Boolean eq/lt/le/gt/ge |
| `0x2374`, `0x2380`, `0x2394`, `0x23a8`, `0x23bc` | Float64 Boolean eq/lt/le/gt/ge |
| `0x3d4`, `0x3dc`, `0x2354`, `0x2364` | Reversed/normal float32 and float64 condition-flag comparison |

The interfaces preserve these notable behaviors:

- 32-bit division by zero returns zero quotient and the input numerator as
  remainder. Signed `INT_MIN / -1` returns the wrapped quotient without C UB.
- The public 64-bit ABI divide wrapper returns all-ones quotient for nonzero
  numerator divided by zero, zero for zero/zero, and leaves the zero divisor
  words in R2/R3. Direct internal `0x550` zero-divisor behavior is separately
  tested and is not replaced with the public-wrapper policy.
- Signed float-to-int overflow and NaNs follow the firmware's sign-dependent
  saturation. Unsigned conversion follows its original signed-conversion
  composition, including negative and NaN inputs; it is not a host-language
  cast assumed to behave identically.
- Quiet/signaling NaN payloads and signs, signed zeros, gradual underflow,
  infinity operations and round-to-nearest ties are compared as raw bits.
- Comparison flag helpers preserve their argument registers (or the original
  reversed argument ordering), callee-saved registers and NZCV result flags.

## Differential tests and instruction exercise

`tests/test_runtime_arithmetic.py` compiles a fresh isolated ARM ELF using
`tools/build_runtime_arithmetic.py`, then runs it through
`tools/arm_rebuild_oracle.py`. The ELF links with `-nostdlib` and **without
`-lgcc`**, so undefined arithmetic dependencies cause a link failure. The
original image is non-executable in the candidate emulator; candidates cannot
fall back to original instructions. The build emits a source/compiler/ELF
hash manifest and remains explicitly nonflashable, with relocated code and
additional harness RAM as described in `arm-rebuild.md`.

The suite covers all mapped entries with raw-bit results compared against the
original emulator, register preservation, direct remainder memory writes,
condition flags, signed switch offsets and original return quirks. It includes
seeded random inputs plus structured exponent gaps, adjacent significands,
cancellation, carry propagation, tie rounding and boundary conversions.
This avoids relying only on random cases that rarely reach precision-boundary
paths. The final scoped checkpoint passed **32 tests in 10.16 seconds**, with
tracked inputs unchanged during execution. An earlier mixed checkpoint also
passed four native timer regressions, proving compatibility with the shared
native-library build. The final suite includes linkable ABI alias checks and
five exact-body comparisons in addition to the arithmetic cases.

The historical scoped report `analysis/runtime-arithmetic-test-instruction-coverage.json`
recorded **4,474 / 4,483** identified original instructions exercised before the
final static-boundary corrections. Current accounting is in the full-suite
checkpoint and reconstruction ledger. Every mapped entry is exercised. The
original nine unexercised instructions are guards in generic soft-fp code:

- `0xa8a`: the fallback after testing the packed operand classes exceeds 15.
  Each operand class has two bits; combining the shifted first class with the
  second class always yields 0..15. Ordinary entry arguments cannot take it.
- `0xaca..0xad0`: division's rounding-overflow normalization. Finite nonzero
  operands normalize to integer significands `m,n` in `[2^23, 2^24-1]`.
  The normalized quotient is `m/n` or `2m/n`, below 2 by at least `2^-23`.
  Rounding up to 2 requires being within `2^-24`; hence this carry guard cannot
  fire for float32 operands. Subnormal inputs normalize to the same bound.
- `0xe7c..0xe82`: the high-word carry in generic wide multiplication. Each
  unpacked significand has fewer than 27 bits. Its upper 16-bit-split portion
  is below `2^11`, so the cross-product sum plus low-product carry is below
  `2^29`, and cannot wrap a 32-bit word. This generic carry guard is unreachable.

The final static audit additionally corrected Ghidra's ARM-mode decoding of
`0xbc0` and restored 47 omitted Thumb instructions to float-divide's body.
The full-suite execution reached 36 of them. The other 11 are generic dispatch
residuals: `0xa94/0xa96` and `0xbca/0xbcc` are targeted only by second-table
indices 3, 7, 11, and 15, while that table is entered only for denominator
classes 1 (zero) or 2 (infinity). On reachable paths to `0xa9e`, the class in
R10 is always 3 (NaN), making `0xaa4` and `0xaac..0xab6` unreachable. These are
ordinary-entry bounds, not an excuse to discard reachable untested code. See
`static-inventory-gaps.md` for table addresses and excluded literal/padding bytes.

These bounds concern normal entry execution with immutable inputs, not
asynchronous corruption of temporary registers. We do not inject impossible
mid-function register states simply to raise an instruction count.

Run from `syscon-re`:

```sh
.venv/bin/python tools/build_runtime_arithmetic.py
SYSCON_COVERAGE_OUTPUT=analysis/runtime-arithmetic-test-instruction-coverage.json \
  .venv/bin/python -m pytest -q tests/test_runtime_arithmetic.py
```

No board, USB adapter, debug probe or flash was accessed. Tests demonstrate
finite differential coverage, not proof across every bit combination. The
rebuilt instruction streams generally differ from the original; there is no
whole-image byte identity, original placement, boot integration or physical
RAM-fit claim here.

## Linking consumers

For unsigned/signed 32-bit division and 64-bit multiplication, compile
`src/runtime_arithmetic.c` with `-mcpu=cortex-m0plus -mthumb -mfloat-abi=soft`
and `-Iinclude`, then link that object instead of installed `libgcc`. The ARM
build exports the verified `__aeabi_uidiv`, `__aeabi_uidivmod`, signed variants,
`__aeabi_lmul`, leading-zero and comparison symbols. Add
`target/runtime_arithmetic_abi.S` for `__aeabi_uldivmod`, condition-flag compare
helpers and the three `__gnu_thumb1_case_*` dispatch symbols. Source consumers
requiring soft-float operations should use the complete source set in the
builder. Native builds intentionally omit ARM ABI aliases; arithmetic test
coverage is actual compiled ARM execution, not host floating-point behavior.
