"""Link the complete bank/save/controller packet at checked owned addresses.

The native entry plan uses actual linked symbols. Linking is not installing:
calendar/actor registration, resource relocation, text/save redirects, mail,
and profile composition remain the enclosing category installer's consumers.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_bank_frontend import ROOTS
from v3_console_disk_install import reservations

RAM,ART,END=0x807D8040,0x807E2040,0x807E8040
CODE_GUARD=bytes.fromhex('424E4347')*4
ART_GUARD=bytes.fromhex('424E4147')*4
SOURCES=('tools/v3_bank_link.py','tools/v3_bank_april_install.py',
    'overlays/v3/bank_config.c','overlays/v3/bank.ld')


def layout(prior):
    if any(a<END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Complete bank packet overlaps retained resident memory')
    return dict(packet=dict(ram=RAM,bytes=END-RAM),
        code=dict(ram=RAM,bytes=ART-RAM-16),code_guard=dict(ram=ART-16,bytes=16),
        artwork=dict(ram=ART,bytes=END-ART-16),art_guard=dict(ram=END-16,bytes=16))


def relocate_art(data,receipt):
    if len(data)!=receipt['bytes'] or sha256(data)!=receipt['sha256']:
        raise ValueError('Changed complete prepared bank artwork')
    if len(data)>END-ART-16:raise ValueError('Complete bank artwork exceeds its reservation')
    out=bytearray(data);hooks=[];models=receipt['compiled_models'];resources=receipt['resources']
    if {r['symbol'] for r in models}!=set(ROOTS):raise ValueError('Incomplete bank drawing roots')
    regions=[(r['native_offset'],r['native_offset']+r['bytes'],r['kind']) for r in resources]
    for row in resources:
        at,n=row['native_offset'],row['bytes']
        if not 0<=at<at+n<=len(data) or sha256(data[at:at+n])!=row['output_sha256']:
            raise ValueError('Changed complete bank art resource: '+row['symbol'])
    for model in models:
        at,n=model['native_offset'],model['bytes']
        if (at%8 or n%8 or not 0<=at<at+n<=len(data) or
                sha256(data[at:at+n])!=model['output_sha256']):
            raise ValueError('Changed complete bank display list: '+model['symbol'])
        for pos in range(at,at+n,8):
            command,target=struct.unpack_from('>II',data,pos);op=command>>24
            if op not in (0x01,0xFD,0xDE):continue
            if target>>24!=6:raise ValueError('Unreviewed bank display-list resource pointer')
            offset=target&0xFFFFFF
            if op==0xDE:
                valid=any(offset==m['native_offset'] for m in models)
            else:
                kinds={'vertices'} if op==0x01 else {'palette','texture'}
                valid=any(a<=offset<b and k in kinds for a,b,k in regions)
            if not valid:raise ValueError('Bank display-list pointer escapes complete resources')
            # Physical segment-zero addresses avoid taking segment six away
            # from the native submenu/font's retained owners. No texels,
            # vertices, commands, or model dimensions change.
            relocated=(ART&0x1FFFFFFF)+offset
            struct.pack_into('>I',out,pos+4,relocated)
            hooks.append(dict(offset=pos+4,before=target,after=relocated,opcode=op))
    if not hooks:raise ValueError('Complete bank artwork has no bound native resources')
    allowed={h['offset']+i for h in hooks for i in range(4)}
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(data,out))):
        raise ValueError('Bank relocation changes unrelated resource bytes')
    symbols={row['symbol']:ART+row['native_offset'] for row in models}
    return bytes(out),dict(sha256=sha256(out),bytes=len(out),original_sha256=sha256(data),
        root_symbols=symbols,pointer_bindings=hooks,resource_bytes_preserved=True,
        native_segment_six_unchanged=True)


def link(prepared,lock,output):
    from v3_furniture_install import inputs
    from v3_bank_april import native_bindings as april_bindings
    from v3_bank_storage import layout as saved_layout
    from v3_post_office_install import native_bindings,native_entries,ENTRIES
    prepared=Path(prepared).resolve();output=Path(output).resolve()
    if (not prepared.is_relative_to(ROOT/'build') or not output.is_relative_to(ROOT/'build') or
            output.exists()):raise ValueError('Use an existing ignored preparation and fresh ignored link directory')
    base,prior=inputs(lock);report=json.loads((prepared/'prepared.json').read_bytes())
    if (report['format']!='AFV3-BANK-FRONTEND-PREPARED-1' or
            report['base_sha256']!=sha256(base) or report['base_abi']!=prior['runtime_abi'] or
            report['object']['compiler']!=IMAGE or
            sha256((prepared/'post-office.o').read_bytes())!=report['object']['sha256'] or
            report['saved_owner_memory']!=saved_layout(prior)):
        raise ValueError('Changed complete prepared bank object or current base')
    for path,digest in report['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale complete bank source: '+path)
    for path,digest in report['generated_sha256'].items():
        if sha256((prepared/path).read_bytes())!=digest:raise ValueError('Changed complete generated bank source: '+path)
    fixed,receipt=native_bindings(base,prior);april,april_receipt=april_bindings(base,prior);fixed.update(april)
    if fixed!=report['object']['bound_native_services'] or receipt!=report['native_bindings'] or\
            april_receipt!=report['april']['native_bindings']:
        raise ValueError('Changed actual bank native bindings')
    if {line.split()[-1] for line in report['object']['unbound_services']}!={'af_bank_account_mode',*ROOTS}:
        raise ValueError('Complete bank preparation still needs additional native providers')
    memory=layout(prior);art,art_report=relocate_art((prepared/'bank-art.bin').read_bytes(),report['artwork'])
    output.mkdir(parents=True)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    # GNU MIPS ld -r has already applied absolute R_MIPS_26 addends in the
    # partially bound preview. Linking that preview a second time adds those
    # addresses again. Validate the complete original objects against the
    # preview, then bind native APIs exactly once in the final link.
    objects=['bank-source.o','bank-account.o','bank-native.o','pelly-source.o',
        'pelly-native.o','bank-admission.o','bank-entries.o','bank-april.o',
        'bank-storage.o','bank-codec.o','bank-cards.o','bank-collection.o','bank-dialogue.o']
    for name in objects:write_new(output/name,(prepared/name).read_bytes())
    services=dict(fixed,**report['saved_owner']['bound_services'])
    run('ld','-EB','-r',*(f'--defsym={n}=0x{a:X}' for n,a in services.items()),
        *objects,'-o','checked-post-office.o')
    if sha256((output/'checked-post-office.o').read_bytes())!=report['object']['sha256']:
        raise ValueError('Original bank objects do not reproduce the checked complete preparation')
    run('gcc',*report['object']['flags'],'/source/overlays/v3/bank_config.c','-o','bank-config.o')
    run('ld','-EB','-T','/source/overlays/v3/bank.ld',
        *(f'--defsym={n}=0x{a:X}' for n,a in services.items()),
        *(f'--defsym={n}=0x{a:X}' for n,a in art_report['root_symbols'].items()),
        *objects,'bank-config.o','-o','bank.elf','-Map','bank.map')
    if run('nm','--undefined-only','bank.elf').strip():raise ValueError('Linked bank still has unresolved symbols')
    definitions={name:(int(address,16),kind) for address,kind,name in
        (line.split() for line in run('nm','--defined-only','bank.elf').splitlines())}
    symbols={n:a for n,(a,k) in definitions.items() if k.upper() in ('T','D','B','R','A')}
    if any(definitions.get(n)!=(a,'A') for n,a in services.items()):
        raise ValueError('Final bank service does not resolve to the checked native API')
    for name in ENTRIES+('af_bank_april_construct','af_bank_april_destruct',
            'af_bank_pelly_april_clip','af_bank_april_player_clear','af_bank_native_account',
            'af_v3_save_pack','af_v3_save_check','af_v3_console_storage_commit'):
        address,kind=definitions.get(name,(0,''))
        if kind!='T' or not RAM<=address<ART-16:raise ValueError('Bank entry is not genuine linked code: '+name)
    bss_start,bss_end=symbols['af_bank_bss_start'],symbols['af_bank_bss_end']
    if not RAM<=bss_start<=bss_end<=ART-16:raise ValueError('Complete bank BSS exceeds its reservation')
    mode,kind=definitions['af_bank_account_mode']
    if kind!='B' or not bss_start<=mode<bss_end:raise ValueError('Bank mode lacks owned initialized storage')
    run('objcopy','-O','binary','bank.elf','bank-code.bin');code=(output/'bank-code.bin').read_bytes()
    if len(code)>bss_start-RAM or len(code)>memory['code']['bytes']:
        raise ValueError('Complete bank initialized code exceeds owned storage')
    packet=bytearray(END-RAM);packet[:len(code)]=code
    packet[ART-RAM:ART-RAM+len(art)]=art
    packet[ART-RAM-16:ART-RAM]=CODE_GUARD;packet[-16:]=ART_GUARD
    if any(packet[bss_start-RAM:bss_end-RAM]) or packet[mode-RAM]:
        raise ValueError('Complete bank transient state/configuration is not initialized')
    owners,entry_report=native_entries(base,symbols,code_bounds=(RAM,ART-16))
    from aflib import CODE_VROM
    from v3_bank_april_install import native_owners
    april_owners,april_entries=native_owners(base,prior,symbols,code_bounds=(RAM,ART-16),
        entry_core=owners[CODE_VROM])
    if owners.keys()&april_owners.keys()!={CODE_VROM}:
        raise ValueError('April/bank complete resources collide')
    owners.update(april_owners)
    for vrom,data in owners.items():write_new(output/f'owner-{vrom:08X}.bin',data)
    write_new(output/'bank-packet.bin',packet);write_new(output/'bank-art-linked.bin',art)
    result=dict(format='AFV3-BANK-LINKED-1',base_abi=prior['runtime_abi'],base_sha256=sha256(base),
        prepared=str(prepared.relative_to(ROOT)),prepared_sha256=sha256((prepared/'prepared.json').read_bytes()),
        memory=memory,saved_owner_memory=report['saved_owner_memory'],symbols=symbols,
        code=dict(ram=RAM,bytes=len(code),used_bytes=bss_end-RAM,sha256=sha256(code),
            bss_start=bss_start,bss_end=bss_end),
        packet=dict(ram=RAM,bytes=len(packet),sha256=sha256(packet)),artwork=art_report,
        account_mode=dict(address=mode,bytes=1,initial_value=0,profile_control_installed=False),
        entries=entry_report,april_entries=april_entries,
        owners=[dict(vrom=v,bytes=len(data),sha256=sha256(data)) for v,data in owners.items()],
        original_objects={n:sha256((prepared/n).read_bytes()) for n in objects},
        native_services_bound_once=True,retained_services=services,
        compiler=IMAGE,sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        fully_linked=True,installed=False,native_execution_verified=False,
        pending=['April calendar, actor lifecycle, personal deletion, and official text',
            'startup packet transfer and full overlay resource relocation',
            'message/choice banks and complete saved-owner redirects',
            'mail templates, delivery acknowledgement, scheduling, and independent profile controls'])
    write_new(output/'linked.json',(json.dumps(result,indent=2)+'\n').encode());return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=link(args.prepared,args.base_lock,args.output)
    print(json.dumps({k:r[k] for k in ('base_abi','code','packet','account_mode','fully_linked','installed')}))


if __name__=='__main__':main()
