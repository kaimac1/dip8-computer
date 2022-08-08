
#define size 8191

int main(void) {

    unsigned int count;
    unsigned int prime;
    unsigned int k;
    unsigned char *flags = 0x1000;

    count = 0;
    for (unsigned int i=0; i<size; i++) {
        flags[i] = 1;
    }
    for (unsigned int i=0; i<size; i++) {
        if (flags[i]) {
            prime = i + i + 3;
            k = i + prime;
            while (k < size) {
                flags[k] = 0;
                k += prime;
            }
            count = count + 1;
        }
    }

    return count;

}



//#define UART (unsigned char *)0xF000
//static int glob = 32;
//const char hexdigits[16] = "0123456789abcdef";



    // unsigned char x = *UART;
    // unsigned char y = *UART;
    // unsigned char z = *UART;
    // int w = 231;

    // int x = 4523;

    // x ^= 0xAA55;
    // unsigned char x = 0xf3;

    // *UART = hexdigits[(unsigned char)(x >> 4)];
    // *UART = hexdigits[x & 0x0F];




    //if (x >= 32) return 1;

    // int x;
    // int y = 1;
    // int z = 0;

    // for (unsigned char n=0; n<10; n++) {
    //     x = y;
    //     y = z;
    //     z = x + y;
    // }



    // char *message = "Hello!";
    // *UART = message[x++];
    // *UART = message[x++];
    // *UART = message[x++];
    // *UART = message[x++];
    // *UART = message[x++];


    // int z = x + y;
    // int w = x + z;
    // y = (y + 5) - z;

    /*int y = 3;
    char x = *(char *)(y);

    int z = 4;
    char w = *(char *)(0x1000 + z);

    int *j = &global;
    *(j+5) = 6;*/



/*

;print an 8-bit hexadecimal value
; x   number to print
; y   clobbered
; bc  saved

printxh     push b
            mov b, #hexdigits
            mov y, #0
_loop       cmp x, #16      ; while x >= 16
            jcc write
            sub x, #16
            inc y
            jmp loop
_write      ldy b+y         ; y = hi nib
            sty UART
            ldy b+x         ; x = low nib
            sty UART
            pop b
            ret

hexdigits   .byte "0123456789abcdef"

*/

