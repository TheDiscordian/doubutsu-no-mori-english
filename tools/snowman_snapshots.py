"""Prevalidate the complete fixed Snowman gifts and both capitalization states."""

import struct

from aflib import sha256
from audit_snowman_letters import audit,GIFTS
from extended_items import COUNTS
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
import mail_creator_catalog as creator_catalog

ROW_BYTES,TABLE_BYTES = 36,864


def snapshots(native,catalog,items):
    approval = audit(native,catalog,items)
    if creator_catalog.identity(catalog)!=4: raise ValueError('Snowman snapshots require complete glyph catalogue four')
    data = bytearray();cases = []
    for choice,gift in enumerate(GIFTS):
        at = 32+(sum(COUNTS[:-1])+(gift&4095))*16 if gift>>12==1 else 32+(sum(COUNTS[:(gift>>8)-0x20])+(gift&255))*16
        name = items[at:at+16]
        for capital in (0,1):
            record = Record(4,0,(0x202+choice,),((0,Field(name)),),bool(capital))
            wire = pack(record);text = output_bytes(record,templates(catalog,record))
            if wire[2]!=29 or any(wire[32:]) or text[14] not in (0,1):
                raise ValueError('Unexpected Snowman snapshot layout or capitalization')
            data.extend(struct.pack('>HBB',gift,text[14],0)+wire[:32])
            cases.append({'choice':choice,'gift':gift,'template':0x202+choice,'capital':capital,
                          'wire':wire.hex(),'text':text.hex(),'name_sha256':sha256(name)})
    if len(data)!=TABLE_BYTES: raise ValueError('Wrong Snowman snapshot table size')
    return bytes(data),{'approval':approval,'table_sha256':sha256(data),'cases':cases,
                        'installed':False,'runtime_allocation_bytes':0,'runtime_dma_calls':0}
