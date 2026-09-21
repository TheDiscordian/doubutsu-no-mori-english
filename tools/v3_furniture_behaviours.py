"""Source-checked behaviour categories shared by automatic furniture imports."""
import struct
import copy
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS, ITEMS, slot
from v3_catalogue import PREVIEW_COUNT
from v3_villager_audio import (GC_SECTIONS, NATIVE_HEADERS, NATIVE_FILES,
    read_audio_donor, header_entry, resource, span, instrument)

RAM, LIMIT = 0x80483D00, 0x80483FC0
ENTRY, END = 0x800BED5C, 0x800BEE50
SOURCE_SHA = 'ec58cd8da4eaf4a51e8913f75023a704995ef7f98a00a77ad08bd7a4c4e20339'
NATIVE_CATEGORIES, NATIVE_SOUNDS = 0x8010D314, 0x8010D6C8
CATEGORY_SHA = '6e88fc4da791a5e31e72b21c59876c4f2f5adf0d721dcb8d4b8d268c56dc0a73'
SWITCH_FIRST,SWITCH_END,SWITCH_PATCH=0x80937FB0,0x809380EC,0x809380A0
SWITCH_SHA='6b2851d0f6e927d1593011130e4691a7983fa6fb8172cb3aa4c32cd2396dd0ac'
SWITCH_BEFORE=bytes.fromhex('240B0001240CFFFFA20B012C1000000AA20C012E')
# Existing native bed geometry, entry, and exit use the expanded profile table.
# This is a shared engine contract, not a list of approved bed identities.
BED_HEAD, BED_FOOT_SIDES, BED_PILLOW_SIDES = 0x80940304, 0x80940498, 0x80940784
# Complete bed consumers with the installed profile-table/range bindings.
# Unrelated placement and rig functions in the same owner may evolve without
# changing these consumers. Keep complete function checks, not just entry bytes.
BED_FUNCTIONS = (
    (0x80940304,0x80940378,'ea92f54a016cb2ddb55c567f45fc18341fe0ad8287277435bb820126cc061bd1'),
    (0x80940498,0x80940784,'525a96d61a69e0519d73e5446d5b4c06870bac61f6e66d1a35b409d4268a410b'),
    (0x80940784,0x80940A64,'b3ff8c8decbbede285143189da5a74545e18e6d34aadfc1120530f04e79641ee'),
    (0x80940D4C,0x809410FC,'f74591acddf4a73931b8af4e9678429bdf592fdda08de92769e295d15299e020'),
    (0x80941868,0x80941C08,'ff545f4472ce3a7fe776d67b13f82dce6733eb777bc9066c01ddf1774f794a64'),
)
SOURCES = ('tools/v3_furniture_behaviours.py','tools/v3_four_cell_items.py','overlays/v3/items.c',
           'tools/v3_asset_loader.py','overlays/v3/furniture_behaviours.c',
           'overlays/v3/furniture_behaviours.S','overlays/v3/furniture_behaviours.ld',
           'overlays/v3/fire.ld','overlays/v3/items_large.ld')


def initial_switch_patch(entry):
    if type(entry) is not int or entry&3 or not RAM<=entry<LIMIT:raise ValueError('Initial switch helper escapes shared behaviour reservation')
    # The branch delay also executes on reload, where the following two native
    # shifts overwrite a1 before use. The gyroid path never enters this block.
    return struct.pack('>5I',0x00402825,0x0C000000|(entry>>2&0x3FFFFFF),0x02002025,0x1000000A,0)


def initial_switch_source(source):
    raw,receipt=source.function(0x1014D8)
    if (receipt['symbol']!='aMR_SetSwitchStepData' or len(raw)!=316 or
            sha256(raw)!='050371a19917f2f5533253987cee15a0aa0b3d269a8791e57a0acfbfd4aa4697'):
        raise ValueError('Changed complete donor fresh-placement switch rule')
    return receipt


