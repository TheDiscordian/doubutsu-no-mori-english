.set noreorder
.section .module_header,"aw",@progbits
.balign 4
.word 0x41465254 # AFRT
.word 1          # ABI version
.word 0x4000     # Reserved RAM
.word __module_used
.word 0          # Ready flag
.word 0          # Original heap base
.word 0          # Original heap size
.word 0          # New heap base
.word 0          # New heap size
.word 0          # Initialization count
.word 20         # Plain choice capacity
.word 32         # Resident row stride
.word af_choice_storage
.word af_choice_storage + 128
