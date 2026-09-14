"""One bounded V3 file for resident code and demand-loaded import resources."""
START, END = 0x02200000, 0x02400000
SOURCES = ('tools/v3_storage.py', 'overlays/v3/storage.h')


def pack(prefix, resources, existing):
    if not 0 < len(prefix) <= END-START or len(prefix) % 16:
        raise ValueError('V3 resident prefix exceeds its aligned storage reservation')
    if any(entry.vstart < END and START < entry.vend for entry in existing.values()):
        raise ValueError('V3 storage reservation overlaps an existing ROM resource')
    output = bytearray(prefix)
    for address, data in sorted(resources.items()):
        offset = address-START
        if not data or address % 16 or len(data) % 16 or offset < len(output) or address+len(data) > END:
            raise ValueError('V3 resource overlaps its prefix, another resource, or storage limit')
        output.extend(bytes(offset-len(output)))
        output.extend(data)
    return bytes(output)
