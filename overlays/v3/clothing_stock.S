/* The original caller retains its selected clothing list in callee-saved s1. */
.set noreorder
.set noat
.text
.globl af_v3_clothing_stock_call
af_v3_clothing_stock_call:
    j af_v3_clothing_stock_index
    move $a1, $s1
