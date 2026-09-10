# The complete-end letter explanation can span English continuation records.
# Defer cleanup to normal conversation closure, just as native end 00 does.
.set noreorder
.set noat
.text
.globl af_first_job_letter_advice_word
af_first_job_letter_advice_word:
    addiu $t0, $zero, 11          # 8091D4C8: WAIT_NOTHING, not premature FINISH
