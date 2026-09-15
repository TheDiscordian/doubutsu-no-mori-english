.set noreorder
.set noat
.section .text.af_v3_native_action_sound,"ax",@progbits
.globl af_v3_native_action_sound
af_v3_native_action_sound:
    # The shared reader calls this only for original indices 0..946. Restore
    # the original bound register and resume the complete unchanged switch.
    slti $at, $a0, 947
    j 0x800BED64
    nop
