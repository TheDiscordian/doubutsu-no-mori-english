"""Shared source-derived placement layers and native collision-flag contract."""
import struct

from aflib import by_vrom, sha256, u32
from v3_furniture_runtime import VROM, RELOC, RAM, SIZE, RESIDENT, SOURCE_SHA
from v3_import_storage import PACKAGE, PACKAGE_RAM
from v3_furniture_tables import CAPACITY

NATIVE_TABLE = 0x8094C27C
NATIVE_SHA = '99ed21c15fc975526d9dad6352a0c5aecdf7193414c7a3aa30e7c9d788b199b8'
DONOR_SHA = '2388484ca40f750fc1e162ea1a3de1c4b43b8d1124ddbcf782b916508fafca75'
TABLE = 0x80474200
FIRST, END = TABLE-16, 0x80474A20
GUARD = bytes.fromhex('AFF7C0DE')*4
REFERENCES = ((0x8093825C,0x80938268), (0x80943878,0x8094387C),
              (0x80943978,0x8094397C), (0x80943A34,0x80943A40),
              (0x809462C8,0x809462D4))
REGISTER, REGISTER_END = 0x809381FC, 0x80938310
REGISTER_SHA = 'f74b801debd93ec2daa89dbcb541b19b0f3557f2c9dd423306bafa54793808f7'
SOURCES = ('tools/v3_furniture_placement.py',)


