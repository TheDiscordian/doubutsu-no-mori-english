"""Complete GameCube wording in the native editor confirmation's existing slots."""
import struct

from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from font import WIDTH_TABLE
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256
from textcodec import ENCODE
from catalogue_names import Image
from npc_mail_show import relocate_verified_data

VROM,RELOC,RAM=0x799580,0x79A1E0,0x80895E00
OWNER_SHA='075807e24ac1374be646561638d14c6d0d355e478b89efb232f7b6347f20504b'
RELOC_SHA='29d17144eaf385a563aff0838a39caff74c04bbc0baca13ec5ea57446ca5249e'
SECTIONS=(2896,256,16,16,37)
ROWS=((0xBF4,9,12,0x7F46C,b'Is this OK?'),(0xC00,2,4,0x7F478,b'Yes'),
      (0xC04,5,8,0x7F47C,b'Rewrite'),(0xC0C,9,12,0x7F484,b'Throw it out'))


def source(native):
    files=by_vrom(verified_rom(native));data=files[VROM].extract(native);reloc=files[RELOC].extract(native)
    if sha256(data)!=OWNER_SHA or sha256(reloc)!=RELOC_SHA or struct.unpack_from('>5I',reloc)!=SECTIONS:
        raise ValueError('Changed editor confirmation source')
    return data,reloc


def patch_owner(native,built,rel,symbols):
    old,reloc=source(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied editor confirmation reference')
    data=bytearray(old);widths=by_vrom(built)[CODE_VROM].extract(built)[WIDTH_TABLE:WIDTH_TABLE+256]
    prompt=ROWS[0][-1];width=sum(12-widths[c] for c in prompt)
    if width!=62:raise ValueError('Confirmation prompt font metrics changed')
    x=96+(108-width)/2
    position=struct.unpack('>I',struct.pack('>f',x))[0]
    if position&65535:raise ValueError('Confirmation position needs a wider native constant')
    for offset,length,capacity,donor,text in ROWS:
        if rel[DATA_BASE+donor:DATA_BASE+donor+len(text)]!=text or len(text)>capacity:
            raise ValueError('Confirmation wording does not match its complete supplied reference')
        data[offset:offset+capacity]=text+bytes(capacity-len(text))
    for at,before,after in ((0x808964B0-RAM,0x3C0142C0,0x3C010000|(position>>16)),
                            (0x80896500-RAM,0x24060009,0x2406000B)):
        if struct.unpack_from('>I',old,at)[0]!=before:raise ValueError('Changed native confirmation prompt reader')
        struct.pack_into('>I',data,at,after)
    for i,(offset,length,_,_,text) in enumerate(ROWS[1:]):
        at=0xC18+i*8
        if struct.unpack_from('>2I',old,at)!=(RAM+offset,length):raise ValueError('Changed native answer reader')
        struct.pack_into('>I',data,at+4,len(text))
    image=Image(RAM,len(old)+16,SECTIONS)
    allowed=set(range(0xBF4,0xC18))|set(range(0xC18,0xC30))|set(range(0x6B0,0x6B4))|set(range(0x700,0x704))
    for address in (0x801A0010,0x802F8010,0x803F0010):
        before=relocate_verified_data(image,old,reloc,address)
        after=relocate_verified_data(image,bytes(data),reloc,address)
        if any(a!=b and at not in allowed for at,(a,b) in enumerate(zip(before,after))):
            raise ValueError('Confirmation change affects an unrelated native relocation')
    return bytes(data),{'version':1,'owner_sha256':sha256(data),'native_sha256':OWNER_SHA,
        'relocation_sha256':RELOC_SHA,'reference_rel_sha256':REL_SHA256,
        'prompt_width':width,'prompt_x':x,'answer_positions_changed':False,
        'allocation_changed':False,'saved_format_changed':False,
        'strings':[{'offset':at,'source_length':n,'length':len(text),'text':text.decode()}
                   for at,n,_,_,text in ROWS]}


def measure_text(ledger,native,built,report,rel,symbols):
    old,reloc=source(native);installed=report.get('editor_confirmation')
    if installed:
        expected,profile=patch_owner(native,built,rel,symbols);files=by_vrom(built)
        if installed!=profile or files[VROM].extract(built)!=expected or files[RELOC].extract(built)!=reloc:
            raise ValueError('Changed installed editor confirmation')
    for i,(at,length,_,_,text) in enumerate(ROWS):
        identity=f'ui_editor_confirmation:{i:04X}'
        ledger.add(identity,old[at:at+length])
        if installed:ledger.credit(identity,text,'editor_confirmation')
