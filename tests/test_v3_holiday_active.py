"""Current cartridge and one connected host check; no native fixture replay."""
import os
from pathlib import Path
import re
import struct
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
from v3_asset_loader import BLOB
from v3_holiday_active import ADDRESS,COMMON,donor_update,patch_core
from v3_holiday_native import identities

CURRENT=ROOT/os.environ.get('V3_HOLIDAY_ACTIVE_BUILD','build/v3-diary-category-work-01/state-transition-connected-01')


class HolidayActiveTests(unittest.TestCase):
    def test_live_dispatch_cartridge(self):
        """Only the current owner/packet changes; no old-build execution."""
        import zlib
        from v3_campsite_manager import VROM,RELOC,RAM as OWNER
        current=ROOT/os.environ.get('V3_HOLIDAY_DISPATCH_BUILD',
            'build/v3-diary-category-work-01/event-owner-connected-02')
        image,r=inputs(current/'build-lock.json');base,prior=inputs(current/'base-lock.json')
        e=r['equipment_resources'];old=prior['equipment_resources'];events=e['npc_extra']['events']
        dispatch=events['dispatch'];symbols=dispatch['code']['symbols']
        for name,start,stop,code in (
                ('npc_extra',ADDRESS,COMMON,dispatch['code']),
                ('holiday_state',0x806F8800,0x806FB200,dispatch['reserved_code'])):
            p=e[name]['packet'];before=old[name]['packet']
            data=image[p['physical']:p['physical']+p['bytes']]
            expected=bytearray(base[before['physical']:before['physical']+before['bytes']])
            self.assertEqual((p['ram'],p['physical'],p['bytes']),
                (before['ram'],before['physical'],before['bytes']))
            self.assertEqual((sha256(data),zlib.crc32(data)),(p['sha256'],p['crc32']))
            a=start-p['ram'];b=stop-p['ram']
            self.assertEqual(sha256(data[a:a+code['bytes']]),code['sha256'])
            self.assertFalse(any(data[a+code['bytes']:b]))
            expected[a:b]=data[a:b];self.assertEqual(data,expected)
        self.assertEqual(e['holiday_fishing']['packet'],e['holiday_state']['packet'])
        files=by_vrom(image);before=by_vrom(base)
        self.assertEqual(files[CODE_VROM].extract(image),before[CODE_VROM].extract(base))
        self.assertEqual(files[RELOC].extract(image),before[RELOC].extract(base))
        actual=files[VROM].extract(image);expected=bytearray(before[VROM].extract(base))
        hooks=dispatch['callbacks_bound'];self.assertEqual(len(hooks),48)
        self.assertEqual(len({h['donor'] for h in hooks}),14)
        names=('start','stop','in','out','behind')
        for h in hooks:
            at=h['address']-OWNER;self.assertEqual(u32(expected,at),h['before'])
            self.assertEqual(h['after'],symbols['af_holiday_dedicated_'+names[h['phase']]])
            struct.pack_into('>I',expected,at,h['after'])
        self.assertEqual(actual,expected)
        self.assertEqual(sha256(actual),r['campsite_manager']['output_sha256'])
        p=e['npc_extra']['packet'];flag=p['physical']+e['npc_extra']['record']['flags_offset']
        self.assertEqual(image[flag:flag+4],bytes(4))
        self.assertEqual(r['save_codec'],prior['save_codec'])
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertTrue(events['active']['owner_dispatch_bound'])
        self.assertFalse(events['active']['owner_services_bound'])
        self.assertEqual(symbols['af_holiday_dedicated_native'],dispatch['reserved_code']['symbols']['af_holiday_dedicated_native'])
        self.assertEqual(symbols['af_holiday_transition_live_fade'],events['transition']['code']['symbols']['af_holiday_transition_live_fade'])
        self.assertEqual(symbols['af_holiday_native_index'],0x804A2B00)
        self.assertEqual(dispatch['additional_resident_bytes'],0)
        self.assertFalse(dispatch['native_execution_verified'])
        # Both changed packets are transferred with their new checksum by the
        # current startup directory; the shared fishing reference stays in sync.
        blob=files[BLOB].extract(image);boot=e['surface_bootstrap']['code'];offset=e['blob_offset']-e['ram']
        table=offset+boot['symbols']['packets']
        rows=[struct.unpack_from('>5I',blob,table+20*i) for i in range(18)]
        for name in ('npc_extra','holiday_state'):
            p=e[name]['packet'];row=next(row for row in rows if row[0]==p['ram'])
            self.assertEqual(row[1:3],(p['physical']|0x80000000,p['bytes']))
            self.assertEqual(u32(blob,offset+row[3]),p['crc32'])

    def test_connected_hourly_source_and_host(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        body,report=donor_update(source);self.assertEqual(len(report['functions']),2)
        header=(ROOT/'local/ac-decomp/include/m_event.h').read_text()
        enum=re.search(r'enum event_table\s*\{[^{}]+\}\s*;',header)[0]
        macros=re.findall(r'^#define mEv_(?:STATUS_|EVENT_HOUR_)\w+[^\n]*',header,re.M)
        forward,_=identities()
        with tempfile.TemporaryDirectory(prefix='v3-holiday-active-') as temp:
            out=Path(temp)
            write_new(out/'holiday-active-source.h',(enum+'\n'+'\n'.join(macros)+'\n'+body).encode())
            write_new(out/'holiday-active-identities.h',('\n'.join(
                'const unsigned char '+name+'[]={'+','.join(map(str,b))+'};'
                for name,b in (('af_holiday_native_ids',forward[:128]),('af_holiday_source_ids',forward[128:])))+'\n').encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),
                '-I'+str(out),'tests/v3_holiday_active_test.c','overlays/v3/holiday_active.c','-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                if r.stdout:print(r.stdout.strip())

    def test_installed_path_and_reset_instructions(self):
        image,current=inputs(CURRENT/'build-lock.json')
        # Inspect the immediate input for preservation; do not execute it.
        base,prior=inputs(CURRENT/'base-lock.json')
        npc=current['equipment_resources']['npc_extra'];active=npc['events']['active'];p=npc['packet']
        data=image[p['physical']:p['physical']+p['bytes']]
        oldp=prior['equipment_resources']['npc_extra']['packet'];before=base[oldp['physical']:oldp['physical']+oldp['bytes']]
        self.assertEqual(data[:ADDRESS-p['ram']],before[:ADDRESS-p['ram']])
        self.assertEqual(data[COMMON-p['ram']+4:],before[COMMON-p['ram']+4:])
        self.assertEqual(data[COMMON-p['ram']:COMMON-p['ram']+4],b'\xff'*4)
        self.assertEqual(sha256(data[ADDRESS-p['ram']:ADDRESS-p['ram']+active['code']['bytes']]),active['code']['sha256'])
        actual=by_vrom(image)[CODE_VROM].extract(image)
        # Restore only each recorded input instruction block in memory, then
        # let the complete original-function guards verify that input.
        expected=bytearray(actual)
        for hook in active['hooks']:
            at=hook['address']-CODE_RAM
            self.assertEqual(actual[at:at+hook['bytes']],bytes.fromhex(hook['after']))
            expected[at:at+hook['bytes']]=bytes.fromhex(hook['before'])
        hooks,_=patch_core(expected,active['code']['symbols']['af_holiday_active_update'])
        self.assertEqual(actual[0x8007D140-CODE_RAM:0x80081E48-CODE_RAM],expected[0x8007D140-CODE_RAM:0x80081E48-CODE_RAM])
        self.assertEqual(actual[0x80078A10-CODE_RAM:0x80078A88-CODE_RAM],expected[0x80078A10-CODE_RAM:0x80078A88-CODE_RAM])
        self.assertEqual(hooks,active['hooks'])
        self.assertEqual(current['save_codec'],prior['save_codec'])
        self.assertEqual(current['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertEqual(data[npc['record']['flags_offset']:npc['record']['flags_offset']+4],bytes(4))
        self.assertFalse(active['native_execution_verified'])
        # Execute the actual rewritten ClearEventInfo prefix, including call
        # delay slots. Native memset and saved-event reset are bounded doubles.
        regs=[0]*32;regs[29]=0x807FF000;regs[31]=0x80001234
        memory={a:0x12345678 for a in range(0x8013A0D8,0x8013A104,4)};calls=[]
        pc=0x8007D1DC;pending=None
        while pc<0x8007D214:
            w=u32(actual,pc-CODE_RAM);op=w>>26;rs=w>>21&31;rt=w>>16&31;imm=w&65535
            signed=imm if imm<32768 else imm-65536;call=None
            if op==9:regs[rt]=(regs[rs]+signed)&0xFFFFFFFF
            elif op==15:regs[rt]=imm<<16
            elif op==43:memory[(regs[rs]+signed)&0xFFFFFFFF]=regs[rt]
            elif op==3:call=0x80000000|((w&0x3FFFFFF)<<2);regs[31]=pc+8
            elif w==0:pass
            elif op==0 and w&63==37:regs[w>>11&31]=regs[rs]|regs[rt]
            else:self.fail(f'Unexpected reset instruction {w:08X}')
            if pending is not None:
                calls.append(pending)
                if pending==0x8003B9B0:
                    self.assertEqual((regs[4],regs[5],regs[6]),(0x8013A0E0,0,28))
                    for at in range(regs[4],regs[4]+regs[6],4):memory[at]=0
                else:self.assertEqual(pending,0x8007D4A0)
                # Every caller-saved register may change across either call.
                for r in (*range(2,16),24,25):regs[r]=0xBAD00000+r
            regs[0]=0;pending=call;pc+=4
        self.assertEqual(calls,[0x8003B9B0,0x8007D4A0])
        self.assertEqual(memory[COMMON],0xFFFFFFFF)
        self.assertEqual(memory[0x807FF000-4],0x80001234)
        for at in range(0x8013A0E0,0x8013A0FC,4):self.assertEqual(memory[at],0)
        for at in (0x8013A0D8,0x8013A0DC,0x8013A0FC,0x8013A100):self.assertEqual(memory[at],0x12345678)
        # Common reset insertion follows the existing t9=-1/t0=806F0000 loads.
        words=struct.unpack_from('>30I',actual,0x80078A10-CODE_RAM)
        self.assertEqual((words[13],words[21],words[24]),(0x2419FFFF,0x3C08806F,0xAD193FE0))
        e=current['equipment_resources'];stage=npc['events']['transition'];p=e['holiday_state']['packet']
        raw=image[p['physical']:p['physical']+p['bytes']];old=stage['original_packet']
        self.assertEqual(p['bytes'],0xC000)
        self.assertEqual(raw[:0x8000],base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual(sha256(raw[0x8000:0x8000+stage['code']['bytes']]),stage['code']['sha256'])
        self.assertEqual(raw[-16:],bytes.fromhex('41464853')*4)
        self.assertFalse(any(raw[0x8000+stage['code']['bytes']:-16]))
        self.assertFalse(stage['native_scene_services_bound'])
        self.assertEqual(current['shared_runtime_refresh']['additional_resident_bytes'],0x4000)
        boot=e['surface_bootstrap']['code'];blob=by_vrom(image)[BLOB].extract(image)
        ram=e['surface_bootstrap']['ram'];offset=e['blob_offset']+ram-e['ram']
        code=blob[offset:offset+boot['bytes']];self.assertEqual(sha256(code),boot['sha256'])
        symbols=boot['symbols'];self.assertEqual(u32(code,symbols['holiday_state_crc']-ram),p['crc32'])
        table=symbols['packets']-ram
        rows=[tuple(u32(code,table+i*20+j*4) for j in range(5)) for i in range(18)]
        self.assertEqual(rows[-1],(p['ram'],p['physical']|0x80000000,p['bytes'],symbols['holiday_state_crc'],0))


if __name__=='__main__':unittest.main()
