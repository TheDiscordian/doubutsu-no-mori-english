"""Complete installed Nook owners, resources, bounds, and retained save state.

These checks establish installation, not native conversation or hardware play.
"""
import json
import os
from pathlib import Path
import struct
import sys
import subprocess
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from shop_units import SHOPS as ORIGINAL_SHOPS,PRICE_BIASES
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_nook_font import VROM as FONT
from v3_nook_native import SHOPS
from v3_sound_programs import installed_resource
from v3_physical_resources import verify

OUT=ROOT/os.environ.get('V3_NOOK_INSTALLED','build/v3-nook-password-installed-10')
PREPARED=ROOT/os.environ.get('V3_NOOK_PREPARED','build/v3-nook-password-prepared-12')


class NookInstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.image),by_vrom(cls.base)
        cls.nook=cls.report['equipment_resources']['passwords']['nook']

    def test_complete_shop_appends_and_native_loader_descriptors(self):
        core=self.files[CODE_VROM].extract(self.image)
        for name,(descriptor,_,_) in SHOPS.items():
            row=self.nook['native']['owners'][name]
            old=self.prior['shop_actors']['owners'][name]
            new=self.report['shop_actors']['owners'][name]
            a=self.before[old['vrom']].extract(self.base)
            b=self.files[new['vrom']].extract(self.image)
            ar=self.before[row['previous_reloc_vrom']].extract(self.base)
            br=self.files[row['installed_reloc_vrom']].extract(self.image)
            self.assertEqual(b,(PREPARED/'native'/name/'installed.bin').read_bytes())
            self.assertEqual(br,(PREPARED/'native'/name/'installed-relocation.bin').read_bytes())
            self.assertEqual(sha256(b),new['output_sha256'])
            self.assertEqual(sha256(br),new['relocation_sha256'])
            self.assertEqual(self.files[new['vrom']].index+1,
                             self.files[row['installed_reloc_vrom']].index)
            config=struct.unpack_from('>6I',core,descriptor-CODE_RAM)
            self.assertEqual(config[:4],(new['vrom'],new['vrom']+len(b),new['ram'],new['ram']+len(b)))
            self.assertEqual(u32(b,config[5]-new['ram']+12),0x96C)
            touched={i for p in row['patches'] for i in range(p['offset'],p['offset']+4)}
            for ram in (0x80200010,0x80370010):
                bias=(PRICE_BIASES[ORIGINAL_SHOPS[name].vrom],)
                x=relocate_verified_data(Image(old['ram'],len(a),struct.unpack_from('>5I',ar)),a,ar,ram,address_constants=bias)
                y=relocate_verified_data(Image(new['ram'],len(b),struct.unpack_from('>5I',br)),b,br,ram,address_constants=bias)
                self.assertEqual(bytes(v for i,v in enumerate(x) if i not in touched),
                                 bytes(y[i] for i in range(len(x)) if i not in touched))

    def test_complete_font_and_guarded_password_packet(self):
        r=self.nook['font'];font=self.files[FONT].extract(self.image)
        self.assertEqual(font,(PREPARED/'font/font.bin').read_bytes()+(PREPARED/'font/relocation.bin').read_bytes())
        self.assertEqual(len(r['glyphs']),256)
        self.assertEqual({g['code'] for g in r['glyphs']},set(range(256)))
        config=struct.unpack_from('>8I',self.files[MODULE].extract(self.image),0x68)
        self.assertEqual(config[:5],(FONT,len(font),r['bytes'],r['relocation_bytes'],r['bytes']))
        self.assertEqual(config[6],zlib.crc32(font))
        self.assertLessEqual(r['bytes'],0x7FF0)
        self.assertEqual(u32(self.files[MODULE].extract(self.image),r['loader_bound']['offset']),0x2C427FF1)
        p=self.report['equipment_resources']['passwords'];blob=self.files[BLOB].extract(self.image)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256'])
        self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertFalse(any(packet[0x7800:-16]))
        self.assertTrue(p['acquisition_installed']);self.assertTrue(p['name_conversion_installed'])
        self.assertTrue(p['conversation']['native_bindings_installed'])
        self.assertFalse(p['native_execution_tested']);self.assertFalse(p['ordinary_gameplay_tested'])

    def test_complete_audio_and_checked_keyboard_blocker_move(self):
        core=self.files[CODE_VROM].extract(self.image);audio=self.nook['audio']
        for kind,key,index in (('seq','sequence',199),('bank','font',audio['font_index']),('wave','wave',audio['wave_index'])):
            data,_,_=installed_resource(self.image,core,kind,index)
            self.assertEqual(data,(PREPARED/'audio'/('nook-'+key+'.bin')).read_bytes())
        old=self.prior['fire_sound']['wave_file'];new=self.report['fire_sound']['wave_file']
        a=self.before[old['vrom']].extract(self.base);b=self.files[new['vrom']].extract(self.image)
        self.assertEqual(b[:len(a)],a);self.assertEqual(len(b)-len(a),2912)
        self.assertEqual(self.before[0x4630000].extract(self.base),self.files[0x4630000].extract(self.image))
        self.assertNotEqual(self.before[0x4630000].pstart,self.files[0x4630000].pstart)
        self.assertEqual(self.before[0x4620000].extract(self.base),self.files[0x4620000].extract(self.image))

    def test_text_physical_resources_and_save_formats(self):
        verify(self.image,self.report['physical_resources'])
        for row in self.prior['physical_resources']:
            at,n=row['physical'],row['bytes']
            current=next(r for r in self.report['physical_resources'] if r['id']==row['id'])
            self.assertEqual(current['bytes'],n);self.assertEqual(current['sha256'],row['sha256'])
            start=current['physical']
            self.assertEqual(self.image[start:start+n],self.base[at:at+n],row['id'])
            if start!=at:self.assertEqual(row['id'],'golden-rewards-GAFE01-r0')
        for row in self.nook['dialogue']['resources']:
            data=self.files[row['vrom']].extract(self.image)
            self.assertEqual(sha256(data),row['sha256'])
            self.assertEqual(data,(OUT/row['file']).read_bytes())
        self.assertEqual(len(self.nook['dialogue']['provenance_entries']),22)
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertFalse(self.nook['saved_format_changed'])
        self.assertFalse(self.nook['saved_profile_changed'])
        self.assertEqual(self.nook['additional_shop_bytes'],15040)
        self.assertEqual(self.nook['additional_system_font_bytes'],0)
        self.assertEqual(self.nook['additional_font_owner_bytes'],2752)
        self.assertEqual(self.nook['additional_resident_font_bytes'],61728)
        font=self.nook['font']
        self.assertEqual(font['pixels_ram'],0x804DA000)
        self.assertEqual(font['pixels_end'],0x804E9120)
        self.assertEqual(font['pixel_allocation_bytes'],0)
        self.assertEqual(self.nook['additional_resident_title_bytes'],18480)
        self.assertLessEqual(font['pixels_end'],font['title_buffer']['ram'])
        self.assertLessEqual(font['title_buffer']['end'],0x80500000)
        rigs=self.report['equipment_resources']['room_rigs']
        for owner in (rigs['packet'],rigs['reactions']['state'],rigs['colours']['state']):
            for first,last in ((font['pixels_ram'],font['pixels_end']),
                    (font['title_buffer']['ram'],font['title_buffer']['end'])):
                self.assertFalse(first<owner['ram']+owner['bytes'] and owner['ram']<last)

    def test_current_private_browser_and_offline_profiles_agree(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        composition.use_build_lock(OUT/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report)
        choices=options(self.image,self.report);plan=browser.rules(self.image,self.report)
        cases=[]
        for name,requested in (('empty',[]),('net-only',['GAFE01-r0/item/2239']),('all',list(catalog))):
            selected=composition.resolve(catalog,requested,behaviour_options=choices)
            result,_,blob=composition.compose(self.image,self.report,catalog,selected)
            if not requested:self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            if name=='all':self.assertEqual(result,self.image)
            if blob is not None:
                current=by_vrom(result)
                self.assertEqual(current[FONT].extract(result),self.files[FONT].extract(self.image))
                font=self.nook['font']['physical_resource'];at,n=font['physical'],font['bytes']
                self.assertEqual(result[at:at+n],self.image[at:at+n])
            cases.append(dict(name=name,requested=requested,behaviours={},selection=selected,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-nook-composition-') as temp:
            fixture=Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan,cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composition.stable_reference(self.report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())
        self.assertEqual(self.nook['additional_password_bytes'],0)


if __name__=='__main__':unittest.main()
