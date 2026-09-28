"""Connected native directory checks; no new emulator harness or old-build run."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_furniture_install import inputs
from v3_holiday_events import encode
from v3_holiday_native import DAYS,REFERENCES,IDS,OWNER,VROM,RELOC,identities,patch_core,patch_manager
from v3_registry import SPECIAL_NPCS

OUT=ROOT/os.environ.get('V3_HOLIDAY_NATIVE','build/v3-diary-category-work-01/tortimer-native-01')


class NativeDirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.npc=cls.report['equipment_resources']['npc_extra']
        cls.native=cls.npc['events']['native_directory']

    def test_installed_consumers_and_retention(self):
        base,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-events-02/build-lock.json')
        files=by_vrom(self.image);before_files=by_vrom(base)
        original=before_files[CODE_VROM].extract(base);expected=bytearray(original)
        hooks=patch_core(expected);actual=files[CODE_VROM].extract(self.image)
        self.assertEqual(hooks,self.native['core_hooks'])
        self.assertEqual(actual[0x8007D140-CODE_RAM:0x80081E48-CODE_RAM],
                         expected[0x8007D140-CODE_RAM:0x80081E48-CODE_RAM])
        owners,manager=patch_manager(base)
        for vrom,data in owners.items():self.assertEqual(files[vrom].extract(self.image),data)
        self.assertEqual(manager,self.native['manager'])
        self.assertEqual(len(manager['removed_relocations']),6)
        self.assertEqual(u32(owners[VROM],0x809622C8-OWNER),29) # No unbound actor callbacks enabled.
        self.assertEqual(u32(actual,0x8007E668-CODE_RAM),u32(original,0x8007E668-CODE_RAM))
        for table in ('save_runtime',):
            self.assertEqual(self.report[table]['profile_hex'],prior[table]['profile_hex'])
        p=self.npc['packet'];packet=self.image[p['physical']:p['physical']+p['bytes']]
        oldp=prior['equipment_resources']['npc_extra']['packet']
        old=base[oldp['physical']:oldp['physical']+oldp['bytes']]
        self.assertEqual(sha256(packet),p['sha256'])
        c=self.native['code'];self.assertEqual(sha256(packet[0x8300:0x8300+c['bytes']]),c['sha256'])
        ids,rows=identities();self.assertEqual(rows,self.native['identities'])
        self.assertEqual(packet[IDS-p['ram']:IDS-p['ram']+256],ids)
        self.assertEqual(packet[:0x8300],old[:0x8300]);self.assertEqual(packet[0x9800:IDS-p['ram']],old[0x9800:IDS-p['ram']])
        self.assertEqual(packet[IDS-p['ram']+256:],old[IDS-p['ram']+256:])
        self.assertFalse(self.native['actor_active']);self.assertFalse(self.native['native_schedule_caller_bound'])
        self.assertEqual(packet[self.npc['record']['flags_offset']:self.npc['record']['flags_offset']+4],bytes(4))
        self.assertEqual((self.native['days_ram'],self.native['manager_references_ram']),(DAYS,REFERENCES))
        bad=bytearray(original);bad[0x8007E2B0-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'complete native event core'):patch_core(bad)

    def test_connected_host_directory(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-native-') as temp:
            d=Path(temp);ids,_=identities();packet=encode(self.npc['events']['contract'])
            data='\n'.join('const unsigned char '+name+'[]={'+','.join(map(str,b))+'};'
                for name,b in (('af_holiday_native_ids',ids[:128]),('af_holiday_source_ids',ids[128:]),
                               ('af_holiday_event_data',packet)))+'\n'
            write_new(d/'holiday-native-data.h',data.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),
                '-I'+str(d),f"-DAF_HOLIDAY_MIKO_PROFILE={SPECIAL_NPCS['GAFE01-r0/npc/ev-miko']['profile']}",
                'tests/v3_holiday_native_test.c','overlays/v3/holiday_native.c','overlays/v3/holiday_observers.c',
                'overlays/v3/holiday_events.c','overlays/v3/diary_calendar.c',
                'overlays/v3/diary.c','-o',str(d/'check')]
            for cmd in (command,[str(d/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_actual_manager_capacity_branch(self):
        # Execute just the changed straight-line MIPS block, including the taken
        # branch's delay slot. This tests the emitted instructions, not a C model
        # with an accidentally corrected bound. No emulator fixture is started.
        owner=by_vrom(self.image)[VROM].extract(self.image)
        for count in (0,31,32,79,80,0xFFFFFFFF):
            regs=[0]*32;regs[2]=count;regs[17]=0x80200000
            regs[18]=0x80300000;regs[19]=REFERENCES;writes={};pc=0x8096131C;target=None
            while pc<0x80961340:
                w=u32(owner,pc-OWNER);op=w>>26;rs=w>>21&31;rt=w>>16&31;rd=w>>11&31;imm=w&65535
                next_target=None
                if op==11:regs[rt]=int(regs[rs]<imm)
                elif op==4:
                    if regs[rs]==regs[rt]:next_target=pc+4+4*(imm if imm<32768 else imm-65536)
                elif op==9:regs[rt]=(regs[rs]+imm)&0xFFFFFFFF
                elif op==43:writes[(regs[rs]+imm)&0xFFFFFFFF]=regs[rt]
                elif w&63==0:regs[rd]=(regs[rt]<<(w>>6&31))&0xFFFFFFFF
                elif w&63==33:regs[rd]=(regs[rs]+regs[rt])&0xFFFFFFFF
                else:self.fail(f'Unexpected instruction {w:08X}')
                regs[0]=0;pc=target if target is not None else pc+4;target=next_target
            self.assertEqual(writes,{REFERENCES+count*4:0x80200000,0x80300000:count+1} if count<80 else {})


if __name__=='__main__':unittest.main()
