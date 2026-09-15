"""Read-only current house/player observations for the exterior crash check."""
import struct


def snapshot(debug, scene_heap=False):
    def read(address, length):
        if address & 3 or not 0x80000000 <= address <= 0x80400000-length:
            raise ValueError('Invalid house diagnostic pointer')
        return debug.read_memory(address, length)

    game = int.from_bytes(read(0x8010EF90, 4), 'big')
    players, player = struct.unpack('>2I', read(game+0x1C8C, 8))
    count, actor = struct.unpack('>2I', read(game+0x1C7C, 8))
    if count > 64:
        raise ValueError('Invalid structure actor count')
    houses, seen = [], set()
    for _ in range(count):
        if actor in seen or not actor:
            raise ValueError('Invalid structure actor chain')
        seen.add(actor)
        data = read(actor, 0x174)
        if data[2] != 0:
            raise ValueError('Wrong structure actor category')
        name, fg = struct.unpack_from('>H', data)[0], struct.unpack_from('>H', data, 6)[0]
        if name == 0x28:
            houses.append({'address': f'{actor:08X}', 'fg_name': f'{fg:04X}',
                           'home': list(struct.unpack_from('>3f', data, 0xC)),
                           'world': list(struct.unpack_from('>3f', data, 0x28))})
        actor = int.from_bytes(data[0x158:0x15C], 'big')
    if actor:
        raise ValueError('Structure actor chain exceeds declared count')
    result = {'player_count': players, 'player': f'{player:08X}', 'houses': houses,
              'house_owner': debug.read_memory(0x80137348, 2).hex().upper(), 'read_only': True}
    if scene_heap:
        node = int.from_bytes(read(0x80141FA0, 4), 'big')
        seen, previous, free, allocated = set(), 0, [], []
        while node:
            if node in seen or node & 15 or len(seen) >= 256:
                raise ValueError('Invalid house-scene arena chain')
            seen.add(node)
            magic, isfree, size, following, prev = struct.unpack('>2H3I', read(node, 16))
            if magic != 0x7373 or isfree not in (0, 1) or prev != previous or node+16+size > 0x80400000:
                raise ValueError('Invalid house-scene arena node')
            (free if isfree else allocated).append(size)
            previous, node = node, following
        result['scene_heap'] = {'nodes': len(seen), 'allocated_bytes': sum(allocated),
                                'free_bytes': sum(free), 'largest_free_bytes': max(free, default=0)}
    return result
