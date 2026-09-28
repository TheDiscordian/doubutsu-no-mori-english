"""Connected cover installation and current room adapter, without old ROM replay."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_import_storage import ROWS, ITEMS, slot
from npc_mail_show import relocate_verified_data

OUT = ROOT/os.environ.get('V3_DIARY_ROOM', 'build/v3-diary-category-work-01/room-art-02')


class DiaryRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = inputs(OUT/'build-lock.json')
        cls.base, cls.prior = inputs(OUT/'base-lock.json')
        cls.d = cls.report['equipment_resources']['diary_items']
        cls.a = cls.d['room_art']
        cls.files, cls.oldfiles = by_vrom(cls.image), by_vrom(cls.base)

    def test_complete_covers_profiles_relocation_and_retained_consumers(self):
        a, d = self.a, self.d
        data = self.files[a['vrom']].extract(self.image)
        rel = self.files[a['reloc']].extract(self.image)
        old = self.oldfiles[a['previous_vrom']].extract(self.base)
        old_rel = self.oldfiles[a['previous_reloc']].extract(self.base)
        self.assertEqual((sha256(data), sha256(rel)), (a['sha256'], a['relocation_sha256']))
        self.assertEqual((a['rows'], len(d['profiles']), a['art_bytes']), (50, 16, 35616))
        self.assertEqual(self.files[a['vrom']].index, self.oldfiles[a['previous_vrom']].index)
        self.assertEqual(self.files[a['reloc']].index, self.files[a['vrom']].index+1)
        expected = bytearray(old)
        for p in a['table_patches']:
            self.assertEqual(u32(expected, p['offset']), p['before'])
            struct.pack_into('>I', expected, p['offset'], p['after'])
        self.assertEqual(data[:len(old)], expected)
        self.assertEqual(data[len(old):a['table_offset']], bytes(16))
        self.assertEqual(data[a['table_offset']:a['table_offset']+34*20], old[0xFB0:0xFB0+34*20])
        self.assertEqual(data[a['table_offset']+50*20:a['table_offset']+51*20], bytes(20))
        blob = self.files[BLOB].extract(self.image)
        core = self.files[CODE_VROM].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', core, 0x80101330-CODE_RAM),
            (a['vrom'], a['vrom']+len(data), a['ram'], a['ram']+len(data)))
        for style, r in enumerate(d['profiles']):
            raw = (ROOT/a['prepared']/r['source']['object_file']).read_bytes()
            off, n = r['object_offset'], r['object_bytes']
            self.assertEqual(data[off:off+n], raw)
            self.assertEqual(sha256(raw), r['object_sha256'])
            self.assertEqual(r['object_vrom'], a['vrom']+off)
            i = slot(int(r['item_id'], 16))
            row, meta = blob[ROWS+i*80:ROWS+(i+1)*80], blob[ITEMS+i*32:ITEMS+(i+1)*32]
            self.assertEqual(sha256(row), r['profile_record_sha256'])
            self.assertEqual(sha256(meta), r['item_record_sha256'])
            self.assertEqual(row[8:76].hex(), r['profile_hex'])
            self.assertEqual(struct.unpack_from('>HHI', row), (1087+style, 0x30FC+style*4, 0))
            self.assertEqual(struct.unpack_from('>HH', meta, 28), (0x2B10+style, 0))
            self.assertFalse(blob[0x40+i//8] & (1 << (i&7)))
            table = struct.unpack_from('>HH4I', data, a['table_offset']+(34+style)*20)
            self.assertEqual(table[:2], (0x2B10+style,)*2)
            lists = {a['ram']+off+m['native_offset'] for m in r['source']['models']}
            self.assertTrue(any(table[2:]))
            self.assertTrue(all(not v or v in lists for v in table[2:]))
        for patch, original, target in a['fixups']:
            self.assertEqual(u32(data, patch), original)
            self.assertEqual(original >> 24, 6)
            self.assertTrue(a['art_offset'] <= target < len(data))
        for address in (0x801A0010, 0x80310010):
            loaded = relocate_verified_data(SimpleNamespace(ram=a['ram'], resident_bytes=len(data),
                sections=struct.unpack_from('>5I', rel)), data, rel, address)
            previous = relocate_verified_data(SimpleNamespace(ram=a['ram'], resident_bytes=len(old)+16,
                sections=struct.unpack_from('>5I', old_rel)), old, old_rel, address)
            changed = {i for p in a['table_patches'] for i in range(p['offset'], p['offset']+4)}
            self.assertFalse(any(x != y and i not in changed for i, (x, y) in enumerate(zip(loaded, previous))))
            for style in range(16):
                at = a['table_offset']+(34+style)*20+4
                for i in range(4):
                    value = u32(data, at+i*4)
                    self.assertEqual(u32(loaded, at+i*4), value-a['ram']+address if value else 0)
        # Stable exported entries route to the new implementation; no other code changes.
        g = self.report['equipment_resources']['room_goods']
        p = g['packet']; oldblob = self.oldfiles[BLOB].extract(self.base)
        expect = bytearray(oldblob[p['blob_offset']:p['blob_offset']+p['bytes']])
        for h in a['dispatch']:
            at = h['address']-p['ram']
            self.assertEqual(expect[at:at+8].hex(), h['before'])
            expect[at:at+8] = bytes.fromhex(h['after'])
        self.assertEqual(blob[p['blob_offset']:p['blob_offset']+p['bytes']], expect)
        p = d['packet']; packet = self.image[p['physical']:p['physical']+p['bytes']]
        oldp = self.prior['equipment_resources']['diary_items']['packet']
        expect = bytearray(self.base[oldp['physical']:oldp['physical']+oldp['bytes']])
        expect[0x800:0x800+a['compiled']['bytes']] = packet[0x800:0x800+a['compiled']['bytes']]
        expect[0x3000:0x3000+a['config_bytes']] = packet[0x3000:0x3000+a['config_bytes']]
        self.assertEqual(packet, expect)
        self.assertEqual((sha256(packet), zlib.crc32(packet)), (p['sha256'], p['crc32']))
        self.assertEqual(self.report['save_runtime'], self.prior['save_runtime'])
        self.assertEqual(self.report['equipment_resources']['scenery'], self.prior['equipment_resources']['scenery'])

    def test_sanitized_current_model_rebase_and_all_style_rotation(self):
        a = self.a
        header = (0x41464452, 1, len(a['fixups']), a['bytes'], a['table_offset'], a['rows'], a['art_offset'], a['bytes'])
        config = header+tuple(v for row in a['fixups'] for v in row)
        with tempfile.TemporaryDirectory(prefix='v3-diary-room-') as tmp:
            tmp = Path(tmp)
            (tmp/'goods_config.inc').write_text('u32 af_test_goods_model_config[] = {'+
                ','.join(hex(v)+'u' for v in config)+'};\n')
            flags = [s for s in a['compiled']['flags'] if s.startswith('-D')]
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fno-pie', '-no-pie', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                *flags, '-I'+str(tmp), str(ROOT/'tests/v3_diary_room_test.c'), '-o', str(tmp/'test')],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(tmp/'test')], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('all 16 covers', result.stdout)


class DiaryCatalogueTests(unittest.TestCase):
    def test_current_catalogue_scoring_and_packet_consumers(self):
        from v3_diary_items import catalogue_rows
        from v3_furniture_pipeline import Source
        from v3_furniture_capacity import checked
        import v3_catalogue as catalogue
        import v3_hra as hra
        import v3_feng_shui as feng
        out=ROOT/os.environ.get('V3_DIARY_CATALOGUE','build/v3-diary-category-work-01/catalogue-03')
        image,r=inputs(out/'build-lock.json');base,prior=inputs(out/'base-lock.json')
        files,oldfiles=by_vrom(image),by_vrom(base)
        e=r['equipment_resources'];d=e['diary_items'];cat=r['catalogue']
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rows=catalogue_rows(source)
        self.assertEqual(d['catalogue']['imports'],rows)
        self.assertEqual([x for x in cat['imports'] if x.get('representation')=='diary'],rows)
        self.assertEqual([x for x in cat['imports'] if x.get('representation')!='diary'],prior['catalogue']['imports'])
        data=files[catalogue.VROM].extract(image)
        at=cat['code']['symbols']['af_v3_catalogue_order']-catalogue.RAM
        self.assertEqual(data[at+436*4:at+cat['total_rows']*4],
            b''.join(struct.pack('>HH',x['catalogue_index'],x['mode']) for x in cat['imports']))
        self.assertIn(f'-DAF_V3_DIARY_CATALOGUE_QUERY=0x{d["catalogue"]["query"]:X}u',cat['linked_code']['flags'])
        self.assertEqual(checked(image,r),12288)
        self.assertEqual(cat['category_pool_bytes']-prior['catalogue']['category_pool_bytes'],256)
        for key,tool,width in (('hra',hra,4),('feng_shui',feng,2)):
            previous=bytearray(oldfiles[tool.NEW_VROM].extract(base));actual=files[tool.NEW_VROM].extract(image)
            at=r[key]['metadata_address']-tool.RAM
            for row in d['scoring']['rows']:
                offset=at+row['runtime_index']*width
                previous[offset:offset+width]=bytes.fromhex(row['native_hra_hex'] if width==4 else row['feng_hex'])
            if key=='hra':
                h=d['scoring']['clutter'];offset=h['address']-tool.RAM
                self.assertEqual(u32(previous,offset),h['before'])
                struct.pack_into('>I',previous,offset,h['after'])
                self.assertEqual(h['after'],0x0C000000 | (h['target']>>2 & 0x3FFFFFF))
                self.assertEqual(h['compiled']['symbols']['af_diary_clutter_query'],0x806E1000)
            self.assertEqual(actual,previous)
            self.assertEqual(sha256(actual),r[key]['output_sha256'])
        p=d['packet'];oldp=prior['equipment_resources']['diary_items']['packet']
        packet=image[p['physical']:p['physical']+p['bytes']]
        expected=bytearray(base[oldp['physical']:oldp['physical']+oldp['bytes']])
        count=d['scoring']['clutter']['compiled']['bytes']
        expected[0x1000:0x1000+count]=(out/'diary-catalogue/code.bin').read_bytes()
        self.assertEqual(packet,expected)
        self.assertEqual((sha256(packet),zlib.crc32(packet)),(p['sha256'],p['crc32']))
        a=d['room_art']
        self.assertEqual(files[a['vrom']].extract(image),oldfiles[a['vrom']].extract(base))
        self.assertEqual(d['profiles'],prior['equipment_resources']['diary_items']['profiles'])
        self.assertEqual(r['save_runtime'],prior['save_runtime'])
        blob=files[BLOB].extract(image);boot=e['surface_bootstrap']['code']
        at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        self.assertEqual(struct.unpack_from('>5I',blob,at+15*20)[:3],(p['ram'],p['physical']|0x80000000,p['bytes']))
        crc=u32(blob,at+15*20+12)
        self.assertEqual(u32(blob,e['blob_offset']+crc-e['ram']),zlib.crc32(packet))

    def test_sanitized_connected_previews_and_clutter(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-catalogue-') as tmp:
            target=Path(tmp)/'test'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DAF_V3_DIARY_CATALOGUE_QUERY=1',str(ROOT/'tests/v3_held_catalogue_test.c'),'-o',str(target)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(target)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('All 16 diary profiles',result.stdout)


if __name__ == '__main__':
    unittest.main()