def checked_initial_switch(base,report,blob):
    """Bind the complete current helper and native placement consumer."""
    from v3_furniture_runtime import VROM,RELOC,RAM as OWNER_RAM
    binding=report.get('furniture_initial_switch')
    if binding is None:return None
    code=report['furniture_behaviours']['code'];entry=code['symbols'].get('af_v3_furniture_initial_switch')
    first=PACKAGE+RAM-PACKAGE_RAM;end=PACKAGE+LIMIT-PACKAGE_RAM
    owner=by_vrom(base)[VROM].extract(base);rel=by_vrom(base)[RELOC].extract(base)
    after=initial_switch_patch(entry);at=SWITCH_PATCH-OWNER_RAM
    restored=bytearray(owner[SWITCH_FIRST-OWNER_RAM:SWITCH_END-OWNER_RAM])
    restored[SWITCH_PATCH-SWITCH_FIRST:SWITCH_PATCH-SWITCH_FIRST+len(after)]=SWITCH_BEFORE
    if (binding['format']!='AFV3-INITIAL-SWITCH-1' or binding['mask']!=0x1000 or
            binding['entry']!=entry or binding['patch_address']!=SWITCH_PATCH or
            binding['before']!=SWITCH_BEFORE.hex() or binding['after']!=after.hex() or
            owner[at:at+len(after)]!=after or sha256(restored)!=SWITCH_SHA or
            sha256(owner[SWITCH_FIRST-OWNER_RAM:SWITCH_END-OWNER_RAM])!=binding['function_sha256'] or
            not 0<code['bytes']<=LIMIT-RAM or sha256(blob[first:first+code['bytes']])!=code['sha256'] or
            any(blob[first+code['bytes']:end]) or '-DAF_V3_INITIAL_SWITCH=1' not in code['flags']):
        raise ValueError('Changed complete imported fresh-placement rule')
    sections=struct.unpack_from('>5I',rel)
    if sections[:4]!=(0x10E50,0x5BE0,0x1E0,0x22F0) or len(rel)!=6208 or 20+sections[4]*4>len(rel)-4:
        raise ValueError('Changed placement owner relocation dimensions')
    for (word,) in struct.iter_unpack('>I',rel[20:20+sections[4]*4]):
        address=OWNER_RAM+sum(sections[:(word>>30)-1])+(word&0xFFFFFF)
        if SWITCH_PATCH<=address<SWITCH_PATCH+len(after):raise ValueError('Resident placement call must not relocate')
    return dict(mask=binding['mask'],entry=entry,owner_patch_sha256=sha256(after))


def install_initial_switch(base,prior,blob,source,output):
    """Extend the shared behaviour helper once, preserving the whole native owner."""
    from v3_furniture_runtime import VROM,RAM as OWNER_RAM
    source_receipt=initial_switch_source(source)
    if prior.get('furniture_initial_switch'):
        return checked_initial_switch(base,prior,blob),{},{}
    original=by_vrom(base)[VROM].extract(base);owner=bytearray(original);at=SWITCH_PATCH-OWNER_RAM
    if sha256(owner[SWITCH_FIRST-OWNER_RAM:SWITCH_END-OWNER_RAM])!=SWITCH_SHA or owner[at:at+20]!=SWITCH_BEFORE:
        raise ValueError('Changed native fresh-placement branch')
    old=prior['furniture_behaviours']['code'];first=PACKAGE+RAM-PACKAGE_RAM;end=PACKAGE+LIMIT-PACKAGE_RAM
    if sha256(blob[first:first+old['bytes']])!=old['sha256'] or any(blob[first+old['bytes']:end]):
        raise ValueError('Changed shared behaviour helper reservation')
    helper,compiled=compile_part('furniture_behaviours',output/'furniture_behaviours',
        extra_sources=('overlays/v3/furniture_behaviours.S',),defines=('AF_V3_INITIAL_SWITCH=1',))
    if not 0<len(helper)<=LIMIT-RAM or compiled['symbols']['af_v3_furniture_action_sound']!=RAM:
        raise ValueError('Placement helper changes shared behaviour entry or capacity')
    entry=compiled['symbols']['af_v3_furniture_initial_switch'];after=initial_switch_patch(entry)
    owner[at:at+20]=after;blob[first:end]=helper+bytes(end-first-len(helper))
    metadata=dict(format='AFV3-INITIAL-SWITCH-1',mask=0x1000,entry=entry,source=source_receipt,
        patch_address=SWITCH_PATCH,before=SWITCH_BEFORE.hex(),after=after.hex(),
        function_sha256=sha256(owner[SWITCH_FIRST-OWNER_RAM:SWITCH_END-OWNER_RAM]),
        original_function_sha256=SWITCH_SHA,owner_before_sha256=sha256(original),owner_after_sha256=sha256(owner),
        original_indices_unchanged=True,reload_path_unchanged=True,gyroid_path_unchanged=True,
        additional_resident_bytes=0,saved_format_changed=False)
    updated=copy.deepcopy(prior['furniture_behaviours']);updated['code']=compiled
    compact=dict(mask=0x1000,entry=entry,owner_patch_sha256=sha256(after))
    return compact,{VROM:bytes(owner)},dict(furniture_initial_switch=metadata,furniture_behaviours=updated)


