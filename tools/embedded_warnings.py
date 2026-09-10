"""Complete English data tables for native inventory and Controller Pak warnings."""
from dataclasses import dataclass
import math
import struct

from aflib import by_vrom,sha256,verified_rom,CODE_VROM
from font import WIDTH_TABLE
from textcodec import encode,command_info,has_japanese
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256


@dataclass(frozen=True)
class WindowOwner:
    name: str
    vrom: int
    relocation: int
    ram: int
    sections: tuple
    source_sha: str
    relocation_sha: str
    first_line: int
    table: int
    windows: int
    new_vrom: int
    new_relocation: int
    parent_at: int
    parent_hex: str


WARNING=WindowOwner('inventory_warning',0x79A290,0x79AFD0,0x80896B20,(2192,1200,0,16,78),
    '05cf6aa2ae96ddcfeaea98af50b34d3b432602277da5dbf3c09042cb2c15a47b',
    'a583a6a5ecf59b2fed4cc561d17bf361e990b4c227e7cfbf91b0f99ab0ce8e13',
    0x9E8,0xC08,16,0x3E00000,0x3E10000,0x2C10,
    '0079a2900079afd080896b20808978708089730c808973948089728c00000000')
PAK=WindowOwner('controller_pak_warning',0x79F810,0x7A0F40,0x808A2EA0,(4864,1056,16,16,98),
    'a30ee0787e1f5af42f95574ee2e6cc8265af43ad2bc9a0198853681399d9162c',
    'c64e7efe9879f74fba6eb9112d9c5629182f5b64e3d85668918aac335c4dbe9b',
    0x1430,0x1610,13,0x3E20000,0x3E30000,0x2C50,
    '0079f810007a0f40808a2ea0808a45e0808a40f0808a4188808a405800000000')
OWNERS=(WARNING,PAK)
WIDTH_SHA='74ecbd2d0f1ca55cd55fc57f977d3a957dc2659068e7ad99360f097ef9834fc1'

# Keep the native two-body-line layout and choice indices. These translations
# preserve N64-only restrictions, while matching supplied GC wording where it fits.
WARNING_TEXT=(
    ("You can't hold any more letters!","Throw away some old ones?","Yes","No"),
    ("You can't pull out a present","when your item screen is full!"),
    ("You can't carry","more than 50,000 Bells!"),
    ("You can't mail","turnips or living things!"),
    ("You can't mail","someone else's belongings!"),
    ("You can't store","things that can spoil!"),
    ("You can't store","someone else's belongings!"),
    ("You can't store","that item!"),
    ("You can't sell","someone else's belongings!"),
    ("You can't put","any more items out!"),
    ("You can't put","any more items there!"),
    ("You can't drop","any more items here!"),
    ("You can't plant","anything else here!"),
    ("You can't open a bag","without room for three items!"),
    ("You can't mail","a wrapped present!"),
    ("You can't carry more letters,","so you can't write a new one!"),
)
PAK_TEXT=(
    ('Reading data from','the Controller Pak.','Please wait.'),
    ('Saving...',),
    ('Deleting the selected data.','Please wait.'),
    ('Please insert a','Controller Pak into','Controller 1.'),
    ('The data could not','be written.'),
    ('The data could not','be read.'),
    ('A different Controller Pak','has been inserted.'),
    ('The data could not','be deleted.'),
    ("The Controller Pak's",'data is damaged.','Reconnect the Pak','or repair it.'),
    ('Repairing the Pak','may erase its data.','Do you want','to continue?'),
    ('Please insert a','Controller Pak into','Controller 1.'),
    ('Reconnect','Repair','Quit'),
    ('Yes','No'),
)
# Direct supplied GC source strings; the remaining wording is an explicit native
# adaptation, not a claim of an exact GC line or of GC Pak functionality.
GC_STRINGS=((0x83F30,'Yes'),(0x83F34,'No'),
    (0x83F38,"You can't pull out a present"),(0x83F54,'when your item screen is full!'),
    (0x83F74,"You can't carry"),(0x83F9C,"You can't mail"),
    (0x83FAC,'turnips or living things!'),(0x83FC8,"someone else's belongings!"),
    (0x83FE4,'a wrapped present!'),(0x8400C,"so you can't write a new one!"),
    (0x84078,"You can't put"),(0x84088,'any more items out!'),(0x8409C,'any more items there!'),
    (0x84108,"You can't drop"),(0x84118,'any more items here!'),
    (0x8412C,"You can't plant"),(0x8413C,'anything else here!'),(0x84150,"You can't open a bag"))


