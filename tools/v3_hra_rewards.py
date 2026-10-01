"""Original HRA model reward integration, retaining the complete current creator."""
import copy
import json
import struct
import zlib
from types import SimpleNamespace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from catalogue_names import elf_inventory
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT, compile_part
import v3_hra_mail as mail
import v3_hra as owner
import v3_npc_mail_heap as heap

FORMAT = 'AFV3-HRA-REWARDS-1'
CREATOR_SHA = 'f701078ae3cd1148178eb484d5bfcc9c25d655040a0bbc96fe734831b18f21d6'
CREATOR_IMAGE = 62768
SCORE_ENTRY = 0x25F0
INTERNAL = dict(af_mail_create_guard=0x1484, af_academy_mail_create=0x23A0,
                af_mail_capture_set=0xEE4, af_mail_generate=0x100C)
EXTERNAL = dict(af_format_year=0x80195CB0, af_format_month=0x80195CC0,
                af_format_day=0x80195CE0, af_load_item_name=0x801969C8)
SOURCES = ('tools/v3_hra_rewards.py', 'tools/v3_asset_loader.py',
           'overlays/v3/hra_reward_mail.ld',
           'overlays/v3/hra_rewards.S', 'overlays/v3/hra_rewards.ld',
           'overlays/mail_generation/academy_score_creator.c',
           'overlays/mail_generation/academy_score_creator.h')+heap.SOURCES
SEND, SEND_END = 0x80925E48, 0x809260A4
BINDINGS = dict(af_hra_mail_free=0x8009C534,
    af_hra_native_letter=0x80925BB8, af_hra_english_mail=0x80197BB4,
    af_hra_mail_copy=0x8009C67C, af_hra_mail_receipt=0x800B6A3C,
    af_hra_import_selected=0x80465000)
DONOR_FUNCTIONS = (
    ('mMkRm_ProcAfterSending',0x161F70,56,
     '1fa305825a2500bad0768a550d6d616e171f54d957a1db26ec75e9be46104c5a'),
    ('mMkRm_DecideLetterNo',0x161FA8,440,
     '0b60a0b8a45eb48a7cea4711c87b8da5e4b90d42f3a9a23b18c10653cfd0f175'),
    ('mMkRm_SendMarkLetter',0x1621F0,584,
     'eb740977694f3215648e06b8e25859c803c5def2bfcc1fbd774b9c034b22ff29'))
NATIVE_FUNCTIONS = (
    ('house_initialization',0x80094520,368,
     'f567fa8e97fffe0beec1b6177054c2c2eff4f0b36325d67ddc2621eda7aaa61a'),
    ('hra_date_clear',0x8009C9F0,100,
     '50d8b32368d4e012d291a516e0884f981a8180d4b4ac8f233f4ea03d2da372a2'),
    ('hra_after_delivery',0x8009CB5C,164,
     '57929566cace5a60c8468b8c1ddac4c179c19cab4efe39de6032a77bab47b9c5'),
    ('hra_house_dirty',0x8009CC00,148,
     '7c20bcb4ad22ba3c2f36c00ebc866c4bf42ef560f7d70c358c4e715e05e2a2db'),
    ('hra_scheduler',0x8009CDA8,520,
     '53d3793d54156581ee51255c24bb126a6dc6f88ffd6dfe746d69bb41884bc9c3'))


