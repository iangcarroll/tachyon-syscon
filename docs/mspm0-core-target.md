# GPIO routing, interrupts and reset control

`src/drivers/mspm0_core_target.c` provides thirteen original-ABI entries with direct volatile RAM/MMIO operations and real indirect callback calls. `include/mspm0_core_target.h` is the target interface. This module does not use `mspm0_core_execute`, the host environment callbacks, or original executable code as a fallback.

| Original | Symbol suffix after `syscon_target_` | Scope |
|---|---|---|
| `0x798c` | `watchdog_init` | Five ordered protected-register writes, return zero |
| `0x79d0` | `watchdog_feed` | Exact restart write, return zero |
| `0x7a50` | `hal_noop` | Original empty function |
| `0x7a54` | `gpio_lookup` | Unsigned index check and linker-resolved descriptor pointer |
| `0x7c08` | `reset_cause` | Cached raw reset cause and category table |
| `0x7c3c` | `reset_cause_name` | Named C strings and UNKNOWN fallback |
| `0x7f58` | `gpio_config` | Input/output configuration, pull selection and optional initial level |
| `0x8054` | `gpio_write` | Set/clear atomic register write |
| `0x80ac` | `gpio_toggle` | Toggle atomic register write |
| `0x80f8` | `gpio_read` | Input sample then physical-pin-byte read |
| `0x8148` | `gpio_attach` | Callback/context stores, polarity, flags/mask and NVIC enable |
| `0x81f8` | `gpio_detach` | Callback/context clearing and mask update |
| `0x8258` | `gpio_irq` | Shared group check, descriptor scan, first-match dispatch |

GPIO descriptors and callback records are typed C objects declared in `include/gpio_state.h` and defined in `src/drivers/gpio_state.c`. The board routing table, handler array and reset-cause cache are allocated by the linker. Their eight-byte record layouts preserve the existing interfaces; no production code depends on the old object addresses. Register shifts use ARM's low-eight-bit shift-count semantics, including zero results at counts 32–255. The interrupt polarity helper first doubles its physical-pin-relative count, then applies that rule; malformed descriptor bytes can therefore wrap the count back to zero. These original behaviors are preserved without C undefined shifts.

The implementation preserves ordering even when configuration memory or descriptors alias a register write. GPIO configuration captures the physical pin before powering the port, but reads the mux byte afterwards. GPIO reads fetch the input register before rereading the descriptor's physical pin. Callback registration writes the callback and context separately before reading the port, performs two distinct polarity read/modify/write operations, reads the interrupt-clear register before ORing the mask, and finally writes the NVIC enable register. It neither makes registration atomic nor changes the original interrupt-clear read into a fabricated value.

Attach returns zero in R0 and the original logical pin in R1, represented by a `uint64_t` return. Other scalar returns preserve the original values; no-op retains the incoming R0 in the compiled/tested body. No instruction-count, flags, or other caller-saved-register equivalence is claimed for functions whose ABI does not specify them.

The IRQ handler accepts CPUSS group index exactly one. It computes `(GPIO_IIDX - 1) & 255`, scans descriptors in logical-pin order, and stops at the first matching port/pin. A null callback at that match stops dispatch, even if another matching descriptor has a callback. Nonzero callbacks execute through their actual Thumb function pointers with `(logical_pin, context)`.

## Dependencies and image layout

Assertions keep the original basename, line and expression contents as normal
C strings. Null configuration is checked before an invalid pin. Reset categories
and names are also C tables; changing their length or placement requires no
address edits. The assertion implementation is a separate production dependency.

Only isolated differential fixtures retain old object placement to compare
ordered accesses. The physical linker reuses vacated peripheral and callback
storage while other subsystems finish migration. Startup initializes the named
data/BSS, including after a warm reset. This split layout is transitional.

## Local validation

`tests/test_mspm0_core_target.py` compiles the target source and reconstructed runtime string helpers with `-mcpu=cortex-m0plus -Os -nostdlib`. It compares original ARM execution with rebuilt ARM execution using the shared relocated loader, which denies execution of the original image. Tests compare normal return values, ordered RAM/MMIO access widths and values, RAM effects, callee-saved registers, and stack restoration. The register environment is explicit; this function-level harness does not substitute a full electrical/peripheral model.

The suite covers every physical descriptor byte, every GPIO mode/pull/initial-value byte, each configuration flag bit and its complement, unsigned pin boundaries, reset caching, polarity shifts and normalization, read-after-write aliases, configuration/base-pointer faults, faults at every GPIO memory access boundary, and assertion text/line contents including a basename-without-separator control. Negative tests include unmapped and read-only flash writes and invalid callback destinations/Thumb state.

Callback integration tests execute a small Thumb callback fixture that stores its actual arguments into RAM; they do not trap the callback into a host success response. An attach → IRQ → callback → detach → IRQ sequence verifies state composition. The direct suite traps **only assertion entry `0x2678`** as an explicitly reported nonreturning dependency boundary. It does not claim to validate the assertion body; that implementation can be linked separately.

Full-domain formal equivalence, identical binaries, precise fault exception frames/program counters, physical timing, full board reset, and hardware readiness are separate unproven claims. In particular, reproducing the original interrupt-clear read does not establish what that write-only register returns on silicon.

Additional tests poison the original GPIO/reset ROM tables and messages.
The complete-image relocation test requires the button callback to be registered
in the actual linked handler array, then drives GPIO edges through interrupts,
debouncing and application event consumption. It compares UART and power output
against the original. Warm-reset tests poison routing, handlers and the cache
and compare reinitialization. Current results are CI artifacts, not a frozen
instruction-count claim.
