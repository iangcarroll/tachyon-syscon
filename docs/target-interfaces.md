# Combined target-interface link

`tools/build_target_interfaces.py` cross-compiles the direct target interfaces
and source runtime/flash-controller dependencies into one relocatable object
and archive. It detects duplicate symbols and exposes every unresolved binding.
The archive contains no original executable bytes, installed runtime archives,
or emulator endpoint stubs.

The link includes configuration storage helpers, callbacks, GPIO/core, ADC,
UART initialization/rings, assertions, fault breadcrumbs, scheduler/timers,
retained state, diagnostics, the complete application main loop, power-key and
RGB state machines, logger/formatting, integer/soft-float/memory runtime, heap,
stdio, scanning and printf. `target/interface_bindings.c` supplies real memory,
assertion, color and logger UART bindings. Diagnostic UART output retains the
original fault-stage-17 update before transmission; modem output uses UART1.

Application protocol, modem, power and expander interfaces are integrated. The
combined archive currently has zero unresolved symbols. The authoritative list is
`build/target-interfaces/manifest.json`, regenerated with:

```sh
make -C syscon-re target-interfaces
```

The manifest records compiler flags, input hashes, artifact hashes and every
unresolved symbol. Rebuilding replaces the archive to prevent stale members.
A final executable link must resolve every dependency from source. The linked
tests contain no generated trap fixtures for missing implementations.
The linked tests exercise real UART IRQ/ring helpers, callback aliasing, config
assertion forwarding, compiler memset, and logger through real clock, formatter,
diagnostic-stage update and UART MMIO without any function-body hooks. They also
exercise UART IRQ through the receive ring, parser, VERSION, configuration
readback, HELP and unknown-command handlers to real UART MMIO. Runtime
initialization and the pinned always-failing sbrk entry have direct comparisons.

This relocatable artifact is separate from the strict physical-layout build in
`tools/build_physical_firmware.py`. A whole-image stack bound and whole-firmware
proof remain open. The archive's existence does not imply that source firmware boots. Original-image
reset boot in the MCU emulator is separately validated. Neither artifact is
authorization or evidence that a replacement is safe to flash.
