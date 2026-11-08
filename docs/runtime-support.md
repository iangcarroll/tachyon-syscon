# Runtime glue and character tables

`src/runtime/runtime_support.c` covers ten target-only entries. ARM tests execute the
recompiled source against the original with 32-bit pointers and memory addresses.

| Original | Replacement |
| --- | --- |
| `0x969c` | `syscon_rt_arm_atexit` |
| `0x96aa` | `syscon_rt_atoi` |
| `0x96b8` | `syscon_rt_cxa_atexit` |
| `0x971c` | `syscon_rt_isalnum` |
| `0x9a40` | `syscon_rt_toupper` |
| `0x9a54` | `syscon_rt_getreent` |
| `0xa828` | `syscon_rt_strtoul_alias` |
| `0xa8ac` | `syscon_rt_lock_acquire` |
| `0xa8ae` | `syscon_rt_lock_release` |
| `0xa8c6` | `syscon_rt_memmove` |

The weak exit-registration function in the pinned image is absent (literal zero),
so both exit-registration interfaces return success without saving a callback.
The two low-level lock functions are actual no-ops; reconstructed heap wrappers
still call them in the original order. Reentrancy reads the linker-resolved `syscon_runtime_current` pointer. Its
100-byte context and three zero-filled stdio placeholders are declared in
`runtime_state.h`; these placeholders are not initialized UART drivers.
Startup restores this ordinary data on warm reset, as the original did.

Character classification implements the original ASCII flags directly in C,
independent of private ROM tables or the host locale. Differential tests cover
all 256 byte values and EOF, including poisoning the obsolete table. For
integers outside that domain, classification now returns zero and `toupper`
returns its input. This intentional boundary change replaces accidental reads
from unrelated firmware bytes; production callers use byte values.


Memmove preserves the original unsigned 32-bit overlap decision and copy order.
Tests compare full memory regions and return pointers across both overlap
directions, equal pointers, zero lengths and boundary sizes. Unmapped/wrapping
input pointers remain memory faults; no host-native invalid-pointer test runs.

Initial wrapper tests expose the strtol/strtoul dependency boundaries explicitly.
The combined runtime integration additionally links the reconstructed parsers,
FILE machinery, allocator, memory functions and integer arithmetic, without
installed libc or libgcc, and compares real atoi/strtoul alias calls.

These implementations preserve their defined observable ABI. Incidental
caller-saved registers are not guaranteed identical, and compiler-emitted bytes
are not claimed equal unless recorded in a binary comparison report.