def references(data, relocation, target):
    """Resolve all actual HI/LO pairs, rejecting shared unrelated high halves."""
    sections = struct.unpack_from('>5I',relocation)
    if (len(data)!=SIZE or sections[:4]!=(0x10E50,0x5BE0,0x1E0,0x22F0)
            or len(relocation)!=6208 or 20+sections[4]*4>len(relocation)-4
            or u32(relocation,len(relocation)-4)!=len(relocation)):
        raise ValueError('Changed complete furniture owner/relocation dimensions')
    high, groups, locations = {}, {}, set()
    rows = struct.unpack_from('>'+str(sections[4])+'I',relocation,20)
    for record in rows:
        section,kind,offset=record>>30,record>>24&63,record&0xFFFFFF
        if section not in (1,2,3) or kind not in (2,4,5,6) or offset%4 or offset+4>sections[section-1]:
            raise ValueError('Invalid furniture relocation')
        at=sum(sections[:section-1])+offset
        if at in locations: raise ValueError('Duplicate furniture relocation')
        locations.add(at); word=u32(data,at)
        if kind==5:
            if word>>26!=15: raise ValueError('Invalid table high instruction')
            high[word>>16&31]=at; groups[at]=[]
        elif kind==6:
            register=word>>21&31
            if register not in high: raise ValueError('Unpaired table relocation')
            hi=high[register]
            address=((u32(data,hi)&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            groups[hi].append((at,address))
        elif kind==2 and target<=word<target+947:
            raise ValueError('Unimplemented absolute placement-table reference')
    pairs=[]
    for hi,lows in groups.items():
        if any(target<=address<target+947 for _,address in lows):
            if len(lows)!=1 or lows[0][1]!=target:
                raise ValueError('Placement table shares an unrelated high half or interior reference')
            pairs.append((RAM+hi,RAM+lows[0][0]))
    return tuple(sorted(pairs)), rows, locations


def install(original, base, prior, blob, imports, source):
    native_files,files=by_vrom(original),by_vrom(base)
    native=native_files[VROM].extract(original)
    current=files[VROM].extract(base); relocation=files[RELOC].extract(base)
    original_reloc=native_files[RELOC].extract(original)
    native_table=native[NATIVE_TABLE-RAM:NATIVE_TABLE-RAM+947]
    donor=source.raw('aMR_layer_set_info')
    if (sha256(native)!=SOURCE_SHA or sha256(native_table)!=NATIVE_SHA
            or sha256(donor)!=DONOR_SHA or len(donor)!=1266
            or current[NATIVE_TABLE-RAM:NATIVE_TABLE-RAM+947]!=native_table
            or sha256(native[REGISTER-RAM:REGISTER_END-RAM])!=REGISTER_SHA
            or references(native,original_reloc,NATIVE_TABLE)[0]!=REFERENCES
            or CAPACITY!=2051 or TABLE+CAPACITY>END-16):
        raise ValueError('Changed source placement categories or native consumers')
    # The twenty immutable accessory rows end at package +1140; complete
    # accessory objects begin at +2000. This table occupies the intervening gap.
    begin,end=PACKAGE+FIRST-PACKAGE_RAM,PACKAGE+END-PACKAGE_RAM
    if not PACKAGE+0x1140<=begin<end<=PACKAGE+0x2000:
        raise ValueError('Placement table overlaps accessory records or artwork')
    previous=prior.get('furniture_placement')
    data=bytearray(current)
    pairs,rows,locations=references(current,relocation,NATIVE_TABLE)
    patches=[]
    for hi,lo in REFERENCES:
        for address,part in ((hi,(TABLE+0x8000)>>16),(lo,TABLE&65535)):
            old=u32(native,address-RAM); new=old&0xFFFF0000|part
            if u32(current,address-RAM)!=(new if previous else old):
                raise ValueError('Changed current placement-table instruction')
            struct.pack_into('>I',data,address-RAM,new)
            patches.append(dict(address=address,before=old,after=new))
    patched={p['address']-RAM for p in patches}
    if previous:
        if (pairs or locations&patched or previous['patches']!=patches
                or previous['table_ram']!=TABLE or previous['capacity']!=CAPACITY
                or sha256(blob[begin:end])!=previous['reservation_sha256']):
            raise ValueError('Changed installed placement reservation or native bindings')
        new_reloc=relocation
    else:
        if pairs!=REFERENCES or not patched<=locations or any(blob[begin:end]):
            raise ValueError('Placement table reservation or reference inventory is not available')
        sections=struct.unpack_from('>5I',relocation)
        retained=[r for r in rows if sum(sections[:(r>>30)-1])+(r&0xFFFFFF) not in patched]
        if len(rows)-len(retained)!=10: raise ValueError('Incomplete placement relocation removal')
        new_reloc=bytearray(relocation)
        struct.pack_into('>I',new_reloc,16,len(retained))
        new_reloc[20:-4]=struct.pack('>'+str(len(retained))+'I',*retained)+bytes(len(relocation)-24-len(retained)*4)
        new_reloc=bytes(new_reloc)
    # Registration is the unchanged native NO_COLLISION/shop exception reader;
    # its only altered instructions are the relocated layer-table address.
    registration=bytearray(data[REGISTER-RAM:REGISTER_END-RAM])
    for p in patches:
        if REGISTER<=p['address']<REGISTER_END:
            struct.pack_into('>I',registration,p['address']-REGISTER,p['before'])
    if sha256(registration)!=REGISTER_SHA: raise ValueError('Changed native collision-registration behaviour')
    table=bytearray(CAPACITY); table[:947]=native_table
    records=[]; seen=set()
    for row in imports:
        index=row['runtime_index']; item=int(row['item_id'],16)
        if not 1024<=index<len(donor) or index!=1024+(item-0x3000)//4 or index in seen:
            raise ValueError('Invalid canonical placement identity')
        value=donor[index]
        if value not in (0,1,2): raise ValueError('Unsupported furniture placement category')
        table[index]=value;seen.add(index);row['layer_type']=value
        records.append(dict(item_id=row['item_id'],runtime_index=index,source_index=index,layer_type=value))
    # Display aliases retain their native mannequin category, not an unrelated
    # donor furniture row at the alias index.
    if set(native_table[491:746])!={0}: raise ValueError('Changed native clothing placement category')
    for row in prior['aloha_display']['rows']:
        index,donor_index=row['runtime_index'],row['donor_runtime_index']
        if (not 947<=index<CAPACITY or index in seen or not 491<=donor_index<746
                or donor[donor_index]!=native_table[donor_index]):
            raise ValueError('Changed clothing-display placement correspondence')
        table[index]=donor[donor_index];seen.add(index)
        records.append(dict(item_id=row['item_id'],runtime_index=index,source_index=donor_index,layer_type=table[index]))
    reservation=GUARD+table+bytes(END-TABLE-len(table)-16)+GUARD
    if len(reservation)!=end-begin: raise ValueError('Incorrect placement reservation size')
    blob[begin:end]=reservation
    return {VROM:bytes(data),RELOC:new_reloc},dict(table_ram=TABLE,capacity=CAPACITY,
        reservation_start=FIRST,reservation_end=END,reservation_sha256=sha256(reservation),
        table_sha256=sha256(table),native_table_sha256=NATIVE_SHA,donor_table_sha256=DONOR_SHA,
        registration_function_sha256=REGISTER_SHA,patches=patches,imports=records,
        owner_sha256=sha256(data),relocation_sha256=sha256(new_reloc),
        additional_resident_bytes=0,saved_format_changed=False,ordinary_placement_tested=False)
