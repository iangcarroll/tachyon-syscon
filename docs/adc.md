# ADC HAL reconstruction

`src/adc.c` reconstructs initialization (`0x7c54`), calibrated temperature (`0x7d54`), raw ADC readings (`0x7e7c`), and millivolt conversion (`0x7f24`). The six-entry pin mapping is read from the original initialized RAM table at offset `0xf4`; pin arguments are truncated to eight bits before lookup. Invalid pins and null initialization configuration reach an explicit assertion boundary.

The environment supplies every 32-bit register read, register write, cycle delay, and assertion event. It is not a simulated analog device. `tools/adc_oracle.py` maps only required register pages and refuses an unprovided register read. Tests supply initial register contents and scripted status changes explicitly. No register reset values, calibration constants, or electrical behavior are fabricated.

Initialization executes the original driver-helper register transformations directly, then copies seven configuration bytes to RAM offset `0x685` and writes the unsigned 16-bit reference scale as a 32-bit value at `0x68c`. The fixed hardware configuration is independent of most caller configuration fields. Temperature initialization uses the original byte-field OR behavior, writing `0x81` to VREF control, not the apparent packed value `0x8001`; the differential test exposed that distinction.

Raw sampling disables conversion, selects the channel, reenables conversion, raises the start bit, delays 32000 cycles, clears the start bit, delays 3200 cycles, and reads the low 16 result bits from the original peripheral alias address. Millivolt conversion multiplies by the stored scale with signed 32-bit wrapping and truncates division by 4096 toward zero. It is integer fixed-point arithmetic, not floating point.

Temperature conversion initializes VREF only once using RAM flag `0x694`, polls readiness up to 100 times with 320-cycle delays, and performs one additional readiness read after the loop. This final check permits readiness on the 101st read. The original factory-calibration access temporarily changes the SYSCTL register at `0x40401300` to 5 and restores only the old low three bits. Calibration values zero and `0xfff`, or an unready reference, return `INT32_MIN`. Otherwise the firmware computes the wrapped signed expression `(raw16 - calibration) * 14000 / -7168 + 300`. The original ARM signed-division helper executes in the oracle.

Six differential groups passed in **1.29 seconds**. They compare returned values, all global RAM through offset `0x7ff`, complete ordered MMIO and delay traces, final modeled registers, and consumption of scripted read responses. Coverage includes every mapped pin, eight-bit pin truncation, arbitrary seven-byte configurations, raw channel selection, signed multiplication wrap/truncation, readiness transitions and timeout, invalid calibration values, and missing-register failure. The tests do not validate physical ADC accuracy, conversion completion timing, hardware reset side effects, or safety of flashing a replacement.

```sh
.venv/bin/python -m pytest -q tests/test_adc.py
```