def donor_contract(source):
    """Derive rewards from the complete compiled selector and delivery routines."""
    functions = []
    for name, at, size, digest in DONOR_FUNCTIONS:
        raw, receipt = source.function(at)
        if (receipt['symbol'] != name or len(raw) != size or sha256(raw) != digest):
            raise ValueError('Changed complete source HRA reward function: '+name)
        functions.append(receipt)
    raw = source.function(DONOR_FUNCTIONS[1][1])[0]
    rows = []
    for position, index, points, flag in ((23,1033,70000,8),(34,1034,100000,4)):
        gift, letter = struct.unpack_from('>2I',raw,position*4)
        if gift>>16 != 0x3800 or letter>>16 != 0x3860:
            raise ValueError('Changed source HRA gift/template instructions')
        item, template = gift&65535, letter&65535
        if (item != 0x3000+(index-1024)*4 or
                template != 0x221+len(rows) or source.raw('mRmTp_birth_type')[index] != 20):
            raise ValueError('Changed source HRA reward identity or acquisition category')
        rows.append(dict(item=item,index=index,points=points,flag=flag,template=template))
    return json.loads(json.dumps(dict(functions=functions,rewards=rows,
        source_symbol=DONOR_FUNCTIONS[1][0],source_sha256=DONOR_FUNCTIONS[1][3],
        catalogue_orderable=False)))


def native_contract(core):
    """Keep native house initialization, scheduler, and all existing flag bits."""
    rows = []
    for name, address, size, digest in NATIVE_FUNCTIONS:
        raw = core[address-CODE_RAM:address-CODE_RAM+size]
        if sha256(raw) != digest:
            raise ValueError('Changed native HRA reward dependency: '+name)
        rows.append(dict(name=name,address=address,bytes=size,sha256=digest))
    return dict(functions=rows,house_base=0x8012A428,house_stride=0xB48,
                flag_offset=0x1C,mailbox_offset=0x478,
                retained_flags_mask=0xF3,saved_format_changed=False)


def patch_controller(data, relocation, code, compiled):
    """Replace only the existing mail wrapper and its internal jump relocations."""
    from academy_score_letters import entry_patch
    start, end = SEND-owner.RAM, SEND_END-owner.RAM
    sections = struct.unpack_from('>5I',relocation)
    if (sections[:4] != (len(data),0,0,0) or len(data) > 0x8000 or
            data[start:end] != entry_patch(BINDINGS['af_hra_english_mail']) or
            not code or len(code)%4 or len(code)>end-start or
            compiled['symbols'].get('af_hra_reward_send') != SEND):
        raise ValueError('Changed original HRA send wrapper or new controller boundary')
    rows = list(struct.unpack_from('>'+str(sections[4])+'I',relocation,20))
    removed = [r for r in rows if r>>30==1 and start <= r&0xFFFFFF < end]
    if removed != [0x44000000|start+20*4]:
        raise ValueError('Changed original HRA send relocation inventory')
    rows = [r for r in rows if r not in removed]
    inventory = elf_inventory(compiled['elf_relocations'],ram=owner.RAM)
    calls = []
    for at,kind,target,name in inventory:
        if kind != 4 or at&3 or not start <= at <= start+len(code)-4:
            raise ValueError('HRA send has an unsupported or displaced relocation')
        actual = ((u32(code,at-start)&0x3FFFFFF)<<2)|(SEND&0xF0000000)
        if name == '.text':
            if target != SEND or not SEND <= actual < SEND+len(code):
                raise ValueError('HRA local helper target escapes its wrapper')
        elif BINDINGS.get(name) != target or actual != target:
            raise ValueError('HRA send uses an unbound native function')
        if owner.RAM <= actual < owner.RAM+len(data):
            rows.append(0x44000000|at)
        calls.append(dict(offset=at,target=actual,symbol=name))
    if (len(calls)!=8 or len({r['offset'] for r in calls})!=8 or
            sum(r['symbol']=='.text' for r in calls)!=1 or
            {r['symbol'] for r in calls if r['symbol']!='.text'}!=set(BINDINGS) or
            sum(r['symbol']=='af_hra_import_selected' for r in calls)!=2):
        raise ValueError('Incomplete HRA source delivery or independent selection calls')
    rows.sort(key=lambda r:(r>>30,r&0xFFFFFF))
    if len({r&0xFFFFFF for r in rows})!=len(rows):
        raise ValueError('Duplicate HRA send relocation')
    minimum=(24+len(rows)*4+15)&~15
    length=len(relocation)
    if minimum > length or length%16 or u32(relocation,length-4)!=length:
        raise ValueError('HRA controller exceeds its existing relocation allocation')
    rel=(struct.pack('>5I',len(data),0,0,0,len(rows))+
         struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-len(rows)*4)+struct.pack('>I',length))
    result=bytearray(data); result[start:end]=code.ljust(end-start,b'\0')
    for loaded in (0x801A0010,0x802F8010,0x803D0010):
        old=relocate_verified_data(SimpleNamespace(ram=owner.RAM,resident_bytes=len(data),
            sections=sections),data,relocation,loaded)
        new=relocate_verified_data(SimpleNamespace(ram=owner.RAM,resident_bytes=len(data),
            sections=(len(data),0,0,0,len(rows))),result,rel,loaded)
        if old[:start]!=new[:start] or old[end:]!=new[end:]:
            raise ValueError('HRA send changes unrelated relocated scoring code or data')
        for call in calls:
            word=u32(new,call['offset'])
            actual=((word&0x3FFFFFF)<<2)|(loaded&0xF0000000)
            expected=call['target']
            if owner.RAM <= expected < owner.RAM+len(data):expected+=loaded-owner.RAM
            if actual!=expected:raise ValueError('HRA send native call relocates incorrectly')
    return bytes(result),rel,dict(code=dict(compiled,ram=SEND),calls=calls,
        patch=dict(offset=start,bytes=end-start,before=data[start:end].hex(),
                   after=bytes(result[start:end]).hex()),
        removed_relocations=removed,sections=(len(data),0,0,0,len(rows)))


