# Production source mapping

The [generated firmware source inventory](reconstruction-ledger.md) checks every statically identified function against the production build's source list. Its table uses the production mapping where one exists and keeps legacy host-model provenance separate. Run `make ledger` to inspect the current tree; an old checked-in report is not current evidence.

A source mapping is one part of validation. The physical-image tests check reset/vector integration and build boundaries; relocation tests edit source and move code, data and globals; complete-image tests exercise UART, configuration, retained state, power inputs and reset paths. Their current results come from the exact tested commit's CI artifacts. The [emulator documentation](mcu-emulator.md) describes modeled behavior and limits.

Copied flash-programming code remains part of the identified flash-controller implementation, rather than an extra function in the static flash inventory. Its execution address in the rebuilt image is linker-resolved; original SRAM addresses in oracle tests describe the original image. A clean source inventory does not prove exhaustive discovery, complete behavioral equivalence, or safe physical recovery. See the [hardware record](debug-probe.md#controlled-replacement-round-trip) for commit-specific live results and remaining recovery limits.
