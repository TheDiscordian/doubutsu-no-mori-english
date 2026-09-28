"""Shared placement checks: donor search comparison and current cartridge only."""
import json
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
from v3_furniture_pipeline import Source
from v3_holiday_placement import ADDRESS,OWNER_CODE,KEEP,NAMES,contract,observer_contract,patch_reset,patch_manager
from v3_holiday_native import identities
from v3_holiday_events import discover,encode
from v3_campsite_manager import RAM as OWNER,VROM,RELOC,METADATA

OUT=ROOT/os.environ.get('V3_HOLIDAY_PLACEMENT','build/v3-diary-category-work-01/tortimer-observers-01')


class PlacementTests(unittest.TestCase):
    def test_connected_placement_against_complete_donor_search(self):
        source=(ROOT/'local/ac-decomp/src/actor/ac_event_manager.c').read_text()
        reference=source[source.index('static int search_select_unit_cancel_check('):
                         source.index('static int search_empty_unit(')]
        with tempfile.TemporaryDirectory(prefix='v3-holiday-placement-') as temp:
            d=Path(temp);write_new(d/'holiday-placement-reference.inc',reference.encode())
            donor=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
            ids,_=identities();packet=encode(discover(donor))
            data='\n'.join('const unsigned char '+name+'[]={'+','.join(map(str,b))+'};' for name,b in (
                ('af_holiday_native_ids',ids[:128]),('af_holiday_source_ids',ids[128:]),('af_holiday_event_data',packet)))+'\n'
            write_new(d/'holiday-placement-data.h',data.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-parameter',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(d),'tests/v3_holiday_placement_test.c',
                *(f'overlays/v3/{s}.c' for s in ('holiday_placement','holiday_owner','holiday_events','diary_calendar','diary')),
                '-o',str(d/'check')]
            for cmd in (command,[str(d/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_current_packet_bindings_and_retention(self):
        image,report=inputs(OUT/'build-lock.json');npc=report['equipment_resources']['npc_extra']
        placement=npc['events']['placement'];p=npc['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
        code=placement['code'];start=ADDRESS-p['ram'];end=start+code['bytes']
        self.assertEqual(sha256(packet),p['sha256'])
        self.assertEqual(sha256(packet[start:end]),code['sha256'])
        self.assertLessEqual(end,len(packet)-16)
        for name,address in placement['bindings'].items():self.assertEqual(code['symbols'][name],address)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        checked=contract(source,image);self.assertEqual(len(checked['functions']),13)
        observers=observer_contract(source,image)
        self.assertEqual(json.loads(json.dumps(observers)),placement['observers']['contract'])
        self.assertEqual(observers['shrine_landmark_offset'],0x22C)
        self.assertEqual(observers['miko_reservation']['profile'],0xCD)
        for name in ('af_holiday_npc_bind','af_holiday_npc_unregister'):
            self.assertTrue(ADDRESS<=code['symbols'][name]<ADDRESS+code['bytes'])
        self.assertFalse(placement['observers']['event_world_bound'])
        base,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-native-01/build-lock.json')
        oldp=prior['equipment_resources']['npc_extra']['packet'];before=base[oldp['physical']:oldp['physical']+oldp['bytes']]
        owner=placement['owner_code'];oa=OWNER_CODE-p['ram'];oe=oa+owner['bytes']
        self.assertEqual(sha256(packet[oa:oe]),owner['sha256'])
        self.assertEqual(packet[:oa],before[:oa]);self.assertEqual(packet[oe:KEEP-p['ram']],before[oe:KEEP-p['ram']])
        self.assertEqual(packet[KEEP-p['ram']:NAMES-p['ram']],bytes(8))
        self.assertEqual(packet[NAMES-p['ram']:NAMES-p['ram']+4],bytes.fromhex('d0900000'))
        self.assertEqual(packet[NAMES-p['ram']+4:start],before[NAMES-p['ram']+4:start])
        self.assertEqual(packet[end:],before[end:])
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        core=bytearray(by_vrom(base)[CODE_VROM].extract(base));patch_reset(core)
        owners,manager,resizes=patch_manager(base,prior,npc['events'],owner['symbols'],core)
        for vrom,data in owners.items():self.assertEqual(by_vrom(image)[vrom].extract(image),data)
        actual_core=by_vrom(image)[CODE_VROM].extract(image)
        self.assertEqual(actual_core[METADATA-CODE_RAM:METADATA-CODE_RAM+16],core[METADATA-CODE_RAM:METADATA-CODE_RAM+16])
        self.assertEqual(actual_core[0x8007FFC4-CODE_RAM:0x80080080-CODE_RAM],core[0x8007FFC4-CODE_RAM:0x80080080-CODE_RAM])
        self.assertEqual(manager['control_count'],73);self.assertEqual(manager['holiday_owners']['retained_controls'],29)
        self.assertFalse(placement['actor_active']);self.assertTrue(placement['owner_callbacks_bound'])
        self.assertEqual(packet[npc['record']['flags_offset']:npc['record']['flags_offset']+4],bytes(4))

    def test_actual_common_reset_preserves_native_state(self):
        # A bounded interpreter for this changed straight-line block executes
        # both instructions and delay slots. Only its two existing calls are
        # substituted: bzero and the unchanged private-info initializer.
        image,_=inputs(OUT/'build-lock.json');code=by_vrom(image)[CODE_VROM].extract(image)
        native,_=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-native-01/build-lock.json')
        before=by_vrom(native)[CODE_VROM].extract(native)
        def execute(data):
            regs=[0]*32;regs[29]=0x80300000;regs[31]=0x80001234
            memory={0x80126EA0+i:(i*17+3)&255 for i in range(0x10AB8)}
            memory.update({KEEP+i:0xA5 for i in range(12)})
            pc=0x80078A10;pending=None;calls=[]
            def store(at,n,value):
                for i in range(n):memory[at+i]=(value>>(8*(n-1-i)))&255
            for _ in range(50):
                if pc==0x80001234:break
                w=u32(data,pc-CODE_RAM);op=w>>26;rs=w>>21&31;rt=w>>16&31;imm=w&65535
                signed=imm if imm<32768 else imm-65536;next_pending=None
                if op==15:regs[rt]=imm<<16
                elif op==13:regs[rt]=regs[rs]|imm
                elif op==9:regs[rt]=(regs[rs]+signed)&0xFFFFFFFF
                elif op in (35,36):
                    n=4 if op==35 else 1;at=(regs[rs]+signed)&0xFFFFFFFF
                    regs[rt]=int.from_bytes(bytes(memory[at+i] for i in range(n)),'big')
                elif op in (40,41,43):store((regs[rs]+signed)&0xFFFFFFFF,{40:1,41:2,43:4}[op],regs[rt])
                elif op==3:regs[31]=pc+8;next_pending=('call',0x80000000|((w&0x3FFFFFF)<<2))
                elif w&63==8:next_pending=('return',regs[rs])
                elif w!=0:self.fail(f'Unexpected reset instruction {w:08X}')
                pc+=4
                if pending:
                    kind,target=pending
                    if kind=='return':pc=target
                    else:
                        calls.append((target,regs[4],regs[5] if target==0x8002F4C0 else None))
                        if target==0x8002F4C0:
                            for i in range(regs[5]):memory[regs[4]+i]=0
                        else:self.assertEqual(target,0x8008EF94)
                        # Calls may clobber all caller-saved registers.
                        for r in (*range(1,16),24,25):regs[r]=0xBAD00000+r
                pending=next_pending;regs[0]=0
            else:self.fail('Common reset did not return')
            self.assertEqual(regs[29],0x80300000)
            return memory,calls
        old,oldcalls=execute(before);new,newcalls=execute(code)
        self.assertEqual(oldcalls,newcalls)
        for at,value in old.items():
            if not KEEP<=at<KEEP+8:self.assertEqual(new[at],value,f'{at:08X}')
        self.assertEqual([new[KEEP+i] for i in range(8)],[0]*8)


if __name__=='__main__':unittest.main()