def creator_source(source, module, report):
    size = report['image_bytes']
    at, width = report['name_table_address']-mail.RAM, report['name_table_bytes']
    relocation = source[size:]
    if (report.get('reward_creator') or sha256(source) != CREATOR_SHA
            or sha256(source) != report['output_sha256'] or size != CREATOR_IMAGE
            or len(source) != size+mail.RELOC_BYTES or report['name_rows'] != 60
            or at != mail.IMAGE or width != 60*26
            or sha256(source[at:at+width]) != report['name_table_sha256']
            or any(source[at+width:size])
            or struct.unpack_from('>5I', relocation) != (size,0,0,0,233)
            or u32(relocation,len(relocation)-4) != len(relocation)
            or list(struct.unpack_from('>8I',module,0x48)) != report['configuration']
            or report['configuration'] != [mail.VROM,len(source),size,len(relocation),
                                           0xEBF0,size,zlib.crc32(source),0x41464E01]):
        raise ValueError('Changed complete HRA creator, expanded names, or loader')
    rows = list(struct.unpack_from('>233I',relocation,20))
    if any(row>>30 != 1 or SCORE_ENTRY <= row&0xFFFFFF < SCORE_ENTRY+8 for row in rows):
        raise ValueError('HRA score entry displaces a native relocation')
    return rows


