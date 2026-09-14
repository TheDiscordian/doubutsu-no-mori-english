"""Preserve the 245 native catalogue garments and add the selected cherry shirt."""
import struct

from aflib import sha256
from gc_names import symbol_data
from v3_furniture_art import verify_sources
from v3_clothing_display import profile_dependency
from v3_display_items import scoring_identity

ABI = 44
SOURCES = ('tools/v3_clothing_catalogue.py',)
POINTER, COUNT, TABLE = 0x808AF7BC, 0x808AF7C0, 0x808AF354
NATIVE_COUNT = 245
NATIVE_SHA = 'a9d533486e8a0ebae4f3fd9e3bfe6ef8992c8f9f6f28194e0bd6df5693c32601'


def table(base, rel, symbols):
    from v3_catalogue import sources, RAM
    data, _, _ = sources(base)
    verify_sources(rel, symbols)
    native = data[TABLE-RAM:TABLE-RAM+NATIVE_COUNT*2]
    if (sha256(native) != NATIVE_SHA
            or struct.unpack_from('>2I', data, POINTER-RAM) != (TABLE, NATIVE_COUNT)):
        raise ValueError('Changed complete native clothing catalogue')
    display = profile_dependency()
    donor_index = scoring_identity(rel, symbols, display)
    donor = symbol_data(rel, symbols.decode(), 'mCL_cloth_idx_list')
    values = list(struct.unpack('>'+str(len(donor)//2)+'H', donor))
    if (sha256(donor) != '3eb4ab9626f6da11b6222e5707201bef8d69cea6583824f58022cb786874d4aa'
            or values.count(donor_index) != 1 or len(set(values)) != len(values)):
        raise ValueError('Garment is not a unique actual donor catalogue entry')
    catalogue_index = (int(display['item_id'], 16)-0x1000)//4
    if len(set(struct.unpack('>245H', native))) != NATIVE_COUNT or catalogue_index < 2048:
        raise ValueError('Imported catalogue identity overlaps original garments')
    return native+struct.pack('>H', catalogue_index), {
        **display, 'catalogue_index': catalogue_index, 'native_rows': NATIVE_COUNT,
        'total_rows': NATIVE_COUNT+1, 'native_table_sha256': NATIVE_SHA,
        'donor_table_sha256': sha256(donor), 'donor_rows': len(values),
        'donor_position': values.index(donor_index), 'donor_runtime_index': donor_index,
        'preview_scale': 1.0, 'preview_height': 38.0, 'preview_model_y': -4.0,
        'ordinary_order_payment_tested': False}
