/* Native profile/DMA entries retain their complete original function bodies.
 * For original indices, reproduce only the displaced prologue and jump to the
 * real loaded My_Room overlay, never its link address. No caller state is lost.
 */
.set noreorder
.set noat
.text
.macro native_bridge name, imported, continuation, frame, ra_offset
.globl \name
.ent \name
\name:
    andi $t0, $a0, 0xffff
    sltiu $t0, $t0, 947
    beqz $t0, 1f
    nop
    lui $t0, 0x8010
    lw $t0, 0x0e00($t0)
    beqz $t0, 2f
    nop
    addiu $t0, $t0, \continuation
    addiu $sp, $sp, -\frame
    jr $t0
    sw $ra, \ra_offset($sp)
1:
    j \imported
    nop
2:
    jr $ra
    move $v0, $zero
.end \name
.endm

native_bridge af_v3_furniture_load, af_v3_furniture_import_profile, 0x84, 64, 28
native_bridge af_v3_furniture_dma, af_v3_furniture_import_dma, 0x2154, 48, 20
