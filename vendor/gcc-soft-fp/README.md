# Vendored source provenance

These files were downloaded unmodified from the GNU project's official
`gcc-mirror/gcc` mirror, release tag `releases/gcc-13.3.0`.
`provenance.json` records each exact URL and SHA-256. This pins the replacement
sources; it does not assert that the original Particle firmware used that
release or those exact compiler options.

The selected `libgcc/soft-fp/*.c` operations, their macro headers, ARM
`sfp-machine.h`, and `include/longlong.h` are compiled from source by
`tools/build_runtime_arithmetic.py`. Installed `libgcc.a` is not linked.
`reference/libgcc2.c` is provenance/reference only, not compiled; its
`TARGET_HAS_NO_HW_DIVIDE` unsigned 64-bit align/subtract algorithm informed
`src/runtime/runtime_arithmetic.c`. That adapted file preserves defined ARM behavior
for zero-divisor internal calls explicitly, instead of relying on undefined
C full-width shifts.

Keep the copyright notices and licenses with these sources. Most soft-fp
files and `longlong.h` carry LGPL-2.1-or-later with the additional linking
permission in their headers. `libgcc2.c` carries GPL-3.0-or-later with GCC
Runtime Library Exception 3.1. Full upstream license files are included as
`COPYING.LIB`, `COPYING3`, and `COPYING.RUNTIME` (`COPYING` is also preserved).
Read each original file header for its applicable notice. Locally adapted
source is separate from these unmodified upstream files.
