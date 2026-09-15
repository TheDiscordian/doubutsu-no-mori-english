"""Read/check the single text-source catalogue, or seed it from local evidence.

Seeding is a one-time migration and refuses to overwrite an existing catalogue.
Queries are views, never a second maintained review list. Nintendo text remains
in local inputs; the catalogue stores locators/hashes, not an extracted script.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, verified_rom
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT/'translations/provenance.json'
ROM = ROOT/'build/v3-official-credits-01/animal-forest-v3-asset-loader.z64'
ROM_SHA = 'dfac082b4a900711aedf19b2e0cc869ee8622e1eb110e04be66591a448ea1d4e'
KINDS = {'official', 'fan', 'human', 'assistant', 'original', 'unresolved', 'blank'}
CREDITS = {
    'official': 'Nintendo — Animal Crossing English localization team; individual line author unspecified',
    'fan': 'AFProjectDistro contributors; individual line author unspecified',
    'human': 'Project human translation — named contributors on the locale entry',
    'assistant': 'OpenAI coding assistant — project-authored English; human translation source not recorded',
    'original': 'Nintendo — original Japanese N64 game',
    'blank': 'Nintendo — preserved empty or padding-only record',
    'unresolved': 'Unresolved — do not infer authorship from matching wording',
}


def classify(edit):
    provenance = edit.get('provenance', '')
    source = provenance.get('source', '') if isinstance(provenance,dict) else provenance
    if source == 'user-supplied GAFE01 revision 0 disc': return 'official'
    if edit.get('status') == 'intentional_blank': return 'blank'
    if ('original translation' in source.lower() or 'project-authored' in source.lower()
            or 'original english translation' in source.lower()
            or 'native_name' in edit and 'evidence' in edit
            or edit.get('status') in ('draft','original_translation','source_reviewed_original_translation')):
        return 'assistant'
    return 'unresolved'


def validate(catalogue):
    if (catalogue.get('schema') != 1 or not isinstance(catalogue.get('credits'),dict)
            or set(catalogue['credits']) != KINDS
            or any(not isinstance(v,str) or not v.strip() for v in catalogue['credits'].values())):
        raise ValueError('Unknown text-provenance schema or credits')
    seen = set()
    for row in catalogue['entries']:
        identity = row['id']
        if identity in seen: raise ValueError('Duplicate text identity: '+identity)
        seen.add(identity)
        if not row.get('locales'): raise ValueError('Missing locale: '+identity)
        for locale, text in row['locales'].items():
            if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*', locale):
                raise ValueError('Invalid language tag')
            if text.get('credit') not in KINDS or not text.get('locator'):
                raise ValueError('Missing credit or edit locator: '+identity)
            if not re.fullmatch('[0-9a-f]{64}', text.get('encoded_sha256','')):
                raise ValueError('Missing output identity: '+identity)
            if text['credit'] == 'official' and not text.get('source'):
                raise ValueError('Official credit requires its actual reference: '+identity)
            if text['credit'] == 'human' and not text.get('contributors'):
                raise ValueError('Human translation requires named contributors: '+identity)
            if text.get('human_review') == 'approved' and not text.get('reviewer'):
                raise ValueError('Human review requires an identified reviewer')
    return dict(Counter(row['locales']['en']['credit'] for row in catalogue['entries']))


def seed():
    inputs = {}
    def read(path):
        raw = (ROOT/path).read_bytes(); inputs[str(path)] = sha256(raw); return raw
    native = verified_rom(read('local/rom/Doubutsu no Mori (Japan).z64'))
    image = read(str(ROM.relative_to(ROOT)))
    if sha256(image) != ROM_SHA: raise ValueError('Changed catalogue inspection cartridge')
    info = module_command_info(native); files = by_vrom(image)
    original = {b.name:b for b in banks(native)}
    candidates = json.loads(read('build/gyroid-default-candidates/translations.json'))
    if inputs['build/gyroid-default-candidates/translations.json'] != 'eb2e0a256e0286541cfe51368c50a34c754e7ba583a83d80d71fef634d65b351':
        raise ValueError('Changed complete candidate provenance evidence')
    # Build receipts retain authoritative identities. Later names/labels only
    # replace a candidate below when their actual installed bytes match.
    for path in ('build/design-items-resource/names.json','build/display-names/names.json',
                 'build/catchphrases/catchphrases.json'):
        report = json.loads(read(path)); candidates += report['edits']
    locators = defaultdict(list)
    for path in sorted((ROOT/'translations').glob('*.json')):
        if path == CATALOGUE: continue
        obj = json.loads(read(str(path.relative_to(ROOT))))
        if not isinstance(obj,list): continue
        for row in obj:
            if isinstance(row,dict) and 'id' in row and 'translation' in row:
                locators[(row['id'],row['translation'])].append(str(path.relative_to(ROOT)))
                candidates.append(row)
    refs = {r['id']:r for r in map(json.loads,read('build/gamecube/text/string.jsonl').decode().splitlines())}
    inventory = {r['id']:r for r in map(json.loads,read('build/inventory/string.jsonl').decode().splitlines())}
    import credits_strings
    candidates += list(credits_strings.candidates(native,refs,inventory,info).values())
    import reserve_strings, residual_general, reserve_letters, apology_targets
    candidates += reserve_strings.with_candidates(native,[])
    candidates += apology_targets.with_candidates(native,[])
    for n,value in residual_general.reference(native).items():
        candidates.append(dict(id=f'string:{n:04X}',translation=value.decode('ascii'),
            source_sha256=sha256(original['string'].entries()[n]),
            provenance=dict(source='user-supplied GAFE01 revision 0 disc',
                reference_id=f'string:{n:04X}',reference_sha256=refs[f'string:{n:04X}']['sha256'])))
    for name,value in reserve_letters.values(native).items():
        for n in reserve_letters.TEMPLATES:
            candidates.append(dict(id=f'{name}:{n:04X}',translation=decode(value,info),
                source_sha256=sha256(original[name].entries()[n]),
                status='draft' if name=='mail' else 'mechanically_validated_candidate_not_reviewed',
                provenance=dict(source='original translation of the Japanese N64 record' if name=='mail'
                    else 'user-supplied GAFE01 revision 0 disc',reference_id=f'{name}:{n:04X}',
                    adaptation='native line breaks retained')))
    by_id, aliases = defaultdict(list), defaultdict(list)
    for edit in candidates:
        try: data = encode(edit['translation'],info,extended_glyphs=edit['id'].startswith('message:') or edit['id'] in apology_targets.TARGETS).rstrip(b' ')
        except ValueError: continue
        by_id[edit['id']].append((edit,data))
        aliases[(edit.get('source_sha256'),data)].append(edit)
    entries = {}
    def add(identity, current, source=None, edits=None, locator=None):
        if identity in entries: raise ValueError('Duplicate imported identity: '+identity)
        native_hash = sha256(source) if source is not None else None
        matches = [e for e,data in by_id[identity] if data == current.rstrip(b' ') and
                   (source is None or e.get('source_sha256') == native_hash)] if edits is None else edits
        if not matches and source is not None:
            matches = aliases.get((native_hash,current.rstrip(b' ')),[])
        edit = matches[-1] if matches else None
        if edit:
            kind = classify(edit); provenance = edit.get('provenance')
            location = locators.get((edit['id'],edit['translation']), [])
            if not location:
                if identity.startswith('string:') and int(identity.split(':')[1],16) in range(credits_strings.FIRST,credits_strings.END):
                    location = ['tools/credits_strings.py']
                elif 'development label' in str(provenance): location = ['tools/placeholder_text.py']
                elif 'sapling counter' in str(provenance): location = ['tools/shop_units.py']
                elif identity in reserve_strings.IDS: location = ['tools/reserve_strings.py']
                elif identity in apology_targets.TARGETS: location = ['tools/apology_targets.py']
                elif identity.split(':')[0] in reserve_letters.LINES and int(identity.split(':')[1],16) in reserve_letters.TEMPLATES:
                    location = ['tools/reserve_letters.py']
                elif edit.get('native_item_name'): location = ['translations/n64-item-names.json','translations/n64-design-item-names.json']
                else: location = [locator or 'tools/reference_candidates.py']
            value = dict(credit=kind, locator=location, source=provenance or edit.get('evidence'),
                         evidence_id=edit['id'], human_review='not_recorded')
            if kind == 'assistant': value['text'] = edit['translation']
            if edit.get('adaptations'): value['adaptations'] = edit['adaptations']
        elif not current.strip(b' '): value = dict(credit='blank', locator=[locator or identity])
        elif source is not None and current.rstrip(b' ') == source.rstrip(b' '):
            value = dict(credit='original', locator=[locator or identity])
        else: value = dict(credit='unresolved', locator=[locator or identity],human_review='needed')
        value['encoded_sha256'] = sha256(current)
        entries[identity] = dict(id=identity,native_sha256=native_hash,locales={'en':value})
        return entries[identity]
    from translation_progress import installed_entries
    moved = {0xBD4000:0x01FA0000,0xD05000:0x025F0000,0xD16000:0x02600000}
    for bank in original.values():
        actual = installed_entries(bank,lambda v:files[v].extract(image),moved)
        for n,source in enumerate(bank.entries()):
            identity = f'{bank.name}:{n:04X}'
            add(identity,actual[n],source,locator=f'N64/{bank.name}/{n:04X}')
    # Replace the editable full-name route, retaining the shorter native backing
    # identity as the same logical text rather than crediting its old contents.
    from extended_items import COUNTS
    data = files[0x02A00000].extract(image); offset = 32
    for group,count in zip((*range(0x20,0x30),0x10),COUNTS):
        bank = original[f'item_{group:02X}']
        for n,source in enumerate(bank.entries()[:count]):
            identity = f'{bank.name}:{n:04X}'; entries.pop(identity)
            add(identity,data[offset:offset+16],source,locator='tools/extended_items.py')
            offset += 16
    import accent_items
    for identity,root in {**{k:k for k in accent_items.ROWS},**accent_items.ALIASES}.items():
        text,symbol,index,source_hash,donor_hash = accent_items.ROWS[root]
        value = accent_items.encoded(text)
        if entries[identity]['locales']['en']['encoded_sha256'] != sha256(value):
            raise ValueError('Changed installed accented name')
        entries[identity]['locales']['en'].update(credit='official',locator=['tools/accent_items.py'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',symbol=symbol,index=index,
                        reference_sha256=donor_hash),human_review='not_recorded')
    from display_names import special_table
    data = files[0x02C00000].extract(image)
    name_ids = [(f'npc_names:{n:04X}',original['npc_names'].entries()[n]) for n in range(216)]
    name_ids += [(f'special_names:{actor:04X}',original['string'].entries()[n]) for actor,_,n,_ in special_table(native)]
    for n,(identity,source) in enumerate(name_ids):
        entries.pop(identity,None); add(identity,data[32+n*8:40+n*8],source,locator='tools/display_names.py')
    from catchphrases import native_table
    defaults = native_table(native); data = files[0x02E00000].extract(image)
    for at in range(32,len(data),16):
        n = int.from_bytes(data[at+4:at+6],'big')-0xE000
        add(f'catchphrases:{n:04X}',data[at+6:at+16],original['string'].entries()[defaults[n][1]],
            locator='tools/catchphrases.py')
    # The full mail catalogue is its own logical source namespace: donor indices
    # are not assumed to identify the same native letter just because they match.
    from mail_reference import load_reference
    from mail_catalog import parse, verify_registered
    donor,mail_report = load_reference(ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data',
        ROOT/'local/ac-decomp', ROOT/'build/gamecube/files/foresta.rel.szs.decoded',extended_glyphs=True)
    data = files[0x030A0000].extract(image); verify_registered(data); _,parts = parse(data)
    for bank,rows in parts.items():
        for n,current in enumerate(rows):
            if current is None: continue
            identity = f'GAFE01-r0/{bank}:{n:04X}'
            edits = []
            if donor[bank][n] == current:
                edits = [dict(id=identity,provenance=dict(source='user-supplied GAFE01 revision 0 disc',
                    reference_id=f'{bank}:{n:04X}',resource='forest_1st.arc/data/'+bank+'_data.bin'),
                    translation='',status='mechanically_validated_candidate_not_reviewed')]
            add(identity,current,edits=edits,locator='tools/mail_reference.py')
    # Additive V3 message IDs have explicit mappings, never guessed offsets.
    report = json.loads(read('build/v3-official-credits-01/build.json'))
    from textbanks import Bank
    for kind,vrom,table_vrom in (('message',0x01FA0000,0xCF9000),('select',0x025F0000,0xD06000)):
        actual = Bank(kind,0,0,files[vrom].extract(image),files[table_vrom].extract(image)).entries()
        key = 'messages' if kind=='message' else 'choices'
        for row in report['camper_text'][key]:
            value = actual[row['id']]
            if sha256(value) != row['encoded_sha256']:
                raise ValueError('Changed installed summer text')
            identity = f'{kind}:{row["id"]:04X}'
            add(identity,value,edits=[dict(id=identity,translation='',
                provenance=dict(source='user-supplied GAFE01 revision 0 disc',
                    reference_id=f'{kind}:{row["donor_id"]:04X}',reference_sha256=row['source_sha256']))],
                locator='tools/v3_camper_text.py')
    # Twenty full names and phrases are embedded in fixed 32-byte metadata
    # records. Their six-byte save aliases are not distinct translations.
    blob = files[0x02200000].extract(image)
    for row in report['villager_text']['imports']:
        at = 0x2C00+(int(row['actor_id'],16)-0xE0DA)*32
        record = blob[at:at+32]
        if sha256(record) != row['record_sha256']: raise ValueError('Changed imported villager text record')
        for field,start,end,source_key in (('name',8,16,'donor_name_sha256'),
                                           ('catchphrase',16,26,'donor_phrase_sha256')):
            value = record[start:end]
            if value.rstrip(b' ') != row[field].encode('ascii'):
                raise ValueError('Imported villager text does not match installed bytes')
            identity = row['id']+'/'+field
            add(identity,value,edits=[dict(id=identity,translation='',
                provenance=dict(source='user-supplied GAFE01 revision 0 disc',
                    reference_id=identity,reference_sha256=row[source_key],
                    binding='tools/v3_villager_text.py metadata()'))],locator='tools/v3_villager_text.py')
    # Actual embedded editor confirmations, with donor offsets as well as IDs.
    import editor_confirmation
    from title_assets import DATA_BASE
    rel = read('build/gamecube/files/foresta.rel.szs.decoded')
    for n,(offset,old_length,capacity,donor_offset,value) in enumerate(editor_confirmation.ROWS):
        if (files[editor_confirmation.VROM].extract(image)[offset:offset+len(value)] != value
                or rel[DATA_BASE+donor_offset:DATA_BASE+donor_offset+len(value)] != value):
            raise ValueError('Changed actual editor confirmation text')
        identity = f'ui/editor-confirmation/{n}'
        add(identity,value,edits=[dict(id=identity,translation='',
            provenance=dict(source='user-supplied GAFE01 revision 0 disc',
                reference_resource='foresta.rel',data_offset=f'{donor_offset:08X}',reference_sha256=sha256(value)))],
            locator='tools/editor_confirmation.py#ROWS')
    import embedded_warnings as warnings
    symbols = read('local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    warnings.reference(rel,symbols)
    reference_lines = {text:offset for offset,text in warnings.GC_STRINGS}
    for owner in warnings.OWNERS:
        source,_ = warnings.source(native,owner)
        current = files[owner.new_vrom].extract(image)
        texts = warnings.WARNING_TEXT if owner==warnings.WARNING else warnings.PAK_TEXT
        for group,(_,_,lines) in enumerate(warnings.line_groups(source,owner)):
            for line,(at,x,y,pointer,length) in enumerate(lines):
                target,size = struct.unpack_from('>II',current,at+8)
                value = current[target-owner.ram:target-owner.ram+size]
                text = texts[group][line]
                if value != encode(text,info): raise ValueError('Changed embedded warning line')
                identity = f'ui/{owner.name}/{group}/{line}'
                provenance = dict(source='original translation of the Japanese N64 record',
                    native_address=f'{pointer:08X}',adaptation='N64 restrictions and Controller Pak retained')
                if text in reference_lines:
                    provenance = dict(source='user-supplied GAFE01 revision 0 disc',
                        reference_resource='foresta.rel',data_offset=f'{reference_lines[text]:08X}',
                        reference_sha256=sha256(value))
                add(identity,value,source[pointer-owner.ram:pointer-owner.ram+length],
                    edits=[dict(id=identity,translation=text,provenance=provenance)],
                    locator='tools/embedded_warnings.py#'+('WARNING_TEXT' if owner==warnings.WARNING else 'PAK_TEXT'))
    from gc_names import symbol_data
    names = symbol_data(rel,symbols.decode(),'ftrName2_table')
    imports = report['furniture_items']['imports']
    for row in imports:
        item = int(row['item_id'],16); slot = (item-0x3000)//4
        at = 0x225000+slot*32
        value = blob[at+8:at+24]
        donor_name = names[slot*16:slot*16+16]
        if (value != donor_name or value.rstrip(b' ') != row['name'].encode()
                or sha256(donor_name) != row.get('donor_name_sha256',sha256(donor_name))):
            raise ValueError('Changed imported furniture name')
        identity = f'GAFE01-r0/item/{item:04X}/name'
        add(identity,value,edits=[dict(id=identity,translation='',
            provenance=dict(source='user-supplied GAFE01 revision 0 disc',symbol='ftrName2_table',
                index=slot,reference_sha256=sha256(donor_name)))],locator='tools/v3_furniture_items.py')
    speed = report['speed_bag']; item = int(speed['item_id'],16); slot = (item-0x3000)//4
    at = int(speed['metadata_ram'],16)-0x80460000
    value = blob[at+8:at+24]; donor_name = names[slot*16:slot*16+16]
    if value != donor_name: raise ValueError('Changed speed-bag name')
    identity = f'GAFE01-r0/item/{item:04X}/name'
    if identity not in entries:
        add(identity,value,edits=[dict(id=identity,translation='',
            provenance=dict(source='user-supplied GAFE01 revision 0 disc',symbol='ftrName2_table',
                index=slot,reference_sha256=sha256(value)))],locator='tools/v3_speed_bag_runtime.py')
    clothes = symbol_data(rel,symbols.decode(),'itemName_cloth')
    for n,row in enumerate(report['clothing']['imports']):
        item = int(row['donor_item_id'],16); offset = 0x2820+n*32
        value = blob[offset+12:offset+28]; index = item&255
        if value != clothes[index*16:index*16+16]: raise ValueError('Changed imported shirt name')
        identity = f'GAFE01-r0/item/{item:04X}/name'
        add(identity,value,edits=[dict(id=identity,translation='',
            provenance=dict(source='user-supplied GAFE01 revision 0 disc',symbol='itemName_cloth',
                index=index,reference_sha256=sha256(value)))],locator='tools/v3_clothing.py')
    # Project-written N64 control captions, bound to the current real editor.
    from keyboard_rc1_fix import VROM as KEYBOARD_VROM
    keyboard = files[KEYBOARD_VROM].extract(image)
    for word in ('Case','Page','Move','Cursor','Type','Del','Space','Done'):
        value = word.encode()
        if value+b'\0' not in keyboard: raise ValueError('Missing installed keyboard caption')
        identity = 'ui/keyboard/'+word.lower()
        add(identity,value,edits=[dict(id=identity,translation=word,provenance=
            'Original English translation of the N64 controller function label')],
            locator='overlays/keyboard_v2_layout/controls.c#af_v2_labels')
    import shrine_labels
    value = files[0x03B00000].extract(image)[shrine_labels.LABEL_AT:shrine_labels.LABEL_AT+6]
    if value != b'Shrine': raise ValueError('Changed native landmark correction')
    row = add('ui/map/shrine',value,edits=[],locator='tools/shrine_labels.py')
    row['locales']['en'].update(credit='human',contributors=['TheDiscordian'],text='Shrine',
        source='User playtest report identifies the native landmark as the Shrine, not the GameCube Wishing Well',
        human_review='not_recorded')
    catalogue = dict(schema=1, credits=CREDITS, inspection_rom_sha256=ROM_SHA,
        inspection_rom=str(ROM.relative_to(ROOT)), evidence_files=inputs,
        maintenance='Edit this catalogue; never overwrite human attribution/review using a new seed.',
        coverage=dict(native_banks='all stored records; full item/name/catchphrase routes take precedence',
            full_mail='all available catalog-4 parts, each compared with the actual converted donor',
            complete_whole_rom_provenance=False,
            unresolved_work=[
                'Add remaining inline runtime/UI labels and bitmap lettering as individual stable identities.',
                'Record per-letter exceptions in other immutable catalog variants; do not infer catalog-4 equivalence.',
            ]), entries=[entries[k] for k in sorted(entries)])
    validate(catalogue)
    return catalogue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--author',choices=sorted(KINDS))
    parser.add_argument('--id')
    parser.add_argument('--text',action='store_true')
    args = parser.parse_args()
    if args.seed:
        if CATALOGUE.exists(): raise ValueError('The canonical catalogue already exists; do not overwrite it')
        value = seed()
        # Mechanical migration of existing provenance, not a new authored script.
        with CATALOGUE.open('x') as handle:
            header = {k:v for k,v in value.items() if k!='entries'}
            handle.write(json.dumps(header,indent=2,ensure_ascii=False)[:-2]+',\n  "entries": [\n')
            handle.write(',\n'.join('    '+json.dumps(row,ensure_ascii=False) for row in value['entries']))
            handle.write('\n  ]\n}\n')
    value = json.loads(CATALOGUE.read_text()); counts = validate(value)
    if args.check or not (args.author or args.id): print(json.dumps(counts,sort_keys=True)); return
    for row in value['entries']:
        current = row['locales']['en']
        if args.author and current['credit'] != args.author or args.id and row['id'] != args.id: continue
        if args.text: print(row['id'],current.get('text','[text remains at its recorded source]'),current['locator'],sep='\n')
        else: print(json.dumps(row,ensure_ascii=False))


if __name__ == '__main__': main()
