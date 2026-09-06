ROM ?= local/rom/Doubutsu no Mori (Japan).z64
LEGACY_UPS ?= local/legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups
PYTHON ?= python3

.PHONY: test inspect inventory halfwidth
test:
	$(PYTHON) -m unittest discover -s tests -v

inspect:
	$(PYTHON) tools/inspect_inputs.py --rom "$(ROM)" --legacy-ups "$(LEGACY_UPS)"

inventory: inspect
	$(PYTHON) tools/inventory.py --rom "$(ROM)"

halfwidth: test
	$(PYTHON) tools/build.py --rom "$(ROM)"