def contact_contract(base, prior, blob, imports):
    beds = [row for row in imports
            if blob[ROWS+slot(int(row['item_id'],16))*80+8+60] in (8,16)]
    if not beds: return None
    from v3_furniture_runtime import VROM, RAM as OWNER_RAM
    owner = by_vrom(base)[VROM].extract(base)
    if any(sha256(owner[a-OWNER_RAM:z-OWNER_RAM])!=digest for a,z,digest in BED_FUNCTIONS):
        raise ValueError('Changed native bed/contact engine requires category review')
    tables = prior['furniture']['expanded_tables']
    if tables['profile_table_ram'] != '80470010' or tables['capacity'] != 2051:
        raise ValueError('Bed contact readers require the complete expanded profile table')
    # The reviewed bed-profile readers retain the same checked table base.
    for high,low in ((0x809404D0,0x809404DC),(0x809407BC,0x809407C8),
                     (0x80940FA8,0x80940FB8),(0x809419D0,0x809419E0)):
        hi,lo=struct.unpack_from('>I',owner,high-OWNER_RAM)[0],struct.unpack_from('>I',owner,low-OWNER_RAM)[0]
        address=((hi&65535)<<16)+(lo&65535)-(65536 if lo&32768 else 0)
        if address != int(tables['profile_table_ram'],16):
            raise ValueError('Bed contact profile binding is not expanded')
    actions=sorted({blob[ROWS+slot(int(row['item_id'],16))*80+8+60] for row in beds})
    return dict(contact_actions=actions,category='native-bed',native_owner_sha256=sha256(owner),
        functions=[dict(start=a,end=z,sha256=digest) for a,z,digest in BED_FUNCTIONS],
        profile_table_ram=tables['profile_table_ram'],imports=[r['item_id'] for r in beds],
        head_direction_entry=BED_HEAD,foot_sides_entry=BED_FOOT_SIDES,pillow_sides_entry=BED_PILLOW_SIDES,
        added_runtime_bytes=0,ordinary_bed_gameplay_tested=False)


def four_cell_contract(original, prior, blob, imports, source):
    rows=[row for row in imports if blob[ITEMS+slot(int(row['item_id'],16))*32+6]==2]
    if not rows: return None
    from v3_four_cell_items import source_evidence
    evidence=source_evidence(original,source.rel,source.symbols.encode())
    reader=prior['import_storage']['item_code'];at=PACKAGE+0x80483000-PACKAGE_RAM
    if (reader['sha256'] != 'baf6957601fea4fc0829382bbc21604ade478479e9f0f6375c6e4d49e2f0317d'
            or reader['bytes'] != 1020 or sha256(blob[at:at+reader['bytes']])!=reader['sha256']
            or '-DAF_V3_FOUR_CELL_ITEMS=1' not in reader['flags']):
        raise ValueError('Four-cell imports require the checked complete native item readers')
    return dict(imports=[r['item_id'] for r in rows],source=evidence,
        reader_sha256=reader['sha256'],reader_ram='80483000',added_runtime_bytes=0)


