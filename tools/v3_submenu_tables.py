"""Append shared native menu tables while preserving original overlay contents."""
import struct

from aflib import CODE_RAM,sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_player_actions import native_references


class Owner:
    def __init__(self,data,relocation,ram,*,address_constants=()):
        self.original=bytes(data);self.data=bytearray(data);self.relocation=relocation;self.ram=ram
        self.address_constants=tuple(address_constants)
        self.groups,self.absolute,rows,self.locations,_=native_references(
            data,relocation,expected_sections=(len(data),0,0,0))
        self.rows=list(rows);self.patches=[];self.tables=[]

    def append(self,data,*,pointers=()):
        self.data.extend(bytes(-len(self.data)%4));at=len(self.data);self.data.extend(data)
        for relative in pointers:
            if relative%4 or not 0<=relative<=len(data)-4:
                raise ValueError('Unbounded appended native pointer')
            self.rows.append(0x42000000|(at+relative))
        return self.ram+at

    def patch(self,address,before,after,*,remove_relocation=False):
        at=address-self.ram
        if u32(self.data,at)!=before:raise ValueError(f'Changed submenu instruction {address:08X}')
        struct.pack_into('>I',self.data,at,after)
        self.patches.append(dict(address=address,before=before,after=after))
        if remove_relocation:
            if self.locations.get(at)!=0x44000000|at:
                raise ValueError('Changed native call relocation')
            self.rows.remove(self.locations[at])

    def table(self,address,count,stride,extra,*,pointer_offsets=(0,),expected_references):
        at=address-self.ram;size=count*stride
        if len(extra)%stride or not 0<=at<=len(self.original)-size:
            raise ValueError('Invalid native table extension')
        old=self.original[at:at+size]
        pointers=[]
        for offset in range(0,len(old),stride):
            for field in pointer_offsets:
                if u32(old,offset+field):
                    if self.locations.get(at+offset+field)!=0x42000000|(at+offset+field):
                        raise ValueError('Original table has an unrelocated pointer')
                    pointers.append(offset+field)
        for offset in range(0,len(extra),stride):
            pointers.extend(size+offset+field for field in pointer_offsets if u32(extra,offset+field))
        target=self.append(old+extra,pointers=pointers);delta=target-address;refs=[]
        for hi,lows in self.groups.items():
            matched=[(lo,value) for lo,value in lows if address<=value<address+size]
            if not matched:continue
            if len(matched)!=len(lows):raise ValueError('Shared high half also references unrelated data')
            halves={(value+delta+0x8000)>>16&65535 for _,value in lows}
            if len(halves)!=1:raise ValueError('Extended table requires split high halves')
            before=u32(self.data,hi)
            self.patch(self.ram+hi,before,before&0xFFFF0000|next(iter(halves)))
            for lo,value in lows:
                before=u32(self.data,lo)
                self.patch(self.ram+lo,before,before&0xFFFF0000|(value+delta)&65535)
                refs.append((self.ram+hi,self.ram+lo,value))
        if len(refs)!=expected_references or any(address<=v<address+size for v in self.absolute.values()):
            raise ValueError('Changed complete native table-reference inventory')
        self.tables.append(dict(original=address,address=target,count=count+len(extra)//stride,
            original_count=count,stride=stride,references=refs))
        return target

    def finish(self):
        self.data.extend(bytes(-len(self.data)%16))
        if len({w&0xFFFFFF for w in self.rows})!=len(self.rows):raise ValueError('Duplicate native relocation')
        n=(24+4*len(self.rows)+15)&~15
        relocation=(struct.pack('>5I',len(self.data),0,0,0,len(self.rows))+
            struct.pack('>'+str(len(self.rows))+'I',*self.rows)+bytes(n-24-4*len(self.rows))+struct.pack('>I',n))
        allowed={p['address']-self.ram+i for p in self.patches for i in range(4)}
        for base in (0x80200010,0x80348010):
            before=relocate_verified_data(Image(self.ram,len(self.original),struct.unpack_from('>5I',self.relocation)),
                self.original,self.relocation,base,address_constants=self.address_constants)
            after=relocate_verified_data(Image(self.ram,len(self.data),struct.unpack_from('>5I',relocation)),
                self.data,relocation,base,address_constants=self.address_constants)
            if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))):
                raise ValueError('Submenu extension changes an unrelated native byte')
            for table in self.tables:
                old=table['original']-self.ram;new=table['address']-self.ram
                size=table['original_count']*table['stride']
                if after[new:new+size]!=before[old:old+size]:
                    raise ValueError('Appended table loses original relocated records')
        return bytes(self.data),relocation,dict(original_sha256=sha256(self.original),
            owner_sha256=sha256(self.data),relocation_sha256=sha256(relocation),
            bytes=len(self.data),tables=self.tables,patches=self.patches)


def resize(parent,core,*,vrom,ram,offset,before,after):
    previous=bytes(parent[offset:offset+32])
    if struct.unpack_from('>4I',previous)!=(vrom,vrom+before,ram,ram+before):
        raise ValueError('Changed submenu allocation owner')
    struct.pack_into('>4I',parent,offset,vrom,vrom+after,ram,ram+after)
    extra=((after+63)&~63)-((before+63)&~63)
    at=0x800C4B10-CODE_RAM;word=u32(core,at);updated=word+extra
    if word>>16!=0x25CE or extra<0 or (word^updated)&0xFFFF8000:
        raise ValueError('Native submenu arena growth exceeds its checked instruction')
    struct.pack_into('>I',core,at,updated)
    return dict(offset=offset,before=previous.hex(),after=parent[offset:offset+32].hex(),
        additional_pool_bytes=extra,pool_patch=dict(address=at+CODE_RAM,before=word,after=updated))
