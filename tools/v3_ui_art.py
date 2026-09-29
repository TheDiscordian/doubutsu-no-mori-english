"""Shared, strict Dolphin submenu conversion using the ordinary native emitter.

UI lists may inherit caller textures/colour state, or contain state only. Those
contracts are explicit, rather than relaxed furniture-model validation. Resource
families and model roots share one packet, preserving source vertices and UVs.
"""
import struct

from aflib import sha256
from title_assets import model_texture_shape, pack4, untile
from v3_furniture_art import packed, command_source
from v3_villager_art import native_palette, normalise_vertex_flags

# Actual F3DEX2 expressions; values are the number of texture tiles read.
# The two-texture button combines colour from tile zero and alpha from tile one.
COMBINERS = {
    (0xFCFFFFFF,0xFFFDF238):1, (0xFCFFFFFF,0xFFFDF638):0,
    (0xFCFFFFFF,0xFFFCF279):1, (0xFCFFFFFF,0xFFFDF2F9):1,
    (0xFCFFFFFF,0xFFFDF6FB):0, (0xFCFFFFFF,0xFFFCF438):2,
    (0xFC30FFFF,0x5FFEF238):1, (0xFC12FFFF,0x3FFDF238):1,
    (0xFCFFB3FF,0xFF65FEFF):1, (0xFC30FE61,0x55FEF379):1,
    # Letter-frame setup: texture times shade, texture alpha, one tile.
    (0xFC127E24,0xFFFFF3F9):1,
}
RENDER_MODES = {0x0C1841C8,0x0C184240,0x0C192048,0x00504240,0x00552048,
                0x0F0A4000}  # Letter background: G_RM_OPA_SURF / SURF2.
GEOMETRY = {(0xD9000000,0x00200404),(0xD9000000,0x00200004),
            (0xD9FFFFFF,0x00200004),(0xD9F0F9FE,0),(0xD9000000,0x00210405)}
OTHER_MODES = {(0xEF182C10,0x0C184241),(0xEF18AC10,0x0C184340),
    (0xEF08AC10,0x00504340),(0xEF082C10,0x00553048),(0xEF18ACF0,0x0C193048),
    (0xEF08AC10,0x00504240)}
FORMATS = {(2,0):'CI4',(4,0):'I4',(4,1):'I8',(0,2):'RGBA16',
           (3,1):'IA8',(3,2):'IA16'}


def validate_state(a,b):
    op=a>>24
    valid = ((op==0xFC and (a,b) in COMBINERS) or
        (op==0xE2 and a==0xE200001C and b in RENDER_MODES) or
        (op==0xEF and (a,b) in OTHER_MODES) or
        (op==0xE3 and (a,b)==(0xE3001001,0)) or  # G_TT_NONE for letter lines.
        (op==0xD9 and (a,b) in GEOMETRY) or
        (op==0xE7 and (a,b)==(0xE7000000,0)) or
        (op==0xFA and a&0xFFFFFF00==0xFA000000) or
        (op==0xFB and a==0xFB000000))
    if not valid:raise ValueError(f'Unsupported UI state {a:08X}:{b:08X}')


