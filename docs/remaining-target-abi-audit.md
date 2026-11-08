# Remaining target-ABI audit

This audit reads the `target_abi` overlays in `analysis/reconstruction-ledger.json`, then checks current target files. The ledger's original `source` field often still names the historical host adapter; that field alone does not establish an implementation gap.

Outside ongoing SG560D, control-command and formatter work, the remaining distinctions are:

| Entries | Current state |
|---|---|
| `0x2738`, `0x7af4`, `0x7b10`, `0x7b44`, `0x7b60`, `0xaae0`, copied RAM executor | New original-ABI source and direct ARM tests in `flash_abi_target`; production image now binds config-storage calls to these direct entries and places the source RAM executor at the original address |
| `0x96d4` | New `target/app/runtime_init_target.c`; physical reset now calls it |
| `0x79f0` | Physical reset source in `target/physical/startup.c`; tested with explicitly labelled dependencies, not a complete rebuilt-board boot |
| `0x8e6c`, `0x8e7c` | Physical startup's UART wrappers use original bases and source UART IRQ body; mapping/integration evidence remains distinct from standalone original-instruction comparison |
| `0x76f0` | Already implemented as original always-failing `syscon_rt_sbrk` in `target/runtime/runtime_heap.c`; needs ledger target mapping, not another host-context implementation |
| `0x74f8`, `0x7ae8` | Already source target sleep/cycle helpers in `target/drivers/core_helpers.c`; fixed-cycle helper has separate emitted-byte evidence |
| `0x79e4`, `0x7bb8`, `0x7bcc` | Already direct source exception handlers in `target/drivers/fault_handlers.c`; no host context |
| `0x74e8` | Original raw modem sender belongs to ongoing SG target work |

After applying the current overlays and inspecting these files, no additional application function outside those scopes was found to exist solely as a host-context adapter. This is an audit of the identified function inventory, not a proof that the static inventory is exhaustive or that all target implementations are universally equivalent. Runtime memory/arithmetic/stdio/heap implementations already have actual target ABI tests, but their documented bounds and unresolved full-domain proof obligations still apply.

The remaining work is therefore integration and evidence as well as source coverage: finish/review active modules, resolve production code pointers, establish a complete-image stack bound, compare full reset/IRQ/application paths, and address counterexamples. A clean inventory does not mean the board is safe to flash.
