ROM ?= local/rom/Doubutsu no Mori (Japan).z64
LEGACY_UPS ?= local/legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups
PYTHON ?= python3
GC_DISC ?= local/gamecube/Animal Crossing (USA, Canada).ciso
AF_XVFB ?= Xvfb
SMOKE_OUT ?= build/smoke-pilot
V1_OUT ?= build/v1-rebuilt
V0_OUT ?= build/v0-rebuilt

.PHONY: test inspect inventory halfwidth opening references gamecube candidates pilot smoke v1 complete
test:
	$(PYTHON) -m unittest discover -s tests -v

inspect:
	$(PYTHON) tools/inspect_inputs.py --rom "$(ROM)" --legacy-ups "$(LEGACY_UPS)"

inventory: inspect
	$(PYTHON) tools/inventory.py --rom "$(ROM)"
	$(PYTHON) tools/keyboard_inventory.py --rom "$(ROM)"

halfwidth: test
	$(PYTHON) tools/build.py --rom "$(ROM)"

opening: test
	$(PYTHON) tools/build.py --rom "$(ROM)" --translations translations/opening.json --english-keyboard --output build/opening

references:
	$(PYTHON) tools/check_references.py

gamecube: inventory references
	$(PYTHON) tools/gamecube.py --disc "$(GC_DISC)" --extract
	$(PYTHON) tools/gc_text.py
	$(PYTHON) tools/gc_names.py

candidates: gamecube
	$(PYTHON) tools/reference_candidates.py --rom "$(ROM)" --english-runtime

pilot: test candidates
	$(PYTHON) tools/build.py --rom "$(ROM)" --translations build/candidates/translations.json --english-keyboard --english-runtime --output build/pilot

smoke:
	$(PYTHON) tools/emulator_smoke.py --rom build/pilot/animal-forest-halfwidth.z64 --output "$(SMOKE_OUT)" --xvfb "$(AF_XVFB)" --seconds 220 --scenario tests/keyboard-scenario.json

v1:
	$(PYTHON) tools/rebuild_v1.py --rom "$(ROM)" --output "$(V1_OUT)"

complete:
	$(PYTHON) tools/rebuild_v0.py --output "$(V0_OUT)"
	$(PYTHON) "$(V0_OUT)/source/tools/rebuild_v1.py" --output "$(V0_OUT)/source/build/v1-complete"
