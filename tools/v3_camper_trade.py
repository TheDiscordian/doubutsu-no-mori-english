"""Install selected summer rewards and the full-ID pocket picker in ABI 81."""
import argparse
import copy
import json
from pathlib import Path
import re
import struct
from types import SimpleNamespace
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256,
                   verified_rom, fix_checksum, make_ups, apply_ups)
from apply_translation import write_new
from catalogue_names import elf_inventory
from gc_names import rel_sections, symbol_data
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT, BLOB, MODULE, STARTUP, CONFIG, compile_part
from v3_camping_items import TENT
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources
from v3_import_storage import END, replace_checked
from v3_villager_art import data_pointers

BASE = ROOT/'build/v3-official-credits-01'
BASE_SHA = 'dfac082b4a900711aedf19b2e0cc869ee8622e1eb110e04be66591a448ea1d4e'
REPORT_SHA = '4a0d360e39e68bb9da6e20b79ee107b5e559b991705f2d78d22ef5300d4aa9fa'
ABI, VROM, RELOC, RAM, SIZE = 81, 0x03910000, 0x03918000, 0x8091D7B0, 19392
QUEST, QUEST_RELOC, QUEST_RAM = 0x849B50, 0x84C8A0, 0x80954D80
SOURCES = {
    VROM: '2415efa8c41f6268bc870a7b24ae8ff68670bc2f35cb0678d764eaf1f3373dca',
    RELOC: 'cafc6c298d54915be15feef31c6661d20cff68e4d3f9817f454991e784ded12e',
    QUEST: '1788f01c775b2050a406fb157bd0b6f258aa04eb875f518027381aca2e50e861',
    QUEST_RELOC: '0488d8c93b285bcd03b84105e838bb887878f26acf6670ba8448198162b2c678'}
IMPORTS = dict(native_private=0x80136FD8, native_trade_state=0x80921DE8,
    native_scene=0x80126EB4, camper_last_gift=0x804A1A12, native_rare_item=0x80135C00,
    native_random=0x8002C9AC, native_item_kind=0x80468000, native_house_item=0x800ABAA8,
    native_random_goods=0x800BFCF0, native_goods_priority=0x800C1BF0,
    native_item_name=0x800BB6A0, native_other_fruit=0x8008D6E0, native_trade_body=0x8091EFE4)


def words(*values): return struct.pack('>'+str(len(values))+'I', *values)
def jump(target): return 0x08000000 | (target >> 2 & 0x3FFFFFF)


def donor_sources():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    raw = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel, raw); symbols = raw.decode(); sections = rel_sections(rel)
    result = []
    # These static names also occur in the island owner. Bind the normal owner
    # explicitly; first-name lookup would silently select different code.
    for name, section, offset, size, digest in (
        ('aQMgr_get_possession_ftr_cpt_wl_rnd', '.text', 0x1228F4, 0x174,
         'fb6261b2b1f599fd0d50e5ae43964725530fc7a9b96481fbf43a3c15f87b5620'),
        ('aQMgr_order_decide_trade_common_item', '.text', 0x122B8C, 0x230,
         '2dd3759580ba1ffd978e27469c2a16d3a8cc03473582a6fe2d6be83224ee2270')):
        matches = re.findall(r'^'+re.escape(name)+r' = (\.\w+):0x([\dA-Fa-f]+);[^\n]* size:0x([\dA-Fa-f]+)', symbols, re.M)
        if (section, offset, size) not in [(s, int(a,16), int(n,16)) for s,a,n in matches]:
            raise ValueError('Missing exact normal trade owner symbol')
        start = sections[1][0]+offset; data = rel[start:start+size]
        if sha256(data) != digest: raise ValueError('Changed donor normal trade code')
        result.append(dict(symbol=name, section=section, offset=offset, bytes=size, sha256=digest))
    tent = symbol_data(rel, symbols, 'ftr_listTent')
    cats = rel[sections[5][0]+0x3E248:sections[5][0]+0x3E260]
    if (tent != struct.pack('>11H', *TENT) or cats != words(0,3,4,2,1,5)):
        raise ValueError('Changed actual tent items or complete trade categories')
    for name, address, a in (('carpet',0x62B3A0,0x62B300), ('wall',0xAC8408,0xAC8368)):
        pointers = data_pointers(rel, address, 92)
        if pointers.get(address) != a or address+22*4 in pointers:
            raise ValueError('Changed donor carpet/wall TENT-to-A fallback')
        result.append(dict(symbol='mSP_'+name+'_list', offset=address,
                           a_list=a, tent_pointer=None, bytes=92))
    for name in ('mQst_GetGoods_common', 'mSP_SelectRandomItem_New'):
        data = symbol_data(rel, symbols, name)
        result.append(dict(symbol=name, bytes=len(data), sha256=sha256(data)))
    result.append(dict(symbol='ftr_listTent', bytes=len(tent), sha256=sha256(tent), items=list(TENT[:-1])))
    return result


