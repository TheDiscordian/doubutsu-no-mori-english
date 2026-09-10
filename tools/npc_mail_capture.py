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
IMAGE_BYTES_MAX = 0x10000
WORD_HASH = '698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1'
DESIGN_WORD_HASH = '3e06014a398b03a9ccac58fa8c9ac57ba3c5a5312e39167b288c314cc6dee4f9'
WORD_PROFILES = frozenset((WORD_HASH, DESIGN_WORD_HASH))
CAPTURE_SOURCE = 'overlays/mail_generation/npc_capture.c'
LEGACY_CAPTURE_SOURCE_HASH = '68d4bf2c1624ec1df86f4a779dd820243dbb833e0012cf8dee31af4791bd8180'
PROFILE_CAPTURE_SOURCE_HASH = '43208dfee76a7a811dab70b3dbd103b79033c8badfc3be3da3258801f4830169'
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


def creator_imports(*,villager_events=False,academy_scores=False,notice_treasure=False):
    return IMPORTS+(('af_load_item_name',) if villager_events else ())+(('af_format_year','af_format_month','af_format_day') if academy_scores else ())+(('af_crc32','af_mail_format','af_mail_record_unpack','af_item_name_index') if notice_treasure else ())


def source_hashes(*,mother_letters=False,departed_letters=False,villager_events=False,academy_letters=False,academy_scores=False,post_office=False,museum=False,shop_notices=False,quest_replies=False,notice_treasure=False,notice_owner=False,notice_seasonal=False):
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
    if post_office:
        if not academy_scores: raise ValueError('Post-office creator requires academy score dispatch')
        names += ['overlays/mail_generation/'+name for name in
                  ('post_office_creator.c','post_office_creator.h','post_office_capture.ld')]
    if museum:
        if not post_office: raise ValueError('Museum creator requires post-office dispatch')
        names += ['overlays/mail_generation/'+name for name in ('museum_creator.c','museum_creator.h','museum_capture.ld')]
    if shop_notices:
        if not museum: raise ValueError('Shop notice creator requires museum dispatch')
        names += ['overlays/mail_generation/'+name for name in ('shop_notice_creator.c','shop_notice_creator.h','shop_notice_capture.ld')]
    if quest_replies:
        if not shop_notices: raise ValueError('Quest reply creator requires shop notice dispatch')
        names += ['overlays/mail_generation/'+name for name in ('quest_reply_creator.c','quest_reply_creator.h','quest_reply_capture.ld')]
    if notice_treasure:
        if not quest_replies: raise ValueError('Treasure creator requires complete quest reply dispatch')
        names += ['overlays/mail_generation/'+name for name in
                  ('notice_treasure_creator.c','notice_treasure_creator.h','notice_treasure_capture.ld',
                   'item_article.c','item_article.h','item_article_sources.s')]
        names += ['tools/item_articles.py', 'translations/n64-item-articles.json']
        names += ['runtime/notice/'+name for name in ('record.c','record.h','initial.h','treasure.c','treasure.h')]
        names += ['runtime/crc32.h']
    if notice_owner:
        if not notice_treasure: raise ValueError('Treasure owner requires complete treasure text and articles')
        names += ['overlays/mail_generation/'+name for name in ('notice_owner.c','notice_owner.h','notice_owner_capture.ld')]
    if notice_seasonal:
        if not notice_owner: raise ValueError('Seasonal creator requires the complete treasure owner')
        names += ['overlays/mail_generation/'+name for name in
                  ('notice_seasonal_creator.c', 'notice_seasonal_creator.h', 'notice_seasonal_capture.ld')]
        names += ['runtime/notice/seasonal.c', 'runtime/notice/seasonal.h', 'tools/notice_seasonal.py']
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def verified_resources(words,aliases):
    digest = sha256(words)
    if digest not in WORD_PROFILES:
        raise ValueError('Unapproved complete NPC reply-word profile')
    unpack_words(words,digest)
    unpack_aliases(aliases,ALIAS_HASH)


def catalog_id(report):
    if 'mail_glyphs' in report and report['mail_glyphs'] is not True:
        raise ValueError('Unknown mail-glyph creator variant')
    return 4 if report.get('mail_glyphs') is True else 2


def source_report_matches(actual, expected, *, article_names=None, word_hash=None):
    versions = [expected]
    # The default-profile recompilation must reproduce the retained image.
    # Only this exact conditional-digest source change permits its predecessor;
    # future C edits do not inherit an exemption, nor does the corrected profile.
    if word_hash == WORD_HASH and expected.get(CAPTURE_SOURCE) == PROFILE_CAPTURE_SOURCE_HASH:
        versions.append({**expected, CAPTURE_SOURCE: LEGACY_CAPTURE_SOURCE_HASH})
    # Each retained immutable article profile also accepts its pinned original
    # generator provenance. Every compiled source and resource remains checked;
    # this does not let new name profiles claim the old generator.
    from item_articles import PROFILE_GENERATORS, PROFILE_ORIGINAL_ARTICLES
    if isinstance(article_names, str) and article_names in PROFILE_GENERATORS and 'tools/item_articles.py' in expected:
        versions += [{**version, 'tools/item_articles.py': PROFILE_GENERATORS[article_names],
                      'translations/n64-item-articles.json': PROFILE_ORIGINAL_ARTICLES[article_names]}
                     for version in tuple(versions)]
    return actual in versions


