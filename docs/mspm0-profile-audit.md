# MSPM0L1306 profile metadata audit

The profile audit compared the pinned TI device/CMSIS headers and DFP 1.3.1 SVD,
using the pack's device memory definitions as an independent reference. The
[MSPM0L130x datasheet, revision D](https://www.ti.com/lit/ds/symlink/mspm0l1306.pdf),
Tables 8-4/8-5 and memory footnote 3, corroborate the flash/SRAM geometry, aliases,
ADC SVT base, and CPU fault boundary at the final eight flash bytes. The physical
board's precise silicon identity remains unconfirmed.

Two metadata corrections were made in `tools/mspm0/profile.py`:

- The SVD repeats the TIMG0/1/2/4, DMA, and COMP0 interrupt-event clusters with a
  44-byte stride. That is the occupied register span, not the block stride.
  The pinned `hw_gptimer.h`, `hw_dma.h`, and `hw_comp.h` put the blocks at offsets
  `0x1020`, `0x1050`, and, where present, `0x1080`. Correcting the stride to
  48 bytes removes fictitious registers in reserved gaps and restores the proper
  addresses/access classifications of the generic event blocks. The override is
  scoped to these six named peripherals and rejects an unexpected input layout.
- The device header also declares DEBUGSS on shared IRQ 0 and COMP0 on shared
  IRQ 1. These were missing from the declarative IRQ table and are now included.
  This does not add executable peripheral models for those devices.

The existing ADC correction is supported independently by the device base macros
and `ADC12_SVTMEM_Regs`/`ADC12_ULLMEM_Regs`: the pack double-counts the SVT
relocation, and its missing ULL result aliases refer to the same conversion data.
The tests compare implemented result counts against the device SVD, not the
larger family header's full 24-result capacity. Header CPU definitions also
support the existing no-MPU, VTOR-present, two-priority-bit overrides.

`tests/test_mspm0_profile.py` passed **11 tests**. They verify pinned input hashes
and SVD extraction, device memory geometry/non-overlap, CPU/IRQ definitions,
header-derived interrupt register addresses and access modes, reserved gaps,
ADC aliases, register interval/width/reset-mask bounds, and device field masks
against independent family-header masks. The field comparison permits narrower
device-specific fields: this device has 16-bit timers and fewer flash banks,
event channels, and ADC options than some generic header types support.

The audit did not change the core or peripheral implementations. It also does not
establish every reset value from silicon measurements or a complete technical
reference manual audit: reset values remain the pinned SVD values, checked for
width/field consistency. The 49 byte-wide EVENTLP registers remain byte-wide in
metadata; EVENTLP itself is explicitly unsupported by the executable model.
Metadata presence alone does not mean a peripheral is emulated.
