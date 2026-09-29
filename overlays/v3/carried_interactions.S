.set noreorder
.set noat
.text
/* Retain the native constructor's saved player and original message ID. */
.globl af_carried_net_message_call
.type af_carried_net_message_call,@function
af_carried_net_message_call:
    move $a1,$a0
    j af_carried_net_message
    lw $a0,0x50($sp)
.size af_carried_net_message_call,.-af_carried_net_message_call
