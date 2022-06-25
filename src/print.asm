;print

            ldb #$f000      ; uart
            lda #$48
            sta b
            lda #$65
            sta b
            lda #$6c
            sta b
            lda #$6c
            sta b
            lda #$6f
            sta b
            lda #$20
            sta b