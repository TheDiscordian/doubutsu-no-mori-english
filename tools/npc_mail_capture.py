"""Bounded native NPC capture image, source resources, and relocation checks."""

from pathlib import Path
import struct

from aflib import CODE_RAM,sha256
from npc_mail_generation import native_evidence
from npc_mail_names import unpack_aliases
from npc_mail_words import unpack_words
from runtime_layout import MODULE_RAM,RESERVATION

ROOT = Path(__file__).resolve().parents[1]
RAM = 0x80B00000
WORD_HASH = '698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1'
ALIAS_HASH = 'a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6'
ACADEMY_SERIES_HASH = 'be1258e1806e2a5e38a64cad52863c632d45b4610685ec9590dd264bb1569a38'
IMPORTS = ('af_mail_record_pack','af_mail_restore','af_mail_catalog_header_valid')
HOOKS = ((0x800A8E48,0x800A8C48,'af_npc_mail_prepare'),(0x800A8F6C,0x800A8C48,'af_npc_mail_prepare'),
         (0x800A8C90,0x800ACD18,'af_npc_mail_sender_name'),(0x800A8CB8,0x800ACD18,'af_npc_mail_other_name'),
         (0x800A8CF8,0x800ACD18,'af_npc_mail_other_name'),(0x800A8D70,0x800C3F70,'af_npc_mail_word'),
         (0x800A8F0C,0x800A8B84,'af_npc_mail_composite'),(0x800A8FD8,0x80093F04,'af_npc_mail_classic'))


def call_patches(code,module):
    native_evidence(code)
    output = []
    for address,original,symbol in HOOKS:
        before = code[address-CODE_RAM:address-CODE_RAM+4]
        if before != struct.pack('>I',0x0C000000|((original>>2)&0x3FFFFFF)):
            raise ValueError('Unexpected original NPC capture call')
        target = int(module['symbols'].get(symbol,'0'),16)
        if target&3 or not MODULE_RAM+0x300 <= target < MODULE_RAM+min(module['linked_bytes'],0x6000):
            raise ValueError('NPC capture hook target is outside resident code')
        output.append((address,before,struct.pack('>I',0x0C000000|((target>>2)&0x3FFFFFF))))
    return output


def creator_imports(*,villager_events=False,academy_scores=False):
    return IMPORTS+(('af_load_item_name',) if villager_events else ())+(('af_format_year','af_format_month','af_format_day') if academy_scores else ())


def source_hashes(*,mother_letters=False,departed_letters=False,villager_events=False,academy_letters=False,academy_scores=False):
    names = ['overlays/mail_generation/'+name for name in
             ('digest.c','digest.h','npc_capture.c','npc_capture.h','generate.c','generate.h',
              'npc_creator.c','npc_creator.h','capture.ld','sources.s')]
    names += ['runtime/mail/'+name for name in ('npc_generation.h','npc_loader.h','catalog.h','format.h','record.h','glyph.h')]
    if mother_letters:
        names += ['overlays/mail_generation/'+name for name in ('mother_creator.c','mother_creator.h','system_capture.ld')]
    if departed_letters:
        if not mother_letters: raise ValueError('Departed creator requires the Mom dispatcher')
        names += ['overlays/mail_generation/'+name for name in ('departed_creator.c','departed_creator.h','departed_capture.ld')]
    if villager_events:
        if not departed_letters: raise ValueError('Villager-event creator requires the departed dispatcher')
        names += ['overlays/mail_generation/'+name for name in ('villager_event_creator.c','villager_event_creator.h','villager_event_capture.ld')]
        names += ['runtime/item_name.h']
    if academy_letters:
        if not villager_events: raise ValueError('Academy creator requires the villager-event dispatcher')
        names += ['overlays/mail_generation/'+name for name in ('academy_creator.c','academy_creator.h','academy_capture.ld')]
    if academy_scores:
        if not academy_letters: raise ValueError('Academy score creator requires welcome/advice dispatch')
        names += ['overlays/mail_generation/'+name for name in
                  ('academy_score_creator.c','academy_score_creator.h','academy_score_capture.ld','academy_score_sources.s')]
        names += ['runtime/dateformat.h']
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def verified_resources(words,aliases):
    unpack_words(words,WORD_HASH)
    unpack_aliases(aliases,ALIAS_HASH)