def extend_creator(source, module, report, output):
    """Append one compiled score creator; preserve every other current reader."""
    rows = creator_source(source,module,report)
    size = report['image_bytes']
    bindings = {name:mail.RAM+offset for name,offset in INTERNAL.items()}
    bindings.update(EXTERNAL)
    bindings['af_academy_series_data'] = report['name_table_address']
    code,compiled = compile_part('hra_reward_mail',output/'hra_reward_mail',
        primary_source='overlays/mail_generation/academy_score_creator.c',
        defines=('AF_V3_HRA_REWARDS=1','AF_MAIL_CREATOR_CATALOG=4',
                 'AF_V3_HRA_SERIES_COUNT=60'),
        link_symbols={**bindings,'AF_HRA_MAIL_RAM':mail.RAM+size})
    new_size = size+len(code)
    if len(code)%16 or not code or compiled['symbols']['af_academy_score_mail_create'] != mail.RAM+size:
        raise ValueError('HRA reward creator has an invalid entry or image boundary')
    inventory = elf_inventory(compiled['elf_relocations'],ram=mail.RAM)
    seen = set()
    for at,kind,target,name in inventory:
        if at in seen or at&3 or not size <= at <= new_size-4:
            raise ValueError('HRA reward relocation escapes the appended code')
        seen.add(at)
        if mail.RAM <= target < mail.RAM+new_size:
            if kind not in (2,4,5,6):
                raise ValueError('Unsupported HRA internal relocation')
            rows.append(0x40000000|kind<<24|at)
        elif bindings.get(name) != target or kind != 4:
            raise ValueError('HRA reward creator uses an unbound native import')
    entry = struct.pack('>2I',0x08000000|((mail.RAM+size)>>2)&0x3FFFFFF,0)
    rows.append(0x44000000|SCORE_ENTRY)
    if len({row&0xFFFFFF for row in rows}) != len(rows):
        raise ValueError('Duplicate HRA reward creator relocation')
    length = (24+len(rows)*4+15)&~15
    relocation = (struct.pack('>5I',new_size,0,0,0,len(rows))
        +struct.pack('>'+str(len(rows))+'I',*rows)
        +bytes(length-24-len(rows)*4)+struct.pack('>I',length))
    result = bytearray(source[:size]+code)
    before = bytes(result[SCORE_ENTRY:SCORE_ENTRY+8])
    result[SCORE_ENTRY:SCORE_ENTRY+8] = entry
    if len(result)+len(relocation) > 0x10000:
        raise ValueError('HRA reward code and relocation exceed the complete creator allocation')
    old_spec = SimpleNamespace(ram=mail.RAM,resident_bytes=size,sections=(size,0,0,0,233))
    spec = SimpleNamespace(ram=mail.RAM,resident_bytes=new_size,sections=(new_size,0,0,0,len(rows)))
    for loaded in (0x801A0010,0x802F8010,0x803D0010):
        old = relocate_verified_data(old_spec,source[:size],source[size:],loaded)
        new = relocate_verified_data(spec,result,relocation,loaded)
        if old[:SCORE_ENTRY] != new[:SCORE_ENTRY] or old[SCORE_ENTRY+8:] != new[SCORE_ENTRY+8:size]:
            raise ValueError('HRA reward relocation changes retained creator code or resources')
        expected = struct.pack('>2I',0x08000000|((loaded+size)>>2)&0x3FFFFFF,0)
        if new[SCORE_ENTRY:SCORE_ENTRY+8] != expected:
            raise ValueError('HRA reward score entry relocates incorrectly')
    result = bytes(result+relocation)
    configuration = list(report['configuration'])
    configuration[1:4] = len(result),new_size,len(relocation)
    configuration[5:7] = new_size,zlib.crc32(result)
    struct.pack_into('>8I',module,0x48,*configuration)
    extension = dict(format=FORMAT,installed=True,previous_sha256=sha256(source),
        prefix_bytes=size,entry_offset=SCORE_ENTRY,before=before.hex(),after=entry.hex(),
        previous_relocation=source[size:].hex(),code=dict(compiled,ram=mail.RAM+size),
        elf_inventory=inventory,rows=len(rows),bytes=len(code),
        native_execution_verified=False,sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return result,{**copy.deepcopy(report),'output_sha256':sha256(result),
        'image_bytes':new_size,'bytes':len(result),'relocation_bytes':len(relocation),
        'configuration':configuration,'reward_creator':extension,
        'native_letter_generation_tested':False}


def install(base, prior, core, module, output):
    """Use the existing owner-refresh path; no item becomes selectable here."""
    from v3_furniture_pipeline import Source
    from v3_furniture_install import relocate_resource_plan
    from v3_asset_loader import BLOB
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if prior.get('hra',{}).get('model_rewards'):
        checked(source,base,prior,require_heap=False)
        equipment,records,writes=heap.install(base,prior,module,output)
        return {},dict(hra=copy.deepcopy(prior['hra']),equipment_resources=equipment,
                       physical_resources=records),writes
    native=native_contract(core);donor=donor_contract(source)
    files = by_vrom(base)
    old = files[mail.VROM].extract(base)
    creator,letters = extend_creator(old,module,prior['hra']['score_letters'],output)
    old_data,old_reloc=(files[v].extract(base) for v in (owner.NEW_VROM,owner.NEW_RELOC))
    if (sha256(old_data)!=prior['hra']['output_sha256'] or
            sha256(old_reloc)!=prior['hra']['relocation_sha256']):
        raise ValueError('Changed complete current HRA scoring owner')
    code,compiled=compile_part('hra_rewards',output/'hra_rewards',
        primary_source='overlays/v3/hra_rewards.S',link_symbols=BINDINGS)
    data,reloc,controller=patch_controller(old_data,old_reloc,code,compiled)
    hra = copy.deepcopy(prior['hra']);hra['score_letters'] = letters
    hra.update(output_sha256=sha256(data),relocation_sha256=sha256(reloc),
        model_rewards=dict(format=FORMAT,installed=True,source=donor,native=native,
            controller=controller,wrapper_stack_bytes=256,
            native_delivery_tested=False,ordinary_gameplay_tested=False,
            sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}))
    _, growth=relocate_resource_plan(base,files,mail.VROM,creator,
        minimum_physical=files[BLOB].pstart+files[BLOB].size,append_only=False,
        reservations=prior.get('physical_resources',[]))
    equipment,records,writes=heap.install(base,prior,module,output)
    return {mail.VROM:creator,owner.NEW_VROM:data,owner.NEW_RELOC:reloc},dict(
        hra=hra,resource_growth=[growth],equipment_resources=equipment,
        physical_resources=records),writes


