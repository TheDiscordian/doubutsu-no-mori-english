"""Exact five-byte English labels for the native general-string reserve slots."""
from dataclasses import dataclass, replace
from functools import lru_cache
import json

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from fortune_strings import source_entries, STRING_RELOCATION
from textbanks import banks

NUMBERS = (*range(0x2C5,0x2CA), *range(0x2ED,0x2F4), *range(0x561,0x566), *range(0x5DE,0x61A))
IDS = tuple(f'string:{n:04X}' for n in NUMBERS)
SOURCE = bytes.fromhex('60F7')
VALUE = b'spare'
SOURCE_SHA = '037e75125021be40f5556e5c16dfac744af0e537b45c93449ee7eda498ecf9c5'
START, END = 0x800C3E30, 0x800C4090
LOADER_SHA = 'd23c5c2bd27d2457026bcf821fed0f0c6e7dbf1d4c936973803103abab7e0ea5'
CALLS_SHA = 'bd82abe8450100425c893cb61f2d70a6502e497e3c7ed446bc7a498a92aaf9e5'


@dataclass(frozen=True)
class ReservePermit:
    source_sha256: str = SOURCE_SHA
    encoded_sha256: str = sha256(VALUE)


@lru_cache(maxsize=1)
def verify_source(native):
    verified_rom(native)
    originals = source_entries(native)
    if any(originals[n] != SOURCE for n in NUMBERS):
        raise ValueError('Changed native reserve label or range')
    from catchphrases import native_table
    if set(NUMBERS) & {row[1] for row in native_table(native)}:
        raise ValueError('Reserve label intersects four-byte saved defaults')
    from audit_string_callers import audit
    calls = audit(native)['callers']
    signatures = [(r['vrom'],r['call_ram'],r['destination_length'],r['string_id']) for r in calls]
    if len(calls) != 34 or sha256(json.dumps(signatures,sort_keys=True,separators=(',',':')).encode()) != CALLS_SHA:
        raise ValueError('Changed reserve-label consumer inventory')
    code = by_vrom(native)[CODE_VROM].extract(native)
    if sha256(code[START-CODE_RAM:END-CODE_RAM]) != LOADER_SHA:
        raise ValueError('Changed bounded native string loader')


def with_candidates(native, edits):
    verify_source(native)
    result, seen = list(edits), set()
    for row in edits:
        if row['id'] not in IDS: continue
        if (row['id'] in seen or row.get('source_sha256') != SOURCE_SHA
                or row.get('translation') != 'spare' or row.get('control_policy','exact') != 'exact'):
            raise ValueError('Conflicting or duplicate reserve translation')
        seen.add(row['id'])
    result.extend({'id':id, 'source_sha256':SOURCE_SHA, 'translation':'spare',
                   'control_policy':'exact', 'status':'original_translation',
                   'provenance':{'source':'native reserve label', 'meaning':'reserve/spare',
                                 'capacity_contract':'specs/RESERVE_STRINGS.md'}}
                  for id in IDS if id not in seen)
    return result


def permits(native, edits):
    verify_source(native)
    selected = [e for e in edits if e['id'] in IDS]
    if len(selected) != len(IDS) or {r['id'] for r in selected} != set(IDS):
        raise ValueError('Reserve labels require the complete unique group')
    with_candidates(native, selected)
    return {id:ReservePermit() for id in IDS}


def planned(native, replacements):
    verify_source(native)
    files = by_vrom(native)
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(native)))
    _, at, before, after = STRING_RELOCATION
    if code[at-CODE_RAM:at-CODE_RAM+8] != bytes.fromhex(after):
        raise ValueError('Reserve labels require the verified relocated string bank')
    code[at-CODE_RAM:at-CODE_RAM+8] = bytes.fromhex(before)
    if sha256(code[START-CODE_RAM:END-CODE_RAM]) != LOADER_SHA:
        raise ValueError('Changed installed bounded string loader')
    bank = next(b for b in banks(native) if b.name == 'string')
    entries = replace(bank,data=replacements.get(bank.data_vrom,bank.data),
                      table=replacements.get(bank.table_vrom,bank.table)).entries()
    if any(entries[n] != VALUE for n in NUMBERS):
        raise ValueError('Incomplete installed English reserve labels')
    return {'ids':list(IDS), 'source_sha256':SOURCE_SHA, 'encoded_sha256':sha256(VALUE),
            'loader_sha256':LOADER_SHA, 'caller_inventory_sha256':CALLS_SHA,
            'stored_bytes':5, 'new_saved_bytes':0, 'new_runtime_bytes':0}


def verify_installation(built, native, report):
    files = by_vrom(built)
    moved = {int(k,16):int(v,16) for k,v in report.get('vrom_relocations',{}).items()}
    bank = next(b for b in banks(native) if b.name == 'string')
    replacements = {v:files[moved.get(v,v)].extract(built) for v in (CODE_VROM,bank.data_vrom,bank.table_vrom)}
    evidence = planned(native,replacements)
    if report.get('reserve_strings') != evidence:
        raise ValueError('Missing or changed reserve-label evidence')
    return evidence
