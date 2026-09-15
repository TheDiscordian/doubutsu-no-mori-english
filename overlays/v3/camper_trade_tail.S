.set noreorder
.set noat
.section .text.native_trade_original,"ax",@progbits
.globl native_trade_original
native_trade_original:
    /* Displaced original prologue; preserve all five incoming arguments. */
    addiu $sp, $sp, -96
    sw $s6, 56($sp)
    j native_trade_body
    nop