class Packet:
    def __init__(self,source):
        self.source=source
        self.body=bytearray();self.offsets={};self.resources=[];self.models={}

    def resource(self,target,kind,shape=None):
        from v3_furniture_pipeline import native_rgba16,native_ia8,native_ia16
        name,at,size=self.source.containing(target,exact=kind!='vertices')
        raw=self.source.data[at:at+size]
        if len(raw)!=size or self.source.pointers(at,size):
            raise ValueError('Incomplete or pointer-bearing UI resource')
        details={}
        if kind=='palette':
            if size!=32:raise ValueError('UI palette is not sixteen colours')
            data=native_palette(raw)
        elif kind=='vertices':
            if size%16:raise ValueError('Incomplete UI vertex array')
            data=normalise_vertex_flags(raw)[0]
        elif kind=='texture':
            if shape is None or len(shape)!=4:raise ValueError('Missing UI texture shape')
            w,h,fmt,bits=shape
            if (any(type(n) is not int or n<=0 for n in (w,h)) or
                    (fmt,bits) not in FORMATS or w*h*(4<<bits)//8!=size or
                    ((w*(4<<bits)+63)//64)*8*h>(2048 if fmt==2 else 4096)):
                raise ValueError('UI texture escapes TMEM or its complete source')
            data=(native_rgba16(raw,w,h) if fmt==0 else native_ia16(raw,w,h) if bits==2 else
                  native_ia8(raw,w,h) if fmt==3 else untile(raw,w,h,8) if bits==1 else
                  pack4(untile(raw,w,h,4)))
            details=dict(width=w,height=h,format=FORMATS[fmt,bits])
        else:raise ValueError('Unknown UI resource kind')
        if len(data)!=size:raise ValueError('UI resource conversion changes size')
        record=dict(symbol=name,donor_offset=at,bytes=size,source_sha256=sha256(raw),
                    output_sha256=sha256(data),kind=kind,**details)
        if at in self.offsets:
            old=next(r for r in self.resources if r['donor_offset']==at)
            if any(old[k]!=v for k,v in record.items()):
                raise ValueError('Conflicting UI resource formats')
        else:
            self.body.extend(bytes(-len(self.body)%32));self.offsets[at]=len(self.body)
            self.body.extend(data);record['native_offset']=self.offsets[at];self.resources.append(record)
        return at,size

    def model(self,label,parts,*,texture=None,combiner=None,state_only=False,palette=False):
        """Validate complete roots plus explicit caller state before emitting them.

        texture is (width,height,format,size-code), and combiner is a checked
        inherited expression. A caller-supplied CI texture also requires palette.
        Sequence roots retain every command except the intermediate returns.
        """
        if label in self.models or not parts:raise ValueError('Duplicate or empty UI model')
        roots=[(n,*self.source.symbol(n)) if isinstance(n,str) else tuple(n) for n in parts]
        raw,pointers,receipts=self.source.model_sequence(roots,expand_calls=True)
        rows=[];used=set();cache=[None]*32;current_vertex=None
        textures=[];tmem=0;have_palette=bool(palette)
        if texture is not None:
            if (len(texture)!=4 or tuple(texture[2:]) not in FORMATS or
                    any(type(n) is not int or n<=0 for n in texture[:2]) or
                    texture[0]*texture[1]*(4<<texture[3])//8>(2048 if texture[2]==2 else 4096) or
                    texture[2]==2 and not have_palette):
                raise ValueError('Invalid inherited UI texture')
            textures=[tuple(texture)]
        if combiner is not None and tuple(combiner) not in COMBINERS:
            raise ValueError('Invalid inherited UI combiner')
        active=tuple(combiner) if combiner is not None else None
        triangles=0;pos=0
        while pos<len(raw):
            a,b=struct.unpack_from('>II',raw,pos);op=a>>24
            row=dict(opcode=op,words=(a,b));size=8
            if op in (1,0xFD,0xF0):
                if b or pos+4 not in pointers:raise ValueError('Missing UI resource relocation')
                target=pointers[pos+4];used.add(pos+4);row['target']=target
                if op==1:
                    at,n=self.resource(target,'vertices');count=a>>12&255;end=a>>1&127;slot=end-count
                    if (not 1<=count<=32 or not 0<=slot<=32-count or
                            a!=0x01000000|count<<12|end<<1 or (target-at)%16 or target+16*count>at+n):
                        raise ValueError('UI vertices escape their source/cache')
                    # Each row carries its own complete resource base. No list
                    # assumes that all vertex loads refer to the same array.
                    first=(target-at)//16
                    row.update(count=count,first_vertex=first,vertex_slot=slot)
                    cache[slot:slot+count]=[(at,v) for v in range(first,first+count)]
                    current_vertex=at
                elif op==0xF0:
                    if a!=0xF08F4010:raise ValueError('Unsupported UI palette load')
                    self.resource(target,'palette');have_palette=True
                else:
                    shape=model_texture_shape(raw[pos:pos+8]);self.resource(target,'texture',shape)
                    if pos+16>len(raw):raise ValueError('Missing UI texture tile')
                    tile,zero=struct.unpack_from('>II',raw,pos+8)
                    index=tile>>16&7;pal=tile>>12&15;wraps=(tile>>10&3,tile>>8&3)
                    if (tile&0xFFF80000!=0xD2F00000 or zero or index not in (0,1) or 3 in wraps or
                            pal not in ((15,) if shape[2]==2 else (0,15)) or
                            shape[2]==2 and not have_palette):
                        raise ValueError('Unsupported UI texture tile/palette')
                    if index==0:textures=[];tmem=0
                    if index!=len(textures) or index and any(t[2]==2 for t in textures+[shape]):
                        raise ValueError('Incomplete or conflicting UI texture pair')
                    words=((shape[0]*(4<<shape[3])+63)//64)*shape[1]
                    if tmem+words>(256 if shape[2]==2 else 512):raise ValueError('UI layers exceed TMEM')
                    row.update(shape=shape[:2],wrap_modes=wraps,tile_shifts=(tile>>4&15,tile&15),
                               ui_tile=index,ui_tmem=tmem)
                    if shape[2]==4:row['intensity']=True
                    if shape[2:]==(4,1):row['i8']=True
                    if shape[2:]==(0,2):row['rgba16']=True
                    if shape[2:]==(3,1):row['ia8']=True
                    if shape[2:]==(3,2):row['ia16']=True
                    textures.append(shape);tmem+=words;size=16
            elif op in (0x0A,5,6):
                if state_only or active is None or len(textures)<COMBINERS[active]:
                    raise ValueError('UI geometry has missing material state')
                if op==0x0A:
                    count=(a>>17&127)+1;size=(1+(max(0,count-3)+3)//4)*8
                    if pos+size>len(raw):raise ValueError('Truncated UI packed triangles')
                    ts=packed(raw[pos:pos+size],32)
                else:
                    if op==5 and b or op==6 and b&0xFF000000:
                        raise ValueError('Invalid native UI triangle flags')
                    indices=[[(word>>shift)&255 for shift in (16,8,0)] for word in ((a,) if op==5 else (a,b))]
                    if any(i%2 or i>=64 for tri in indices for i in tri):
                        raise ValueError('Invalid native UI triangle indices')
                    ts=[tuple(i//2 for i in tri) for tri in indices]
                if any(cache[v] is None for t in ts for v in t):raise ValueError('UI triangle reads unloaded vertices')
                row.update(opcode=0x0A,triangles=ts);triangles+=len(ts)
            elif op==0xD7:
                if a not in (0xD7000002,0xD7000000) or a==0xD7000000 and b:
                    raise ValueError('Invalid UI texture enable')
                if a==0xD7000000:row['texture_disabled']=True
                elif b:
                    if not b>>16 or not b&65535:raise ValueError('Invalid UI texture scale')
                    row['texture_scale']=(b>>16,b&65535)
            elif op==0xDF:
                if (a,b)!=(0xDF000000,0) or pos+8!=len(raw):raise ValueError('Invalid UI terminator')
            else:
                validate_state(a,b)
                if op==0xFC:active=(a,b)
            rows.append(row);pos+=size
        if (used!=set(pointers) or not rows or rows[-1]['opcode']!=0xDF or
                bool(triangles)==bool(state_only) or state_only and current_vertex is not None):
            raise ValueError('Incomplete UI model or state-only contract')
        self.models[label]=dict(symbol='+'.join(n for n,_,_ in roots),donor_offset=0,source_sha256=sha256(raw),
            source_parts=receipts,native_ui=True,rows=rows,
            caller=dict(texture=texture,combiner=combiner,palette=palette,state_only=state_only))

    def material(self,label,name,shape=None):
        """A native loading list for one complete caller-selected source resource."""
        if label in self.models:raise ValueError('Duplicate UI material')
        at,n=self.source.symbol(name);self.resource(at,'palette' if shape is None else 'texture',shape)
        row=dict(opcode=0xF0 if shape is None else 0xFD,target=at)
        if shape is not None:
            fmt,bits=shape[2:]
            row.update(shape=shape[:2],wrap_modes=(2,2),tile_shifts=(0,0),ui_tile=0,ui_tmem=0)
            if fmt==4:row['intensity']=True
            for flag,kind in (('i8',(4,1)),('rgba16',(0,2)),('ia8',(3,1)),('ia16',(3,2))):
                if (fmt,bits)==kind:row[flag]=True
        self.models[label]=dict(symbol=name,donor_offset=at,source_sha256=sha256(self.source.raw(name)),
            native_ui=True,rows=[row,dict(opcode=0xDF,words=(0xDF000000,0))])

    def prepared(self):
        self.body.extend(bytes(-len(self.body)%8))
        commands,sections=command_source(self.models,self.offsets)
        return dict(kind='submenu-models'),bytes(self.body),self.resources,self.offsets,self.models,commands,sections
