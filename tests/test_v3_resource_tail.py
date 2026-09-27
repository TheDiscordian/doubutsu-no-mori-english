"""Whole-resource spill and subsequent reuse against the current cartridge."""
import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,DMA_START
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,reuse_resource_tail,place_resource_tail
from v3_resource_capacity import LIMIT


class ResourceTailTests(unittest.TestCase):
    def test_complete_spill_and_reuse(self):
        image,prior=inputs(ROOT/'build/v3-creature-world-work-01/connected-15/build-lock.json')
        files=by_vrom(image);old=files[BLOB].extract(image)
        blob,reused=reuse_resource_tail(image,prior,old)
        resources={r['vrom']:files[r['vrom']].extract(image) for r in reused['retired_resources']}
        # The real current tail has only 128 bytes spare without relocating
        # these owners. This fixture models a complete 40-KiB runtime resource.
        added=b'\xA5'*0xA000;blob.extend(added)
        moves,writes,padding=place_resource_tail(image,prior,blob,resources,LIMIT,
            reservations=prior['physical_resources'])
        self.assertEqual(len(moves),3);self.assertEqual(set(writes),set(resources))
        self.assertEqual(len(blob),len(old));self.assertGreater(padding['bytes'],0)
        self.assertEqual(blob[reused['blob_offset']:padding['blob_offset']],added)
        result=bytearray(image);start=files[BLOB].pstart;result[start:start+len(blob)]=blob
        for row in moves:
            self.assertNotIn('blob_offset',row)
            self.assertGreaterEqual(row['physical'],prior['resource_capacity']['reserved_physical_end'])
            raw=writes[row['vrom']];self.assertEqual(sha256(raw),row['sha256'])
            result[row['physical']:row['physical']+len(raw)]=raw
            struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
                row['vrom'],row['vrom']+len(raw),row['physical'],0)
        updated=copy.deepcopy(prior);updated['blob_sha256']=sha256(blob)
        updated['automatic_furniture'].update(resource_moves=moves,resource_tail_padding=padding)
        current=by_vrom(result)
        self.assertEqual(set(current),set(files))
        restored=bytearray(result)
        for row in moves:
            at=DMA_START+files[row['vrom']].index*16
            restored[at:at+16]=image[at:at+16]
        for vrom,entry in files.items():
            if vrom!=BLOB:self.assertEqual(current[vrom].extract(restored),entry.extract(image))
        next_blob,receipt=reuse_resource_tail(result,updated,bytes(blob))
        self.assertEqual(len(next_blob),padding['blob_offset'])
        self.assertEqual(receipt['retired_resources'],[])
        self.assertEqual(receipt['external_resources'],moves)
        next_blob.extend(b'\x5A'*16)
        retained,next_writes,next_padding=place_resource_tail(result,updated,next_blob,resources,LIMIT,
            reservations=prior['physical_resources'])
        self.assertEqual(next_writes,{})
        self.assertEqual([r['physical'] for r in retained],[r['physical'] for r in moves])
        self.assertEqual(next_padding['bytes'],padding['bytes']-16)
        wrong=copy.deepcopy(updated);wrong['automatic_furniture']['resource_moves'][0]['physical']+=16
        with self.assertRaises(ValueError):reuse_resource_tail(result,wrong,bytes(blob))
        damaged=bytearray(blob);damaged[-1]=1;wrong=copy.deepcopy(updated);wrong['blob_sha256']=sha256(damaged)
        with self.assertRaises(ValueError):reuse_resource_tail(result,wrong,bytes(damaged))
        with self.assertRaises(ValueError):
            place_resource_tail(result,updated,bytearray(LIMIT-BLOB+16),resources,LIMIT)


if __name__=='__main__':unittest.main()
