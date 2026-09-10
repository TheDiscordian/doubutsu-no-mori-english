"""Inspect the normally loaded shared grid without modifying game state."""
import struct
from build_keyboard_grid import HOOKS,RAM,jump
from keyboard_grid_overlay import APPROVED


def snapshot(debug,keyboard):
    base=int(keyboard['keyboard_base'],16)
    for at,(name,_) in HOOKS.items():
        if debug.read_memory(base+at-RAM,4)!=struct.pack('>I',jump(base+APPROVED['symbols'][name])):
            raise ValueError('Ordinary keyboard does not use the reviewed grid hook')
    data=debug.read_memory(base+APPROVED['symbols']['af_grid_context'],36)
    state=data[:12]
    submenu,menu,editor,text,draws,error=struct.unpack('>6I',data[12:])
    if (not 0x80000000<=submenu<0x80400000 or not 0x80000000<=menu<0x80400000
            or editor!=base+0x39B0 or debug.read_memory(editor+0x24,4)!=struct.pack('>I',text)
            or not draws or error or state[0]>=10 or state[1]>=4 or state[2]>=2
            or state[3]>=2 or state[4]>=3):
        raise ValueError('Ordinary grid ownership, selection, or drawing failed')
    return {'column':state[0],'row':state[1],'uppercase':bool(state[2]),
        'alphabetical':bool(state[3]),'page':state[4],'draws':draws,'error':error}
