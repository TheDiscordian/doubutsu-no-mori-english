/* The checked native Change_ItemBank call has s0 = player + bank_index * 4.
   A new model can move the following animation even if its index is unchanged.
   Force the native animation path to reload and recalculate both addresses. */
.set noreorder
.set noat
.section .text.af_v3_equipment_model_dma,"ax",@progbits
.globl af_v3_equipment_model_dma
.ent af_v3_equipment_model_dma
af_v3_equipment_model_dma:
    addiu $t0, $zero, -1
    sw $t0, 0x0DE4($s0)
    j 0x800B167C
    nop
.end af_v3_equipment_model_dma
