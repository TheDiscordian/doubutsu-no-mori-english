"""Read-only checks of the retained RC4 loading, movement, and memory evidence."""
import json
import struct

from aflib import by_vrom, sha256
from font_expansion_memory import BASE, FONT, MODULE, expected_font
from rebuild_v1rc4 import FINAL_SHA

STATES = {
    'load': ('rc4-existing-save-diagnostic-01', 'ed153cdc2024db5c3f36f12e5879f2bd726de03dfa6db0685206990749417eff'),
    'movement': ('rc4-town-stick-01', '11edd72e6f3882926d30ace79a316de72567b4240fffd7575c222460db9b1f44'),
    'no_expansion': ('rc4-no-expansion-01', '12ec315b71ed6c39eb36905def04d43eeb13201586042c8c649b3b33fc6a73b1'),
}
SAVE_SHA = 'd489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60'


def verify(image, build):
    if sha256(image)!=FINAL_SHA:
        raise ValueError('RC4 native evidence belongs to another cartridge')
    files=by_vrom(image)
    font=bytearray(expected_font(files[FONT].extract(image),files[MODULE].extract(image)))
    # Checked mutable globals: glyph resource pointer and initial blank town name.
    struct.pack_into('>I',font,11316,BASE+8992)
    font[11324:11340]=b' '*16
    evidence={}
    for name,(directory,digest) in STATES.items():
        path=build/directory
        run=json.loads((path/'run.json').read_text())
        results_raw=(path/'results.json').read_bytes()
        results=json.loads(results_raw)
        raw=(path/'test.bs1').read_bytes()
        size=0x400000 if name=='no_expansion' else 0x800000
        if (sha256(raw)!=digest or raw[:4]!=b'BST1' or len(raw)!=size+157112
                or run['rom_sha256']!=FINAL_SHA or run['audio']!='disabled'
                or results[0]['rom_sha256']!=FINAL_SHA
                or results[-1].get('graceful_shutdown') is not True
                or any(r.get('assertion') not in (None,'passed','not_requested') for r in results)):
            raise ValueError('Changed or incomplete RC4 native evidence: '+name)
        source=raw[103508:103508+size]
        ram=b''.join(source[i:i+4][::-1] for i in range(0,len(source),4))
        def read(a,n):
            if not 0x80000000<=a<=0x80000000+size-n:
                raise ValueError('Native evidence address exceeds detected RAM')
            return ram[a-0x80000000:a-0x80000000+n]
        def word(a):return struct.unpack('>I',read(a,4))[0]
        if word(0x80000318)!=size or word(0x8003CE34):
            raise ValueError('Incorrect memory size or faulted native thread')
        if read(0x8019C8D0,16)!=struct.pack('>4I',*([0xAF32C0DE]*4)):
            raise ValueError('Resident boundary guard changed')
        result={'state_sha256':digest,'results_sha256':sha256(results_raw),'ram_bytes':size,
                'faulted_thread':False,'resident_guard_intact':True}
        if name=='no_expansion':
            if (word(0x80199F04) or word(0x80102200)
                    or read(0x80145640,8)!=bytes.fromhex('0001000000000004')):
                raise ValueError('Unsupported machine installed an upper-memory owner or did not stop')
            result['unsupported_machine_stopped']=True
        else:
            for a,value in ((BASE-16,0xAF46C0DE),(0x80457FF0,0xAF46C0DE),
                            (0x80400000,0xAF54C0DE),(0x804475F0,0xAF54C0DE)):
                if read(a,16)!=struct.pack('>4I',*([value]*4)):
                    raise ValueError('Font/title owner guard changed')
            if word(0x80199F04)!=BASE or read(BASE,len(font))!=font:
                raise ValueError('Complete relocated font differs from its checked state')
            game=word(0x8010EF90);player=word(game+0x1C90)
            if read(player+2,1)!=b'\2':raise ValueError('No loaded player')
            result.update(font_and_title_guards_intact=True,complete_loaded_font_verified=True,
                          position=list(struct.unpack('>3f',read(player+0x28,12))))
            node=word(0x80141FA0);seen=set();previous=0;free=[]
            while node:
                if node in seen or node&15:raise ValueError('Invalid gameplay heap link')
                seen.add(node)
                magic,isfree,length,following,prev=struct.unpack('>2H3I',read(node,16))
                if magic!=0x7373 or prev!=previous or node+16+length>0x80400000:
                    raise ValueError('Gameplay heap metadata is corrupt')
                if isfree:free.append(length)
                previous,node=node,following
            result.update(scene_free_bytes=sum(free),scene_largest_free_bytes=max(free,default=0))
            if result['scene_largest_free_bytes']<528:
                raise ValueError('Gameplay has insufficient memory for the failed allocation')
        if name=='load' and run['seed_files']!=[{'file':'test.flash','sha256':SAVE_SHA,'bytes':131072}]:
            raise ValueError('Loading check did not use the supplied original RC2 save')
        evidence[name]=result
    if evidence['load']['position']==evidence['movement']['position']:
        raise ValueError('Loaded player did not respond to controller movement')
    return evidence
