"""Saved banking uses the existing full-town transaction and native-I/O doubles."""
import unittest
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from tests import test_v3_carried_storage as carried

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from toolchain import IMAGE
from v3_furniture_install import inputs
from v3_bank_storage import layout


class BankStorageTests(unittest.TestCase):
    def test_account_owner_migration_and_profile_rejection(self):
        for mode in (0,1):
            with self.subTest(mode=mode):
                carried.CarriedStorageTests.save_transaction(self,True,0,rewards=True,
                    golden_rewards=True,bank=True,bank_mode=mode)

    def test_checked_memory_and_native_storage_compilation(self):
        import copy
        _,prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        memory=layout(prior)
        self.assertEqual(memory['scratch']['bytes']-memory['scratch']['retained_bytes'],48)
        changed=copy.deepcopy(prior);changed['equipment_resources']['diaries']['memory']['scratch']['bytes']+=16
        with self.assertRaisesRegex(ValueError,'scratch owner'):layout(changed)
        # Compile the actual current full storage, retaining every prior flag.
        # The distinct reservation is required, and linking/installation stays
        # pending the real menu/service bindings, not replaced with stubs.
        flags=prior['save_codec']['active_storage_code']['flags']
        with tempfile.TemporaryDirectory(prefix='v3-bank-mips-',dir=ROOT/'build') as temp:
            out=Path(temp)
            docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
                '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint',
                '/n64_toolchain/bin/mips64-elf-gcc',IMAGE]
            for name in ('console_storage','save_compressed','save_runtime'):
                command=[*docker,*flags,'-DAF_V3_BANK_STORAGE=1',
                    f'-DAF_BANK_STATE_RAM=0x{memory["account"]["ram"]:X}u',
                    f'/source/overlays/v3/{name}.c','-o',f'{name}.o']
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':
    unittest.main()
