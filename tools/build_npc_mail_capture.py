#!/usr/bin/env python3
"""Build complete source capture and generation in a relocatable native overlay."""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from npc_mail_capture import RAM,IMAGE_BYTES_MAX,source_hashes,creator_imports,relocate,verified_resources
from runtime_layout import MODULE_RAM,LINKED_LIMIT


def build(module,words,aliases,out,*,mother_letters=False,departed_letters=False,villager_events=False,academy_letters=False,academy_scores=False,mail_glyphs=False,post_office=False,museum=False,shop_notices=False,quest_replies=False,notice_treasure=False,item_articles=None,notice_owner=False,notice_seasonal=False):
    if type(mail_glyphs) is not bool: raise ValueError('Invalid mail-glyph creator option')
    if type(post_office) is not bool: raise ValueError('Invalid post-office creator option')
    if type(museum) is not bool: raise ValueError('Invalid museum creator option')
    if type(shop_notices) is not bool: raise ValueError('Invalid shop notice creator option')
    if type(quest_replies) is not bool: raise ValueError('Invalid quest reply creator option')
    if type(notice_treasure) is not bool or (notice_treasure and not mail_glyphs):
        raise ValueError('Treasure creation requires the complete glyph catalogue')
    if type(notice_owner) is not bool or (notice_owner and not notice_treasure):
        raise ValueError('Treasure ownership requires complete treasure creation')
    if type(notice_seasonal) is not bool or (notice_seasonal and not notice_owner):
        raise ValueError('Seasonal creation requires the complete treasure owner')
    root = Path(__file__).resolve().parents[1]
    verified_resources(words,aliases)
    variants = dict(mother_letters=mother_letters,departed_letters=departed_letters,villager_events=villager_events,academy_letters=academy_letters,academy_scores=academy_scores,post_office=post_office,museum=museum,shop_notices=shop_notices,quest_replies=quest_replies,notice_treasure=notice_treasure,notice_owner=notice_owner,notice_seasonal=notice_seasonal)
    sources = source_hashes(**variants);out.mkdir(parents=True,exist_ok=True)
    if notice_seasonal:
        from notice_seasonal import compiled_resource
        seasonal_resource = compiled_resource((root/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                               (root/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        (out/'seasonal_data.h').write_text(seasonal_resource['header'])
    (out/'words.bin').write_bytes(words);(out/'aliases.bin').write_bytes(aliases)
    if notice_treasure:
        from item_articles import verify as verify_articles
        if item_articles is None: raise ValueError('Treasure creator requires approved item articles')
        verify_articles(item_articles)
        (out/'articles.bin').write_bytes(item_articles)
    elif item_articles is not None:
        raise ValueError('Item articles require treasure creation')
    if academy_scores:
        from academy_score_letters import references,series_resource
        from npc_mail_capture import ACADEMY_SERIES_HASH
        series = series_resource(references((root/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                            (root/'build/mail-catalog/catalog.bin').read_bytes()))
        if sha256(series) != ACADEMY_SERIES_HASH: raise ValueError('Changed academy series resource')
        (out/'academy-series.bin').write_bytes(series)
    fado = root/'upstream/af/tools/fado'
    fado_sources = sorted((fado/'src').glob('*.c'))+[fado/'lib/fairy/fairy.c',fado/'lib/fairy/fairy_print.c',fado/'lib/vc_vector/vc_vector.c']
    fado_inputs = sorted(set(fado_sources)|set((fado/'include').rglob('*.h'))|set((fado/'lib').rglob('*.h'))
                         |{fado/'src/version.inc',fado/'lib/fairy/fairy_data.inc'})
    fado_hashes = {p.relative_to(fado).as_posix():sha256(p.read_bytes()) for p in fado_inputs}
    subprocess.run(['gcc','-std=c11','-O2','-I'+str(fado/'include'),'-I'+str(fado/'lib'),
                    *(str(p) for p in fado_sources),'-o',str(out/'fado')],check=True,capture_output=True,timeout=60)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'NPC capture {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    imports = {name:int(module['symbols'][name],16) for name in creator_imports(villager_events=villager_events,academy_scores=academy_scores,notice_treasure=notice_treasure)}
    if any(value&3 or not MODULE_RAM+0x300 <= value < MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT)
           for value in imports.values()): raise ValueError('NPC capture imports are outside resident code')
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    if mail_glyphs: flags.append('-DAF_MAIL_CREATOR_CATALOG=4')
    if notice_seasonal: flags.append('-I/out')
    names = ('digest','npc_capture','generate','npc_creator')+(('mother_creator',) if mother_letters else ())
    if departed_letters: names += ('departed_creator',)
    if villager_events: names += ('villager_event_creator',)
    if academy_letters: names += ('academy_creator',)
    if academy_scores: names += ('academy_score_creator',)
    if post_office: names += ('post_office_creator',)
    if museum: names += ('museum_creator',)
    if shop_notices: names += ('shop_notice_creator',)
    if quest_replies: names += ('quest_reply_creator',)
    if notice_treasure: names += ('notice_treasure_creator',)
    if notice_owner: names += ('notice_owner',)
    if notice_seasonal: names += ('notice_seasonal_creator',)
    for name in names:
        run('gcc',*flags,'/source/overlays/mail_generation/'+name+'.c','-o',name+'.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','sources.o','/source/overlays/mail_generation/sources.s')
    objects = [name+'.o' for name in names]+['sources.o']
    if notice_treasure:
        for name in ('record', 'treasure'):
            run('gcc', *flags, '/source/runtime/notice/'+name+'.c', '-o', 'notice_'+name+'.o')
        # Fado emits records in object order; retain the linker's text order.
        run('gcc', *flags, '/source/overlays/mail_generation/item_article.c', '-o', 'item_article.o')
        run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','item_article_sources.o',
            '/source/overlays/mail_generation/item_article_sources.s')
        at = objects.index('notice_treasure_creator.o')
        objects[at:at] = ['notice_record.o', 'notice_treasure.o', 'item_article.o']
        objects.append('item_article_sources.o')
    if notice_seasonal:
        run('gcc', *flags, '/source/runtime/notice/seasonal.c', '-o', 'notice_seasonal.o')
        objects.insert(objects.index('notice_seasonal_creator.o'), 'notice_seasonal.o')
    if academy_scores:
        run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','academy_score_sources.o',
            '/source/overlays/mail_generation/academy_score_sources.s')
        objects.append('academy_score_sources.o')
    result = subprocess.run([str(out/'fado'),*objects,'-n','af_npc_capture','-o','relocation.s'],
                            cwd=out,capture_output=True,text=True,timeout=60)
    (out/'fado.log').write_text(result.stdout+result.stderr)
    if result.returncode: raise ValueError(result.stdout+result.stderr)
    run('as','-EB','-mabi=32','-march=vr4300','-o','relocation.o','relocation.s')
    linker = 'system_capture.ld' if mother_letters else 'capture.ld'
    if departed_letters: linker = 'departed_capture.ld'
    if villager_events: linker = 'villager_event_capture.ld'
    if academy_letters: linker = 'academy_capture.ld'
    if academy_scores: linker = 'academy_score_capture.ld'
    if post_office: linker = 'post_office_capture.ld'
    if museum: linker = 'museum_capture.ld'
    if shop_notices: linker = 'shop_notice_capture.ld'
    if quest_replies: linker = 'quest_reply_capture.ld'
    if notice_treasure: linker = 'notice_treasure_capture.ld'
    if notice_owner: linker = 'notice_owner_capture.ld'
    if notice_seasonal: linker = 'notice_seasonal_capture.ld'
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/'+linker,'-Map=overlay.map',
        f'--defsym=AF_CREATOR_IMAGE_MAX={IMAGE_BYTES_MAX}',
        *(f'--defsym={name}=0x{value:08X}' for name,value in imports.items()),
        '-o','overlay.elf',*objects,'relocation.o')
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Undefined NPC capture symbol')
    run('objcopy','-O','binary','-j','.text','-j','.data','-j','.rodata','overlay.elf','overlay.bin')
    run('objcopy','-O','binary','--set-section-flags','.ovl=alloc,load,readonly,data,contents',
        '-j','.ovl','overlay.elf','relocation.bin')
    data,reloc = (out/'overlay.bin').read_bytes(),(out/'relocation.bin').read_bytes()
    # Independently compare Fado's inventory with the linked ELF's internal
    # relocations. Missing complete HI/LO pairs must not escape jump-only checks.
    elf_relocs = run('readelf','-rW','overlay.elf')
    expected_relocs = []
    for line in elf_relocs.splitlines():
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: continue
        at,kind,target,name = int(match[1],16),match[2],int(match[3],16),match[4]
        if RAM <= target < RAM+len(data):
            expected_relocs.append(0x40000000|({'26':4,'HI16':5,'LO16':6}[kind]<<24)|(at-RAM))
        elif name not in imports or target != imports[name] or kind != '26':
            raise ValueError('Unapproved ELF NPC capture import')
    count = struct.unpack_from('>I',reloc,16)[0]
    if tuple(expected_relocs) != struct.unpack_from('>'+str(count)+'I',reloc,20):
        raise ValueError('Native NPC capture relocation inventory differs from linked ELF')
    for base in (0x801A0000,0x802F8010,0x80400000-len(data)):
        relocate(data,reloc,base,imports.values())
    symbols = {}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0],16)
    if symbols['__capture_start'] != RAM or symbols['__capture_end'] != RAM+len(data):
        raise ValueError('NPC capture linked image bounds disagree')
    for symbol,resource in (('af_npc_word_data',words),('af_npc_alias_data',aliases)):
        at = symbols[symbol]-RAM
        if data[at:at+len(resource)] != resource: raise ValueError('Linked NPC capture resource differs')
    if source_hashes(**variants) != sources or fado_hashes != {p.relative_to(fado).as_posix():sha256(p.read_bytes()) for p in fado_inputs}:
        raise ValueError('NPC capture source changed during compilation')
    report = {'version':1,'ram':RAM,'bytes':len(data),'relocation_bytes':len(reloc),
              'overlay_sha256':sha256(data),'relocation_sha256':sha256(reloc),
              'sources':sources,'module_sha256':module['module_sha256'],'imports':imports,
              'word_sha256':sha256(words),'alias_sha256':sha256(aliases),
              'symbols':{name:value-RAM for name,value in symbols.items() if name.startswith('af_') and RAM <= value < RAM+len(data)},
              'compiler':run('gcc','--version').splitlines()[0],'flags':flags,'toolchain_image':IMAGE,
              'stack_usage':{name:(out/(name+'.su')).read_text() for name in names},
              'fado_sources':fado_hashes,'status':'Complete capture/generation code; gameplay publication not installed'}
    if mother_letters: report['mother_letters'] = True
    if mail_glyphs: report['mail_glyphs'] = True
    if departed_letters: report['departed_letters'] = True
    if villager_events: report['villager_events'] = True
    if academy_letters: report['academy_letters'] = True
    if post_office: report['post_office'] = True
    if museum: report['museum'] = True
    if shop_notices: report['shop_notices'] = True
    if quest_replies: report['quest_replies'] = True
    if notice_owner: report['notice_owner'] = True
    if notice_seasonal:
        report['notice_seasonal'] = True
        for name, payload in (('entries', seasonal_resource['table']), ('data', seasonal_resource['data']),
                              ('shops', b''.join(seasonal_resource['shops']))):
            report['seasonal_'+name+'_sha256'] = sha256(payload)
        report['seasonal_header_sha256'] = sha256(seasonal_resource['header'].encode())
        report['stack_usage']['notice_seasonal'] = (out/'notice_seasonal.su').read_text()
    if notice_treasure:
        report['notice_treasure'] = True
        from item_articles import DATA_HASH, NAMES_HASH
        report['item_articles_sha256'] = DATA_HASH
        report['item_names_sha256'] = NAMES_HASH
        report['stack_usage']['item_article'] = (out/'item_article.su').read_text()
        for name in ('record', 'treasure'):
            report['stack_usage']['notice_'+name] = (out/('notice_'+name+'.su')).read_text()
    if academy_scores:
        report['academy_scores'] = True;report['academy_series_sha256'] = sha256(series)
        at = symbols['af_academy_series_data']-RAM
        if data[at:at+len(series)] != series: raise ValueError('Linked academy series resource differs')
    from npc_mail_capture import validate
    validate(data,reloc,report,module)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    (out/'elf-relocations.txt').write_text(elf_relocs)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--words',type=Path,default=Path('build/npc-mail-words/words.bin'))
    parser.add_argument('--aliases',type=Path,default=Path('build/npc-mail-names/aliases.bin'))
    parser.add_argument('--output',type=Path,default=Path('build/npc-mail-capture'))
    parser.add_argument('--mother-letters',action='store_true',help='Add complete Mom-letter dispatch without changing the resident loader')
    parser.add_argument('--departed-letters',action='store_true',help='Add complete departed-villager letters; requires --mother-letters')
    parser.add_argument('--villager-events',action='store_true',help='Add complete villager-event letters; requires --departed-letters')
    parser.add_argument('--academy-letters',action='store_true',help='Add complete HRA welcome/advice letters; requires --villager-events')
    parser.add_argument('--academy-scores',action='store_true',help='Add complete HRA score capture; requires --academy-letters')
    parser.add_argument('--post-office',action='store_true',help='Add complete catalogue-order and raffle-ticket letters; requires --academy-scores')
    parser.add_argument('--museum',action='store_true',help='Add complete museum notices and fossil letters; requires --post-office')
    parser.add_argument('--shop-notices',action='store_true',help='Add complete spotlight/reopening notices; requires --museum')
    parser.add_argument('--quest-replies',action='store_true',help='Add complete letter-quest replies; requires --shop-notices')
    parser.add_argument('--notice-treasure',action='store_true',help='Add complete treasure post creation; requires --quest-replies and --mail-glyphs')
    parser.add_argument('--item-articles',type=Path,help='Approved articles.bin; required with --notice-treasure')
    parser.add_argument('--notice-owner',action='store_true',help='Add transactional treasure owner; requires --notice-treasure')
    parser.add_argument('--notice-seasonal', action='store_true', help='Add complete seasonal capture; requires --notice-owner')
    parser.add_argument('--mail-glyphs',action='store_true',help='Create new letters with complete glyph catalogue four')
    args = parser.parse_args()
    if args.departed_letters and not args.mother_letters: parser.error('--departed-letters requires --mother-letters')
    if args.villager_events and not args.departed_letters: parser.error('--villager-events requires --departed-letters')
    if args.academy_letters and not args.villager_events: parser.error('--academy-letters requires --villager-events')
    if args.academy_scores and not args.academy_letters: parser.error('--academy-scores requires --academy-letters')
    if args.post_office and not args.academy_scores: parser.error('--post-office requires --academy-scores')
    if args.museum and not args.post_office: parser.error('--museum requires --post-office')
    if args.shop_notices and not args.museum: parser.error('--shop-notices requires --museum')
    if args.quest_replies and not args.shop_notices: parser.error('--quest-replies requires --shop-notices')
    if args.notice_treasure and not (args.quest_replies and args.mail_glyphs):
        parser.error('--notice-treasure requires --quest-replies and --mail-glyphs')
    if args.notice_treasure != bool(args.item_articles):
        parser.error('--notice-treasure and --item-articles must be supplied together')
    if args.notice_owner and not args.notice_treasure: parser.error('--notice-owner requires --notice-treasure')
    if args.notice_seasonal and not args.notice_owner: parser.error('--notice-seasonal requires --notice-owner')
    print(json.dumps(build(json.loads(args.module.read_text()),args.words.read_bytes(),args.aliases.read_bytes(),args.output.resolve(),
                           mother_letters=args.mother_letters,departed_letters=args.departed_letters,
                           villager_events=args.villager_events,academy_letters=args.academy_letters,
                           academy_scores=args.academy_scores,mail_glyphs=args.mail_glyphs,post_office=args.post_office,museum=args.museum,shop_notices=args.shop_notices,quest_replies=args.quest_replies,notice_treasure=args.notice_treasure,
                           item_articles=args.item_articles.read_bytes() if args.item_articles else None,
                           notice_owner=args.notice_owner,notice_seasonal=args.notice_seasonal),indent=2))


if __name__ == '__main__': main()