def checked(source, image, report, *, require_heap=True):
    """Authenticate the installed controller, creator, loader, and original rules."""
    from v3_asset_loader import MODULE, BLOB, BLOB_RAM
    hr=report.get('hra',{});reward=hr.get('model_rewards')
    if not reward:return None
    if require_heap:heap.checked(image,report)
    files=by_vrom(image)
    data,reloc,creator,module=(files[v].extract(image) for v in
        (owner.NEW_VROM,owner.NEW_RELOC,mail.VROM,MODULE))
    native=native_contract(files[CODE_VROM].extract(image))
    donor=donor_contract(source)
    if (reward.get('format')!=FORMAT or not reward.get('installed') or
            reward['source']!=donor or reward['native']!=native or
            sha256(data)!=hr['output_sha256'] or sha256(reloc)!=hr['relocation_sha256']):
        raise ValueError('Changed complete installed HRA reward rules or scoring owner')
    control=reward['controller'];code=control['code'];patch=control['patch']
    start,end=SEND-owner.RAM,SEND_END-owner.RAM
    raw=data[start:start+code['bytes']]
    if (patch['offset']!=start or patch['bytes']!=end-start or
            patch['after']!=data[start:end].hex() or sha256(raw)!=code['sha256'] or
            data[start:end]!=raw.ljust(end-start,b'\0') or code['ram']!=SEND or
            code['symbols'].get('af_hra_reward_send')!=SEND):
        raise ValueError('Changed actual HRA reward send controller')
    # Reconstruct the retained owner, then independently repeat only the checked
    # wrapper/relocation transformation. Scoring rows may have grown since the
    # reward installation; their current contents stay intact.
    old=bytearray(data);old[start:end]=bytes.fromhex(patch['before'])
    sections=struct.unpack_from('>5I',reloc)
    rows=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
    rows=[r for r in rows if not(r>>30==1 and start<=r&0xFFFFFF<end)]
    rows+=control['removed_relocations'];rows.sort(key=lambda r:(r>>30,r&0xFFFFFF))
    prior_rel=(struct.pack('>5I',len(data),0,0,0,len(rows))+
        struct.pack('>'+str(len(rows))+'I',*rows)).ljust(len(reloc)-4,b'\0')+reloc[-4:]
    rebuilt,relinked,receipt=patch_controller(bytes(old),prior_rel,raw,code)
    if rebuilt!=data or relinked!=reloc or json.dumps(receipt,sort_keys=True)!=json.dumps(control,sort_keys=True):
        raise ValueError('Changed complete HRA controller call or relocation inventory')
    letters=hr['score_letters'];extension=letters.get('reward_creator',{})
    size=letters['image_bytes'];prefix=extension.get('prefix_bytes',0)
    if (extension.get('format')!=FORMAT or not extension.get('installed') or
            prefix!=CREATOR_IMAGE or extension.get('entry_offset')!=SCORE_ENTRY or
            sha256(creator)!=letters['output_sha256'] or
            len(creator)!=letters['bytes'] or len(creator)-size!=letters['relocation_bytes'] or
            list(struct.unpack_from('>8I',module,0x48))!=letters['configuration'] or
            letters['configuration']!=[mail.VROM,len(creator),size,len(creator)-size,
                                      0xEBF0,size,zlib.crc32(creator),0x41464E01]):
        raise ValueError('Changed complete installed HRA letter creator or loader')
    previous=bytearray(creator[:prefix]);previous[SCORE_ENTRY:SCORE_ENTRY+8]=bytes.fromhex(extension['before'])
    previous+=bytes.fromhex(extension['previous_relocation'])
    compiled=extension['code'];ram=mail.RAM+prefix
    if (sha256(previous)!=CREATOR_SHA or extension['previous_sha256']!=CREATOR_SHA or
            compiled['ram']!=ram or compiled['bytes']!=size-prefix or
            compiled['symbols'].get('af_academy_score_mail_create')!=ram or
            sha256(creator[prefix:size])!=compiled['sha256'] or
            creator[SCORE_ENTRY:SCORE_ENTRY+8]!=struct.pack('>2I',0x08000000|(ram>>2)&0x3FFFFFF,0) or
            creator[SCORE_ENTRY:SCORE_ENTRY+8].hex()!=extension['after']):
        raise ValueError('Changed HRA reward letter extension or retained English resources')
    current_sections=struct.unpack_from('>5I',creator,size)
    old_rows=list(struct.unpack_from('>233I',previous,prefix+20))
    expected=old_rows[:]
    for at,kind,target,name in elf_inventory(compiled['elf_relocations'],ram=mail.RAM):
        if mail.RAM<=target<mail.RAM+size:expected.append(0x40000000|kind<<24|at)
    expected.append(0x44000000|SCORE_ENTRY)
    if (current_sections!=(size,0,0,0,len(expected)) or
            list(struct.unpack_from('>'+str(len(expected))+'I',creator,size+20))!=expected or
            u32(creator,len(creator)-4)!=len(creator)-size):
        raise ValueError('Changed HRA reward creator relocation inventory')
    # The selector reads furniture indices, not item IDs. Authenticate the
    # complete resident reader which consults each import's actual enabled row.
    expanded=report['furniture']['expanded_tables'];reader=expanded['expanded_code']
    blob=files[BLOB].extract(image)
    entry=next((r for r in expanded['public_entries']
                if r['name']=='af_v3_furniture_import_profile'),None)
    ram=reader['symbols']['af_v3_furniture_import_profile'];at=ram-BLOB_RAM
    expected=struct.pack('>2I',0x08000000|(ram>>2)&0x3FFFFFF,0)
    if (not entry or entry['entry']!=BINDINGS['af_hra_import_selected'] or
            entry['target']!=ram or entry['after']!=expected.hex() or
            blob[entry['entry']-BLOB_RAM:entry['entry']-BLOB_RAM+8]!=expected or
            ram!=0x80465800 or not 0<reader['bytes']<=0x800 or
            sha256(blob[at:at+reader['bytes']])!=reader['sha256']):
        raise ValueError('Changed independent HRA import-selection reader')
    return dict(**donor,native_delivery_installed=True,ordinary_gameplay_tested=False)


