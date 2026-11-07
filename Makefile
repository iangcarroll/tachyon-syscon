PYTHON ?= .venv/bin/python
ARM_CC ?= arm-none-eabi-gcc
ARM_AR ?= arm-none-eabi-ar
ARM_FLAGS = -std=c11 -mcpu=cortex-m0plus -mthumb -Os -ffreestanding -ffunction-sections -fdata-sections -Wall -Wextra -Werror -Iinclude
SOURCES := $(wildcard src/*.c)
OBJECTS := $(patsubst src/%.c,build/arm/%.o,$(SOURCES))
HEADERS := $(wildcard include/*.h)
# Daily feedback: helpers plus real ARM configuration, ADC and power subsystems.
# Full image cold starts and exhaustive fault sweeps remain in `make test` / CI.
QUICK_TESTS := tests/test_differential.py tests/test_uart.py \
	tests/test_config_commands_target.py tests/test_config_slot_read_order.py \
	tests/test_adc_target.py tests/test_power_curves.py tests/test_power_key_target.py tests/test_runtime_memory.py \
	tests/test_firmware_fetch.py tests/test_reference_fetch.py

.PHONY: all arm test quick-test inputs firmware-fetch inventory binary-check boot-probe references-fetch references-check ledger emulate target-interfaces physical-firmware rebuilt-system proof-checksum proof-physical-checksum proof-test
all: arm
arm: build/arm/libsyscon-reconstruction.a

build/arm/%.o: src/%.c $(HEADERS)
	mkdir -p build/arm
	$(ARM_CC) $(ARM_FLAGS) -c $< -o $@

build/arm/libsyscon-reconstruction.a: $(OBJECTS)
	$(ARM_AR) rcs $@ $(OBJECTS)

inputs: references-fetch firmware-fetch

firmware-fetch:
	$(PYTHON) tools/fetch_firmware.py

test: inputs
	$(PYTHON) -m pytest -q tests

quick-test: inputs
	SYSCON_COVERAGE_OUTPUT=build/quick-test-coverage.json $(PYTHON) -m pytest -q $(QUICK_TESTS) --durations=10

inventory: firmware-fetch
	$(PYTHON) tools/inventory.py

binary-check: firmware-fetch
	$(PYTHON) tools/verify_binary.py
	$(PYTHON) tools/verify_runtime_binary.py
	$(PYTHON) tools/verify_runtime_arithmetic_binary.py

boot-probe:
	$(PYTHON) tools/boot_probe.py

references-fetch:
	$(PYTHON) tools/fetch_references.py

references-check:
	$(PYTHON) tools/fetch_references.py --check

ledger:
	$(PYTHON) tools/reconstruction_ledger.py

emulate: inputs
	$(PYTHON) tools/emulate.py --scenario fixtures/emulator/tachyon-synthetic.json --instructions 1000000 --stop-at 0x3c9a --command VERSION --report build/emulation-boot-version.json

target-interfaces:
	$(PYTHON) tools/build_target_interfaces.py

physical-firmware:
	$(PYTHON) tools/build_physical_firmware.py

rebuilt-system: physical-firmware inputs
	$(PYTHON) tools/rebuilt_system.py

proof-checksum: firmware-fetch
	$(PYTHON) tools/proof_checksum.py
	$(PYTHON) tools/proof_checksum.py --mutant --output analysis/proof-checksum-negative

proof-physical-checksum: firmware-fetch
	$(PYTHON) tools/proof_physical_checksum.py

proof-test: firmware-fetch
	PYTHONPATH=tools $(PYTHON) -m pytest -q tools/tests/test_proof_checksum.py tools/tests/test_proof_physical_checksum.py