def audio_contract(original, base, prior, source):
    """Bind complete sounds: matching numbers alone do not prove matching audio."""
    from v3_sound_programs import installed_resource
    native = by_vrom(original); current = by_vrom(base)
    code = native[CODE_VROM].extract(original); now = current[CODE_VROM].extract(base)
    nr = lambda at,n: span(code,at-CODE_RAM,n)
    sounds = nr(NATIVE_SOUNDS,16)
    donor_sounds = source.raw('soft_chair_se_table$543')+source.raw('hard_chair_se_table$544')
    if (sounds != donor_sounds or sounds.hex() != '0000041f000004220000042000000423'
            or now[NATIVE_SOUNDS-CODE_RAM:NATIVE_SOUNDS-CODE_RAM+16] != sounds
            or sha256(nr(NATIVE_CATEGORIES,947)) != CATEGORY_SHA
            or now[NATIVE_CATEGORIES-CODE_RAM:NATIVE_CATEGORIES-CODE_RAM+947] != nr(NATIVE_CATEGORIES,947)):
        raise ValueError('Changed native/donor sound categories or sound IDs')
    dol,audio = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    ns={k:native[v].extract(original) for k,v in NATIVE_FILES.items()}
    gs={k:span(audio,*struct.unpack_from('>II',header_entry(dol.read,0x800CE450,i)))
        for i,k in enumerate(('seq','bank','wave'))}
    # The current extended sequence keeps the complete native chair programs.
    sequence_record=prior['fire_sound']['resources']['seq']
    blob=current[BLOB].extract(base); at=sequence_record['blob_offset']
    live_sequence=span(blob,at,sequence_record['bytes'])
    if (sequence_record['vrom']!=BLOB+at or
            sequence_record['physical']!=current[BLOB].pstart+at or
            sha256(live_sequence)!=sequence_record['sha256']):
        raise ValueError('Changed installed complete sound sequence')
    wave_file=prior['fire_sound']['wave_file']; wave_record=prior['fire_sound']['resources']['wave']
    waves=current[wave_file['vrom']].extract(base)
    live_wave=span(waves,wave_record['vrom']-wave_file['vrom'],wave_record['bytes'])
    if sha256(waves)!=wave_file['sha256'] or sha256(live_wave)!=wave_record['sha256']:
        raise ValueError('Changed installed complete sound waves')
    records=[]
    for sound_id in struct.unpack('>4I',sounds):
        pair=[]
        for label,read,headers,sources,sequence,mapping in (
            ('GAFE01-r0',dol.read,GC_SECTIONS,gs,242,0x800CE490),
            ('N64-Japan',nr,NATIVE_HEADERS,ns,199,0x80115D80)):
            data,_=resource(read,headers,sources,'seq',sequence)
            table=struct.unpack_from('>H',data,0x188+(sound_id>>8)*2)[0]
            at=struct.unpack_from('>H',data,table+(sound_id&255)*2)[0]
            program=span(data,at,11)
            if (program[0]!=0xEB or program[1]>3 or program[2]>125 or program[3]!=0x88
                    or struct.unpack_from('>H',program,4)[0]!=at+7
                    or program[6:8]!=bytes.fromhex('FF67') or program[-1]!=0xFF):
                raise ValueError('Chair sound has an unsupported channel/note program')
            offset=struct.unpack('>H',read(mapping+sequence*2,2))[0]
            fonts=read(mapping+offset,5)
            if fonts[0]!=4: raise ValueError('Changed four-font sound mapping')
            bank_id=fonts[4-program[1]]
            bank,header=resource(read,headers,sources,'bank',bank_id)
            wave,_=resource(read,headers,sources,'wave',header[10])
            complete=instrument(bank,wave,program[2],header[12],extended=True)
            if label=='N64-Japan':
                current_offset=struct.unpack_from('>H',now,mapping-CODE_RAM+sequence*2)[0]
                live_table=struct.unpack_from('>H',live_sequence,0x188+(sound_id>>8)*2)[0]
                live_font,live_header,_=installed_resource(base,now,'bank',bank_id)
                live_samples,_,_=installed_resource(base,now,'wave',live_header[10])
                if (live_sequence[at:at+11]!=program
                        or struct.unpack('>H',span(live_sequence,live_table+(sound_id&255)*2,2))[0]!=at
                        or now[mapping-CODE_RAM+current_offset:mapping-CODE_RAM+current_offset+5]!=fonts
                        or live_header[8:12]!=header[8:12] or live_header[13:]!=header[13:]
                        or instrument(live_font,live_samples,program[2],live_header[12],extended=True)!=complete
                        or live_wave[:len(wave)]!=wave):
                    raise ValueError('Installed sound route differs from verified native chair sound')
            pair.append(dict(source=label,program_sha256=sha256(program),program_offset=at,
                timing_velocity=program[8:10].hex(),bank=bank_id,instrument=program[2],
                complete_instrument=complete))
        if (pair[0]['complete_instrument']!=pair[1]['complete_instrument']
                or pair[0]['timing_velocity']!=pair[1]['timing_velocity']):
            raise ValueError('Chair sound does not match complete donor instrument/timing')
        records.append(dict(sound_id=f'{sound_id:04X}',sources=pair))
    return dict(native_categories_sha256=CATEGORY_SHA,donor_categories_sha256=sha256(source.raw('mRmTp_ftr_se_type')),
        sound_table_sha256=sha256(sounds),sounds=records,new_audio_bytes=0)


