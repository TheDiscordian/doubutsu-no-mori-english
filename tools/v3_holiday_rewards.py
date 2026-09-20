"""Compile complete source holiday selectors; actor/calendar installation is separate."""
import json
import os
import struct
import subprocess

from aflib import sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT
from toolchain import IMAGE

FUNCTIONS=(
    (0x7C31C,244,'48321dd6e22de9f11751b89f9557c5be837f142f70b36bbe5cbd8ff933ea8234'),
    (0x7BB40,68,'4e63537fb5685f289541d14da7a01f36fadfeaae1b522cc29888747090df787e'),
    (0x77614,72,'edf357ca53e07880d074757d2ea0dfb42ae6de89bdd48523565a1bf620797e4d'),
    (0x1B4844,180,'a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc'),
    (0x1B48F8,172,'adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699'))
SOURCES=('tools/v3_holiday_rewards.py','tools/v3_furniture_pipeline.py',
    'overlays/v3/holiday_rewards.c','overlays/v3/holiday_rewards.h')


def discover(source):
    functions=[];code={}
    for at,n,digest in FUNCTIONS:
        raw,r=source.function(at)
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed complete holiday source function')
        code[at]=raw;functions.append(r)
    module=u32(source.rel,0);rng=(10,0,4,0x8005CCF4)
    expected=(
        {0x3C:rng,0xA0:rng,0x26:(6,module,5,0x1074C),0x2E:(4,module,5,0x1074C),
         0x42:(6,module,4,0x2070),0x46:(4,module,4,0x2070),
         0x6A:(6,module,6,0xBC40),0x6E:(4,module,6,0xBC40),
         0xA6:(6,module,4,0x2074),0xAE:(4,module,4,0x2074),
         0xD2:(6,module,5,0x10714),0xDA:(4,module,5,0x10714)},
        {0xC:rng,0x12:(6,module,4,0x2068),0x1A:(4,module,4,0x2068)}, {},
        {0x2E:(6,module,6,0xBC40),0x36:(4,module,6,0xBC40)},
        {0x6A:(6,module,6,0xBC40),0x72:(4,module,6,0xBC40)})
    if any(r['relocations']!=e for r,e in zip(functions,expected,strict=True)):
        raise ValueError('Changed complete holiday source dependencies')
    fixed=source.raw('soncho_item_table$582');events=source.raw('event_table')
    if (sha256(fixed)!='2bf4a655de09672b8c202cad690e6595cae1859656b5f379e9b9347822ea2fd9' or
            sha256(events)!='a166d30f03dd45dfe223f04c1dfe8c3ccf6c6bad27731cebe2f79cd285e49136' or
            source.symbol('soncho_item_table$582')!=(0x10714,56) or source.symbol('event_table')!=(0x106F8,28) or
            source.pointers(0x10714,56) or source.pointers(0x106F8,28)):
        raise ValueError('Changed complete holiday reward/calendar table')
    table,n=0x1074C,104
    name,at,size=source.containing(table,exact=True)
    targets={p:r for p,r in source.relocations.items() if table<=p<table+n}
    if (at!=table or size!=n or any(source.data[table:table+n]) or
            set(targets)!=set(range(table,table+n,4)) or any(r[:3]!=(1,True,1) for r in targets.values()) or
            sha256(json.dumps(targets,sort_keys=True,separators=(',',':')).encode())!=
                '10a50ad380d828482ad9294730a706a0757c4e549f6e05daac9d723e6e8e18c5'):
        raise ValueError('Incomplete source holiday selector jump table')
    raw=code[0x7C31C];station=code[0x7BB40]
    constants=[]
    for at,expected_count in ((0x2070,15),(0x2068,15),(0x2074,9)):
        data=source.rel[source.sections[4][0]+at:source.sections[4][0]+at+4]
        if data!=struct.pack('>f',expected_count):raise ValueError('Changed complete holiday random range')
        constants.append(dict(section=4,offset=at,hex=data.hex(),count=expected_count))
    def furniture(index):
        if not 0<=index<1266:raise ValueError('Holiday furniture index exceeds donor tables')
        return 0x1000+index*4 if index<1024 else 0x3000+(index-1024)*4
    forms={0x3C:('random-diary',[((u32(raw,0x5C)&65535)+(i&15)) for i in range(constants[0]['count'])]),
        0x68:('gender',[u32(raw,at)&65535 for at in (0x84,0x8C)]),
        0x94:('random-station',[furniture((u32(station,0x2C)&65535)+i) for i in range(constants[1]['count'])]),
        0xA0:('random-flower',[furniture((u32(raw,0xC0)&65535)+i) for i in range(constants[2]['count'])])}
    rows=[]
    for event,calendar in enumerate(events):
        target=targets[table+event*4][3]-0x7C31C if event<26 else 0xD0
        if target==0xD0:kind,items='fixed',[struct.unpack_from('>H',fixed,event*2)[0]]
        elif target in forms:kind,items=forms[target]
        else:raise ValueError('Unsupported holiday selector branch')
        rows.append(dict(event=event,calendar_event=calendar,selector=kind,source_items=[f'{i:04X}' for i in items]))
    return dict(format='AFV3-HOLIDAY-REWARDS-1',rows=rows,functions=functions,
        jump_table=dict(symbol=name,offset=table,bytes=n,targets=targets),constants=constants,
        fixed_table_sha256=sha256(fixed),event_table_sha256=sha256(events),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        new_year_diary_variants=15,source_diary_off_by_one_preserved=True,
        runtime_installed=False,calendar_installed=False,npc_installed=False,acquisition_installed=False)