def validate(data,reloc,report,module):
    mother = report.get('mother_letters') is True
    if 'mother_letters' in report and not mother: raise ValueError('Unknown system creator variant')
    departed = report.get('departed_letters') is True
    if 'departed_letters' in report and not departed: raise ValueError('Unknown departed creator variant')
    events = report.get('villager_events') is True
    if 'villager_events' in report and not events: raise ValueError('Unknown villager-event creator variant')
    academy = report.get('academy_letters') is True
    if 'academy_letters' in report and not academy: raise ValueError('Unknown academy creator variant')
    scores = report.get('academy_scores') is True
    if 'academy_scores' in report and not scores: raise ValueError('Unknown academy score creator variant')
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != len(data)
            or report.get('relocation_bytes') != len(reloc) or report.get('overlay_sha256') != sha256(data)
            or report.get('relocation_sha256') != sha256(reloc) or report.get('sources') != source_hashes(mother_letters=mother,departed_letters=departed,villager_events=events,academy_letters=academy,academy_scores=scores)
            or report.get('module_sha256') != module['module_sha256']
            or report.get('imports') != {name:int(module['symbols'][name],16) for name in creator_imports(villager_events=events,academy_scores=scores)}
            or report.get('word_sha256') != WORD_HASH or report.get('alias_sha256') != ALIAS_HASH):
        raise ValueError('Stale or changed NPC capture overlay')
    # Validate lengths before reading even the first relocation-header word.
    relocate(data,reloc,MODULE_RAM+RESERVATION,report['imports'].values())
    text = struct.unpack_from('>I',reloc)[0]
    symbols = report.get('symbols',{})
    required = {'af_mail_capture_reset','af_mail_capture_set','af_mail_generate','af_mail_source_digest',
                'af_npc_mail_sources_init','af_npc_mail_source_word','af_npc_mail_source_name',
                'af_npc_mail_source_alias','af_npc_mail_capture_event','af_npc_mail_create',
                'af_npc_word_data','af_npc_alias_data'}
    if mother: required.add('af_system_mail_create')
    if departed: required.add('af_departed_mail_create')
    if events: required.add('af_villager_event_mail_create')
    if academy: required.add('af_academy_mail_create')
    if scores: required.update(('af_academy_score_mail_create','af_academy_series_data'))
    if set(symbols) != required or any(type(at) is not int or at&3 or not 0 <= at < len(data) for at in symbols.values()):
        raise ValueError('Invalid NPC capture exports')
    if any(at >= text for name,at in symbols.items() if name not in ('af_npc_word_data','af_npc_alias_data','af_academy_series_data')):
        raise ValueError('NPC capture function points outside text')
    w,a = symbols['af_npc_word_data'],symbols['af_npc_alias_data']
    if w&15 or a&15 or not text <= w or a != w+11328 or a+6368 != len(data):
        raise ValueError('NPC capture resource offsets are invalid')
    verified_resources(data[w:a],data[a:])
    if scores:
        series = symbols['af_academy_series_data']
        if (series&15 or not text <= series or series+1440 != w or sha256(data[series:w]) != ACADEMY_SERIES_HASH
                or report.get('academy_series_sha256') != ACADEMY_SERIES_HASH):
            raise ValueError('Invalid complete academy series-name resource')


def relocate(data,reloc,base,imports):
    if (not 0 < len(data) <= 0x8000 or len(data)&15 or len(reloc) < 24 or len(reloc)&3
            or len(reloc) > 0x1000 or type(base) is not int or base&15
            or not MODULE_RAM+RESERVATION <= base <= 0x80400000-len(data)):
        raise ValueError('Invalid NPC capture relocation buffer')
    text,writable,rodata,bss,count = struct.unpack_from('>5I',reloc)
    if (text+rodata != len(data) or writable or bss or not text or text&15 or rodata&15
            or count > (len(reloc)-24)//4 or any(reloc[20+count*4:-4])
            or struct.unpack_from('>I',reloc,len(reloc)-4)[0] != len(reloc)):
        raise ValueError('Invalid NPC capture relocation sections')
    out,high,previous,jumps = bytearray(data),{},-1,set()
    for entry in struct.unpack_from('>'+str(count)+'I',reloc,20):
        section,kind,at = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section != 1 or at&3 or at <= previous or at+4 > text:
            raise ValueError('Invalid NPC capture relocation section/order')
        previous = at;word = struct.unpack_from('>I',data,at)[0]
        if kind == 4:
            target = 0x80000000|((word&0x3FFFFFF)<<2)
            if word>>26 not in (2,3) or not RAM <= target < RAM+text:
                raise ValueError('Invalid NPC capture internal jump')
            word = (word&0xFC000000)|(((base+target-RAM)&0xFFFFFFF)>>2)
            jumps.add(at)
        elif kind == 5:
            register = (word>>16)&31
            if word>>26 != 15 or register in high: raise ValueError('Invalid NPC capture high relocation')
            high[register] = at,word
            continue
        elif kind == 6:
            register = (word>>21)&31
            opcode = word>>26
            if opcode not in (9,49) or register not in high: raise ValueError('Invalid NPC capture low relocation')
            hi_at,hi_word = high.pop(register)
            target = ((hi_word&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            if not RAM <= target < RAM+len(data): raise ValueError('NPC capture data pointer escapes image')
            if opcode == 49 and (target&3 or not RAM+text <= target <= RAM+len(data)-4):
                raise ValueError('NPC capture floating constant is outside aligned read-only data')
            target += base-RAM
            struct.pack_into('>I',out,hi_at,(hi_word&0xFFFF0000)|(((target+32768)>>16)&65535))
            word = (word&0xFFFF0000)|(target&65535)
        else: raise ValueError('Unsupported NPC capture relocation type')
        struct.pack_into('>I',out,at,word)
    if high: raise ValueError('Unpaired NPC capture high relocation')
    seen = set()
    for at in range(0,text,4):
        word = struct.unpack_from('>I',data,at)[0]
        if word>>26 not in (2,3): continue
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        if RAM <= target < RAM+text: seen.add(at)
        elif target not in imports: raise ValueError('Unapproved NPC capture external jump')
    if seen != jumps: raise ValueError('Missing NPC capture jump relocation')
    return bytes(out)