def source_owners(base):
    files = by_vrom(base); sources = {v:files[v].extract(base) for v in SOURCES}
    if (any(sha256(sources[v]) != digest for v,digest in SOURCES.items())
            or len(sources[VROM]) != SIZE or struct.unpack_from('>5I',sources[RELOC]) != (SIZE,0,0,0,542)
            or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed complete current normal/quest owner or relocation')
    # Keep the actual native goods algorithm, including house roll and rare-item
    # exclusion, with the existing selected-clothing list adapter intact.
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    original = by_vrom(native)[CODE_VROM].extract(native)
    code = bytearray(files[CODE_VROM].extract(base))
    replace_checked(code,0x800BFE4C-CODE_RAM,words(0x0C1183D8),words(0x0C02FEAA))
    for start,end in ((0x800BC454,0x800BC528),(0x800BFCF0,0x800BFF8C),(0x800C1BF0,0x800C1C38)):
        if code[start-CODE_RAM:end-CODE_RAM] != original[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed native goods, rare-item, or priority body')
    return sources


def install(base, suffix, compiled):
    sources = source_owners(base); donor = donor_sources(); symbols = compiled['symbols']
    if (len(suffix) != compiled['bytes'] or sha256(suffix) != compiled['sha256'] or len(suffix)%16
            or any(symbols.get(name) != target for name,target in IMPORTS.items())
            or symbols.get('af_v3_camper_pocket') != RAM+SIZE):
        raise ValueError('Changed trade suffix or native bindings')
    data = bytearray(sources[VROM]+suffix); hooks = []
    for address, before, name in (
        (0x8091ED64, words(0x27BDFFD0,0xAFBF001C), 'af_v3_camper_pocket'),
        (0x8091EFDC, words(0x27BDFFA0,0xAFB60038), 'af_v3_camper_trade')):
        target = symbols[name]
        if not RAM+SIZE <= target < RAM+len(data): raise ValueError('Trade entry outside suffix')
        after = words(jump(target),0); replace_checked(data,address-RAM,before,after)
        hooks.append(dict(address=address, before=before.hex(), after=after.hex(), target=target))
    tail = symbols['native_trade_original']-RAM
    if data[tail:tail+16] != words(0x27BDFFA0,0xAFB60038,jump(IMPORTS['native_trade_body']),0):
        raise ValueError('Changed complete native non-summer trampoline')
    rows = [r for (r,) in struct.iter_unpack('>I',sources[RELOC][20:20+542*4])]
    if any(any(h['address']-RAM <= r&0xFFFFFF < h['address']-RAM+8 for h in hooks) for r in rows):
        raise ValueError('Changed original trade entry relocations')
    rows += [0x44000000 | h['address']-RAM for h in hooks]
    for pos,kind,target,name in elf_inventory(compiled['elf_relocations'],ram=RAM):
        if not SIZE <= pos <= len(data)-4 or pos&3: raise ValueError('Trade relocation outside suffix')
        if RAM <= target < RAM+len(data): rows.append(0x40000000 | kind<<24 | pos)
        elif IMPORTS.get(name) != target or kind not in (2,4,5,6):
            raise ValueError('Unknown external trade reference')
    if len({r&0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate trade relocation')
    length = (24+len(rows)*4+15)&~15
    sections = (len(data),0,0,0,len(rows))
    relocation = words(*sections,*rows)+bytes(length-24-len(rows)*4)+words(length)
    if len(data)+length > 0x8800 or VROM+len(data) > RELOC:
        raise ValueError('Trade owner exceeds existing shared buffer or VROM gap')
    for address in (0x80204000,0x80308000):
        old = relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=SIZE,sections=(SIZE,0,0,0,542)),
                                      sources[VROM],sources[RELOC],address)
        current = bytearray(relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=len(data),sections=sections),
                                                  data,relocation,address))
        for h in hooks:
            at = h['address']-RAM; current[at:at+8] = old[at:at+8]
        if current[:SIZE] != old: raise ValueError('Trade suffix changes unrelated relocated owner bytes')
    quest = bytearray(sources[QUEST]); patches = []
    # Descriptor constants are not addresses inside the quest owner and do not relocate.
    for at,before,after in ((0x2460,VROM+SIZE,VROM+len(data)),(0x2468,RAM+SIZE,RAM+len(data))):
        replace_checked(quest,at,words(before),words(after))
        patches.append(dict(offset=at,before=before,after=after))
    qrel = sources[QUEST_RELOC]; qsec = struct.unpack_from('>5I',qrel)
    for address in (0x80204000,0x80308000):
        spec = SimpleNamespace(ram=QUEST_RAM,resident_bytes=len(quest)+qsec[3],sections=qsec)
        old = relocate_verified_data(spec,sources[QUEST],qrel,address)
        current = bytearray(relocate_verified_data(spec,quest,qrel,address))
        for p in patches:
            at = p['offset']
            if current[at:at+4] != words(p['after']): raise ValueError('Foreign normal descriptor unexpectedly relocates')
            current[at:at+4] = old[at:at+4]
        if current != old: raise ValueError('Trade loader change escapes declared descriptor')
    return {VROM:bytes(data), RELOC:relocation, QUEST:bytes(quest)}, dict(
        code=compiled, donor=donor, hooks=hooks, quest_patches=patches,
        vrom=VROM,relocation_vrom=RELOC,ram=RAM,bytes=len(data),sha256=sha256(data),
        original_bytes=SIZE,on_demand_growth=len(suffix),sections=sections,
        relocation_bytes=len(relocation),relocation_sha256=sha256(relocation),
        shared_buffer_bytes=0x8800,additional_heap_bytes=0,additional_resident_bytes=0,
        selected_reward_items=list(TENT[:-1]),saved_format_changed=False,saved_profile_changed=False,
        summer_selection_installed=True,selected_rewards_installed=True,
        ordinary_conversations_tested=False,web_patcher_enabled=False)


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Choose fresh ignored output')
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes(); raw = (BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw)) != (BASE_SHA,REPORT_SHA): raise ValueError('Changed current complete base')
    prior,files = json.loads(raw),by_vrom(base); source_owners(base); output.mkdir(parents=True)
    suffix,compiled = compile_part('camper_trade',output/'trade',extra_sources=('overlays/v3/camper_trade_tail.S',))
    changes,trade = install(base,suffix,compiled)
    blob = bytearray(files[BLOB].extract(base)); old_size = len(blob); moves = []
    for vrom in (VROM,RELOC):
        payload = changes.pop(vrom); blob.extend(bytes(-len(blob)%16)); pos = len(blob); blob.extend(payload)
        moves.append(dict(vrom=vrom,bytes=len(payload),physical=files[BLOB].pstart+pos,
                          blob_offset=pos,sha256=sha256(payload)))
        if any(e.vstart < vrom+len(payload) and vrom < e.vend for v,e in files.items() if v!=vrom):
            raise ValueError('Extended trade resource overlaps a live VROM')
    start,end = files[BLOB].pstart+old_size,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size) for v,e in files.items()
                   if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+old_size<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Trade append overlaps used cartridge storage')
    startup,startup_report = compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module = bytearray(files[MODULE].extract(base)); old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup)); struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    changes.update({BLOB:blob,MODULE:module}); image = bytearray(base)
    for vrom,payload in changes.items():
        e = files[vrom]
        if e.pend or vrom!=BLOB and len(payload)!=e.size: raise ValueError('Unexpected owner allocation change')
        image[e.pstart:e.pstart+len(payload)] = payload
    struct.pack_into('>I',image,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',image,DMA_START+files[row['vrom']].index*16,
                         row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(image); image = bytes(image); installed = by_vrom(image)
    if (set(installed)!=set(files) or image[DMA_END-16:DMA_END]!=bytes(16)
            or any(installed[v]!=files[v] for v in files if v not in (VROM,RELOC,BLOB))):
        raise ValueError('Trade suffix changes unrelated DMA metadata')
    patch = make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Trade patch reconstruction failed')
    report = copy.deepcopy(prior); trade['moves'] = moves
    report.update(build='v3-camper-trade',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,camper_trade=trade,
        native_test='pending current summer trade execution; greeting caller stop remains unresolved')
    report['camper_greeting']['selected_rewards_installed'] = True
    for row in report['camper_quest']['owners']:
        if int(row['vrom'],16)==QUEST: row['patched_sha256'] = sha256(installed[QUEST].extract(image))
    report['import_storage']['remaining_bytes'] = END-BLOB-len(blob)
    names = ('tools/v3_camper_trade.py','tools/v3_asset_loader.py','overlays/v3/camper_trade.c',
             'overlays/v3/camper_trade.h','overlays/v3/camper_trade.ld','overlays/v3/camper_trade_tail.S')
    report['sources'].update({name:sha256((ROOT/name).read_bytes()) for name in names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({k:report[k] for k in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
