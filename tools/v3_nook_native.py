"""Append one shared code/gift adapter to each complete native Nook counter."""
import copy
import json
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,dma_entries,sha256
from catalogue_names import Image
from letter_ui_fix import compile_part
from accent_mail_overlays import rows
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT
from shop_units import SHOPS as ORIGINAL_SHOPS,PRICE_BIASES

SHOPS={
    'cranny':(0x80101290,0x809CDFF4,0x809CE0AC),
    'conv':(0x801014B0,0x809A9548,0x809A9600),
    'depart':(0x801014F0,0x809ADE68,0x809ADF40),
    'super':(0x801014D0,0x809D2F24,0x809D2FDC),
}
IMPORTS={
    'af_np_window':0x8009D1F0,'af_np_continue':0x8009E908,
    'af_np_hidden':0x8009D274,'af_np_opened':0x8009D294,
    'af_np_hide':0x8009D4F0,'af_np_open':0x8009D620,'af_np_force':0x8009E9C0,
    'af_np_set_message':0x8009DBA4,'af_np_change_message':0x8009E658,
    'af_np_lock':0x8009E9E8,'af_np_unlock':0x8009E9F8,
    'af_np_choice_window':0x80065040,'af_np_choice_number':0x800654FC,
    'af_np_order_get':0x8007B49C,'af_np_order_set':0x8007B44C,
    'af_np_foreign':0x800951C0,'af_np_pocket_index':0x800B8068,
    'af_np_insert':0x800B8B8C,'af_np_town':0x800950D8,'af_np_editor':0x800C4DD8,
    'af_np_free_string':0x8009D6D0,'af_np_item_name':0x801969C8,
    'af_np_item_string':0x8009D88C,'af_np_sound':0x800D1D58,
}
SOURCES=('tools/v3_nook_native.py','overlays/v3/nook_native.c',
    'overlays/v3/nook_password.h','overlays/v3/password_runtime.h',
    'tools/letter_ui_fix.py','upstream/af/src/boot/ovlmgr.c',
    'upstream/af/src/boot/O2/loadfragment2.c')


def generated(dialogue,password,rustle):
    mapping={int(k):v for k,v in dialogue['mapping'].items()}
    if (len(dialogue['native_to_donor'])!=256 or len(dialogue['donor_to_native'])!=256 or
            len(dialogue['native_extended_name_codes'])!=256 or not 0<=rustle<=65535):
        raise ValueError('Missing complete Nook name/font or source sound binding')
    table_bytes=next(r['bytes'] for r in password['parts'] if r['offset']==0x2800)
    text=f'#define AF_NP_TABLE_BYTES {table_bytes}u\n#define AF_NP_RUSTLE {rustle}\n'
    for key,donor in (('OTHER',0x3E07),('FULL',0x3E09),('SAY',0x3E0A),
            ('FOREIGN',0x3E13),('LIMIT',0x3E15)):
        text+=f'#define AF_NP_{key}_ID {mapping[donor]}\n'
    # All four original counters share category 24, the ordinary decline.
    text+='#define AF_NP_CANCEL_NATIVE_ID 0x1093\n'
    text+='static const int af_np_results[10]={'+','.join(map(str,dialogue['result_messages']))+'};\n'
    text+='static const u16 af_np_native_to_donor[256]={'+','.join(map(str,dialogue['native_to_donor']))+'};\n'
    names=[int(v,16) for v in dialogue['donor_to_native']]
    if any(not v or not 0<v<=65535 for v in names):
        # Native byte zero is a legitimate mapped glyph, not a missing field.
        if any(v<0 or v>65535 for v in names):raise ValueError('Invalid donor name mapping')
    text+='static const u16 af_np_donor_to_native[256]={'+','.join(map(str,names))+'};\n'
    return text.encode()


