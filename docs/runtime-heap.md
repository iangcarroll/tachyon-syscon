# Reconstructed nano heap

`target/runtime_heap.c` supplies seven original entry points using the original
32-bit pointer ABI and RAM globals. It is target-only C; host libc allocation is
not used as an oracle or substitute.

| Original | Replacement |
| --- | --- |
| `0xa8ec` | `syscon_rt_free_r` |
| `0xa980` | `syscon_rt_malloc_r` |
| `0xaa3c` | `syscon_rt_realloc_r` |
| `0xaa88` | `syscon_rt_sbrk_r` |
| `0xaaac` | `syscon_rt_malloc_lock` |
| `0xaabc` | `syscon_rt_malloc_unlock` |
| `0xaacc` | `syscon_rt_malloc_usable_size_r` |

The free-list head remains at `0x20000818`, initial heap pointer at `0x2000081c`,
global errno at `0x20000810`, and lock object at `0x20000814`. Lock wrappers call
the separately reconstructed no-op lock endpoints. Chunks retain their four-byte
headers, address-sorted free list, minimum twelve-byte allocation size,
eight-byte returned-pointer alignment, and negative alignment adjustment header.
Allocation splits suitable free chunks from their high end; free coalesces
adjacent chunks and reports overlap with errno 12.

The pinned image's sbrk endpoint (`0x76f0`) always returns `-1`. The default
`syscon_rt_sbrk` preserves this and is explicitly weak so a different backing
implementation can be supplied. `_sbrk_r` clears global errno first and copies it
to the supplied reentrancy object only when the call fails and global errno
becomes nonzero. Tests distinguish the actual always-failing endpoint from a
scripted hypothetical backing store; successful allocation tests are not evidence
that the original image has a working OS allocator.

The original realloc behavior is preserved: growing an allocation copies the
**requested new size**, rather than the old allocation size, before freeing the
old block. This can read adjacent metadata or beyond the old allocation. Tests
compare the resulting complete emulated arena; the overread is not executed on
live hardware or in native host C.

Three heap groups and six related stdio groups passed together, comparing actual
original ARM code against recompiled Cortex-M0+ C. Heap scenarios cover every
initial alignment, repeated allocation/free/reallocation, splitting/coalescing,
zero-size/null cases, failure at individual sbrk calls, injected errno, overlap
rejection and large-size arithmetic boundaries. They compare return values, the
complete 64 KiB emulated arena, allocator globals, reentrant errno bytes and
ordered sbrk transactions. The scoped report `analysis/heap-stdio-reference-coverage.json` records all 935
discovered instruction addresses across these seven heap and seven stdio entries
exercised; this is not branch/path completeness. The stdio integration adds integer formatting through
real FILE writes and these allocator routines, including failed growth.

`tools/heap_stdio_oracle.py` builds the target modules with the reconstructed
memory functions and `target/runtime_support.c` lock/memmove functions. Compiler
arithmetic helpers are linked from the independently reconstructed
`src/runtime_arithmetic.c` and `target/runtime_arithmetic_abi.S`; no installed libgcc or host arithmetic runtime is
linked into this test image. The build keeps the sbrk call boundary visible.

This model does not validate real heap placement, stack/heap collision detection,
concurrency, memory-protection faults, arbitrary corrupted free-list graphs or
address-space wrapping. Successful byte/state comparisons do not constitute a
complete machine-code match or a safe-to-flash image.
