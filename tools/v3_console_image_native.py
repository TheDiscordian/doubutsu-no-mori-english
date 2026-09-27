"""Install all console images and the shared bounded physical-ROM reader."""
import copy
import json
import zlib
from aflib import by_vrom,sha256
from v3_asset_loader import BLOB,ROOT,compile_part
import v3_physical_resources as physical

RAM,SIZE,METADATA=0x804F9020,0x5800,0x3800
PI_SHA='059be53c24779644893f8e950fdc1015954bf094f8425a7f3cb93239de3abec3'
SOURCES=physical.SOURCES+('tools/v3_console_image_native.py','tools/v3_console_games.py',
    'tools/v3_furniture_install.py','tools/v3_room_goods.py','tools/v3_asset_loader.py',
    'overlays/v3/console_image_native.c','overlays/v3/console_image_native.ld',
    'overlays/v3/console_image.c','overlays/v3/console_image.h',
    'overlays/v3/console_save.c','overlays/v3/console_save.h','overlays/v3/surface_bootstrap.c')


def install(base,prior,blob,output,directory):
    prepared=json.loads((directory/'games.json').read_bytes());stream=prepared['streaming']
    metadata=(directory/'games-metadata.bin').read_bytes();pool=(directory/'games-pool.bin').read_bytes()
    if (sha256(metadata)!=stream['metadata_sha256'] or len(metadata)!=stream['metadata_bytes'] or
            sha256(pool)!=stream['pool_sha256'] or len(pool)!=stream['pool_bytes'] or
            len(metadata)>SIZE-METADATA-16 or len(stream['rows'])!=19):
        raise ValueError('Changed complete console metadata/game pool')
    for path,digest in stream['loader']['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale console conversion: '+path)
    equipment=copy.deepcopy(prior['equipment_resources']);storage=equipment['console_storage']
    if equipment.get('console_images') or storage['save_format']!=5:
        raise ValueError('Console images require installed format-five storage')
    if storage['hash']['guard']+16>RAM or RAM+SIZE>prior['furniture']['bank_pool']['start']:
        raise ValueError('Console image packet overlaps retained save/model memory')
    def reservations(value):
        if isinstance(value,dict):
            if isinstance(value.get('ram'),int) and isinstance(value.get('bytes'),int):
                yield value['ram'],value['bytes']
            for v in value.values():yield from reservations(v)
        elif isinstance(value,list):
            for v in value:yield from reservations(v)
    if any(at<RAM+SIZE and RAM<at+n for at,n in reservations(equipment)):
        raise ValueError('Console image packet intersects a retained allocation')
    boot=by_vrom(base)[0x1060].extract(base)
    if sha256(boot[0x80026500-0x80025C60:0x800266C4-0x80025C60])!=PI_SHA:
        raise ValueError('Changed native synchronous physical-ROM reader')
    records=copy.deepcopy(prior.get('physical_resources',[]))
    record=physical.allocate(base,records,pool,'console-games-GAFE01-r0');records.append(record)
    code,compiled=compile_part('console_image_native',output/'console_image_native',
        extra_sources=('overlays/v3/console_image.c','overlays/v3/console_save.c'),defines=(
            f'AF_CONSOLE_POOL_ROM=0x{record["physical"]:X}u',f'AF_CONSOLE_POOL_BYTES={len(pool)}u',
            f'AF_CONSOLE_METADATA_RAM=0x{RAM+METADATA:X}u',f'AF_CONSOLE_METADATA_BYTES={len(metadata)}u'))
    if len(code)>METADATA:raise ValueError('Console loader exceeds its code reservation')
    packet=(code.ljust(METADATA,b'\0')+metadata).ljust(SIZE-16,b'\0')+bytes.fromhex('AF4E4553')*4
    blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(packet)
    receipt=dict(format='AFV3-CONSOLE-IMAGES-NATIVE-1',compiled=compiled,
        packet=dict(ram=RAM,bytes=SIZE,blob_offset=offset,vrom=BLOB+offset,
            sha256=sha256(packet),crc32=zlib.crc32(packet)),
        metadata=dict(ram=RAM+METADATA,bytes=len(metadata),sha256=sha256(metadata)),
        pool=record,streaming=stream,workspace_bytes=1024,
        physical_reader=dict(address=0x80026500,bytes=0x1C4,sha256=PI_SHA),
        installed=True,native_execution_tested=False,launch_installed=False,choices_added=0,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    equipment['console_images']=receipt
    return equipment,dict(physical_resources=records),[(record,pool)]
