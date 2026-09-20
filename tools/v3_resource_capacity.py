"""Expand the shared import reservation without adding a DMA-directory entry."""
import copy
import struct

from aflib import CODE_RAM,CODE_VROM,DMA_START,by_vrom,sha256,u32
from textbanks import Bank
from v3_import_storage import END as LEGACY_LIMIT

START,LIMIT=0x02200000,0x02800000
FORMAT='AFV3-RESOURCE-CAPACITY-1'
SOURCES=('tools/v3_resource_capacity.py','tools/v3_furniture_install.py','tools/aflib.py','tools/textbanks.py')
# These are shared text resources, not item-specific allocations. Their original
# directory rows and physical data remain in place; only virtual identities move.
TEXT=(('select',0x025F0000,0x029E0000,0x00D06000,0x80065528,0x80065614,
       '4b390c18cf32573d48069bc65fa219b4801f0e6f78c90dc29e1a13860fceba97'),
      ('string',0x02600000,0x029F0000,0x00D18000,0x800C3E30,0x800C3F1C,
       'eec19caaf3449a2368fba6339713c07c056af7a2917dd6ab76afb64fa65966d6'))


def reader_pair(vrom):
    if vrom&0xFFFF:raise ValueError('Text resource base must be 64-KiB aligned')
    return struct.pack('>2I',0x3C180000|(vrom>>16),0x27180000)


def checked_limit(image,report):
    """A declared larger bound is valid only with its actual relocated readers."""
    limit=report['import_storage']['virtual_limit'];files=by_vrom(image)
    if limit==LEGACY_LIMIT:return limit
    capacity=report.get('resource_capacity',{})
    if limit!=LIMIT or capacity.get('format')!=FORMAT or capacity.get('virtual_limit')!=LIMIT:
        raise ValueError('Unknown import-storage reservation')
    core=files[CODE_VROM].extract(image)
    if len(capacity.get('resources',[]))!=len(TEXT):raise ValueError('Incomplete relocated text records')
    for spec,row in zip(TEXT,capacity['resources'],strict=True):
        name,old,new,table,first,reader,_=spec
        entry=files.get(new)
        if (entry is None or old in files or row['name']!=name or row['vrom']!=new or row['table_vrom']!=table
                or entry.index!=row['directory_index'] or entry.size!=row['bytes']
                or sha256(entry.extract(image))!=row['sha256']
                or sha256(files[table].extract(image))!=row['table_sha256']
                or core[reader-CODE_RAM:reader-CODE_RAM+8]!=reader_pair(new)
                or sha256(core[first-CODE_RAM:first-CODE_RAM+0x140])!=row['reader_sha256']):
            raise ValueError('Expanded import bound lacks complete relocated text/readers')
    if any(e.vstart<LIMIT and START<e.vend for v,e in files.items() if v!=START):
        raise ValueError('Expanded import reservation overlaps another virtual resource')
    return limit


def expand(image,prior,core):
    """Check both complete shared consumers, then retarget their immutable bases."""
    if checked_limit(image,prior)!=LEGACY_LIMIT or prior.get('resource_capacity'):
        raise ValueError('Import storage is already expanded')
    files=by_vrom(image);old_blob=files[START];moves=[];records=[]
    if old_blob.vend>LEGACY_LIMIT or old_blob.pend:
        raise ValueError('Unexpected existing import mapping')
    permitted={START,*(r[1] for r in TEXT)}
    if any(e.vstart<LIMIT and START<e.vend for v,e in files.items() if v not in permitted):
        raise ValueError('Import expansion crosses an undeclared virtual resource')
    physical_start=old_blob.pstart+old_blob.size;physical_end=old_blob.pstart+LIMIT-START
    if (physical_end>len(image) or any(image[physical_start:physical_end]) or
            any(e.pstart<physical_end and physical_start<(e.pend or e.pstart+e.size)
                for v,e in files.items() if v!=START and e.pstart!=0xFFFFFFFF)):
        raise ValueError('Import expansion crosses live or nonempty physical cartridge data')
    for name,old,new,table,first,reader,digest in TEXT:
        entry=files[old];data=entry.extract(image);offsets=files[table].extract(image)
        padded=(entry.size+15)&~15
        padding_start=entry.pstart+entry.size;padding_end=entry.pstart+padded
        before=bytes(core[first-CODE_RAM:first-CODE_RAM+0x140])
        if (sha256(before)!=digest or core[reader-CODE_RAM:reader-CODE_RAM+8]!=reader_pair(old)
                or padded>0x10000 or entry.pend
                or any(e.vstart<new+padded and new<e.vend for e in files.values())):
            raise ValueError('Changed complete text consumer or occupied relocation destination')
        # Native text loaders round transfers up to eight bytes. The complete
        # final entry must fit that read, even when the text ends on an odd byte.
        if (padding_end>len(image) or any(image[padding_start:padding_end]) or
                any(e.pstart<padding_end and padding_start<(e.pend or e.pstart+e.size)
                    for v,e in files.items() if v!=old and e.pstart!=0xFFFFFFFF)):
            raise ValueError('Text DMA padding overlaps live or nonempty physical data')
        # Check all LUI registers, not only the known t8 encoding. There must
        # be precisely one native-core consumer of this resource's upper half.
        loads=[CODE_RAM+at for at in range(0,len(core)-3,4)
               if u32(core,at)>>26==15 and u32(core,at)&0xFFFF==old>>16]
        if loads!=[reader]:raise ValueError('Unreviewed text-base consumer')
        entries=Bank(name,old,table,data,offsets).entries()
        if not entries or sum(map(len,entries))>len(data):raise ValueError('Incomplete complete text resource')
        core[reader-CODE_RAM:reader-CODE_RAM+8]=reader_pair(new)
        moves.append(dict(old_vrom=old,vrom=new,bytes=padded,previous_bytes=entry.size,directory_index=entry.index,
                          physical=entry.pstart,physical_end=entry.pend))
        records.append(dict(name=name,old_vrom=old,vrom=new,table_vrom=table,
            directory_index=entry.index,bytes=padded,source_bytes=entry.size,source_sha256=sha256(data),
            dma_padding_bytes=padded-entry.size,sha256=sha256(data+bytes(padded-entry.size)),table_sha256=sha256(offsets),
            entries=len(entries),reader=reader,reader_start=first,reader_bytes=0x140,
            previous_reader_sha256=digest,reader_sha256=sha256(core[first-CODE_RAM:first-CODE_RAM+0x140]),
            before=reader_pair(old).hex(),after=reader_pair(new).hex(),consumer_addresses=loads))
    storage=copy.deepcopy(prior['import_storage'])
    storage.update(virtual_limit=LIMIT,remaining_bytes=LIMIT-old_blob.vend,
                   choice_vrom=TEXT[0][2],general_strings_vrom=TEXT[1][2])
    return dict(import_storage=storage,resource_capacity=dict(format=FORMAT,
        virtual_start=START,virtual_limit=LIMIT,previous_limit=LEGACY_LIMIT,
        additional_virtual_bytes=LIMIT-LEGACY_LIMIT,resources=records,
        reserved_physical_start=physical_start,reserved_physical_end=physical_end,
        directory_entries_added=0,additional_resident_bytes=0,saved_format_changed=False,
        saved_profile_changed=False)),moves


