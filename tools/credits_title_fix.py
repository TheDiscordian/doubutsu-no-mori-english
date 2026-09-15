"""Apply the official localized credit title to preserved current cartridges."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import DMA_START, by_vrom, sha256, verified_rom, fix_checksum, make_ups, apply_ups
from apply_translation import write_new
from credits_strings import ADAPTED_REFERENCES, adapted_reference_evidence
from textbanks import Bank

ROOT = Path(__file__).resolve().parents[1]
DATA, TABLE, TITLE = 0x02600000, 0x00D18000, 0x4EA
BASES = {
    'v2': ('build/v2-keyboard-fit-11', 'Animal Forest English V2',
           '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'),
    'v3': ('build/v3-camper-greeting-runtime-02', 'animal-forest-v3-asset-loader',
           '22293297ece2547c93f26d038fb74396163943ad548dab53b3b9ded9af9fdf39'),
}


def patch(base):
    if sha256(base) not in {row[2] for row in BASES.values()}:
        raise ValueError('Credits correction requires a pinned current cartridge')
    adapted_reference_evidence()
    files = by_vrom(base)
    bank = Bank('string', DATA, TABLE, files[DATA].extract(base), files[TABLE].extract(base))
    before = bank.entries()
    if before[TITLE] != b'Animal Forest':
        raise ValueError('Changed credit title')
    after = list(before); after[TITLE] = ADAPTED_REFERENCES[TITLE][2]
    data, table = bank.rebuild(after, allow_expand=True)
    old = files[DATA]; end = old.pstart + len(data)
    if (old.pend or files[TABLE].pend or len(data) - old.size != 2
            or end > len(base) or any(base[old.pstart+old.size:end])
            or any(v != DATA and e.pstart != 0xFFFFFFFF and
                   e.pstart < end and old.pstart < (e.pend or e.pstart+e.size)
                   for v,e in files.items())
            or any(v != DATA and e.vstart < DATA+len(data) and DATA < e.vend
                   for v,e in files.items())):
        raise ValueError('Localized credit title exceeds checked string-bank padding')
    image = bytearray(base)
    image[old.pstart:end] = data
    image[files[TABLE].pstart:files[TABLE].pstart+len(table)] = table
    struct.pack_into('>I', image, DMA_START+old.index*16+4, DATA+len(data))
    fix_checksum(image)
    installed = by_vrom(image)
    if Bank('string', DATA, TABLE, installed[DATA].extract(image),
            installed[TABLE].extract(image)).entries() != after:
        raise ValueError('Credit-title bank reconstruction failed')
    for v,e in files.items():
        if v not in (DATA,TABLE,0x19D40) and e.extract(base) != installed[v].extract(image):
            raise ValueError('Credit-title correction changes an unrelated resource')
    return bytes(image)


def build(kind, output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    folder,name,digest = BASES[kind]
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base = (ROOT/folder/(name+'.z64')).read_bytes()
    image = patch(base); ups = make_ups(native,image)
    if apply_ups(native,ups) != image: raise ValueError('Credit-title UPS reconstruction failed')
    previous = json.loads((ROOT/folder/'build.json').read_bytes())
    report = copy.deepcopy(previous)
    report.update(build=kind+'-official-credits-title', output_sha256=sha256(image),
                  patch_sha256=sha256(ups), input_build_sha256=digest)
    report['credits_title'] = dict(native_id='string:04EA', reference_id='string:077B',
        reference_sha256=sha256(ADAPTED_REFERENCES[TITLE][1]), translation='Animal Crossing',
        source='Nintendo, Animal Crossing GAFE01 revision 0, active English credits',
        wording_changed=True, executable_code_changed=False, saved_format_changed=False,
        bank_growth=2, native_retest='not run; data-only change within the existing 25-byte row',
        web_patcher_updated=False)
    report.setdefault('sources',{}).update({p:sha256((ROOT/p).read_bytes()) for p in
        ('tools/credits_title_fix.py','tools/credits_strings.py')})
    output.mkdir(parents=True)
    for suffix,raw in (('.z64',image),('.ups',ups)):
        write_new(output/(name+suffix),raw)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',choices=BASES,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); report = build(args.base,args.output)
    print(json.dumps({k:report[k] for k in ('build','output_sha256','patch_sha256')},indent=2))
