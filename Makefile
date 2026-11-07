PYTHON ?= .venv/bin/python
ARM_CC ?= arm-none-eabi-gcc
ARM_AR ?= arm-none-eabi-ar
ARM_FLAGS = -std=c11 -mcpu=cortex-m0plus -mthumb -Os -ffreestanding -ffunction-sections -fdata-sections -Wall -Wextra -Werror -Iinclude
SOURCES := $(wildcard src/*.c)
OBJECTS := $(patsubst src/%.c,build/arm/%.o,$(SOURCES))
HEADERS := $(wildcard include/*.h)

.PHONY: all arm test inventory binary-check boot-probe references-check ledger emulate target-interfaces physical-firmware rebuilt-system proof-checksum proof-physical-checksum
all: arm
arm: build/arm/libsyscon-reconstruction.a

build/arm/%.o: src/%.c $(HEADERS)
	mkdir -p build/arm
	$(ARM_CC) $(ARM_FLAGS) -c $< -o $@

build/arm/libsyscon-reconstruction.a: $(OBJECTS)
	$(ARM_AR) rcs $@ $(OBJECTS)

test:
	$(PYTHON) -m pytest -q tests

inventory:
	$(PYTHON) tools/inventory.py

binary-check:
	$(PYTHON) tools/verify_binary.py
	$(PYTHON) tools/verify_runtime_binary.py
	$(PYTHON) tools/verify_runtime_arithmetic_binary.py

boot-probe:
	$(PYTHON) tools/boot_probe.py

references-check:
	$(PYTHON) tools/catalog_references.py

ledger:
	$(PYTHON) tools/reconstruction_ledger.py

emulate:
	$(PYTHON) tools/emulate.py --scenario fixtures/emulator/tachyon-synthetic.json --instructions 1000000 --stop-at 0x3c9a --command VERSION --report analysis/emulation-boot-version.json

target-interfaces:
	$(PYTHON) tools/build_target_interfaces.py

physical-firmware:
	$(PYTHON) tools/build_physical_firmware.py

rebuilt-system: physical-firmware
	$(PYTHON) tools/rebuilt_system.py

proof-checksum:
	$(PYTHON) tools/proof_checksum.py
	$(PYTHON) tools/proof_checksum.py --mutant --output analysis/proof-checksum-negative

proof-physical-checksum:
	$(PYTHON) tools/proof_physical_checksum.py
