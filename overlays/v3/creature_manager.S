.set noreorder
.set noat
.text
/* Set_Manager owns the actual relocated program at actor+178. */
.globl af_spawn_original
.type af_spawn_original,@function
af_spawn_original:
    addiu $t9,$a0,(0x178+0x8092ECB4-0x8092DBC0)
    addiu $sp,$sp,-80
    jr $t9
    sw $s0,32($sp)
.size af_spawn_original,.-af_spawn_original

.globl af_spawn_make
.type af_spawn_make,@function
af_spawn_make:
    addiu $t9,$a0,(0x178+0x8092EBC0-0x8092DBC0)
    addiu $t0,$a0,0x4180
    move $a0,$a1
    jr $t9
    move $a1,$t0
.size af_spawn_make,.-af_spawn_make
