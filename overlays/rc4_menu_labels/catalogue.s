.set noreorder
.set noat
.section .text
.global af_catalog_price_draw
af_catalog_price_draw:
    /* The unchanged caller saves the selected item's price at sp+0x40.
       Keep its five-byte copy; the twelve-byte English never enters that buffer. */
    lw      $t6, 0x40($sp)
    bnez    $t6, 1f
    nop
    lui     $a1, %hi(af_catalog_not_for_sale)
    addiu   $a1, $a1, %lo(af_catalog_not_for_sale)
    addiu   $a2, $zero, 12
    mtc1    $a3, $f4
    lui     $t6, 0x4110
    mtc1    $t6, $f6
    sub.s   $f4, $f4, $f6
    mfc1    $a3, $f4
    lwc1    $f4, 0x10($sp)
    lui     $t6, 0x3f80
    mtc1    $t6, $f6
    sub.s   $f4, $f4, $f6
    swc1    $f4, 0x10($sp)
    lui     $t6, 0x3f60
    sw      $t6, 0x2c($sp)
    sw      $t6, 0x30($sp)
1:
    j       af_catalog_native_font
    nop
.global af_catalog_not_for_sale
af_catalog_not_for_sale:
    .ascii "Not for Sale"
.balign 16
