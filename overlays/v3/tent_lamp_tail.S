.set noreorder
.set noat
.set nomacro
.text
.globl native_environment_body
native_environment_body:
    addiu $sp,$sp,-32
    sw $s0,24($sp)
    j native_environment_continue
     nop
.globl native_room_prim_body
native_room_prim_body:
    addiu $sp,$sp,-56
    lui $t6,0x8014
    j native_room_prim_continue
     nop
