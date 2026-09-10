"""Bounded native startup, capture, generation, and notice-reader check."""
import argparse
import json
from pathlib import Path
from aflib import by_vrom
from accent_items_install import verify_installation


def scenario(native,built,report):
    verify_installation(built,native,report)
    files=by_vrom(built);module=report['runtime_module'];request={'module':module,'images':{}}
    from native_species_scenario import BOOT_HELPERS
    request['boot_helpers']={f'{start:08X}':native[0x1060+start-0x80025C60:0x1060+end-0x80025C60].hex()
                             for start,end in BOOT_HELPERS}
    for kind,vrom,relv,overlay in (
            ('creator',0x03200000,None,module['npc_mail_loader']['overlay']),
            ('notice',0x03920000,0x03928000,report['noticeboard']['overlay']),
            ('event',0x03800000,0x03810000,report['event_actor']['overlay'])):
        raw=files[vrom].extract(built);size=overlay['bytes']
        image,reloc=(raw[:size],raw[size:]) if relv is None else (raw,files[relv].extract(built))
        request['images'][kind]={'vrom':vrom,'relocation_vrom':vrom+size if relv is None else relv,
            'image':image.hex(),'relocations':reloc.hex(),'overlay':overlay}
    font=module['extended_font'];request['font_blob']=files[0x03400000].extract(built).hex()
    return [{'wait':8},{'read':['80000318',4],'expect':'00400000'},
            {'save_state':True},{'pause_game_thread':True},{'test_accent_mail':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=Path('build/accent-items-pilot'))
    p.add_argument('--output',type=Path,default=Path('build/accent-mail-scenario.json'))
    a=p.parse_args()
    actions=scenario(Path('local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((a.build/'build.json').read_text()))
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'output':str(a.output)}))


if __name__=='__main__':main()