def reference(rel,symbols):
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied warning reference')
    for offset,text in GC_STRINGS:
        if rel[DATA_BASE+offset:DATA_BASE+offset+len(text)]!=text.encode():
            raise ValueError('Changed complete GC warning wording')


def source(native,owner):
    files=by_vrom(verified_rom(native));data=files[owner.vrom].extract(native)
    reloc=files[owner.relocation].extract(native)
    if (sha256(data)!=owner.source_sha or sha256(reloc)!=owner.relocation_sha
            or struct.unpack_from('>5I',reloc)!=owner.sections
            or files[owner.relocation].index!=files[owner.vrom].index+1
            or files[0x7749C0].extract(native)[owner.parent_at:owner.parent_at+32]!=bytes.fromhex(owner.parent_hex)):
        raise ValueError('Changed native warning owner, relocation, or parent')
    return data,reloc


def line_groups(data,owner):
    groups=[]
    for i in range(owner.windows):
        ptr,count,sx,sy=struct.unpack_from('>IIff',data,owner.table+i*16)
        offset=ptr-owner.ram
        if (not owner.first_line<=offset<=owner.table-count*16 or (offset-owner.first_line)%16
                or not 1<=count<=4 or not 0.5<=sx<=1.5 or not 0.5<=sy<=1.5):
            raise ValueError('Unexpected native warning window table')
        rows=[]
        for n in range(count):
            at=offset+n*16;x,y,ptr,length=struct.unpack_from('>ffII',data,at)
            if (not owner.sections[0]<=ptr-owner.ram<owner.first_line
                    or not 1<=length<=32 or ptr-owner.ram+length>owner.first_line):
                raise ValueError('Unbounded native warning text')
            rows.append((at,x,y,ptr,length))
        groups.append((sx,sy,rows))
    if {at for _,_,rows in groups for at,*_ in rows}!=set(range(owner.first_line,owner.table,16)):
        raise ValueError('Uninventoried native warning line')
    return groups


def flattened_relocations(original,owner,size):
    words=[];s=owner.sections
    for row in struct.unpack_from('>'+str(s[4])+'I',original,20):
        section,kind,at=row>>30,row>>24&63,row&0xFFFFFF
        if section not in (1,2,3) or kind not in (2,4,5,6):raise ValueError('Unexpected warning relocation')
        at+=(0,s[0],s[0]+s[1])[section-1]
        words.append(0x40000000|kind<<24|at)
    if len({word&0xFFFFFF for word in words})!=len(words):raise ValueError('Duplicate warning relocation')
    size_word=struct.unpack_from('>I',original,len(original)-4)[0]
    if size_word!=len(original) or len(original)<24+len(words)*4:raise ValueError('Changed warning relocation size')
    return struct.pack('>5I',size,0,0,0,len(words))+struct.pack('>'+str(len(words))+'I',*words)+bytes(len(original)-24-len(words)*4)+struct.pack('>I',len(original))