def acquisition(binding, reward):
    return dict(route='hra',destination_item=f'{reward["item"]:04X}',
        points=reward['points'],template=reward['template'],flag=reward['flag'],
        dependencies=[],native_delivery_installed=True,ordinary_gameplay_tested=False)


def furniture(source, item, index, lists):
    contract=donor_contract(source)
    reward=next((r for r in contract['rewards'] if r['item']==item),None)
    if reward is None:return None
    if reward['index']!=index or lists:
        raise ValueError('Changed source HRA reward identity or unrelated stock membership')
    binding=getattr(source,'hra_acquisition',None)
    if binding is None:
        from v3_furniture_pipeline import ReviewRequired
        raise ReviewRequired('acquisition needs an adapter: complete original HRA reward delivery')
    if binding['rewards']!=contract['rewards']:
        raise ValueError('Installed HRA rewards differ from the complete source selector')
    return dict(donor_list=contract['source_symbol'],donor_list_sha256=contract['source_sha256'],
        stock_group=255,reward_route=0,ordinary_stock=False,catalogue_orderable=False,
        hra_acquisition=acquisition(binding,reward))


def catalogue_source(source, item, index, row):
    contract=donor_contract(source)
    reward=next((r for r in contract['rewards'] if r['item']==item),None)
    return bool(reward and reward['index']==index and
        row.get('donor_acquisition_list')==contract['source_symbol'] and
        row.get('catalogue_orderable') is False and
        row.get('hra_acquisition')==acquisition(contract,reward))


