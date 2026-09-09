"""Source-bound original item translations where the donor names differ."""
import json
from pathlib import Path
import re

from aflib import sha256
from item_aliases import ordinary_item
from item_matches import identity_key, verify_source
from textcodec import LATIN, encode, tokenize

PATH = Path(__file__).resolve().parents[1]/'translations/n64-item-names.json'
SOURCE = 'project-authored translation of the native Japanese item name'


def load_names(path=PATH):
    rows = json.loads(path.read_text())
    if not isinstance(rows,list):
        raise ValueError('Native item names require a list')
    result = {}
    for row in rows:
        if (not isinstance(row,dict) or not isinstance(row.get('id'),str) or
                identity_key(row['id']) != row['id'] or row['id'] in result or
                any(not isinstance(row.get(k),str) or not row[k].strip()
                    for k in ('native_name','translation','evidence')) or
                not isinstance(row.get('source_sha256'),str) or
                not re.fullmatch('[0-9a-f]{64}',row['source_sha256'])):
            raise ValueError('Invalid complete native item-name approval')
        text = row['translation'].encode('ascii',errors='strict')
        if not 1 <= len(text) <= 16 or text.strip() != text or any(b not in LATIN for b in text):
            raise ValueError('Native item translation must be complete supported Latin within sixteen bytes')
        result[row['id']] = {**row,'reference_id':'native:'+row['id'],
                            'reference_sha256':sha256(text.ljust(16,b' '))}
    return result


def approval_key(id,names):
    direct = identity_key(id)
    if direct in names:
        return direct
    # The cartridge normalises these placed clothing/creature/umbrella IDs.
    # Infer the approved alias even if an edit removes its metadata.
    matches = [key for key in names if key.startswith('item_10:') and
               (number := 0x1000+int(key.split(':')[1],16)) != (converted := ordinary_item(number)) and
               id == f'item_{converted >> 8:02X}:{converted & 255:04X}']
    if len(matches) > 1:
        raise ValueError('Conflicting native item-name alias approvals')
    return matches[0] if matches else None


def validate(edit,source,info,names):
    if not edit['id'].startswith('item_'):
        if 'native_item_name' in edit:
            raise ValueError('Native item metadata belongs only to item names')
        return False
    key = approval_key(edit['id'],names)
    if key is None:
        if 'native_item_name' in edit:
            raise ValueError('Unknown or unrelated native item-name approval')
        return False
    row = names[key]
    if 'item_reference_match' in edit or edit.get('native_item_name',key) != key:
        raise ValueError('Conflicting native and donor item-name identities')
    bank,index = key.split(':'); index = int(index,16)
    if bank not in source or index >= len(source[bank]):
        raise ValueError('Native item-name source is absent')
    native = source[bank][index]
    verify_source(row,native,info)
    if bank == 'item_10' and source[bank][index:index+4] != [native]*4:
        raise ValueError('Native item-name rotation fields differ')
    target,number = edit['id'].split(':'); number = int(number,16)
    if (target not in source or number >= len(source[target]) or source[target][number] != native or
            edit.get('source_sha256') != sha256(native)):
        raise ValueError('Native item name changes its actual source or alias')
    provenance = edit.get('provenance',{})
    if (not isinstance(provenance,dict) or provenance.get('source') != SOURCE or
            provenance.get('reference_id') != row['reference_id'] or
            provenance.get('reference_sha256') != row['reference_sha256'] or
            edit.get('translation') != row['translation'] or edit.get('control_policy') != 'exact'):
        raise ValueError('Native item name must retain its complete original translation and provenance')
    encoded = encode(edit['translation'],info)
    if any(t.kind != 'text' or t.data[0] not in LATIN for t in tokenize(encoded,info)):
        raise ValueError('Native item name contains nonplain text')
    if identity_key(edit['id']) != key:
        donor = provenance.get('native_equivalent_id','')
        if (not isinstance(donor,str) or not donor.startswith('item_10:') or identity_key(donor) != key):
            raise ValueError('Native item name requires its exact placed alias donor')
        number = 0x1000+int(donor.split(':')[1],16)
        if (provenance.get('match_basis') != 'native_placed_conversion_and_identical_source_name' or
                provenance.get('native_item_id') != f'{number:04X}' or
                provenance.get('converted_item_id') != f'{ordinary_item(number):04X}'):
            raise ValueError('Native item name changes the cartridge alias conversion')
    return True
