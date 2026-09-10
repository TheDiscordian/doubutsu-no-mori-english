"""Temporary apology input retains complete sun/skull tokens and ten-byte bounds."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


class ApologyInputTests(unittest.TestCase):
    def test_exact_targets_scoped_permissions_and_combined_allocation(self):
        import apology_targets as t
        import apology_overlay as a
        from aflib import by_vrom
        from runtime_module import module_command_info
        from fortune_strings import source_entries
        from textcodec import encode
        from textvalidate import validate_entry
        from translation_progress import CounterLedger
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        info=module_command_info(native);originals=source_entries(native)
        edits=t.with_candidates(native,[])
        self.assertEqual(t.with_candidates(native,edits),edits)
        for row in edits:
            id=row['id'];original=originals[int(id[7:],16)]
            data=encode(row['translation'],info);self.assertEqual(data,t.TARGETS[id][2])
            validate_entry(original,data,info,'string',resident_runtime=True,apology_permit=t.approved(id))
            with self.assertRaises(ValueError):validate_entry(original,data,info,'string',resident_runtime=True)
            for bank,policy,source,value in (('message','exact',original,data),
                    ('string','presentation',original,data),('string','exact',b'xx',data),
                    ('string','exact',original,data[:-1]),('string','exact',original,b'Other \x80\xa7')):
                with self.assertRaises(ValueError):
                    validate_entry(source,value,info,bank,policy,resident_runtime=True,apology_permit=t.approved(id))
            ledger=CounterLedger(info);ledger.add(id,original)
            ledger.credit(id,data,'native_bank');self.assertFalse(ledger.rows[id]['replacements'])
            ledger.credit(id,data,'apology_input',apology=True);self.assertTrue(ledger.rows[id]['replacements'])
            with self.assertRaises(ValueError):ledger.credit(id,data,'native_bank',apology=True)
        for field,value in (('translation','U R my sun!'),('source_sha256','0'*64),('control_policy','presentation')):
            changed=copy.deepcopy(edits);changed[0][field]=value
            with self.assertRaises(ValueError):t.with_candidates(native,changed)
        with self.assertRaises(ValueError):t.with_candidates(native,edits+[edits[0]])
        files=by_vrom((ROOT/'build/reserve-strings-pilot/animal-forest-halfwidth.z64').read_bytes())
        import inventory_english as inv
        size=files[inv.NEW_VROM].vend-files[inv.NEW_VROM].vstart
        needed=a.allocation(size)
        self.assertEqual(needed,{'editor_growth':2752,'extra_pool_bytes':256,
            'combined_growth_used':12352,'combined_pool_bytes':247424,'conservative_required':247232})

    @unittest.skipUnless((ROOT/'build/apology-input-pilot/build.json').is_file(),'Complete apology ROM required')
    def test_cartridge_all_prior_resources_pool_targets_and_counter(self):
        import apology_overlay as a
        import apology_targets as t
        from aflib import by_vrom,apply_ups,CODE_VROM,CODE_RAM
        from translation_progress import measure
        from textbanks import Bank
        import struct
        directory=ROOT/'build/apology-input-pilot'
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        old=(ROOT/'build/reserve-strings-pilot/animal-forest-halfwidth.z64').read_bytes()
        built=(directory/'animal-forest-halfwidth.z64').read_bytes()
        report=json.loads((directory/'build.json').read_text())
        a.verify_installation(built,native,report)
        self.assertEqual(apply_ups(native,(directory/'animal-forest-halfwidth.ups').read_bytes()),built)
        files,previous=by_vrom(built),by_vrom(old)
        self.assertEqual(set(files),set(previous))
        allowed={0x19D40,CODE_VROM,a.previous.OWNER,a.previous.NEW_VROM,a.previous.NEW_RELOCATION,0x02600000,0xD18000}
        for v in files:
            if v not in allowed:self.assertEqual(files[v].extract(built),previous[v].extract(old),hex(v))
        code=bytearray(files[CODE_VROM].extract(built))
        struct.pack_into('>I',code,0x800C4B10-CODE_RAM,0x25CE0B20)
        self.assertEqual(code,previous[CODE_VROM].extract(old))
        owner=bytearray(files[a.previous.OWNER].extract(built));at=a.previous.METADATA[a.previous.EDITOR][0]
        owner[at:at+32]=a.previous.metadata()
        self.assertEqual(owner,previous[a.previous.OWNER].extract(old))
        def entries(rom,table):return Bank('string',0x02600000,0xD18000,table[0x02600000].extract(rom),table[0xD18000].extract(rom)).entries()
        for n,(before,after) in enumerate(zip(entries(old,previous),entries(built,files))):
            id=f'string:{n:04X}'
            self.assertEqual(after,t.TARGETS[id][2] if id in t.TARGETS else before)
        ledger=measure(native,built,report)
        self.assertEqual(ledger.summary()['total_source_characters'],751307)
        self.assertEqual(ledger.summary()['replaced_source_characters'],748482+20+35)
        for id in t.TARGETS:self.assertEqual([r['route'] for r in ledger.rows[id]['replacements']],['apology_input'])
        bad=copy.deepcopy(report);bad['apology_input']['allocation']['extra_pool_bytes']=0
        with self.assertRaises(ValueError):a.verify_installation(built,native,bad)
        bad=copy.deepcopy(report);bad['apology_input']['targets']={}
        with self.assertRaises(ValueError):a.verify_installation(built,native,bad)

    def test_scoped_editor_selection_drawing_and_previous_mode_delegation(self):
        with tempfile.TemporaryDirectory(prefix='af-apology-editor-') as directory:
            target=str(Path(directory)/'check')
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I',str(ROOT/'overlays/apology_input'),
                str(ROOT/'overlays/apology_input/edit.c'),str(ROOT/'overlays/apology_input/editor.c'),
                str(ROOT/'tests/apology_editor_check.c'),'-o',target],check=True,capture_output=True,timeout=30)
            subprocess.run([target],check=True,capture_output=True,timeout=10)

    @unittest.skipUnless((ROOT/'build/apology-input-overlay/overlay.json').is_file(),'Compiled apology image required')
    def test_compiled_profile_previous_code_relocation_and_fail_closed_guards(self):
        import apology_overlay as a
        from aflib import sha256
        directory=ROOT/'build/apology-input-overlay'
        data=(directory/'overlay.bin').read_bytes();rel=(directory/'relocation.bin').read_bytes()
        report=json.loads((directory/'overlay.json').read_text())
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        a.validate(native,data,rel,report)
        prefix,old_rel=a.preceding(data,rel)
        self.assertEqual(sha256(prefix),a.APPROVED['previous_sha256'])
        self.assertEqual(sha256(old_rel),a.previous.APPROVED['relocation_sha256'])
        self.assertEqual(len(data)-len(prefix),2752)
        for at in (0,0x808877E4-a.RAM,a.APPROVED['prefix_bytes'],len(data)-1):
            changed=bytearray(data);changed[at]^=1
            with self.assertRaises(ValueError):a.validate(native,changed,rel,report)
        changed=bytearray(rel);changed[-1]^=1
        with self.assertRaises(ValueError):a.validate(native,data,changed,report)
        for field,value in (('imports',{}),('sources',{}),('toolchain_image','unapproved'),('elf_relocations',[])):
            changed=copy.deepcopy(report);changed[field]=value
            with self.assertRaises(ValueError):a.validate(native,data,rel,changed)

    def test_real_core_under_address_and_undefined_behaviour_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-apology-input-') as directory:
            target=str(Path(directory)/'check')
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I',str(ROOT/'overlays/apology_input'),str(ROOT/'overlays/apology_input/edit.c'),
                str(ROOT/'tests/apology_input_check.c'),'-o',target],check=True,capture_output=True,timeout=30)
            subprocess.run([target],check=True,capture_output=True,timeout=10)


if __name__=='__main__':unittest.main()