def patch_owner(native,built,owner):
    old,reloc=source(native,owner);groups=line_groups(old,owner)
    widths=by_vrom(built)[CODE_VROM].extract(built)[WIDTH_TABLE:WIDTH_TABLE+256]
    if sha256(widths)!=WIDTH_SHA:raise ValueError('Changed installed warning font widths')
    info=command_info(by_vrom(native)[CODE_VROM].extract(native))
    texts=WARNING_TEXT if owner==WARNING else PAK_TEXT
    if len(texts)!=owner.windows:raise ValueError('Incomplete English warning inventory')
    data=bytearray(old+bytes(owner.sections[3]));pool={};records={};windows=[]
    allowed=set()
    for i,((sx,sy,rows),lines) in enumerate(zip(groups,texts)):
        if len(rows)!=len(lines):raise ValueError('English warning changes native line/choice count')
        encoded=[encode(t,info) for t in lines];spans=[sum(12-widths[c] for c in t) for t in encoded]
        choices=owner==PAK and i>=11
        half=120 if owner==WARNING else 112
        # Keep vertical geometry, line breaks, and all native selection behaviour.
        # Only body windows may widen; choice origins/cursors stay exactly native.
        new_sx=sx if choices else max(sx,math.ceil((max(spans)+32)/(half*2)*64)/64)
        if new_sx>1.5:raise ValueError('English warning exceeds the native screen width')
        if new_sx!=sx:
            struct.pack_into('>f',data,owner.table+i*16+8,new_sx)
            allowed.update(range(owner.table+i*16+8,owner.table+i*16+12))
        for n,((at,x,y,ptr,length),text,span) in enumerate(zip(rows,encoded,spans)):
            if text not in pool:
                pool[text]=len(data);data.extend(text+b'\0')
            new_x=x if choices or owner==WARNING and i==0 and n>=2 else half*new_sx-span/2
            if new_x<0 or new_x+span>half*2*new_sx:raise ValueError('English warning escapes its frame')
            replacement=struct.pack('>ffII',new_x,y,owner.ram+pool[text],len(text))
            record={'offset':at,'source_address':ptr,'source_length':length,
                    'text':text.decode(),'english_offset':pool[text],'width':span,'x':new_x,'y':y}
            if at in records and records[at]!=record:raise ValueError('Shared warning lines have conflicting translations')
            records[at]=record;data[at:at+16]=replacement;allowed.update(range(at,at+4));allowed.update(range(at+8,at+16))
        windows.append({'window':i,'lines':len(lines),'scale_x':new_sx,'scale_y':sy})
    data.extend(bytes(-len(data)%16));data=bytes(data)
    new_reloc=flattened_relocations(reloc,owner,len(data))
    original_spec=Image(owner.ram,len(old)+owner.sections[3],owner.sections)
    spec=Image(owner.ram,len(data),struct.unpack_from('>5I',new_reloc))
    for base in (0x801A0010,0x802F8010,0x803F0010):
        before=relocate_verified_data(original_spec,old,reloc,base)
        after=relocate_verified_data(spec,data,new_reloc,base)
        if any(a!=b and at not in allowed for at,(a,b) in enumerate(zip(before,after))):
            raise ValueError('Warning translation changes unrelated native code or relocation')
        for row in records.values():
            if struct.unpack_from('>I',after,row['offset']+8)[0]!=base+row['english_offset']:
                raise ValueError('English warning pointer relocates outside its complete text')
    if data[:owner.sections[0]]!=old[:owner.sections[0]] or any(data[len(old):len(old)+owner.sections[3]]):
        raise ValueError('Warning translation changes code or original BSS initialization')
    return data,new_reloc,{'version':1,'name':owner.name,'native_sha256':owner.source_sha,
        'native_relocation_sha256':owner.relocation_sha,'owner_sha256':sha256(data),
        'relocation_sha256':sha256(new_reloc),'bytes':len(data),'native_resident_bytes':len(old)+owner.sections[3],
        'code_unchanged':True,'bss_relative_address_unchanged':True,'font_widths_sha256':WIDTH_SHA,
        'source_rel_sha256':REL_SHA256,'rows':list(records.values()),'windows':windows}


def metadata(owner,size):
    value=bytearray.fromhex(owner.parent_hex)
    struct.pack_into('>4I',value,0,owner.new_vrom,owner.new_vrom+size,owner.ram,owner.ram+size)
    return bytes(value)
