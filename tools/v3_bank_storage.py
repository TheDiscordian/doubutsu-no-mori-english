"""Checked bank-state/save-scratch reservations for the connected bank install."""
from v3_console_disk_install import reservations

STATE_RAM,STATE_BYTES=0x807E9080,64
SCRATCH_RAM=0x80682000
SCRATCH_PRIOR,SCRATCH_BYTES=120368,120416


def layout(prior):
    existing=list(reservations(prior))
    if any(a<STATE_RAM+STATE_BYTES and STATE_RAM<b for a,b in existing):
        raise ValueError('Bank account state overlaps retained resident memory')
    scratch=prior['equipment_resources']['diaries']['memory']['scratch']
    if scratch!={'ram':SCRATCH_RAM,'bytes':SCRATCH_PRIOR}:
        raise ValueError('Changed complete format-twenty save scratch owner')
    end=SCRATCH_RAM+SCRATCH_PRIOR;new_end=SCRATCH_RAM+SCRATCH_BYTES
    if not any(a==SCRATCH_RAM and b==end for a,b in existing) or any(a<new_end and end<b for a,b in existing):
        raise ValueError('Bank save scratch cannot grow safely')
    return dict(account=dict(ram=STATE_RAM,record_bytes=48,guard_bytes=16,bytes=STATE_BYTES),
        scratch=dict(ram=SCRATCH_RAM,retained_bytes=SCRATCH_PRIOR,bytes=SCRATCH_BYTES),
        save_format=21,card_wire=7,installed=False)