def prepare(image,prior,password,dialogue,rustle,out):
    files=by_vrom(image);directory=list(dma_entries(image));core=files[CODE_VROM].extract(image)
    input_hashes={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}
    shared=generated(dialogue,password,rustle);changes={};reports={};descriptors=[]
    for name,(descriptor,setup,frame) in SHOPS.items():
        old=prior['shop_actors']['owners'][name];vrom=old['vrom'];ram=old['ram']
        data=files[vrom].extract(image)
        # The native loader uses the following DMA-directory entry for the
        # relocation file. Its virtual ID need not equal a proposed move that
        # left unchanged relocation bytes at their original directory index.
        relocation=directory[files[vrom].index+1];rel=relocation.extract(image)
        if (len(data)!=old['allocation_bytes'] or sha256(data)!=old['output_sha256'] or
                sha256(rel)!=old['relocation_sha256']):raise ValueError('Changed complete native Nook owner: '+name)
        config=struct.unpack_from('>6I',core,descriptor-CODE_RAM)
        if config[:5]!=(vrom,vrom+len(data),ram,ram+len(data),0):
            raise ValueError('Changed native Nook allocation descriptor')
        profile=config[5];profile_words=struct.unpack_from('>9I',data,profile-ram)
        if profile_words[3]!=0x96C or not ram<=profile_words[5]<ram+len(data):
            raise ValueError('Changed Nook actor size or destructor owner')
        if data[frame-ram:frame-ram+20]!=bytes.fromhex('8e19094002002025022028250320f80900000000'):
            raise ValueError('Changed native Nook callback dispatch')
        if data[setup-ram:setup-ram+16]!=bytes.fromhex('27bdffe8afbf0014afa5001c00067080'):
            raise ValueError('Changed native Nook action setup')
        symbols=password['code']['symbols'];bootstrap=password['bootstrap']['code']['symbols']
        imports=dict(IMPORTS,af_np_setup=setup,af_np_original_destroy=profile_words[5],
            af_np_fault=prior['save_codec']['active_storage_code']['symbols']['af_v3_save_halt'],
            af_v3_password_boot_ready=bootstrap['af_v3_password_boot_ready'],
            af_v3_password_boot_check=bootstrap['af_v3_password_boot_check'],
            af_v3_password_decode=symbols['af_v3_password_decode'],
            af_nook_password_step=symbols['af_nook_password_step'],
            af_nook_password_begin=symbols['af_nook_password_begin'])
        spec=dict(vrom=vrom,reloc=relocation.vstart,ram=ram,sha=sha256(data),reloc_sha=sha256(rel),
            imports=imports,calls={},address_constants=(PRICE_BIASES[ORIGINAL_SHOPS[name].vrom],))
        expanded,newrel,receipt=compile_part(name,image,out/name,spec=spec,
            source='/source/overlays/v3/nook_native.c',generated={'nook-native.inc':shared},flags=('-I/out',))
        result=bytearray(expanded);entries=rows(newrel,len(result));patches=[]
        edits=((frame-ram,struct.pack('>I',0x8E060940)),
            (frame-ram+12,struct.pack('>I',0x0C000000|((ram+receipt['symbols']['af_np_actor_dispatch'])>>2&0x3FFFFFF))),
            (profile-ram+0x14,struct.pack('>I',ram+receipt['symbols']['af_np_destroy'])))
        for at,value in edits:
            patches.append(dict(offset=at,before=data[at:at+4].hex(),after=value.hex()))
            result[at:at+4]=value
        if frame-ram in entries or frame-ram+12 in entries or entries.get(profile-ram+0x14)!=2:
            raise ValueError('Changed Nook dispatch/destructor relocation ownership')
        # Native IDO tables can reuse one high relocation for several low
        # instructions. Preserve the loader's original register-cache order;
        # sorting by instruction address changes those retained instructions.
        entries[frame-ram+12]=4
        values=[0x40000000|kind<<24|at for at,kind in entries.items()]
        size=(24+4*len(values)+15)&~15
        newrel=(struct.pack('>5I',len(result),0,0,0,len(values))+
            struct.pack('>'+str(len(values))+'I',*values)+bytes(size-24-4*len(values))+struct.pack('>I',size))
        result=bytes(result)
        touched={i for at,value in edits for i in range(at,at+len(value))}
        for base in (0x80200010,0x80370010):
            before=relocate_verified_data(Image(ram,len(data),struct.unpack_from('>5I',rel)),data,rel,base,
                address_constants=spec['address_constants'])
            after=relocate_verified_data(Image(ram,len(result),struct.unpack_from('>5I',newrel)),result,newrel,base,
                address_constants=spec['address_constants'])
            if any(before[i]!=after[i] for i in range(len(data)) if i not in touched):
                raise ValueError('Nook code route changes unrelated relocated native behaviour')
        receipt.update(patches=patches,overlay_sha256=sha256(result),relocation_sha256=sha256(newrel),
            previous_reloc_vrom=relocation.vstart,profile=profile,frame=frame,setup=setup,
            native_execution_tested=False,ordinary_gameplay_tested=False)
        (out/name/'installed.bin').write_bytes(result);(out/name/'installed-relocation.bin').write_bytes(newrel)
        (out/name/'installed.json').write_text(json.dumps(receipt,indent=2)+'\n')
        changes.update({vrom:result,relocation.vstart:newrel});reports[name]=receipt
        descriptors.append(dict(address=descriptor,before=list(config[:4]),
            after=[vrom,vrom+len(result),ram,ram+len(result)]))
    if input_hashes!={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}:
        raise ValueError('Nook native adapter sources changed during compile')
    return changes,dict(owners=reports,descriptors=descriptors,source=input_hashes,
        native_execution_tested=False,ordinary_gameplay_tested=False)