def installed_items(report):
    reward=report.get('hra',{}).get('model_rewards',{})
    if not reward.get('installed') or reward.get('format')!=FORMAT:return set()
    return {r['item_id'] for r in report['furniture']['imports']
        if r.get('hra_acquisition',{}).get('route')=='hra' and
        r['hra_acquisition'].get('native_delivery_installed') and
        r['hra_acquisition'].get('destination_item')==r['item_id'] and
        not r['hra_acquisition'].get('dependencies') and r.get('runtime_installed') and
        not set(r.get('remaining',[]))-{'representative native execution','ordinary gameplay and save/restart'}}


def verify_installed_items(image, report):
    items=installed_items(report)
    if not report.get('hra',{}).get('model_rewards'):return items
    from v3_furniture_pipeline import Source
    from v3_furniture_install import catalogue_record,order_mask
    from v3_import_storage import ITEMS
    from v3_asset_loader import BLOB
    from v3_registry import furniture_source
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    binding=checked(source,image,report);blob=by_vrom(image)[BLOB].extract(image)
    for row in report['furniture']['imports']:
        if not row.get('hra_acquisition'):continue
        donor,index=furniture_source(row);record=catalogue_record(row)
        slot=row['runtime_index']-1024;metadata=blob[ITEMS+slot*32:ITEMS+(slot+1)*32]
        if (row['item_id'] not in items or not catalogue_source(source,donor,index,record) or
                row['donor_list_sha256']!=binding['source_sha256'] or row['ordinary_stock'] or
                row['stock_group']!=255 or row['reward_route']!=0 or order_mask(record)!=0 or
                struct.unpack_from('>2H',metadata)!=(row['runtime_index'],int(row['item_id'],16)) or
                metadata[7]!=1 or metadata[24]!=0 or metadata[27]!=0):
            raise ValueError('Changed installed HRA reward acquisition, ordering, or metadata')
    return items
