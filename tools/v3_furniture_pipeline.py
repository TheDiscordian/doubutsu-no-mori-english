"""Discover and convert furniture by format and behaviour, not by item name.

All generated donor data stays under build/. Unsupported cases get explicit
per-item reasons; no callbacks or resource dependencies are silently dropped.
"""
import argparse
from bisect import bisect_right
from collections import Counter
import json
import math
from pathlib import Path
import re
import struct

from aflib import sha256, u32
from apply_translation import write_new
from gc_names import rel_sections
from item_identity_sheet import SHEET_SHA, sheet_rows
from map_artwork import compile_commands, compile_commands_batch
from title_assets import model_texture_shape, pack4, rgb5a3, untile
from v3_asset_loader import ROOT
from v3_furniture_art import SEGMENT, command_source, parse_model, verify_sources
from v3_registry import FURNITURE, LEGACY_FURNITURE, furniture_identity, furniture_source_index
from v3_room_aliases import discover as room_aliases, pending_reason as room_alias_reason
from v3_villager_art import native_palette, normalise_vertex_flags

VERSION = 17
PENDING_MOVE_CATEGORY = 'static-models-pending-move'
LAYERS = ('opaque', 'opaque1', 'translucent', 'translucent1')
BEHAVIOURS = {0: 'static', 1: 'front-seat', 2: 'any-direction-seat', 4: 'front-sofa',
              8: 'single-bed', 16: 'double-bed'}
STOCK = {'ftr_listA': 0, 'ftr_listB': 1, 'ftr_listC': 2,
         'ftr_listEvent': 3, 'ftr_listTrain': 4, 'ftr_listLottery': 5}
# Source list types for shared optional NPC reward selection, not shop stock.
REWARDS = {'ftr_listJonason': 12, 'ftr_listKamakura': 19, 'ftr_listTent': 23}
# Reviewed complete GAFE01-r0 draw implementation, not an item allowlist.
# It selects two opaque models and a palette using (actor index - base) * 12.
INDEXED_STATIC_DRAW_SHA = '612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917'
# Complete callback implementations with only verified address fields removed.
# These identify behaviour, not a list of item names or IDs.
PALETTE_FADE_CODE = {
    'create': (84, '9b0ac9f43f6ff69e3b4a75e7ae02cff615c9fd2050a9d8a940c224a5990c9879',
               {0x1C: (311912, 'zelda_malloc_align'), 0x3C: (2877692, 'fFTR_MorphHousepaletteCt')}),
    'move': (56, '74cb4ff1e7fcd0df934156e4ef7f85e9d14fd7182b96e31d2a3fc0eecdac080d',
             {0x24: (2877124, 'fFTR_MorphHousePalette')}),
    'draw': (204, 'cd20a081d7b57fb39579fb0092c5c9da35956c712ccc057f2c1a66b7c8b5b01f',
             {0x38: (643604, '_Matrix_to_Mtx_new')}),
    'destroy': (44, '93027b93411e9383050c763e5b19a0123d44f51d044e0bab85623c4022c9cce7',
                {0x18: (312052, 'zelda_free')}),
}
# Reviewed pure opaque draw sequences: model addresses are data, never item IDs.
STATIC_SEQUENCE_CODE = {
    116: ('76825aad3256c4118369c78a4240d0264e2e3dc18516ad1d386edf10dfaad8d1', ((0x3E,0x4A),)),
    172: ('d6dde5a8fad4d727364de9b717ef27562e128d4149e3e6da49846727ac9e7d2d',
          ((0x3E,0x52),(0x42,0x56),(0x46,0x5E))),
    180: ('56b8b2fc6b1cd975dc5b119c9d16350198a7c758ebcfef304d8bbed74bf5903e',
          ((0x46,0x66),(0x4E,0x6A))),
}
# Complete indexed draw shapes. Checked table bases/conditional selectors are
# parameters; no item names or per-item model descriptions select this category.
INDEXED_SEQUENCE_CODE = {
    136: ('b472481116e0056e1a592d37240c1c2394c07cdbdbaaed42354a180696c30288', ((0x4A,0x5A),)),
    168: ('6ed186883c4fd49a47d3e9a7077c111a37ac685cb7462e0167cfd475e4cebb33',
          ((0x4A,0x5E),(0x4E,0x62))),
    284: ('288e2fc954229a6c8ac6dc48702c5dcedabc03857f352c02508926d0e02e7459',
          ((0x52,0x66),(0x56,0x6A))),
}
SWITCH_SOUND_CODE = {
    88: ('678f62c4248166f0aae5393058ac1032e32e9967ae77b8674d6852c33a292215', (0x42,), 0x44),
    92: ('c40056198201de07a4cdf163f0dba3260d31c009fb8aaab7464e849350030256', (0x3E,0x46), 0x48),
}


class ReviewRequired(ValueError):
    """A valid donor feature lacks a supported conversion/runtime category."""


