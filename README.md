# dip8-computer
An 8-bit computer constructed from logic ICs


## Overview

* 8-bit data bus
* 16-bit address bus
* 64K of addressable memory - 44K RAM, 16K ROM, 4K memory mapped I/O
* Clock speed: around 1 MHz
* Design goal: keep the IC count low while still having a reasonably efficient ISA. Capable of running a (cooperative) multitasking OS (no interrupts)
* Serial terminal interface. Possibility of adding a graphical output later.


## Registers

* Two 8-bit "accumulators" A and Z, which can be loaded from/stored to memory
* Two general-purpose 8-bit registers X and Y
* Two 16-bit registers B and C, each composed of two 8-bit registers (BH/BL and CH/CL)

Only A and Z can be loaded/stored, with `lda`/`sta`/`ldz`/`stz`. Addressing modes:

    lda #32     ; literal:  A = 32
    lda $ff00   ; absolute: A = mem[0xFF00]
    lda *$ff00  ; indirect: A = mem[mem[0xFF00]]
    lda b       ; address register: A = mem[B] (also lda c)
    lda b+t     ; address reg + offset: A = mem[B] + T
    
