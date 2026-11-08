# Standalone callback helper entries

`target/runtime/callback_helpers.c` implements original ARM interfaces for the three
helpers previously counted only as folded caller behavior:

| Original | Target entry |
| --- | --- |
| `0x3f08` | `syscon_target_failure(command, reason, print)` |
| `0x9012` | `syscon_target_buffer_output(character, context)` |
| `0x9026` | `syscon_target_null_output(character, context)` |

The failure helper preserves callback order, pointer identity (including the
original immutable FAIL pointer), and the final callback return value. The
optional command is skipped only for a zero pointer; the helper does not inspect
or sanitize the pointed-to strings. Callbacks obey AAPCS callee-saved register
rules; they are not a host printer adapter.

The output context has three 32-bit words: buffer address, capacity, used count.
The target reads used before capacity. It reads the buffer pointer only when
unsigned used is less than capacity, then increments used before storing the
low byte of the character. Volatile accesses retain that order even when the
destination aliases any context byte. Address addition explicitly wraps at
32 bits. The original full character word is returned. The null sink returns
that same word without accessing its context.

Five compiled-ARM differential test groups compare original execution, all
context/output bytes, ordered memory reads/writes, return values, and AAPCS
callee-saved registers. Tests cover self-aliasing contexts, arbitrary 32-bit
counts/capacities/characters, wrapped effective addresses, inaccessible buffer
pointers that must not be read when full, and faults after the count has already
been incremented. Callback dependencies in failure-helper tests are explicit
ABI-respecting external boundaries.

These tests remove the missing standalone implementations. They are not a
universal equivalence proof, complete interrupt-interleaving proof, or proof of
full firmware integration. The isolated loader uses extra harness memory;
physical-image integration remains a separate requirement.