def native_rgba16(data, width, height):
    """Convert complete GX RGB5A3 blocks to native RGBA5551 without alpha loss.

    The donor's emu64 format table maps RGBA/16 to GX_RGB5A3, not RGB565.
    Partial alpha needs a wider renderer and is rejected, never thresholded.
    """
    if (type(width) is not int or type(height) is not int or width<=0 or height<=0
            or width%4 or height%4 or len(data)!=width*height*2):
        raise ReviewRequired('RGBA16 texture needs complete four-by-four GX blocks')
    result=bytearray(len(data))
    for y in range(height):
        for x in range(width):
            index=((y//4)*(width//4)+x//4)*16+(y%4)*4+x%4
            value=struct.unpack_from('>H',data,index*2)[0]
            r,g,b,a=rgb5a3(value)
            if a not in (0,255):
                raise ReviewRequired('Partial-alpha RGB5A3 texture needs a wider native renderer')
            struct.pack_into('>H',result,(y*width+x)*2,(r>>3)<<11|(g>>3)<<6|(b>>3)<<1|(a==255))
    return bytes(result)


def native_ia8(data, width, height):
    """GX IA4 stores alpha first; N64 IA8 stores intensity first, losslessly."""
    return bytes((v & 15) << 4 | v >> 4 for v in untile(data,width,height,8))


def native_ia16(data, width, height):
    """GX IA8 has four-by-four blocks and alpha before intensity per pixel."""
    if (type(width) is not int or type(height) is not int or width<=0 or height<=0
            or width%4 or height%4 or len(data)!=width*height*2):
        raise ReviewRequired('IA16 texture needs complete four-by-four GX blocks')
    result=bytearray(len(data))
    for y in range(height):
        for x in range(width):
            source=(((y//4)*(width//4)+x//4)*16+(y%4)*4+x%4)*2
            target=(y*width+x)*2
            result[target:target+2]=data[source:source+2][::-1]
    return bytes(result)


class Source:
    """Index the checked donor once; resolve thousands of dependencies cheaply."""
    def __init__(self, rel, symbols):
        verify_sources(rel, symbols)
        self.rel, self.symbols = rel, symbols.decode()
        self.sections = rel_sections(rel)
        self.base, self.size = self.sections[5]
        self.data = rel[self.base:self.base+self.size]
        self.names, self.spans = {}, {}
        for name, address, size in re.findall(
                r'^(\S+) = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', self.symbols, re.M):
            at, n = int(address, 16), int(size, 16)
            if at+n > self.size or not n: raise ValueError('Invalid donor symbol span')
            self.names.setdefault(name, []).append((at, n))
            self.spans.setdefault((at, n), []).append(name)
        self.starts = sorted({at for at, _ in self.spans})
        self.by_start = {}
        for (at, n), names in self.spans.items():
            self.by_start.setdefault(at, []).append((n, sorted(names)[0]))
        self.functions = {}
        for name, address, size in re.findall(
                r'^(\S+) = \.text:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', self.symbols, re.M):
            at, n = int(address, 16), int(size, 16)
            if not n or at+n > self.sections[1][1]: raise ValueError('Invalid donor function span')
            self.functions.setdefault(at, []).append((name, n))
        self.relocations = self.index_relocations()
        self.relocation_addresses = sorted(self.relocations)
        if sorted(self.names['furniture_quality']) != [(0x39FB4, 5064), (0x7B5B0, 5064)]:
            raise ValueError('Changed complete donor profile tables')
        self.quality = [self.pointers(at, n) for at, n in self.names['furniture_quality']]

    def index_relocations(self):
        rel = self.rel
        module, table, n = u32(rel, 0), u32(rel, 0x28), u32(rel, 0x2C)
        if not n or n%8 or table+n > len(rel): raise ValueError('Invalid import table')
        imports = list(struct.iter_unpack('>II', rel[table:table+n]))
        starts = {row[1] for row in imports}
        if len(starts) != len(imports): raise ValueError('Duplicate relocation streams')
        result, self.code_relocations, self.section_relocations = {}, {}, {}
        for imported, first in imports:
            if first%4 or not 0 <= first < len(rel): raise ValueError('Invalid relocation stream')
            end = min((s for s in starts if s > first), default=len(rel))
            section, address, ended = None, 0, False
            for at in range(first, end-7, 8):
                delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
                if kind == 203: ended = True; break
                if kind == 202:
                    if target_section >= len(self.sections): raise ValueError('Bad source section')
                    section, address = target_section, 0
                    continue
                if section is None: raise ValueError('Missing source section')
                address += delta
                if address > self.sections[section][1]: raise ValueError('Relocation exceeds section')
                if kind in (0, 201, 204): continue
                key = (section, address)
                if key in self.section_relocations: raise ValueError('Duplicate section relocation')
                self.section_relocations[key] = (kind, imported, target_section, target)
                if section == 1:
                    if address in self.code_relocations: raise ValueError('Duplicate code relocation')
                    self.code_relocations[address] = (kind, imported, target_section, target)
                if section != 5: continue
                if address in result: raise ValueError('Duplicate data relocation')
                result[address] = (kind, imported == module, target_section, target)
            if not ended: raise ValueError('Unterminated relocation stream')
        return result

    def function(self, target):
        rows = self.functions.get(target, [])
        if len(rows) != 1: raise ReviewRequired('callback has no unique complete function')
        name, n = rows[0]
        base = self.sections[1][0]
        raw = self.rel[base+target:base+target+n]
        relocations = {at-target: row for at,row in self.code_relocations.items() if target <= at < target+n}
        return raw, dict(symbol=name, offset=target, bytes=n, sha256=sha256(raw),
                        relocations=relocations)

    def checked_callback_code(self, receipt, size, digest, expected, calls, category, constants=None,
                              internal_branches=False):
        """Normalise checked addresses, helper calls, and bounded selector fields."""
        def reject(reason): raise ReviewRequired('custom callbacks: '+category+' '+reason)
        if receipt['bytes'] != size or receipt['relocations'] != expected:
            reject('changed dependencies')
        raw, _ = self.function(receipt['offset']); normalized = bytearray(raw)
        constants = {} if constants is None else constants
        for loc, value in constants.items():
            if loc%4 != 2 or not 0 <= loc < size-1 or loc in expected or struct.unpack_from('>H',raw,loc)[0] != value:
                reject('changed selector constant')
            normalized[loc:loc+2] = bytes(2)
        for loc, (kind, _, _, _) in expected.items():
            if kind in (4,6): normalized[loc:loc+2] = bytes(2)
            elif kind == 10: struct.pack_into('>I',normalized,loc,u32(raw,loc)&0xFC000003)
            else: reject('unsupported code relocation')
        found, helpers, branches = {}, {}, {}
        for loc in range(0, size, 4):
            word = u32(raw,loc)
            if word>>26 != 18 or loc in expected: continue
            if internal_branches and word&3==0:
                displacement=word&0x3FFFFFC
                if displacement&0x2000000:displacement-=0x4000000
                if not 0<=loc+displacement<size:reject('branch escapes complete function')
                branches[loc]=loc+displacement
                # The whole instruction, including its local displacement,
                # stays in the checked digest. Only actual calls normalize.
                continue
            if word & 0xFC000003 != 0x48000001 or loc not in calls:
                reject('unexpected local branch')
            displacement = word & 0x3FFFFFC
            if displacement & 0x2000000: displacement -= 0x4000000
            target = receipt['offset'] + loc + displacement
            if target != calls[loc][0]: reject('changed shared helper target')
            _, helper = self.function(target)
            if helper['symbol'] != calls[loc][1]: reject('changed shared helper identity')
            found[loc] = target; helpers[helper['symbol']] = helper
            struct.pack_into('>I',normalized,loc,word&0xFC000003)
        if set(found) != set(calls) or sha256(normalized) != digest:
            reject('unrecognised complete implementation')
        receipt.update(normalized_sha256=digest, local_calls=found)
        if branches:receipt['internal_branches']=branches
        if constants: receipt['selector_constants'] = constants
        return helpers

    def callback_models(self, profile_at, index):
        """Specialise a checked constant selector; unknown callback effects fail."""
        def reject(reason): raise ReviewRequired('custom callbacks: ' + reason)
        pointer = self.relocations.get(profile_at+48)
        if pointer is None or pointer[:3] != (1, True, 5): reject('invalid vtable pointer')
        name, at, n = self.containing(pointer[3], exact=True)
        if n != 20 or self.data[at:at+n] != bytes(n): reject('unsupported vtable')
        pointers = {p-at: r for p,r in self.relocations.items() if at <= p < at+n}
        if (8 not in pointers or set(pointers)-{0,4,8,12} or
                any(r[:3] != (1,True,1) for r in pointers.values())):
            reject('unsupported callback slots or DMA callback')
        functions = {}
        for slot, role in enumerate(('create','move','draw','destroy')):
            if slot*4 not in pointers: continue
            raw, receipt = self.function(pointers[slot*4][3]); functions[role] = receipt
        from v3_furniture_materials import discover as discover_materials
        materials=discover_materials(self,name,at,functions)
        if materials is not None:return materials
        from v3_furniture_scroll import discover as discover_scroll
        scrolling=discover_scroll(self,name,at,functions)
        if scrolling is not None:return scrolling
        from v3_furniture_rigs import (CODE as RIG_CODE, CLOCK_CODE, STORAGE_CODE,
            discover as discover_rig, discover_clock, discover_storage, discover_fixed)
        if functions.get('create',{}).get('bytes') == RIG_CODE['create'][0]:
            return discover_rig(self,name,at,functions,index)
        if functions.get('create',{}).get('bytes') == CLOCK_CODE['create'][0]:
            return discover_clock(self,name,at,functions,index)
        if functions.get('create',{}).get('bytes') == STORAGE_CODE['create'][0]:
            # Same-sized constructors do not imply the same behaviour. Fixed
            # rigs can be prepared independently of their pending move code.
            if functions.get('move',{}).get('bytes')!=STORAGE_CODE['move'][0]:
                return discover_fixed(self,name,at,functions)
            return discover_storage(self,name,at,functions)
        if functions.get('create',{}).get('bytes') == PALETTE_FADE_CODE['create'][0]:
            if set(pointers) != {0,4,8,12}: reject('unsupported palette-fade callback slots')
            return self.palette_fade_models(name, at, functions)
        for role, receipt in functions.items():
            raw, _ = self.function(receipt['offset'])
            if role != 'draw' and (raw != bytes.fromhex('4e800020') or receipt['relocations']):
                reject('lifecycle effects need an adapter')
        draw = functions['draw']
        if draw['bytes'] in STATIC_SEQUENCE_CODE:
            return self.static_sequence_models(name,at,functions)
        if draw['bytes'] in INDEXED_SEQUENCE_CODE:
            return self.indexed_sequence_models(name,at,functions,index)
        if draw['sha256'] != INDEXED_STATIC_DRAW_SHA: reject('unrecognised draw implementation')
        raw, _ = self.function(draw['offset'])
        table_pointer = draw['relocations'].get(0x1A)
        if table_pointer is None: reject('missing selector table')
        table = table_pointer[3]
        expected = {0x10:(10,0,4,0x8009AECC), 0xAC:(10,0,4,0x8009AF18),
                    0x1A:(6,u32(self.rel,0),5,table), 0x2A:(4,u32(self.rel,0),5,table)}
        if draw['relocations'] != expected: reject('changed draw dependencies')
        table_name, table, size = self.containing(table, exact=True)
        # addi r0,r6,-base; mulli r7,r0,12. These instructions and every
        # other effect are covered by the complete implementation hash above.
        first = -struct.unpack_from('>h',raw,0x26)[0]
        stride = struct.unpack_from('>H',raw,0x2E)[0]
        selected = index-first
        if stride != 12 or size%stride or not 0 <= selected < size//stride:
            reject('selector index escapes the complete table')
        table_raw = self.data[table:table+size]
        dependencies = self.pointers(table,size)
        if table_raw != bytes(size) or set(dependencies) != set(range(table,table+size,4)):
            reject('incomplete selector table')
        models = {layer:self.containing(dependencies[table+selected*stride+i*4],exact=True)
                  for i,layer in enumerate(LAYERS[:2])}
        palette = self.containing(dependencies[table+selected*stride+8],exact=True)
        if palette[2] != 32: reject('selector palette is not sixteen colours')
        return models, {0x08000000:palette[1]}, dict(
            category='indexed-static-model-palette', vtable_symbol=name, vtable_offset=at,
            functions=functions, table_symbol=table_name, table_offset=table, table_bytes=size,
            table_sha256=sha256(table_raw), table_pointers=dependencies,
            first_runtime_index=first, selected_index=selected, entries=size//stride,
            palette_symbol=palette[0], palette_offset=palette[1])

    def static_sequence_models(self, name, at, functions):
        draw=functions['draw'];digest,pairs=STATIC_SEQUENCE_CODE[draw['bytes']]
        module=u32(self.rel,0);expected={};models={};bindings={};palette_record={}
        for i,(hi,lo) in enumerate(pairs):
            pointer=draw['relocations'].get(hi)
            if pointer is None or pointer[:3]!=(6,module,5):
                raise ReviewRequired('custom callbacks: fixed draw missing model dependency')
            target=pointer[3];models[f'part{i}']=self.containing(target,exact=True)
            expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
        if draw['bytes']==180:
            pointer=draw['relocations'].get(0x42)
            if pointer is None or pointer[:3]!=(6,module,5):
                raise ReviewRequired('custom callbacks: fixed draw missing constant palette')
            target=pointer[3];symbol,base,size=self.containing(target,exact=True)
            if size!=32 or self.pointers(base,size):
                raise ReviewRequired('custom callbacks: fixed draw needs a complete constant palette')
            expected.update({0x42:(6,module,5,target),0x56:(4,module,5,target)})
            bindings[0x08000000]=target
            palette_record=dict(constant_palette=dict(symbol=symbol,donor_offset=base,bytes=size,
                source_sha256=sha256(self.data[base:base+size]),segment_address=0x08000000))
        helpers=self.checked_callback_code(draw,draw['bytes'],digest,expected,
            {0x34:(643604,'_Matrix_to_Mtx_new')},'fixed draw')
        return models,bindings,dict(category='constant-model-sequence',vtable_symbol=name,vtable_offset=at,
            functions=functions,helpers=helpers,model_order=list(models),draw_arena='opaque',
            **palette_record,
            null_callbacks=[r for r in ('create','move','destroy') if r not in functions])

    def direct_callback_models(self, profile_at):
        """Keep direct model slots with implemented sound or pending move code."""
        def reject(reason):raise ReviewRequired('custom callbacks: switch sound '+reason)
        pointer=self.relocations.get(profile_at+48)
        if pointer is None or pointer[:3]!=(1,True,5):reject('invalid vtable pointer')
        name,at,n=self.containing(pointer[3],exact=True)
        if n!=20 or any(self.data[at:at+n]):reject('unsupported vtable')
        pointers={p-at:r for p,r in self.relocations.items() if at<=p<at+n}
        if set(pointers)!={4} or pointers[4][:3]!=(1,True,1):
            reject('additional lifecycle, drawing, or DMA effects')
        raw,receipt=self.function(pointers[4][3]);size=len(raw)
        pointers=self.pointers(profile_at,52)
        models={LAYERS[(p-profile_at)//4]:self.containing(target,exact=True)
                for p,target in pointers.items() if p-profile_at in (0,4,8,12)}
        if not models or set(pointers)-{profile_at+i for i in (0,4,8,12,48)}:
            reject('changed profile model dependencies')
        if size not in SWITCH_SOUND_CODE:
            # Direct profile drawing is independent of this move callback.
            # Preserve its source record and refuse gameplay installation,
            # while allowing complete ordinary model preparation in bulk.
            return models,{},dict(category=PENDING_MOVE_CATEGORY,vtable_symbol=name,vtable_offset=at,
                functions=dict(move=receipt),runtime_installed=False,pending_callbacks=['move'],
                null_callbacks=['create','draw','destroy','dma'],
                resource_scope='complete static profile models; move behaviour and spawned effects remain pending')
        sound=self.switch_sound_callback(receipt)
        return models,{},dict(category='switch-trigger-sound',vtable_symbol=name,vtable_offset=at,
            functions=dict(move=receipt),**sound,
            null_callbacks=['create','draw','destroy','dma'])

    def switch_sound_callback(self, receipt):
        """Verify the shared move behaviour independently of its draw category."""
        raw,actual=self.function(receipt['offset']);size=len(raw)
        if receipt!=actual or size not in SWITCH_SOUND_CODE:
            raise ReviewRequired('Unsupported complete switch-trigger move callback')
        digest,locations,call=SWITCH_SOUND_CODE[size]
        constants={loc:struct.unpack_from('>H',raw,loc)[0] for loc in locations}
        signed=struct.unpack_from('>h',raw,locations[-1])[0]
        sound=signed if len(locations)==1 else (constants[locations[0]]<<16)+signed
        if not 0<=sound<=65535:raise ReviewRequired('Switch sound word exceeds its source encoding')
        helpers=self.checked_callback_code(receipt,size,digest,{},
            {call:(0x2BDDE8,'sAdo_OngenTrgStart')},'switch sound',constants)
        return dict(helpers=helpers,sound_word=sound,
            excluded_states=[13,14,15,12],state_offset=0x3C,switch_offset=0x12D,
            switch_value=1,position_offset=8,runtime_installed=False)

    def indexed_sequence_models(self, name, at, functions, index):
        """Select complete ordered lists, retaining conditional translucent parts."""
        def reject(reason): raise ReviewRequired('custom callbacks: indexed sequence ' + reason)
        draw=functions['draw'];size=draw['bytes'];digest,pairs=INDEXED_SEQUENCE_CODE[size]
        raw,_=self.function(draw['offset']);module=u32(self.rel,0)
        special=size==284;constant=0x32 if special else 0x2A
        first=-struct.unpack_from('>h',raw,constant)[0]
        mask=u32(raw,0x3C if special else 0x34)
        leading=mask>>6&31
        if leading not in (29,30) or mask>>11&31 or mask>>1&31!=31:
            reject('unsupported index mask')
        count=1<<(32-leading);selected=index-first
        if not 0 <= selected < count: reject('selector escapes the complete table')
        constants={constant:(-first)&65535}
        expected={0x10:(10,0,4,0x8009AECC if special else 0x8009AED4),
                  size-20:(10,0,4,0x8009AF18 if special else 0x8009AF20)}
        parts=[];tables=[]
        for hi,lo in pairs:
            pointer=draw['relocations'].get(hi)
            if pointer is None or pointer[:3]!=(6,module,5):reject('missing selector table')
            target=pointer[3];symbol,base,n=self.containing(target,exact=True)
            if n!=count*4 or self.data[base:base+n]!=bytes(n):reject('changed complete selector table')
            pointers=self.pointers(base,n)
            if set(pointers)!=set(range(base,base+n,4)):reject('incomplete selector table')
            models=[self.containing(pointers[p],exact=True) for p in range(base,base+n,4)]
            expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
            tables.append(dict(symbol=symbol,offset=base,bytes=n,sha256=sha256(self.data[base:base+n]),
                               pointers=pointers))
            parts.append(models[selected])
        sequences={'opaque':parts};conditional=[]
        if special:
            selector=struct.unpack_from('>H',raw,0x9E)[0]
            if selector!=first+count-1:reject('changed conditional layer selector')
            constants[0x9E]=selector
            for hi,lo in ((0xCA,0xDA),(0xCE,0xDE)):
                pointer=draw['relocations'].get(hi)
                if pointer is None or pointer[:3]!=(6,module,5):reject('missing translucent dependency')
                target=pointer[3];conditional.append(self.containing(target,exact=True))
                expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
            if index==selector:sequences['translucent']=conditional
        calls={loc:(643604,'_Matrix_to_Mtx_new') for loc in ((0x48,0xC0) if special else (0x40,))}
        helpers=self.checked_callback_code(draw,size,digest,expected,calls,'indexed sequence',constants)
        return {label:parts[0] for label,parts in sequences.items()}, {}, dict(
            category='indexed-model-sequence',vtable_symbol=name,vtable_offset=at,
            functions=functions,helpers=helpers,tables=tables,first_runtime_index=first,
            selected_index=selected,entries=count,model_sequences=sequences,
            conditional_translucent=conditional)

    def model_sequence(self, parts):
        """Join ordered state/geometry lists, removing only intermediate returns."""
        joined=bytearray();pointers={};receipts=[]
        for i,(name,at,n) in enumerate(parts):
            if n<8 or n%8 or self.containing(at,exact=True)!=(name,at,n):
                raise ReviewRequired('invalid complete model sequence part')
            raw=self.data[at:at+n]
            if raw[-8:]!=struct.pack('>II',0xDF000000,0):
                raise ReviewRequired('model sequence part lacks a final return')
            fixes=self.pointers(at,n)
            if any(p>=at+n-8 for p in fixes):
                raise ReviewRequired('relocated model sequence return')
            receipts.append(dict(symbol=name,donor_offset=at,bytes=n,sha256=sha256(raw),
                                 joined_offset=len(joined)))
            pointers.update({len(joined)+p-at:target for p,target in fixes.items()})
            joined.extend(raw[:-8] if i<len(parts)-1 else raw)
        if not receipts:raise ReviewRequired('empty model sequence')
        return bytes(joined),pointers,receipts

    def palette_fade_models(self, name, at, functions):
        """Resolve the shared three-model, two-endpoint light-switch behaviour."""
        def reject(reason): raise ReviewRequired('custom callbacks: palette fade ' + reason)
        module = u32(self.rel, 0)
        def address(role, location):
            fix = functions[role]['relocations'].get(location)
            if fix is None or fix[:3] != (6, module, 5): reject('missing data dependency')
            return fix[3]
        off, on = address('create', 0x26), address('create', 0x2A)
        model_addresses = [address('draw', loc) for loc in (0x46, 0x4A, 0x52)]
        def pair(high, low, target): return {high: (6,module,5,target), low: (4,module,5,target)}
        expected = {
            'create': pair(0x26,0x32,off) | pair(0x2A,0x3A,on),
            'move': pair(0x0A,0x1A,off) | pair(0x0E,0x1E,on),
            'draw': {0x10:(10,0,4,0x8009AED4), 0xB8:(10,0,4,0x8009AF20)} |
                    pair(0x46,0x62,model_addresses[0]) | pair(0x4A,0x6A,model_addresses[1]) |
                    pair(0x52,0x6E,model_addresses[2]),
            'destroy': {},
        }
        helpers = {}
        for role, receipt in functions.items():
            size, digest, calls = PALETTE_FADE_CODE[role]
            helpers.update(self.checked_callback_code(receipt,size,digest,expected[role],calls,'palette fade '+role))
        endpoints = {}
        for role, target in (('off',off), ('on',on)):
            symbol, start, size = self.containing(target,exact=True)
            if size != 32 or self.pointers(start,size): reject('invalid endpoint palette')
            raw = self.data[start:start+size]
            native_palette(raw)  # Reject partial alpha, even in unchanged entries.
            endpoints[role] = dict(symbol=symbol, donor_offset=start, bytes=size, sha256=sha256(raw))
        off_words = struct.unpack_from('>16H', self.data, off)
        on_words = struct.unpack_from('>16H', self.data, on)
        if any(a != b and not (a & b & 0x8000) for a,b in zip(off_words,on_words)):
            reject('changing colours must both be opaque RGB5A3')
        models = {f'part{i}': self.containing(target,exact=True) for i,target in enumerate(model_addresses)}
        return models, {}, dict(category='switch-palette-fade', vtable_symbol=name, vtable_offset=at,
            functions=functions, helpers=helpers, endpoints=endpoints, dynamic_palette_segment=0x08000000,
            model_order=list(models), draw_arena='opaque', fade_step_hex='3dcccccd')

    def pointers(self, at, n):
        if at < 0 or n <= 0 or at+n > self.size: raise ValueError('Out-of-range dependency')
        start = bisect_right(self.relocation_addresses, at-1)
        end = bisect_right(self.relocation_addresses, at+n-1)
        result = {}
        for location in self.relocation_addresses[start:end]:
            kind, local, section, target = self.relocations[location]
            if (kind != 1 or not local or section != 5 or location%4 or location+4 > at+n
                    or target >= self.size or u32(self.data, location)):
                raise ReviewRequired('non-data or external dependency')
            result[location] = target
        return result

    def symbol(self, name):
        rows = self.names.get(name, [])
        if len(rows) != 1: raise ReviewRequired('missing or ambiguous symbol: ' + name)
        return rows[0]

    def raw(self, name):
        at, n = self.symbol(name)
        return self.data[at:at+n]

    def containing(self, target, *, exact=False):
        index = bisect_right(self.starts, target)-1
        if index < 0: raise ReviewRequired('dependency has no bounded symbol')
        start = self.starts[index]
        candidates = [(n, name) for n, name in self.by_start[start] if start <= target < start+n]
        if len(candidates) != 1 or exact and start != target:
            raise ReviewRequired('ambiguous or interior dependency')
        n, name = candidates[0]
        return name, start, n

    def profile(self, item):
        index = furniture_source_index(item)
        targets = [table.get(at+index*4) for (at, _), table in zip(self.names['furniture_quality'], self.quality)]
        if targets[0] is None or targets[0] != targets[1]:
            raise ReviewRequired('profile tables disagree or lack the item')
        if targets[0] == self.symbol('iam_dummy')[0]:
            raise ReviewRequired('shared dummy profile: actual artwork absent in this donor')
        name, at, n = self.containing(targets[0], exact=True)
        if n != 52: raise ReviewRequired('unsupported furniture profile format')
        raw = self.data[at:at+n]
        # Inspect all fields before asking for .data pointers: callback pointers
        # may target executable code, and must remain an explicit behaviour gap.
        locations = [p-at for p in self.relocations if at <= p < at+n]
        if any(p >= 16 and p != 48 for p in locations):
            features = {16:'dynamic texture', 20:'dynamic palette', 24:'animation rig',
                        28:'texture animation', 48:'custom callbacks'}
            raise ReviewRequired(', '.join(features.get(p, 'unknown profile dependency') for p in locations if p >= 16))
        if raw[:32] != bytes(32) or raw[48:] != bytes(4):
            raise ReviewRequired('unrelocated profile pointers')
        h, scale, shape, collision, rotation, lighting, contact, pad, interaction = struct.unpack_from('>ff6BH', raw, 32)
        if (not math.isfinite(h) or not 0 < h <= 200 or not math.isfinite(scale) or not 0 < scale <= 1
                or shape not in (3, 4, 5) or collision not in (0, 1, 2, 5)
                or rotation not in (0, 1) or lighting not in (0, 1, 2) or pad):
            raise ReviewRequired('unsupported scalar profile category')
        extra = {}
        if 48 in locations:
            if locations != [48]:models,bindings,adapter=self.direct_callback_models(at)
            else:models, bindings, adapter = self.callback_models(at,index)
            extra = dict(palette_bindings=bindings, callback_adapter=adapter)
        else:
            pointers = self.pointers(at, n)
            if not pointers or any(p-at not in (0, 4, 8, 12) for p in pointers):
                raise ReviewRequired('unsupported static model slots')
            models = {LAYERS[(p-at)//4]: self.containing(target, exact=True) for p, target in pointers.items()}
        adapter = extra.get('callback_adapter', {})
        from v3_furniture_materials import CATEGORY as MATERIAL_CATEGORY
        from v3_furniture_scroll import CATEGORY as SCROLL_CATEGORY
        pending_move=adapter.get('category') in (PENDING_MOVE_CATEGORY,MATERIAL_CATEGORY,SCROLL_CATEGORY)
        pending_fields=[]
        if raw[36:40]!=struct.pack('>f',.01):pending_fields.append('scale')
        if contact not in BEHAVIOURS:pending_fields.append('contact')
        if interaction not in (0,1,2,4,0x10,0x8000):pending_fields.append('interaction')
        if pending_fields and not pending_move:
            raise ReviewRequired('unsupported scalar/contact/interaction profile category')
        if pending_move:
            adapter['pending_profile_fields']=pending_fields
        fading = adapter.get('category') == 'switch-palette-fade'
        if not pending_move and (fading and (interaction != 0x8000 or contact) or interaction == 0x8000 and not fading):
            raise ReviewRequired('contact/interaction requires a checked palette-fade callback')
        from v3_furniture_rigs import RESOURCE_CATEGORIES, STORAGE_CATEGORY
        storage=adapter.get('category')==STORAGE_CATEGORY
        if not pending_move and (storage and (contact or interaction not in (1,2,4)) or interaction in (1,2,4) and not storage):
            raise ReviewRequired('storage interaction requires the complete open/close category')
        if adapter.get('category') in RESOURCE_CATEGORIES:
            if contact or interaction and not storage: raise ReviewRequired('unsupported rig contact/interaction flags')
            extra.update(kind='animated-room-model',skeleton=adapter['skeleton'],joint_models=adapter['joint_models'])
        return dict(profile_symbol=name, profile_offset=at, profile_sha256=sha256(raw),
            scalar_hex=raw[32:48].hex(), behaviour=adapter.get('category') if extra.get('kind') or
                adapter.get('category') in ('switch-trigger-sound',PENDING_MOVE_CATEGORY,MATERIAL_CATEGORY,SCROLL_CATEGORY) else BEHAVIOURS[contact], contact_action=contact,
            interaction_flags=interaction,
            size_code={3:1, 4:0, 5:2}[shape], shape=shape, models=models, **extra)


def prepare(source, item):
    """Discover every model, texture, palette, and vertex dependency from the ROM."""
    return prepare_models(source, source.profile(item))


def prepare_models(source, descriptor):
    """Convert checked model roots independently of furniture/item identity.

    Furniture, equipment, and scenery have separate source discovery. All feed
    the same complete resource/material/geometry converter.
    This function supplies artwork, never gameplay or installation eligibility.
    """
    palettes, textures, vertex_arrays, raw_models = {}, {}, {}, {}
    context = descriptor.get('render_context', {})
    if set(context) - {'palette_slot', 'external_vertices'}:
        raise ReviewRequired('Unknown inherited render context')
    inherited_palette = context.get('palette_slot')
    if inherited_palette is not None and (type(inherited_palette) is not int or not 0 <= inherited_palette <= 15):
        raise ReviewRequired('Invalid inherited palette slot')
    inherited_vertices = 0
    if 'external_vertices' in context:
        name, at, n = context['external_vertices']
        if (tuple(source.containing(at, exact=True)) != (name, at, n)
                or not 16 <= n <= 512 or n % 16 or source.pointers(at, n)):
            raise ReviewRequired('Invalid complete inherited vertex array')
        vertex_arrays[at] = name, n
        inherited_vertices = n // 16
    adapter = descriptor.get('callback_adapter', {})
    from v3_furniture_materials import bindings as frame_bindings
    from v3_furniture_scroll import bindings as scroll_bindings
    material_frames=frame_bindings(adapter);used_frames=set()
    scrolling=scroll_bindings(adapter)
    fading = adapter.get('category') == 'switch-palette-fade'
    dynamic_used = False
    if fading:
        for endpoint in adapter['endpoints'].values():
            palettes[endpoint['donor_offset']] = endpoint['symbol'], endpoint['bytes']
    for frames in material_frames.values():
        if frames['kind']=='palette':
            for frame in frames['frames']:
                palettes[frame['donor_offset']]=frame['symbol'],frame['bytes']
    bindings, used_bindings = descriptor.get('palette_bindings', {}), set()
    for label, (name, at, n) in descriptor['models'].items():
        if n%8: raise ReviewRequired('unaligned display list')
        parts=adapter.get('model_sequences',{}).get(label)
        if parts:
            raw,pointers,receipts=source.model_sequence(parts);at=0;n=len(raw)
        else:
            raw,pointers,receipts=source.data[at:at+n],source.pointers(at,n),None
        position = 0
        while position < n:
            a, b = struct.unpack_from('>II', raw, position)
            op = a >> 24
            if op in (0xF0, 0xFD, 0x01):
                target = pointers.get(at+position+4)
                framed=material_frames.get(b)
                targets=[]
                if framed:
                    if (target is not None or (op,framed['kind']) not in ((0xF0,'palette'),(0xFD,'texture'))):
                        raise ReviewRequired('changed material-frame resource binding')
                    used_frames.add(b)
                    targets=[row['donor_offset'] for row in framed['frames']]
                    if op==0xF0:position+=8;continue
                    target=targets[0]
                elif fading and op == 0xF0 and b == 0x08000000:
                    if target is not None: raise ReviewRequired('relocated dynamic palette binding')
                    dynamic_used = True; position += 8; continue
                elif op == 0xF0 and b in bindings:
                    if target is not None: raise ReviewRequired('relocated constant palette binding')
                    target = bindings[b]; used_bindings.add(b)
                elif target is None or b: raise ReviewRequired('missing model dependency relocation')
                symbol, start, size = source.containing(target, exact=op != 0x01)
                if source.pointers(start, size): raise ReviewRequired('pointer-bearing texture or vertex array')
                if op == 0xF0:
                    if inherited_palette is not None:
                        raise ReviewRequired('Model overwrites its inherited palette contract')
                    if size != 32: raise ReviewRequired('palette is not sixteen colours')
                    palettes[start] = (symbol, size)
                elif op == 0xFD:
                    w, h, fmt, bits = model_texture_shape(raw[position:position+8])
                    if ((fmt,bits) not in ((2,0),(4,0),(0,2),(3,1),(3,2))
                            or w*h*(4<<bits)//8 != size or size>2048):
                        raise ReviewRequired('texture is not complete TMEM-sized CI4/I4/IA8/IA16/RGBA16')
                    if start in textures and textures[start][2:] != (w, h, fmt, bits):
                        raise ReviewRequired('texture has inconsistent dimensions')
                    textures[start] = (symbol, size, w, h, fmt, bits)
                    for frame_target in targets:
                        frame_name,frame_at,frame_size=source.containing(frame_target,exact=True)
                        if (frame_size!=size or source.pointers(frame_at,frame_size) or
                                frame_at in textures and textures[frame_at][2:]!=(w,h,fmt,bits)):
                            raise ReviewRequired('material frames have inconsistent texture layouts')
                        textures[frame_at]=(frame_name,frame_size,w,h,fmt,bits)
                else:
                    if inherited_vertices:
                        raise ReviewRequired('Model overwrites its inherited vertex contract')
                    if size%16: raise ReviewRequired('invalid complete vertex array')
                    vertex_arrays[start] = (symbol, size)
            if op == 0x0A:
                count = (a >> 17 & 127)+1
                position += (1 + (max(0, count-3)+3)//4)*8
            else: position += 8
            if position > n: raise ReviewRequired('truncated packed model')
        raw_models[label] = name, at, raw, pointers, receipts
    if used_bindings != set(bindings): raise ReviewRequired('unused constant palette binding')
    if used_frames != set(material_frames):raise ReviewRequired('unused material-frame binding')
    if fading and not dynamic_used: raise ReviewRequired('unused palette-fade dependency')
    if inherited_palette is not None and (palettes or bindings or fading or not any(r[4]==2 for r in textures.values())):
        raise ReviewRequired('Unused or conflicting inherited palette contract')
    if (any(r[4]==2 for r in textures.values()) and not palettes and inherited_palette is None) or len(vertex_arrays) != 1:
        raise ReviewRequired('static materials need CI4 palettes and one complete vertex array')
    body, resources, offsets = bytearray(32 if fading else 0), [], {}
    def add(at, name, n, convert, **details):
        raw = source.data[at:at+n]
        converted = convert(raw)
        if len(converted) != n: raise ReviewRequired('resource conversion changes allocation')
        body.extend(bytes(-len(body)%32)); offsets[at] = len(body); body.extend(converted)
        resources.append(dict(symbol=name, donor_offset=at, native_offset=offsets[at], bytes=n,
            source_sha256=sha256(raw), output_sha256=sha256(converted), **details))
    for at, (name, n) in sorted(palettes.items()): add(at, name, n, native_palette, kind='palette')
    for at, (name, n, w, h, fmt, bits) in sorted(textures.items()):
        add(at, name, n, lambda data, w=w, h=h, bits=bits, fmt=fmt:
            native_rgba16(data,w,h) if (fmt,bits)==(0,2) else native_ia16(data,w,h) if bits==2 else native_ia8(data,w,h) if bits==1
            else pack4(untile(data,w,h,4)),
            kind='texture',width=w,height=h,format={(2,0):'CI4',(4,0):'I4',(0,2):'RGBA16',(3,1):'IA8',(3,2):'IA16'}[fmt,bits])
    vertex, (name, n) = next(iter(vertex_arrays.items()))
    add(vertex, name, n, lambda data: normalise_vertex_flags(data)[0], kind='vertices')
    models = {}
    for label, (name, at, raw, pointers, receipts) in raw_models.items():
        matrices = 0
        if descriptor.get('kind') in ('animated-held-model','animated-room-model'):
            # The native skeleton drawer publishes each visible joint matrix
            # before its list runs. No list may read a later, uninitialised joint.
            visible = [r['index'] for r in descriptor['skeleton']['rows'] if 'model' in r]
            joints = [r['joint_index'] for r in descriptor['joint_models'] if r['model_label']==label]
            matrices = min(visible.index(index)+1 for index in joints)
        models[label] = dict(symbol=name, donor_offset=at, source_sha256=sha256(raw),
            **({'source_parts':receipts} if receipts else {}),
            rows=parse_model(raw, at, pointers, tuple(palettes),
                {p:(r[2], r[3]) for p,r in textures.items()}, vertex, n, static_materials=True,
                palette_bindings=bindings, palette_fade=fading,
                joint_matrices=matrices, inherited_palette_slot=inherited_palette,
                inherited_vertices=inherited_vertices,
                scrolling=scrolling.get(label),
                material_bindings={address:(row['kind'],row['frames'][0]['donor_offset'])
                                   for address,row in material_frames.items()}))
    # Validate all native emitter rules before creating output files.
    commands, sections = command_source(models, offsets)
    if fading:
        cursor = len(body); destinations = []
        for _, size in sections:
            cursor = (cursor+7)&~7; destinations.append(SEGMENT+cursor); cursor += size
        if len(destinations) != 3: raise ReviewRequired('changed palette-fade model count')
        # Self-describing immutable object header; palettes/models remain in
        # this complete DMA object. This does not imply runtime installation.
        body[:32] = struct.pack('>IHH6I',0x41465031,(cursor+15)&~15,3,
            offsets[adapter['endpoints']['on']['donor_offset']],
            offsets[adapter['endpoints']['off']['donor_offset']],*destinations,0)
    return descriptor, bytes(body), resources, offsets, models, commands, sections


def prepare_native_variant(source, model, reference, reference_model, reference_segment):
    """Pack legacy N64-format donor art against a complete native command list.

    Some donor UI models retain native RGBA5551/linear CI4 resources, unlike
    Dolphin models. Require the same complete command program as a known native
    model, then change only its three resource pointers. This is not a fallback
    for unsupported Dolphin commands or arbitrary native display lists.
    """
    name,start,size=model;raw=source.data[start:start+size]
    original=reference[reference_model:reference_model+size]
    pointers=source.pointers(start,size)
    if (not size or size%8 or len(raw)!=size or len(original)!=size
            or raw[-8:]!=struct.pack('>2I',0xDF000000,0)):
        raise ReviewRequired('Incomplete legacy native model')
    normalized=bytearray(original);resources=[];body=bytearray();fixes={};triangles=0
    vertices=None;palette_count=None;texture_bytes=None;texture_extent=None
    for offset in range(0,size,8):
        a,b=struct.unpack_from('>2I',raw,offset);op=a>>24
        if op not in (0xD7,0xE7,0xE2,0xFC,0xE3,0xFD,0xE8,0xF5,0xE6,
                      0xF0,0xF3,0xF2,0xFA,0xD9,0x01,0x05,0x06,0xDF):
            raise ReviewRequired('Unsupported legacy native command')
        if op==0xDF and offset!=size-8:raise ReviewRequired('Early legacy model return')
        if op in (0x01,0xFD):
            target=pointers.get(start+offset+4)
            if b or target is None:raise ReviewRequired('Missing legacy resource relocation')
            symbol,at,n=source.containing(target,exact=True)
            if source.pointers(at,n):raise ReviewRequired('Pointer-bearing legacy resource')
            native_pointer=u32(original,offset+4)
            if native_pointer>>24!=reference_segment or (native_pointer&0xFFFFFF)+n>len(reference):
                raise ReviewRequired('Native reference resource escapes its bank')
            if op==1:
                count=a>>12&255;end=a>>1&127
                if vertices is not None or count!=end or not 0<count<=32 or n!=count*16:
                    raise ReviewRequired('Unsupported legacy vertex cache layout')
                vertices=count;kind='vertices'
            else:
                fmt,bits=(a>>21)&7,(a>>19)&3
                if bits!=2 or a&0xFFF:raise ReviewRequired('Unsupported legacy texture transfer')
                kind={0:'palette',2:'texture'}.get(fmt)
                if kind is None:raise ReviewRequired('Unsupported legacy material format')
            if any(r['kind']==kind for r in resources):raise ReviewRequired('Multiple legacy resource bindings')
            data=source.data[at:at+n];body.extend(bytes(-len(body)%32));destination=len(body);body.extend(data)
            resources.append(dict(symbol=symbol,donor_offset=at,native_offset=destination,bytes=n,
                source_sha256=sha256(data),output_sha256=sha256(data),kind=kind,
                reference_offset=native_pointer&0xFFFFFF,
                reference_sha256=sha256(reference[native_pointer&0xFFFFFF:(native_pointer&0xFFFFFF)+n])))
            fixes[offset+4]=SEGMENT+destination
            struct.pack_into('>I',normalized,offset+4,0)
        elif op==0xF0:
            if palette_count is not None:raise ReviewRequired('Multiple legacy palette loads')
            palette_count=((b>>14)&1023)+1
        elif op==0xF3:
            if texture_bytes is not None:raise ReviewRequired('Multiple legacy texture loads')
            texture_bytes=(((b>>12)&4095)+1)*2
        elif op==0xF2:
            if texture_extent is not None or a&0xFFFFFF:raise ReviewRequired('Unsupported legacy tile origin')
            texture_extent=(((b>>12)&4095)//4+1,(b&4095)//4+1)
        elif op in (5,6):
            if vertices is None:raise ReviewRequired('Legacy triangles precede vertices')
            for triangle in ((a,) if op==5 else (a,b)):
                indices=[triangle>>shift&255 for shift in (16,8,0)]
                if any(i%2 or i//2>=vertices for i in indices):raise ReviewRequired('Legacy vertex index escapes cache')
                triangles+=1
    if (set(pointers)!={start+p for p in fixes} or normalized!=raw
            or {r['kind'] for r in resources}!={'palette','texture','vertices'}
            or palette_count!=16 or texture_extent is None or not triangles):
        raise ReviewRequired('Legacy program differs from the complete native reference')
    by_kind={r['kind']:r for r in resources};w,h=texture_extent
    if by_kind['palette']['bytes']!=palette_count*2 or by_kind['texture']['bytes']!=texture_bytes or w*h//2!=texture_bytes:
        raise ReviewRequired('Legacy material transfer differs from complete resource sizes')
    by_kind['palette']['format']='RGBA5551'
    by_kind['texture'].update(format='CI4',layout='native-linear',width=w,height=h)
    code=bytearray(raw)
    for offset,pointer in fixes.items():struct.pack_into('>I',code,offset,pointer)
    body.extend(bytes(-len(body)%8));model_offset=len(body);body.extend(code);body.extend(bytes(-len(body)%16))
    compiled=dict(layer='opaque',symbol=name,donor_offset=start,source_sha256=sha256(raw),
        native_offset=model_offset,bytes=len(code),output_sha256=sha256(code),triangles=triangles)
    return bytes(body),dict(format='AFV3-NATIVE-MODEL-1',resources=resources,compiled_models=[compiled],
        model_offsets={'opaque':model_offset},bytes=len(body),sha256=sha256(body),
        reference_model_offset=reference_model,reference_model_sha256=sha256(original))


def prepare_material_pair(source, parts, *, render_context=None):
    """Validate a full material/geometry pair, then retain its separate lists.

    Ground and handover renderers insert per-instance matrices between these
    lists. Scenery may also supply a checked palette or adjusted shadow vertices.
    Never accept an arbitrary fragment without its complete render contract.
    """
    if len(parts)!=2:raise ReviewRequired('Material pair requires exactly two complete lists')
    descriptor=dict(models={'opaque':parts[0]},callback_adapter=dict(
        category='split-material-geometry',model_sequences={'opaque':parts}))
    if render_context is not None: descriptor['render_context'] = render_context
    _,body,resources,offsets,joined,_,_=prepare_models(source,descriptor)
    material=source.data[parts[0][1]:parts[0][1]+parts[0][2]]
    geometry=source.data[parts[1][1]:parts[1][1]+parts[1][2]]
    if any(material[i] in (0x01,0x0A,0xDE) for i in range(0,len(material)-8,8)):
        raise ReviewRequired('Material pair has geometry or a nested call in its material list')
    rows=joined['opaque']['rows'];split=cursor=0
    # One decoded texture row consumes both FD and its paired Dolphin D2
    # command. Counting eight-byte words would move the vertex load before the
    # caller's matrix, so follow the validated material instruction boundaries.
    while cursor<len(material)-8:
        words=struct.unpack_from('>II',material,cursor)
        if split>=len(rows) or rows[split]['words']!=words:
            raise ReviewRequired('Material pair boundary disagrees with complete decoding')
        cursor+=16 if rows[split]['opcode']==0xFD else 8
        split+=1
    if cursor!=len(material)-8:raise ReviewRequired('Material pair splits a texture/tile command')
    if (split<=0 or len(rows)<=split or
            any(r['opcode'] not in (0x01,0x0A,0xDF) for r in rows[split:])):
        raise ReviewRequired('Material pair geometry changes material or uses unsupported commands')
    groups=(rows[:split]+[dict(words=(0xDF000000,0),opcode=0xDF)],rows[split:])
    models={}
    for label,part,raw,group in zip(('material','geometry'),parts,(material,geometry),groups):
        name,at,n=part
        models[label]=dict(symbol=name,donor_offset=at,source_sha256=sha256(raw),
            source_parts=[dict(symbol=name,donor_offset=at,bytes=n,sha256=sha256(raw),joined_offset=0)],
            rows=group,**({'inherited_material':True} if label=='geometry' else {}))
    commands,sections=command_source(models,offsets)
    descriptor.update(kind='split-material-geometry',models=dict(zip(('material','geometry'),parts)))
    descriptor['callback_adapter']=dict(category='split-material-geometry',
        model_order=['material','matrix','geometry'],complete_pair_sha256=sha256(material+geometry))
    return descriptor,body,resources,offsets,models,commands,sections


def compile_models(directory, prepared):
    """Emit a complete native object from the shared preflight description."""
    profile, body, resources, offsets, models, commands, sections = prepared
    source_file = directory/'commands.c'; write_new(source_file, commands.encode())
    compiled = compile_commands(directory/'gbi', source_file, sections)
    return assemble_models(prepared,compiled)


def assemble_models(prepared, compiled):
    """Shared complete-object packing for single, bulk, and reused commands."""
    profile, body, resources, offsets, models, commands, sections = prepared
    if set(compiled)!=set(models) or any(len(compiled[name])!=n for name,n in sections):
        raise ValueError('Compiled models differ from the complete section contract')
    asset, destinations, records = bytearray(body), {}, []
    for label, model in models.items():
        asset.extend(bytes(-len(asset)%8)); destinations[label] = len(asset); asset.extend(compiled[label])
        records.append(dict(layer=label, symbol=model['symbol'], source_sha256=model['source_sha256'],
            **({'source_parts':model['source_parts']} if 'source_parts' in model else {}),
            native_offset=destinations[label], bytes=len(compiled[label]), output_sha256=sha256(compiled[label]),
            triangles=sum(len(r.get('triangles',[])) for r in model['rows'])))
    sequence_record,sequence=draw_sequence(profile,len(body),sections)
    if sequence_record:
        if (sequence_record['model_offsets']!=destinations or sequence_record['native_offset']!=len(asset)):
            raise ValueError('Static draw sequence differs from compiled layout')
        asset.extend(sequence)
    asset.extend(bytes(-len(asset)%16))
    expected = (len(body)+sum(n for _,n in sections)+len(sequence)+15)&~15
    if len(asset) != expected: raise ValueError('Compiled object size differs from preflight')
    return bytes(asset), destinations, records, sequence_record


class PreparedAssets:
    """Explicit source-bound cache; readiness always comes from current rules."""
    def __init__(self, source, directories=()):
        self.rows={}
        for path in directories:
            path=Path(path).resolve();raw=(path/'art.json').read_bytes();art=json.loads(raw)
            if (art.get('format') not in ('AFV3-AUTO-FURNITURE-ASSETS-1','AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1')
                    or type(art.get('version')) is not int or not 1<=art['version']<=VERSION
                    or art.get('source_rel_sha256')!=sha256(source.rel)
                    or art.get('source_symbols_sha256')!=sha256(source.symbols.encode())):
                raise ValueError('Prepared cache has an unsupported source/format')
            seen=set()
            for row in art['objects']:
                item=row.get('donor_item_id',row.get('item_id'))
                if not isinstance(item,str) or not re.fullmatch(r'[13][0-9A-F]{3}',item) or item in seen:
                    raise ValueError('Prepared cache has an invalid or duplicate item')
                seen.add(item)
                self.rows.setdefault(item,[]).append((path,row,sha256(raw)))

    def reuse(self,source,item,prepared):
        from v3_furniture_rigs import suffix
        candidates=self.rows.get(item,[])
        if not candidates:return None
        profile,body,resources,_,models,commands,sections=prepared
        accepted=None
        for path,row,report_sha in candidates:
            file=(path/row['object_file']).resolve();command_file=(path/item/'commands.c').resolve()
            if file.parent!=path or not command_file.is_relative_to(path):
                raise ValueError('Prepared cache file escapes its bundle')
            asset=file.read_bytes()
            if (len(asset)!=row['object_bytes'] or sha256(asset)!=row['object_sha256']
                    or row['resources']!=resources or asset[:len(body)]!=body
                    or command_file.read_text()!=commands):
                raise ValueError('Prepared cache artwork/emitter differs from current source')
            if len(row['models'])!=len(sections):raise ValueError('Prepared cache has incomplete model sections')
            compiled={}
            for old,(label,n) in zip(row['models'],sections,strict=True):
                at=old['native_offset']
                if type(at) is not int or at%8 or at<len(body) or at+n>len(asset):
                    raise ValueError('Prepared cache model escapes its complete object')
                raw=asset[at:at+n]
                model=models[label]
                if (old['layer']!=label or old['bytes']!=n
                        or row['model_offsets'].get(label)!=at
                        or old['source_sha256']!=model['source_sha256']
                        or old.get('source_parts')!=model.get('source_parts')
                        or sha256(raw)!=old['output_sha256']):
                    raise ValueError('Prepared cache model differs from complete source/layout')
                compiled[label]=raw
            packed,destinations,records,sequence=assemble_models(prepared,compiled)
            extra,rig=suffix(source,profile,destinations,start=len(packed));packed+=extra
            if (packed!=asset or row['model_offsets']!=destinations or row['models']!=records
                    or row.get('draw_sequence')!=sequence or row.get('rig',{})!=rig):
                raise ValueError(f'Prepared cache {item} differs from complete reconstructed object')
            if accepted is not None and accepted[0]!=compiled:
                raise ValueError('Conflicting prepared cache objects')
            accepted=(compiled,dict(directory=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                report_sha256=report_sha,object_sha256=sha256(asset)))
        return accepted


def draw_sequence(profile, body_bytes, sections):
    """Link complete opaque lists in donor order, without a runtime callback."""
    adapter=profile.get('callback_adapter',{})
    if adapter.get('category')!='constant-model-sequence': return None,b''
    if (adapter['draw_arena']!='opaque' or adapter['model_order']!=[label for label,_ in sections]
            or not 1<=len(sections)<=4 or body_bytes%8):
        raise ReviewRequired('invalid complete static draw sequence')
    cursor=body_bytes;models={}
    for label,size in sections:
        if size<=0 or size%8: raise ReviewRequired('unaligned static sequence model')
        models[label]=cursor;cursor+=size
    raw=b''.join(struct.pack('>II',0xDE000000,SEGMENT+offset) for offset in models.values())
    raw+=struct.pack('>II',0xDF000000,0)
    return dict(native_offset=cursor,bytes=len(raw),model_offsets=models,
                arena='opaque',output_sha256=sha256(raw)),raw


def identity_rows(path, *, extra_items=(), include_unmapped_legacy=False):
    if sha256(path.read_bytes()) != SHEET_SHA: raise ValueError('Changed identity worksheet')
    rows = list(sheet_rows(path, 'Items'))
    if any(rows[0][1].get(k) != v for k,v in {'C':'ID (AF)', 'E':'ID (AC)', 'J':'Name (English)'}.items()):
        raise ValueError('Changed identity columns')
    result = {}
    for number, cells in rows[1:]:
        value = cells.get('E', '')
        if not re.fullmatch(r'[13][0-9A-F]{3}', value): continue
        item = int(value, 16)
        if item < 0x3000 and item not in extra_items:
            if not include_unmapped_legacy or any(cells.get(k)!='-' for k in ('C','H','CG','CJ')):continue
        if item in result: raise ValueError('Ambiguous worksheet donor identity')
        result[item] = number, cells
    return result


def name_metadata(source, item, identity):
    """Keep prepared-asset names tied to the actual English donor too."""
    index = furniture_source_index(item)
    symbol = 'ftrName_table' if index < 1024 else 'ftrName2_table'
    name_index = index if index < 1024 else index-1024
    name_raw = source.raw(symbol)[name_index*16:(name_index+1)*16]
    try: name = name_raw.decode('ascii').rstrip(' ')
    except UnicodeDecodeError: raise ReviewRequired('name needs supported encoding') from None
    if not name or name != identity[1].get('J') or name in ('DUMMY', 'dummy'):
        raise ReviewRequired('name/identity is ambiguous or unused')
    return dict(id=f'GAFE01-r0/item/{item:04X}', item_id=f'{item:04X}', runtime_index=index,
                name=name, name_sha256=sha256(name_raw), name_source_index=name_index,
                **({'name_source_symbol':symbol} if index < 1024 else {}))


def metadata(source, item, profile, identity):
    from v3_furniture_rigs import FIXED_CATEGORY
    from v3_furniture_materials import CATEGORY as MATERIAL_CATEGORY
    from v3_furniture_scroll import CATEGORY as SCROLL_CATEGORY
    binding=getattr(source,'runtime_profiles',{}).get(f'{item:04X}')
    if profile.get('callback_adapter',{}).get('category')==SCROLL_CATEGORY and not binding:
        raise ReviewRequired('Scrolling artwork is prepared; drawing, lifecycle behaviour, and acquisition need runtime adapters')
    if profile.get('callback_adapter',{}).get('category')==MATERIAL_CATEGORY and not binding:
        raise ReviewRequired('Material-frame artwork is prepared; drawing, lifecycle behaviour, and acquisition need runtime adapters')
    if profile.get('callback_adapter',{}).get('category')==PENDING_MOVE_CATEGORY:
        raise ReviewRequired('Static artwork is prepared; move behaviour, profile interactions, and spawned effects need runtime adapters')
    if profile.get('callback_adapter',{}).get('category')==FIXED_CATEGORY:
        raise ReviewRequired('Fixed rig artwork is prepared; move/destroy behaviour and spawned effects need runtime adapters')
    alias = next((row for row in room_aliases(source)['rows'] if int(row['display_item_id'],16)==item), None)
    if alias:
        raise ReviewRequired(room_alias_reason(alias))
    if item<0x3000 and item not in LEGACY_FURNITURE:
        raise ReviewRequired('legacy donor identity needs native correspondence review and an additive import mapping')
    if binding and (binding['source_profile_sha256']!=profile['profile_sha256'] or
            binding['category']!=profile.get('callback_adapter',{}).get('category')):
        raise ReviewRequired('Installed lifecycle differs from the current source profile')
    if profile.get('kind') == 'animated-room-model' and not binding:
        raise ReviewRequired('Animated room lifecycle needs the shared runtime adapter')
    if profile.get('callback_adapter',{}).get('category')=='switch-trigger-sound' and not binding:
        raise ReviewRequired('Switch-triggered sound needs the shared native sound/runtime adapter')
    number, sheet = identity
    if any(sheet.get(k) != '-' for k in ('C', 'H', 'CG', 'CJ')):
        raise ReviewRequired('native identity/artwork correspondence needs review')
    names = name_metadata(source,item,identity); index = names['runtime_index']
    action_sound = source.raw('mRmTp_ftr_se_type')[index]
    if action_sound not in (0,1,2):
        raise ReviewRequired(f'action-sound category {action_sound} needs the shared seating adapter')
    layer_type = source.raw('aMR_layer_set_info')[index]
    if layer_type not in (0, 1, 2):
        raise ReviewRequired(f'unsupported placement-layer category {layer_type}')
    lists = []
    for key in source.names:
        if re.fullmatch(r'ftr_list\w*', key):
            raw = source.raw(key)
            if len(raw)%2: raise ValueError('Incomplete donor stock list')
            ids = struct.unpack('>'+str(len(raw)//2)+'H', raw)
            if item in ids:
                if ids[-1] or 0 in ids[:-1] or ids.count(item) != 1:
                    raise ReviewRequired('ambiguous acquisition list')
                lists.append((key, sha256(raw)))
    if len(lists) != 1 or lists[0][0] not in STOCK | REWARDS:
        raise ReviewRequired('acquisition needs an adapter: ' + ', '.join(r[0] for r in lists))
    group = (STOCK | REWARDS)[lists[0][0]]
    reward = REWARDS.get(lists[0][0], 0)
    catalogue = list(struct.iter_unpack('>HH', source.raw('mCL_furniture_list')))
    entries = [(position, mode) for position,(i,mode) in enumerate(catalogue) if i == index]
    if len(entries) != 1:
        raise ReviewRequired('catalogue preview needs a framing adapter')
    preview = entries[0][1]
    draw = source.raw('furniture_draw_data$436')
    if len(draw) != 328 or not 0 <= preview < len(draw)//8:
        raise ReviewRequired('catalogue preview exceeds the complete donor table')
    framing = draw[preview*8:preview*8+8]
    scale, y = struct.unpack('>ff',framing)
    if not (math.isfinite(scale) and .1 <= scale <= 2 and math.isfinite(y) and -200 <= y <= 100):
        raise ReviewRequired('unsupported catalogue preview framing')
    price = struct.unpack_from('>H', source.raw('ftr_price_table'), index*2)[0]
    hra = u32(source.data, 0x4FAFC+index*4)
    feng = source.data[0x4EBF0+index*2:0x4EBF0+index*2+2]
    donor_birth, surface, series = hra>>8&63, hra>>6&3, hra>>26
    from v3_hra_birth import donor_categories
    _, categories = donor_categories(source)
    if donor_birth >= len(categories) or hra&63 or series >= 60:
        raise ReviewRequired('scoring needs an acquisition/category adapter')
    birth = categories[donor_birth]
    native_hra = (hra&0xFFFFC000)|(birth<<9)|(surface<<7)
    runtime_index,destination = furniture_identity(item)
    if destination != item:
        names.update(item_id=f'{destination:04X}',runtime_index=runtime_index,
                     donor_item_id=f'{item:04X}',donor_runtime_index=index)
    return dict(**names, action_sound=action_sound,
        layer_type=layer_type, interaction_flags=profile['interaction_flags'],
        price=price, size_code=profile['size_code'], footprint=('1x1','2x1','2x2')[profile['size_code']],
        donor_list=lists[0][0], donor_list_sha256=lists[0][1], stock_group=group,
        reward_route=reward, ordinary_stock=group < 3,
        donor_catalogue_position=entries[0][0], preview_mode=preview,
        donor_preview_scalar_hex=framing.hex(),
        catalogue_orderable=not reward, donor_hra_hex=f'{hra:08x}', native_hra_hex=f'{native_hra:08x}',
        feng_hex=feng.hex(), series=series, birth_category=birth, donor_birth_category=donor_birth, surface=surface,
        donor_series_hex=source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
        identity_worksheet_row=number, behaviour=profile['behaviour'],
        **({k:binding[k] for k in ('room_runtime','room_lifecycle','room_placement') if k in binding} if binding else {}))


def scan(source, worksheet, installed=None):
    from v3_furniture_rigs import estimated_suffix
    installed = set(FURNITURE) if installed is None else set(installed)
    alias_catalogue = room_aliases(source)
    aliases = {int(row['display_item_id'],16):row for row in alias_catalogue['rows']}
    result = []
    for item, identity in sorted(identity_rows(worksheet,extra_items=aliases,include_unmapped_legacy=True).items()):
        row = dict(item_id=f'{item:04X}', name=identity[1].get('J'), installed=item in installed,
                   asset_ready=False)
        try:
            profile, body, resources, offsets, models, commands, sections = prepare(source, item)
            # Prepared batches also require a real, unambiguous donor identity.
            # Keep dummy/unknown names in review, not in the default bulk batch.
            name_metadata(source,item,identity)
            _,sequence=draw_sequence(profile,len(body),sections)
            estimated = (len(body)+sum(n for _,n in sections)+len(sequence)+15)&~15
            estimated += estimated_suffix(source,profile,estimated)
            if estimated > 9216: raise ReviewRequired('complete object exceeds native model-bank capacity')
            formats={r['format'] for r in resources if r['kind']=='texture'}
            categories = [profile['behaviour'], ('1x1','2x1','2x2')[profile['size_code']]]
            if item<0x3000:
                categories.append('legacy-donor-range')
                if profile['behaviour']=='static' and not profile.get('kind'):categories.append('legacy-static')
            categories.append('animated-materials' if profile.get('kind') else 'static-materials')
            if not profile.get('kind') and formats<={'CI4','I4'}: categories.append('static-4bit')
            if not profile.get('kind') and formats=={'CI4'}: categories.append('static-ci4')
            if 'I4' in formats: categories.append('intensity-materials')
            if 'RGBA16' in formats: categories.append('rgba16-materials')
            if 'IA8' in formats: categories.append('ia8-materials')
            if 'IA16' in formats: categories.append('ia16-materials')
            if any(r.get('combine_lerp') for m in models.values() for r in m['rows']):categories.append('translucent-combiners')
            if 'callback_adapter' in profile: categories.append(profile['callback_adapter']['category'])
            if profile.get('callback_adapter',{}).get('constant_palette'):
                categories.append('constant-palette-model-sequence')
            row.update(asset_ready=True, profile=profile,
                object_bytes=estimated, textures=sum(r['kind']=='texture' for r in resources),
                vertices=sum(r['bytes']//16 for r in resources if r['kind']=='vertices'),
                triangles=sum(len(r.get('triangles',[])) for m in models.values() for r in m['rows']),
                categories=categories)
            meta = metadata(source, item, profile, identity)
            row.update(status='supported', metadata=meta, categories=categories+[meta['donor_list']])
        except ValueError as error:
            row.update(status='review', reason=str(error))
        if item in aliases:
            if row['installed']:
                raise ValueError('Room alias is incorrectly installed as independent furniture')
            if not row['asset_ready'] and row.get('reason'):
                row['conversion_reason'] = row['reason']
            row.update(status='review', room_alias=aliases[item], reason=room_alias_reason(aliases[item]))
        result.append(row)
    return dict(format='AFV3-AUTO-FURNITURE-1', version=VERSION,
                source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
                worksheet_sha256=SHEET_SHA, room_aliases=alias_catalogue,
                counts=dict(Counter(r['status'] for r in result)), rows=result)


def convert(source, worksheet, output, selected=(), installed=None, *, assets_only=False, category=None, reuse_assets=()):
    from v3_furniture_rigs import suffix
    inventory = scan(source, worksheet, installed)
    rows = [r for r in inventory['rows'] if (r['asset_ready'] if assets_only else r['status']=='supported') and
            (r['item_id'] in selected if selected else not r['installed']) and
            (bool(selected) or not assets_only or r['item_id'] not in getattr(source,'runtime_profiles',{})) and
            (category is None or category in r['categories'])]
    if selected and set(selected) != {r['item_id'] for r in rows}:
        missing = sorted(set(selected)-{r['item_id'] for r in rows})
        raise ValueError('Unsupported or filtered requested entries: '+json.dumps(missing))
    if not rows: raise ValueError('No supported uninstalled furniture in the requested category')
    identities = identity_rows(worksheet,extra_items={int(r['item_id'],16) for r in rows})
    names = {r['item_id']:name_metadata(source,int(r['item_id'],16),identities[int(r['item_id'],16)]) for r in rows}
    cache=PreparedAssets(source,reuse_assets);plans=[];jobs=[]
    # Resolve and validate the entire batch before starting a compiler. A
    # prepared cache supplies artwork only, never old eligibility or metadata.
    for row in rows:
        item = int(row['item_id'], 16)
        prepared = prepare(source, item)
        reused=cache.reuse(source,row['item_id'],prepared)
        plans.append((row,prepared,reused))
    output.mkdir(parents=True, exist_ok=False)
    for row,prepared,reused in plans:
        directory=output/row['item_id'];directory.mkdir()
        command_file=directory/'commands.c';write_new(command_file,prepared[5].encode())
        if reused is None:jobs.append((row['item_id'],command_file,prepared[6]))
    compiled=compile_commands_batch(output/'compiled',jobs)
    objects = []
    for row,prepared,reused in plans:
        profile, body, resources, offsets, models, commands, sections = prepared
        asset, destinations, records, sequence_record = assemble_models(prepared,reused[0] if reused else compiled[row['item_id']])
        rig_bytes, rig_record = suffix(source,profile,destinations,start=len(asset))
        asset += rig_bytes
        if len(asset) != row['object_bytes']: raise ValueError('Compiled object size differs from preflight')
        name = row['item_id']+'.n64obj.bin'; write_new(output/name, asset)
        objects.append(dict(**row.get('metadata',names[row['item_id']]), profile=profile, resources=resources, models=records,
            import_ready=row['status']=='supported', pending_reason=row.get('reason'),
            **({'room_alias':row['room_alias']} if 'room_alias' in row else {}),
            native_profile_scalar_hex=profile['scalar_hex'], model_offsets=destinations,
            **({'draw_sequence':sequence_record} if sequence_record else {}),
            **({'rig':rig_record} if rig_record else {}),
            **({'reused_artwork':reused[1]} if reused else {}),
            object_file=name, object_bytes=len(asset), object_sha256=sha256(asset)))
        print(json.dumps(dict(converted=row['item_id'], name=row['name'], bytes=len(asset),
                             reused=reused is not None)), flush=True)
    report = dict(format=('AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1' if assets_only else
                          'AFV3-AUTO-FURNITURE-ASSETS-1'), version=VERSION,
        source_rel_sha256=inventory['source_rel_sha256'], source_symbols_sha256=inventory['source_symbols_sha256'],
        objects=objects, runtime_installed=False,
        batch=dict(objects=len(objects),compiled=len(jobs),reused=len(objects)-len(jobs),
                   compiler_containers=int(bool(jobs))))
    write_new(output/'inventory.json', (json.dumps(inventory, indent=2)+'\n').encode())
    write_new(output/'art.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('scan', 'convert', 'import'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--select', action='append', default=[], help='Canonical donor ID; defaults to all supported new furniture')
    parser.add_argument('--category', help='Restrict to a discovered shared category, without an item list')
    parser.add_argument('--representation', choices=('furniture','handheld','scenery','audio','rewards','lifecycle','surfaces'), default='furniture',
                        help='Discover furniture, held equipment, scenery, audio, rewards, lifecycles, or room surfaces')
    parser.add_argument('--assets-only', action='store_true',
                        help='convert only: prepare artwork even when metadata/acquisition is unsupported; never install')
    parser.add_argument('--base-lock', type=Path, default=ROOT/'config/v3-import-build.json')
    parser.add_argument('--reuse-assets', type=Path, action='append', default=[],
        help='Reuse a verified artwork bundle without recompilation; repeat for multiple bundles')
    args = parser.parse_args(); output = args.output.resolve()
    if args.assets_only and args.command != 'convert': parser.error('--assets-only requires convert')
    if args.representation=='audio' and args.command!='convert':
        parser.error('Audio preparation requires convert --assets-only; dispatch/allocation integration is unfinished')
    if args.representation=='lifecycle' and (args.command!='convert' or not args.assets_only):
        parser.error('Lifecycle preparation requires convert --assets-only; missing dependencies remain explicit')
    if args.category and args.command == 'scan': parser.error('--category requires convert or import')
    if args.reuse_assets and (args.command=='scan' or args.representation not in ('furniture','surfaces')):
        parser.error('--reuse-assets requires furniture convert/import or surface preparation')
    if args.representation in ('handheld','scenery','audio','rewards','surfaces') and (args.command == 'import' or
            args.command == 'convert' and not args.assets_only):
        parser.error('This representation requires convert --assets-only; runtime integration is unfinished')
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Use a fresh ignored build path')
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if args.representation=='rewards':
        if args.category in ('password','password-policy'):
            if args.category=='password':from v3_password import prepare as prepare_password
            else:from v3_password_policy import prepare as prepare_password
            if args.select or args.command!='convert':parser.error('Password preparation compiles one complete shared category')
            report=prepare_password(source,output,**({'lock':args.base_lock} if args.category=='password-policy' else {}))
            print(json.dumps({k:report[k] for k in ('bytes','sha256','runtime_installed','acquisition_installed')}))
            return
        from v3_holiday_rewards import discover as discover_rewards,prepare as prepare_rewards
        if args.select or args.category not in (None,'holiday'):
            parser.error('Reward preparation retains the complete shared holiday category; item selection belongs to the runtime profile')
        if args.command=='scan':
            report=discover_rewards(source);output.parent.mkdir(parents=True,exist_ok=True)
            write_new(output,(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
        else:report=prepare_rewards(source,output)
        print(json.dumps(dict(events=len(report['rows']),candidates=sum(len(r['source_items']) for r in report['rows']),
            runtime_installed=False,acquisition_installed=False)))
        return
    if args.representation == 'scenery':
        from v3_scenery import discover as scan_scenery, convert as convert_scenery
        if args.command == 'scan':
            if args.select: parser.error('Scenery dependencies are not selectable items')
            report = scan_scenery(source); output.parent.mkdir(parents=True, exist_ok=True)
            write_new(output, (json.dumps(report, indent=2)+'\n').encode())
            print(json.dumps(report['counts']))
        else:
            report = convert_scenery(source, output, args.select, category=args.category or 'gold-tree')
            print(json.dumps(report['counts']))
        return
    if args.representation == 'handheld':
        from v3_handheld_items import scan as scan_handheld, convert as convert_handheld
        if args.command == 'scan':
            report = scan_handheld(source); output.parent.mkdir(parents=True, exist_ok=True)
            write_new(output, (json.dumps(report, indent=2)+'\n').encode())
            print(json.dumps(report['counts']))
        else:
            convert_handheld(source,output,args.select,category=args.category)
        return
    worksheet = ROOT/'build/item-identity-megasheet.xlsx'
    from v3_furniture_install import inputs, build
    base, base_report = inputs(args.base_lock)
    if args.representation=='surfaces':
        from v3_room_surfaces import discover as discover_surfaces,convert as convert_surfaces
        if args.command=='scan':
            if args.select:parser.error('Surface discovery retains the complete source banks')
            report,_=discover_surfaces(source,base);output.parent.mkdir(parents=True,exist_ok=True)
            write_new(output,(json.dumps(report,indent=2)+'\n').encode())
        else:report=convert_surfaces(source,base,output,args.select,args.category,args.reuse_assets)
        print(json.dumps(report.get('batch',report['counts'])))
        return
    from v3_room_rig_runtime import bind_profiles
    bind_profiles(source,base,base_report)
    installed = [int(r['id'].rsplit('/',1)[1],16) for r in base_report['furniture']['imports']+[base_report['speed_bag']]]
    if args.representation=='lifecycle':
        from v3_furniture_contact import prepare_batch
        report=prepare_batch(source,base,scan(source,worksheet,installed),output,args.select,args.category,base_report)
        print(json.dumps(dict(lifecycles=len(report['rows']),complete_dependencies=report['complete_dependencies'],
            code_bytes=report['code']['bytes'],runtime_installed=False)))
        return
    if args.representation=='audio' and args.command=='convert':
        from v3_sound_programs import prepare_furniture_audio
        report=prepare_furniture_audio(base,base_report,source,scan(source,worksheet,installed),
            output,args.select,args.category)
        print(json.dumps(dict(furniture=len(report['furniture']),programs=len(report['programs']),
            new_instruments=report['layout']['instrument_count']-report['layout']['native_instrument_count'],
            runtime_installed=False)))
        return
    if args.command == 'scan':
        report = scan(source, worksheet, installed); output.parent.mkdir(parents=True, exist_ok=True)
        write_new(output, (json.dumps(report, indent=2)+'\n').encode())
        print(json.dumps(dict(counts=report['counts'], supported_new=[r['item_id'] for r in report['rows']
                         if r['status']=='supported' and not r['installed']])))
    elif args.command == 'convert': convert(source, worksheet, output, args.select, installed,
                                            assets_only=args.assets_only, category=args.category,reuse_assets=args.reuse_assets)
    else:
        output.mkdir(parents=True)
        convert(source,worksheet,output/'assets',args.select,installed,category=args.category,reuse_assets=args.reuse_assets)
        report = build(output/'cartridge',output/'assets',args.base_lock)
        print(json.dumps(dict(runtime_abi=report['runtime_abi'],output_sha256=report['output_sha256'])))


if __name__ == '__main__': main()
