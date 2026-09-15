"""Complete source-bound arrival rooms, retained pilots, and cartridge bounds."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,apply_ups,by_vrom,n64_checksum,sha256
from v3_islander_houses import BASE,BASE_SHA,BLOB,CONFIG,FG,FG_STORAGE,HOUSE,ISLANDERS,MODULE,STARTUP,source_rooms
from v3_import_catalog import read_donor
from v3_villager_houses import STRIDE,layers
from v3_registry import villager_house_layers

OUTPUT=ROOT/'build/v3-islander-houses-02'


@unittest.skipUnless((OUTPUT/'build.json').exists(),'Current islander-house cartridge required')
class IslanderHouses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_text())
        cls.base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.previous=json.loads((BASE/'build.json').read_text())
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom)
        donor=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.rooms,cls.converted,cls.dependencies=source_rooms(cls.native,donor,symbols)

    def test_all_eighteen_complete_source_rooms_surfaces_and_dependencies(self):
        self.assertEqual(self.rooms,self.report['islander_houses']['rooms'])
        self.assertEqual(self.dependencies,self.report['islander_houses']['dependencies'])
        self.assertEqual(len(self.rooms),18)
        self.assertEqual({r['donor_index'] for r in self.rooms},set(ISLANDERS))
        table=self.files[HOUSE].extract(self.rom)
        fg=layers(self.files[FG].extract(self.rom))
        for row in self.rooms:
            at=(int(row['actor_id'],16)&255)*8
            self.assertEqual(table[at:at+8].hex(),row['native_house_hex'])
            self.assertEqual(tuple(l['target_layer'] for l in row['layers']),villager_house_layers(row['donor_index']))
            for layer in row['layers']:
                n=layer['target_layer'];self.assertEqual(fg[n],self.converted[n])
            for kind in ('wall','floor'):
                self.assertEqual(len(row[kind]['native_matches']),1)
        identities={r['donor_item']:r for r in self.dependencies}
        for item in ('11C0','12EB','15A8'):
            self.assertTrue(identities[item]['shared_identity_evidence']['same_model_reference'])
            self.assertTrue(identities[item]['shared_identity_evidence']['same_texture_reference'])

    def test_native_and_pilot_houses_remain_complete(self):
        before=self.old[HOUSE].extract(self.base)
        expected=bytearray(before)
        for row in self.rooms:
            at=(int(row['actor_id'],16)&255)*8
            self.assertEqual(before[at:at+8],bytes(8))
            expected[at:at+8]=bytes.fromhex(row['native_house_hex'])
        self.assertEqual(self.files[HOUSE].extract(self.rom),expected)
        old=self.old[FG].extract(self.base);current=self.files[FG].extract(self.rom)
        self.assertEqual(current[:len(old)],old)
        self.assertEqual(current[len(old):],b''.join(v for k,v in sorted(self.converted.items())))
        self.assertEqual(len(current),244496)
        self.assertEqual(len(layers(current)),472)
        self.assertEqual({r['id'] for r in self.report['villager_houses']['appended_layers']},set(range(856,896)))
        self.assertEqual(len(self.report['villager_houses']['installed_villagers']),20)

    def test_arrival_layouts_do_not_import_gift_placeholders_or_change_furniture_positions(self):
        fg=layers(self.files[FG].extract(self.rom))
        outside={z*16+x for z in range(16) for x in range(16)
                 if not (z<8 and x<8 or z==8 and x in (3,4))}
        for row in self.rooms:
            self.assertEqual(row['house_mode'],'authentic_arrival')
            self.assertNotEqual(row['donor_wishlist_layers'],[r['donor_layer'] for r in row['layers']])
            for slot,layer in enumerate(row['layers']):
                cells=struct.unpack_from('>256H',fg[layer['target_layer']],2)
                self.assertTrue(all(cells[i]==0xFFFF for i in outside))
                self.assertFalse(any(v==0 or 0xFEB3<=v<=0xFEC2 for v in cells))
                furniture=[(i,v) for i,v in enumerate(cells) if v not in (0xFFFF,0xFFFE,0x4080)]
                self.assertEqual(len(furniture),1 if slot==0 else 0)
                for item in layer['furniture']:
                    self.assertEqual(cells[item['z']*16+item['x']],int(item['native_item'],16))

    def test_allocation_bounds_loader_arithmetic_and_immutable_runtime(self):
        previous=self.old[BLOB].extract(self.base);expected=bytearray(previous)
        struct.pack_into('>I',expected,4,56)
        expected.extend(bytes(FG_STORAGE-len(expected))+self.files[FG].extract(self.rom))
        self.assertEqual(expected,self.blob)
        self.assertEqual(self.blob[0x1E60:0x1E74],bytes(20))
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.previous['save_runtime']['profile_hex'])
        self.assertEqual(self.report['islander_houses']['foreground_allocation_growth_bytes'],18648)
        self.assertEqual(self.report['villager_houses']['foreground_pointer_count'],498)
        self.assertLessEqual(len(self.blob),0x200000)
        self.assertEqual(self.files[FG].pstart,self.files[BLOB].pstart+FG_STORAGE)
        current=self.files[CODE_VROM].extract(self.rom)
        expected=bytearray(self.old[CODE_VROM].extract(self.base))
        for row in self.report['islander_houses']['loader_patches']:
            at=int(row['address'],16)-CODE_RAM
            self.assertEqual(expected[at:at+4].hex().upper(),row['before'])
            expected[at:at+4]=bytes.fromhex(row['after'])
        self.assertEqual(current,expected)
        high=struct.unpack_from('>I',current,0x80086100-CODE_RAM)[0]&65535
        low=struct.unpack_from('>h',current,0x80086106-CODE_RAM)[0]
        self.assertEqual((high<<16)+low,FG+len(self.files[FG].extract(self.rom)))

    def test_only_reviewed_physical_writes_checksums_and_patch(self):
        self.assertEqual(set(self.files),set(self.old))
        expected=bytearray(self.base)
        for vrom in (BLOB,HOUSE,CODE_VROM,MODULE):
            entry=self.files[vrom]
            self.assertEqual(entry.pstart,self.old[vrom].pstart)
            expected[entry.pstart:entry.pstart+entry.size]=entry.extract(self.rom)
        for vrom in (BLOB,FG):
            at=DMA_START+self.files[vrom].index*16
            expected[at:at+16]=self.rom[at:at+16]
        expected[0x10:0x18]=self.rom[0x10:0x18]
        self.assertEqual(expected,self.rom)
        for vrom,row in self.files.items():
            if vrom not in (BLOB,FG):self.assertEqual(row,self.old[vrom])
        module=self.files[MODULE].extract(self.rom)
        before=bytearray(self.old[MODULE].extract(self.base));before[STARTUP:CONFIG+16]=module[STARTUP:CONFIG+16]
        self.assertEqual(module,before)
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),(BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),56))
        self.assertEqual(sha256(self.base),BASE_SHA)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom),struct.unpack_from('>2I',self.rom,0x10))
        self.assertEqual(apply_ups(self.native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
