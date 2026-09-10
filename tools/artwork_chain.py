"""Rebuild data-only artwork changes while retaining every reviewed resource."""
import copy

from aflib import verified_rom,by_vrom,sha256,replace_dma,make_ups,apply_ups


def rebuild(native,base,report,changes):
    verified_rom(native)
    if report.get('output_sha256') != sha256(base) or not changes:
        raise ValueError('Artwork chain requires a complete bound predecessor and changes')
    files, originals = by_vrom(base),by_vrom(native)
    boot = originals[0x1060]
    if (files[0x1060].extract(base) != boot.extract(native)
            or base[boot.pstart:boot.pstart+boot.size] != boot.extract(native)):
        raise ValueError('Artwork chain requires the untitled base; combine the title afterwards')
    moved = {int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    reverse = {new:old for old,new in moved.items()}
    replacements = {int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in report['replacement_files']}
    additions = {int(v,16):files[int(v,16)].extract(base) for v in report['added_files']}
    for vrom,data in changes.items():
        if vrom not in files or len(data) != files[vrom].size or vrom in (0x1060,0x19D40):
            raise ValueError('Artwork change has unknown identity or changes owned sizes/boot data')
        if vrom in additions: additions[vrom] = data
        else:
            original = reverse.get(vrom,vrom)
            if original not in originals: raise ValueError('Artwork resource lacks native or added ownership')
            replacements[original] = data
    image = replace_dma(native,replacements,moved,additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Artwork chain changes cartridge/resource identities')
    for vrom,entry in files.items():
        actual,expected = installed[vrom].extract(image),changes.get(vrom,entry.extract(base))
        if vrom == 0x19D40:actual,expected = actual[:16],expected[:16]
        if (actual != expected or installed[vrom].index != entry.index
                or installed[vrom].size != entry.size):
            raise ValueError(f'Artwork chain loses earlier resource {vrom:08X}')
    patch = make_ups(native,image)
    if apply_ups(native,patch) != image:raise ValueError('Artwork UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image),patch_sha256=sha256(patch),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)])
    return image,patch,result