def word_guard_offset(data, symbols, text):
    """Resolve the digest actually passed to the initializer's full-word hash."""
    start = symbols['af_npc_mail_sources_init']
    end = min((at for at in symbols.values() if start < at < text), default=text)
    matches = []
    for at in range(start, end-19, 4):
        hi, lo, size, call, source = struct.unpack_from('>5I', data, at)
        if (hi >> 16 == 0x3C06 and lo >> 16 == 0x24C6 and size == 0x24052C40
                and call >> 26 == 3 and source == 0x02202025):
            target = ((hi & 65535) << 16)+(lo & 65535)-(65536 if lo & 32768 else 0)-RAM
            helper = (0x80000000 | ((call & 0x3FFFFFF) << 2))-RAM
            if not text <= target <= len(data)-32 or target & 3 or not 0 <= helper < text:
                raise ValueError('NPC word initializer has an invalid digest argument')
            matches.append(target)
    if len(matches) != 1:
        raise ValueError('NPC word initializer must bind one complete word digest')
    return matches[0]


def validate(data,reloc,report,module):
    if report.get('classic_letters') is not None:
        from classic_letter_profiles import validate as validate_classic
        old,oldrel,previous=validate_classic('creator',data,reloc,report)
        validate(old,oldrel,previous,module)
        return
    if report.get('accent_mail') is not None:
        from accent_mail_overlay_profile import validate as validate_accent
        old,oldrel,previous,_=validate_accent('creator',data,reloc,report)
        validate(old,oldrel,previous,module)
        return
    catalog = catalog_id(report)
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
    postal = report.get('post_office') is True
    if 'post_office' in report and not postal: raise ValueError('Unknown post-office creator variant')
    museum = report.get('museum') is True
    if 'museum' in report and not museum: raise ValueError('Unknown museum creator variant')
    shop = report.get('shop_notices') is True
    if 'shop_notices' in report and not shop: raise ValueError('Unknown shop notice creator variant')
    quest = report.get('quest_replies') is True
    if 'quest_replies' in report and not quest: raise ValueError('Unknown quest reply creator variant')
    treasure = report.get('notice_treasure') is True
    if 'notice_treasure' in report and not treasure: raise ValueError('Unknown notice treasure creator variant')
    if treasure and catalog != 4: raise ValueError('Treasure creation requires the complete glyph catalogue')
    owner = report.get('notice_owner') is True
    if 'notice_owner' in report and not owner: raise ValueError('Unknown treasure owner variant')
    seasonal = report.get('notice_seasonal') is True
    if 'notice_seasonal' in report and not seasonal: raise ValueError('Unknown seasonal creator variant')
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != len(data)
            or report.get('relocation_bytes') != len(reloc) or report.get('overlay_sha256') != sha256(data)
            or report.get('relocation_sha256') != sha256(reloc) or not source_report_matches(
                report.get('sources'), source_hashes(mother_letters=mother,departed_letters=departed,villager_events=events,academy_letters=academy,academy_scores=scores,post_office=postal,museum=museum,shop_notices=shop,quest_replies=quest,notice_treasure=treasure,notice_owner=owner,notice_seasonal=seasonal),
                article_names=report.get('item_names_sha256') if treasure else None,
                word_hash=report.get('word_sha256'))
            or report.get('module_sha256') != module['module_sha256']
            or report.get('imports') != {name:int(module['symbols'][name],16) for name in creator_imports(villager_events=events,academy_scores=scores,notice_treasure=treasure)}
            or not isinstance(report.get('word_sha256'), str)
            or report['word_sha256'] not in WORD_PROFILES or report.get('alias_sha256') != ALIAS_HASH):
        raise ValueError('Stale or changed NPC capture overlay')
    # Validate lengths before reading even the first relocation-header word.
    relocate(data,reloc,MODULE_RAM+RESERVATION,report['imports'].values())
    text = struct.unpack_from('>I',reloc)[0]
    symbols = report.get('symbols',{})
    required = {'af_mail_capture_reset','af_mail_capture_set','af_mail_generate','af_mail_source_digest',
                'af_npc_mail_sources_init','af_npc_mail_source_word','af_npc_mail_source_name',
                'af_npc_mail_source_alias','af_npc_mail_capture_event','af_npc_mail_create','af_mail_create_guard',
                'af_npc_word_data','af_npc_alias_data','af_npc_mail_catalog_id'}
    if mother: required.add('af_system_mail_create')
    if departed: required.add('af_departed_mail_create')
    if events: required.add('af_villager_event_mail_create')
    if academy: required.add('af_academy_mail_create')
    if scores: required.update(('af_academy_score_mail_create','af_academy_series_data'))
    if postal: required.add('af_post_office_mail_create')
    if museum: required.add('af_museum_mail_create')
    if shop: required.add('af_shop_notice_mail_create')
    if quest: required.add('af_quest_reply_mail_create')
    if treasure:
        required.update(('af_notice_treasure_create','af_notice_record_tagged','af_notice_record_pack',
                         'af_notice_record_expand','af_notice_treasure_mask','af_notice_treasure_valid',
                         'af_notice_treasure_pack','af_notice_treasure_decode_parts',
                         'af_notice_treasure_decode','af_notice_treasure_restore',
                         'af_notice_item_article','af_item_article_data'))
    if owner: required.add('af_notice_owner_create')
    if seasonal:
        required.update(('af_notice_seasonal_create', 'af_notice_seasonal_mask', 'af_notice_seasonal_valid',
                         'af_notice_seasonal_pack', 'af_notice_seasonal_shop', 'af_notice_seasonal_decode_parts',
                         'af_notice_seasonal_decode', 'af_notice_seasonal_restore',
                         'af_notice_seasonal_entries', 'af_notice_seasonal_data', 'af_notice_seasonal_shops'))
    if set(symbols) != required or any(type(at) is not int or at&3 or not 0 <= at < len(data) for at in symbols.values()):
        raise ValueError('Invalid NPC capture exports')
    if any(at >= text for name,at in symbols.items() if name not in ('af_npc_word_data','af_npc_alias_data','af_academy_series_data','af_npc_mail_catalog_id','af_item_article_data','af_notice_seasonal_entries','af_notice_seasonal_data','af_notice_seasonal_shops')):
        raise ValueError('NPC capture function points outside text')
    marker = symbols['af_npc_mail_catalog_id']
    if not text <= marker <= len(data)-4 or struct.unpack_from('>I',data,marker)[0] != catalog:
        raise ValueError('Creator catalogue approval differs from its compiled variant')
    w,a = symbols['af_npc_word_data'],symbols['af_npc_alias_data']
    if w&15 or a&15 or not text <= w or a != w+11328 or a+6368 != len(data):
        raise ValueError('NPC capture resource offsets are invalid')
    verified_resources(data[w:a],data[a:])
    if report['word_sha256'] != sha256(data[w:a]):
        raise ValueError('Declared NPC word profile does not match the embedded resource')
    guard = word_guard_offset(data, symbols, text)
    if data[guard:guard+32] != bytes.fromhex(report['word_sha256']):
        raise ValueError('Compiled NPC word initializer rejects its embedded resource')
    if scores:
        series = symbols['af_academy_series_data']
        if (series&15 or not text <= series or series+1440 != w or sha256(data[series:w]) != ACADEMY_SERIES_HASH
                or report.get('academy_series_sha256') != ACADEMY_SERIES_HASH):
            raise ValueError('Invalid complete academy series-name resource')
    if treasure:
        from item_articles import SIZE, DESIGN_NAMES_HASH, verify
        article = symbols['af_item_article_data']
        if (article&15 or article < text or article+SIZE != symbols['af_academy_series_data']
                or report.get('item_articles_sha256') != sha256(data[article:article+SIZE])
                or report.get('item_names_sha256') != verify(data[article:article+SIZE])):
            raise ValueError('Invalid complete item article resource')
        verify(data[article:article+SIZE])
        if report['item_names_sha256'] == DESIGN_NAMES_HASH and report['word_sha256'] != DESIGN_WORD_HASH:
            raise ValueError('Native design item names require the corrected herabuna NPC word profile')
    if seasonal:
        from notice_seasonal import compiled_resource
        resource = compiled_resource((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                     (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        for name, payload in (('entries', resource['table']), ('data', resource['data']),
                              ('shops', b''.join(resource['shops']))):
            at = symbols['af_notice_seasonal_'+name]
            if (at & 15 or not text <= at <= len(data)-len(payload) or data[at:at+len(payload)] != payload
                    or report.get('seasonal_'+name+'_sha256') != sha256(payload)):
                raise ValueError('Changed approved compiled seasonal '+name)
        if report.get('seasonal_header_sha256') != sha256(resource['header'].encode()):
            raise ValueError('Changed compiled seasonal text profile')


def relocate(data,reloc,base,imports):
    if (not 0 < len(data) <= IMAGE_BYTES_MAX or len(data)&15 or len(reloc) < 24 or len(reloc)&3
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