def encode(description):
    rows=description['rows'];candidates=[];records=bytearray()
    if [r['event'] for r in rows]!=list(range(28)):raise ValueError('Incomplete holiday reward events')
    for r in rows:
        items=[int(i,16) for i in r['source_items']]
        mode={'fixed':0,'random-diary':1,'random-station':1,'random-flower':1,'gender':2}[r['selector']]
        if (not 1<=len(items)<=16 or any(not 0<i<65536 for i in items) or
                mode==0 and len(items)!=1 or mode==2 and len(items)!=2 or not 0<=r['calendar_event']<256):
            raise ValueError('Invalid complete holiday selector range')
        records.extend(struct.pack('>HHBBH',len(candidates),len(items),mode,0,r['calendar_event']));candidates.extend(items)
    if len(candidates)>128:raise ValueError('Holiday candidates exceed bounded format')
    return struct.pack('>4s6H',b'AFHG',1,28,len(candidates),8,2,0)+records+struct.pack('>'+str(len(candidates))+'H',*candidates)


def compile_kernel(output):
    """Prepare a relocatable o32 kernel; do not invent a resident address."""
    compiler='/n64_toolchain/bin/mips64-elf-'
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint']
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-ffunction-sections',
        '-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror']
    subprocess.run(docker+[compiler+'gcc',IMAGE,*flags,'/source/overlays/v3/holiday_rewards.c','-o','holiday_rewards.o'],
        check=True,capture_output=True,text=True,timeout=60)
    undefined=subprocess.run(docker+[compiler+'nm',IMAGE,'--undefined-only','holiday_rewards.o'],
        check=True,capture_output=True,text=True,timeout=30).stdout
    if undefined.strip():raise ValueError('Holiday kernel has unresolved external dependencies')
    return dict(format='ELF-o32-MIPS-big-endian',sha256=sha256((output/'holiday_rewards.o').read_bytes()),
        compiler_image=IMAGE,flags=flags,linked=False,resident_address=None)


def prepare(source,output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored holiday output')
    report=discover(source);data=encode(report)
    output.mkdir(parents=True);write_new(output/'holiday-rewards.bin',data)
    report['kernel']=compile_kernel(output)
    report.update(bytes=len(data),sha256=sha256(data),events=len(report['rows']),
        candidates=sum(len(r['source_items']) for r in report['rows']),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'rewards.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report
