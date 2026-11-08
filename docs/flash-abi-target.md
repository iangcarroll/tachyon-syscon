# Original-ABI flash entries

`src/drivers/flash_abi_target.c` and `include/flash_abi_target.h` add direct target entries for the six original functions below. Unlike `src/drivers/flash_controller.c`, their signatures do not add a callback/environment parameter.

| Original | Source symbol | Contract |
|---|---|---|
| `0x2738` | `syscon_target_flash_report` | Read fixed FLASHCTL status once, mask `0x10f0`, log linked source tag/message text |
| `0x7af4` | `syscon_target_flash_erase` | Write `size OR 2`, target address, execute and return status |
| `0x7b10` | `syscon_target_flash_program` | Configure program/mask/address, load first data word and write it, load second word and write it, execute |
| `0x7b44` | `syscon_target_flash_unprotect` | Clear all three original protection words in order; preserve input base in R0 |
| `0x7b60` | `syscon_target_flash_blank` | Configure blank command/address, execute and return status |
| `0xaae0` | `syscon_target_flash_veneer` | Call the fixed Thumb entry `0x20000001`, preserving the original functional ABI |
| Flash `0xaaf0` copied to SRAM `0x20000000` | `syscon_target_flash_ram_execute` | Write CMDEXEC=1, poll status AND 7 until 1 or 3, return masked status |

The RAM body is standalone source C and currently emits 36 bytes. The dedicated test linker places it at the original SRAM entry. It does not copy any original instruction bytes into the candidate. The original side runs its actual copied firmware routine. The veneer deliberately calls the fixed SRAM address rather than an arbitrarily relocated source symbol; removing SRAM execute permission therefore fails on both sides. Its incidental caller-saved register values/private stack layout are not claimed to match the original hand-generated veneer.

Programming uses actual 32-bit volatile loads, not a host byte-array decoder. Loads interleave with command/data writes, preserving self-aliasing data pointers and faults after partial setup. Addresses and size bits are unchecked and wrap as ARM32 arithmetic. Erase and blank helpers do not invent alignment checks, masked error normalization or early success. Only terminal status low bits 1/3 terminate polling; the negative test externally interrupts a matching trace prefix for stuck status 7. There is no added timeout.

`tools/flash_abi_target_oracle.py` compiles the C for Cortex-M0+, loads its SRAM section at `0x20000000`, and compares actual original versus rebuilt return values and ordered RAM/MMIO accesses. Logger `0x8f88` is the only trapped original dependency. Program input aliases, every observable program-operation fault prefix, base/pointer faults and wrap, every low-byte status, high-bit terminal masks and every report-mask combination are covered.

An integration group uses the existing explicit register-triggered FLASHCTL model. It exercises protection failure, unprotect, erase, blank check, programming, nonblank failure, forbidden zero-to-one programming, invalid address/mode and injected controller failure. The model does not mutate flash until an execute command reaches its terminal success status. It is a digital environment model, not a physical flash/ECC/voltage claim.

The shared checkpoint passed **17 groups in 4.23 seconds**: eight flash-ABI groups and nine physical-startup regressions. `analysis/flash-abi-target-reference-coverage.json` and `analysis/flash-abi-target-mapping.json` record named-function coverage and separately list the observed copied-RAM instruction addresses. Instruction exercise is not full-domain formal equivalence or binary identity.

The physical builder now integrates these entries through the explicit `SYSCON_DIRECT_FLASH_ABI` config-storage binding. It places this source RAM body at the original address and retains it with a linker `KEEP` rule. The generic callback API remains unchanged for standalone tests and is garbage-collected from the production image. See [physical build](physical-firmware-build.md) for the reviewed layout, stack limitations and artifact boundary. No hardware was accessed, and no flash-ready claim is made.
