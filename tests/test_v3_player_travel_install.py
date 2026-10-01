"""Current installed transport bounds, packet preservation, and native bindings."""
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,CODE_RAM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_player_travel_install import STATE,STATE_BYTES,RECORD_BYTES,IO,IO_END,LIFE,LIFE_END
from v3_physical_resources import verify

OUT=ROOT/os.environ.get('V3_PLAYER_TRAVEL_BUILD','build/v3-player-travel-installed-07')


class PlayerTravelInstallation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.e=cls.report['equipment_resources'];cls.t=cls.e['player_travel']

    def test_complete_new_record_is_separate_from_model_pool_and_native_passport(self):
        p=self.t['state_packet'];raw=self.image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual((p['ram'],p['bytes']),(STATE,STATE_BYTES))
        self.assertEqual(struct.unpack_from('>4I',raw),(0x41465431,0,0,0))
        self.assertEqual(raw[16:16+RECORD_BYTES],bytes(RECORD_BYTES))
        self.assertEqual(raw[16+RECORD_BYTES:16+RECORD_BYTES+16],bytes.fromhex('AF54524C')*4)
        self.assertEqual(self.report['furniture']['bank_pool'],self.prior['furniture']['bank_pool'])
        self.assertEqual(self.prior['furniture']['bank_pool']['end'],STATE)
        self.assertLess(STATE+STATE_BYTES,self.e['console_disk']['packet']['ram'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        self.assertEqual(core[0x80116808-CODE_RAM:0x80116810-CODE_RAM],struct.pack('>2I',0x1200,0x6700))

    def test_code_padding_keeps_original_code_bss_guards_and_mutable_state(self):
        for name,p,old in (('io',self.e['diaries']['packets']['ui'],self.prior['equipment_resources']['diaries']['packets']['ui']),
                ('life',self.e['harvest']['packet'],self.prior['equipment_resources']['harvest']['packet'])):
            before=self.base[old['physical']:old['physical']+old['bytes']]
            raw=self.image[p['physical']:p['physical']+p['bytes']];f=self.t['compiled']['fragments'][name]
            start=f['ram']-p['ram'];end=start+f['bytes']
            self.assertEqual(sha256(raw[start:end]),f['sha256'])
            self.assertEqual(before[start:end],bytes(end-start))
            self.assertEqual(raw[:start],before[:start]);self.assertEqual(raw[end:],before[end:])
            self.assertLessEqual(f['ram']+f['bytes'],IO_END if name=='io' else LIFE_END)
        self.assertEqual(self.t['compiled']['fragments']['io']['ram'],IO)
        self.assertEqual(self.t['compiled']['fragments']['life']['ram'],LIFE)
        self.assertEqual(self.t['shared_workspace_bytes'],119932)
        self.assertFalse(self.t['ordinary_visiting_verified'])

    def test_installed_hooks_and_checked_extra_startup_packet(self):
        files=by_vrom(self.image);blob=files[BLOB].extract(self.image)
        boot=self.e['surface_bootstrap']['code'];old=self.prior['equipment_resources']['surface_bootstrap']['code']
        self.assertEqual(boot['packet_count'],old['packet_count']+1)
        self.assertEqual(boot['packet_stride'],16)
        self.assertLessEqual(boot['bytes'],0x804A8FF0-0x804A8D40)
        at=self.e['blob_offset']+boot['symbols']['packets']-self.e['ram']
        rows=[struct.unpack_from('>4I',blob,at+i*16) for i in range(boot['packet_count'])]
        p=self.t['state_packet'];self.assertEqual(rows[-1][:3],(STATE,p['physical']|0x80000000,STATE_BYTES))
        ui=self.e['diaries']['packets']['ui']
        for name,expected in (('af_travel_harvest_crc',self.e['harvest']['packet']['crc32']),
                ('af_travel_record_crc',p['crc32'])):
            ram=self.t['compiled']['symbols'][name]
            self.assertEqual(boot['symbols'][name],ram)
            self.assertEqual(struct.unpack_from('>I',self.image,ui['physical']+ram-ui['ram'])[0],expected)
        for h in self.t['hooks']:
            address=h['address']
            if address<0x80400000:raw=files[CODE_VROM].extract(self.image);offset=address-CODE_RAM
            elif address==0x806558DC:
                p=self.e['creature_fish']['world']['packet'];raw=blob;offset=p['blob_offset']+address-p['ram']
            else:
                p=self.e['carried_items']['quest']['packet'];raw=self.image;offset=p['physical']+address-p['ram']
            self.assertEqual(raw[offset:offset+8].hex(),h['after'])
            self.assertIn(h['target'],self.t['compiled']['symbols'].values())

    def test_physical_owners_and_reconstructed_patch(self):
        for name,digest in self.t['sources'].items():
            self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)
        verify(self.image,self.report['physical_resources'])
        changed={'harvest-connected','diary-ui-GAFE01-r0',self.e['carried_items']['quest']['packet']['id']}
        for p in self.prior['physical_resources']:
            if p['id'] in changed:continue
            self.assertEqual(self.image[p['physical']:p['physical']+p['bytes']],
                self.base[p['physical']:p['physical']+p['bytes']])
        source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(source,(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
