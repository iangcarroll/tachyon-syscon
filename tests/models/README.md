# Host-side test models

These are bounded models used by the differential test suite. They preserve the original image's raw SRAM layout and explicit dependency callbacks so tests can compare individual behaviors with the original Thumb code. They are not the firmware flashed to Tachyon; edit the production implementation under `src/` for firmware changes.

The test library also compiles four production implementations directly: memory, arithmetic, formatting and flash-controller support. `model_memory.h` provides the alignment-safe byte-buffer accessors used only by these legacy models. The physical firmware builder rejects files from `tests/`.