def relocate_directory(result,files,moves):
    for row in moves:
        entry=files[row['old_vrom']]
        if (entry.index!=row['directory_index'] or entry.size!=row['previous_bytes'] or
                (entry.pstart,entry.pend)!=(row['physical'],row['physical_end'])):
            raise ValueError('Changed text directory row before relocation')
        struct.pack_into('>2I',result,DMA_START+entry.index*16,row['vrom'],row['vrom']+row['bytes'])


def native_scenario(image,report):
    """One bounded batch: changed text address/DMA paths and installed clock rigs."""
    if sha256(image)!=report['output_sha256']:raise ValueError('Storage probe requires the checked cartridge')
    checked_limit(image,report);files=by_vrom(image)
    actions=[{'wait':16},{'read':['8019ACD0',4],'expect':'00000001'},
             {'save_state':True},{'pause_game_thread':True}]
    def write(at,data):actions.append(dict(write=[f'{at:08X}',data.hex()]))
    def read(at,data):actions.append(dict(read=[f'{at:08X}',len(data)],expect=data.hex()))
    def call(at,args):actions.append(dict(call=dict(address=f'{at:08X}',arguments=args,return_address='8019AD60')))
    for row in report['resource_capacity']['resources']:
        bank=Bank(row['name'],row['vrom'],row['table_vrom'],files[row['vrom']].extract(image),
                  files[row['table_vrom']].extract(image));entries=bank.entries()
        starts=[0]
        for entry in entries:starts.append(starts[-1]+len(entry))
        width=20 if row['name']=='select' else 64
        chosen=sorted({0,len(entries)-1,max((i for i,e in enumerate(entries) if 0<len(e)<=width),key=lambda i:len(entries[i]))})
        if row['name']=='select':write(0x8019B000,bytes(0x1B0))
        for index in chosen:
            write(0x8019AF00,b'G'*16);call(row['reader_start'],[index,0x8019AF00,0x8019AF04])
            address=row['vrom']+starts[index];data=entries[index]
            read(0x8019AF00,struct.pack('>2I',address,len(data))+b'G'*8)
            write(0x8019AE00,b'G'*96)
            if row['name']=='select':call(0x80065D90,[0x8019B000,0x8019AE08,index,0])
            else:call(0x800C3F70,[0x8019AE08,width,index])
            read(0x8019AE00,b'G'*8+data.ljust(width,b' ')+b'G'*(88-width))
        write(0x8019AF00,b'G'*16)
        call(row['reader_start'],[len(entries),0x8019AF00,0x8019AF04])
        read(0x8019AF00,bytes(8)+b'G'*8)
    if any(r.get('mode')==1 for r in report['equipment_resources']['room_rigs']['rows']):
        actions.append(dict(test_v3_furniture_batch=True,item_batch_section='clock_rigs'))
    actions.extend([{'load_state':True},{'wait':1}])
    read(0x8003CE34,bytes(4));read(0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    read(0x804B1FF0,bytes.fromhex('AF48C0DE')*4)
    read(report['save_runtime']['guard_ram'],bytes.fromhex('AF53C0DE')*4)
    return actions
