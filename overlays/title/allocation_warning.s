# Title-only high-memory allocator with a bounded low-memory instruction screen.
# The unsupported-machine path uses the existing CPU framebuffer/font routines,
# then stops only the caller thread. It raises no exception and writes no save.
.set noreorder
.set noat
.section .text,"ax",@progbits
.globl af_title_allocate
af_title_allocate:
    lui $t0, 0x8010
    ori $t0, $t0, 0x21f0
    bne $a0, $t0, ordinary
    nop
    lui $t0, 0x8000
    lw $t0, 0x0318($t0)
    lui $t1, 0x0080
    bne $t0, $t1, unavailable
    lui $t0, 0x8040
    addiu $t0, $t0, 16
    lui $t1, 0xaf54
    ori $t1, $t1, 0xc0de
    addu $t2, $t0, $a2
    sw $t1, -16($t0)
    sw $t1, -12($t0)
    sw $t1, -8($t0)
    sw $t1, -4($t0)
    sw $t1, 0($t2)
    sw $t1, 4($t2)
    sw $t1, 8($t2)
    sw $t1, 12($t2)
    jr $ra
    sw $t0, 16($a0)
unavailable:
    sw $zero, 16($a0)
    addiu $sp, $sp, -24
    jal 0x800292f4  # fault_DisplayFrameBuffer
    nop
    jal 0x80027cf8  # fault_FillScreenBlack
    nop
    lui $a0, %hi(message)
    jal 0x8002a448  # FaultDrawer_Printf also writes back the framebuffer cache.
    addiu $a0, $a0, %lo(message)
stopped:
    jal 0x8002de10  # osStopThread(NULL), not a deliberate CPU fault.
    move $a0, $zero
    b stopped
    nop
ordinary:
    j 0x800578e0
    nop
message:
    .asciz "Expansion Pak required.\n\nPower off and install it."