def install(original, base, prior, blob, code, imports, source, output):
    contract=audio_contract(original,base,prior,source)
    contacts=contact_contract(base,prior,blob,imports)
    four_cells=four_cell_contract(original,prior,blob,imports,source)
    original_code=by_vrom(original)[CODE_VROM].extract(original)
    original_body=original_code[ENTRY-CODE_RAM:END-CODE_RAM]
    if sha256(original_body)!=SOURCE_SHA: raise ValueError('Changed complete native sound reader')
    offset=PACKAGE+RAM-PACKAGE_RAM; end=PACKAGE+LIMIT-PACKAGE_RAM
    fire=prior['fire']['code']; fire_at=PACKAGE+0x80483800-PACKAGE_RAM
    if (fire['bytes']>RAM-0x80483800 or sha256(blob[fire_at:fire_at+fire['bytes']])!=fire['sha256']
            or any(blob[fire_at+fire['bytes']:offset])):
        raise ValueError('Shared sound reader overlaps the installed fire callbacks')
    previous=prior.get('furniture_behaviours')
    before=bytes(code[ENTRY-CODE_RAM:END-CODE_RAM])
    if previous:
        old=previous['code']
        if (sha256(blob[offset:offset+old['bytes']])!=old['sha256'] or any(blob[offset+old['bytes']:end])
                or before[:8].hex()!=previous['hook']['after'] or before[8:]!=original_body[8:]):
            raise ValueError('Changed installed shared sound reader')
    elif before!=original_body or any(blob[offset:end]):
        raise ValueError('Sound reader/reservation is not unclaimed')
    placement=checked_initial_switch(base,prior,blob)
    helper,compiled=compile_part('furniture_behaviours',output/'furniture_behaviours',
        extra_sources=('overlays/v3/furniture_behaviours.S',),
        defines=('AF_V3_INITIAL_SWITCH=1',) if placement else ())
    if placement and compiled['symbols'].get('af_v3_furniture_initial_switch')!=placement['entry']:
        raise ValueError('Changed live placement helper address')
    if (not 0<len(helper)<=LIMIT-RAM or compiled['symbols']['af_v3_furniture_action_sound']!=RAM
            or compiled['symbols']['af_v3_furniture_import_profile']!=0x80465000):
        raise ValueError('Invalid sound code reservation or shared profile dependency')
    blob[offset:end]=helper+bytes(end-offset-len(helper))
    after=struct.pack('>II',0x08000000|(RAM>>2&0x3FFFFFF),0)
    code[ENTRY-CODE_RAM:ENTRY-CODE_RAM+8]=after
    categories=source.raw('mRmTp_ftr_se_type'); records=[]
    from v3_registry import furniture_source
    for row in imports:
        index,item=row['runtime_index'],int(row['item_id'],16); at=ITEMS+slot(item)*32
        category=categories[furniture_source(row)[1]]
        if (category not in (0,1,2) or blob[at+26]>PREVIEW_COUNT or any(blob[at+28:at+32])
                or blob[at+25] not in (0,category)
                or struct.unpack_from('>HH',blob,at)!=(index,item)):
            raise ValueError('Unsupported furniture action sound or changed metadata slot')
        blob[at+25]=category
        row['action_sound']=category
        records.append(dict(item_id=row['item_id'],runtime_index=index,action_sound=category))
    return dict(code=compiled,hook=dict(address=ENTRY,before=original_body[:8].hex(),after=after.hex()),
        native_function_sha256=SOURCE_SHA,imports=records,donor=contract,contacts=contacts,
        four_cells=four_cells,
        additional_resident_bytes=0,saved_format_changed=False,ordinary_seating_tested=False)
