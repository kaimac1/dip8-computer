#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#define CPU_FREQ 2000000
#define ROM_SIZE 65536
#define MEM_SIZE 65536

// Decoder/ALU ROMs
uint8_t dec0[ROM_SIZE], dec1[ROM_SIZE], dec2[ROM_SIZE];
uint8_t alu[ROM_SIZE];

uint8_t memory[MEM_SIZE];

bool Cint;          // internal carry
bool C, Z, N;       // status flags

uint16_t pc, a;     // program counter, address buffer
uint8_t t;          // t register

char *regnames[] = {"bh", "bl", "ch", "cl", "x", "y", "sh", "sl", "m"};
uint8_t regs[sizeof(regnames)/sizeof(regnames[0])];

uint8_t opcode;
uint8_t tick;       // instruction sequence tick
bool halted;

int cycles;         // counters
int instructions;
float sim_secs;




void clock_cycle(void);

long int microseconds_since(struct timeval start) {
    struct timeval now;
    gettimeofday(&now, NULL);
    return (now.tv_sec - start.tv_sec) * 1000000 + now.tv_usec - start.tv_usec;
}



// Write to memory or peripheral
void memwr(uint16_t addr, uint8_t data) {
    memory[addr] = data;
    if (addr == 0xFF00) {
        // UART
        putchar(data);
        fflush(stdout);
    }
}

void run(void) {

    // Insert a delay every this many cycles
    const int cycleN = 1000;
    const long int cycleN_us = 1000000 * cycleN / CPU_FREQ;

    struct timeval start, now;
    gettimeofday(&start, NULL);
    long int cpu_us = 0;

    while (!halted) {
        clock_cycle();

        // Delay as necessary to keep the real elapsed time equal to the ideal CPU time
        if (cycles % cycleN == 0) {
            cpu_us += cycleN_us;
            long int elapsed_us = microseconds_since(start);
            if (elapsed_us < cpu_us) {
                struct timespec ts = {0, 1000*(cpu_us - elapsed_us)};
                nanosleep(&ts, &ts);
            }
        }
    }

    sim_secs = microseconds_since(start) / 1000000.0f;

}

uint8_t do_alu(uint8_t ina, uint8_t op, bool setflags) {
    bool nsetflags = !setflags;
    uint8_t inb = t;

    // low nibble
    uint8_t al = ina & 0xF;
    uint8_t bl = inb & 0xF;
    uint16_t addr_lo = al<<0 | bl<<4 | nsetflags<<8 | op<<9 | Cint<<13 | C<<14 | 0<<15;
    uint8_t alu0 = alu[addr_lo];

    uint8_t q0 = alu0 & 0xF;
    bool    c0 = alu0 & 0b00010000;
    bool    z0 = alu0 & 0b00100000;
    bool nclki = alu0 & 0b10000000;

    // high nibble
    uint8_t ah = ina >> 4;
    uint8_t bh = inb >> 4;
    uint16_t addr_hi = ah<<0 | bh<<4 | nsetflags<<8 | op<<9 | c0<<13 | c0<<14 | 1<<15;
    uint8_t alu1 = alu[addr_hi];

    uint8_t q1 = alu1 & 0xF;
    bool    c1 = alu1 & 0b00010000;
    bool    z1 = alu1 & 0b00100000;
    bool    n1 = alu1 & 0b01000000;
    bool nclku = alu1 & 0b10000000;

    uint8_t q = q1<<4 | q0;
    if (!nclki) {
        Cint = c1;
    }
    if (!nclku) {
        C = c1;
        Z = z0 && z1;
        N = n1;
    }

    return q;
}

void clock_cycle(void) {

    // Decode

    uint8_t flagbits = N<<2 | Z<<1 | C;
    uint16_t addr = flagbits<<12 | opcode<<4 | (tick & 0xF);
    uint8_t d0 = dec0[addr];
    uint8_t d1 = dec1[addr];
    uint8_t d2 = dec2[addr];

    if (!(d0 & 0b1)) {
        // sig_next - reset tick and re-decode
        tick = 0;
        clock_cycle();
        return;
    }

    bool sig_aout  =   d0 & 0b00000010;
    bool sig_pcinc =  (d0 & 0b00000100);
    bool sig_pcwr  = !(d0 & 0b00001000);
    bool sig_irwr  = !(d0 & 0b00010000);
    bool sig_memrd = !(d0 & 0b00100000);
    bool sig_memwr = !(d0 & 0b01000000);
    bool sig_ainc  =  (d0 & 0b10000000);
    bool sig_ahwr  = !(d1 & 0b00000001);
    bool sig_alwr  = !(d1 & 0b00000010);
    bool sig_regoe = !(d1 & 0b00000100);
    bool sig_regwr = !(d1 & 0b00001000);
    uint8_t sig_opsel  = d1 >> 4;
    uint8_t sig_regsel = d2 & 0b111;
    bool sig_alu    =   !(d2 & 0b00001000);
    bool sig_twr    =    (d2 & 0b00010000);
    bool sig_setflags = !(d2 & 0b00100000);
    bool sig_msel     = !(d2 & 0b01000000);

    if (sig_msel) sig_regsel = 8;


    // Execute

    if (opcode == 0xFF) {
        halted = true;
        return;
    }

    uint16_t abus = sig_aout ? a : pc;

    // dbus writers
    uint8_t dbus;
    if (sig_memrd) {
        dbus = memory[abus];
    } else if (sig_alu) {
        uint8_t alu_a = sig_regoe ? regs[sig_regsel] : 0;
        dbus = do_alu(alu_a, sig_opsel, sig_setflags);
    }

    // dbus readers
    if (sig_memwr) {
        memwr(abus, dbus);
    }
    if (sig_irwr) {
        // Load new instruction
        opcode = dbus;
        instructions++;
    }
    if (sig_ahwr) {
        a &= 0x00FF;
        a |= dbus << 8;
    }
    if (sig_alwr) {
        a &= 0xFF00;
        a |= dbus;
    }
    if (sig_twr)    t = dbus;
    if (sig_regwr)  regs[sig_regsel] = dbus;

    if (sig_pcwr)   pc = abus;
    if (sig_pcinc)  pc++;
    if (sig_ainc)   a++;

    tick = (tick + 1) % 16;
    cycles++;
}





int read_rom(uint8_t *buffer, int buffer_size, char *filename) {

    FILE *f = fopen(filename, "rb");
    if (f == NULL) {
        printf("Error: can't open %s\n", filename);
        return -1;
    }

    size_t size = fread(buffer, 1, buffer_size, f);
    if (size != buffer_size) {
        printf("Error reading %s\n", filename);
        fclose(f);
        return -1;
    }

    fclose(f);
    return 0;

}

int main(int argc, char *argv[]) {

    if (read_rom(dec0, sizeof(dec0), "rom/decoder0.bin")) return -1;
    if (read_rom(dec1, sizeof(dec1), "rom/decoder1.bin")) return -1;
    if (read_rom(dec2, sizeof(dec2), "rom/decoder2.bin")) return -1;
    if (read_rom(alu,  sizeof(alu),  "rom/alu.bin")) return -1;

    memset(memory, 0xFF, MEM_SIZE);

    // Read input image file into memory
    FILE *f = fopen(argv[1], "rb");
    if (f == NULL) {
        printf("Error: can't open %s\n", argv[1]);
        return -1;
    }
    size_t size = fread(memory, 1, MEM_SIZE, f);
    if (size >= MEM_SIZE) {
        printf("Error: image is too large.\n");
        fclose(f);
        return -1;
    }
    fclose(f);

    // Run simulation
    run();

    printf("\n---\nStatistics:\n");
    printf("    %d instructions\n", instructions);
    printf("    %d cycles\n", cycles);
    float cpu_secs = (float)cycles / CPU_FREQ;
    float speed_percent = cpu_secs/sim_secs * 100.0f;
    printf("    %.3f sec at %.1f MHz (%.0f%% speed)\n", cpu_secs, CPU_FREQ/1000000.0f, speed_percent);
    
    uint16_t breg = regs[0]<<8 | regs[1];
    uint16_t creg = regs[2]<<8 | regs[3];
    uint16_t spreg = regs[6]<<8 | regs[7];
    printf("Registers:\n");
    printf("    b: 0x%04x %5d    c: 0x%04x %5d\n", breg, breg, creg, creg);
    printf("    x: 0x%02x   %5d    y: 0x%02x   %5d\n", regs[4], regs[4], regs[5], regs[5]);
    printf("   pc: 0x%04x %5d   sp: 0x%04x %5d\n", pc, pc, spreg, spreg);
    printf("flags: %c%c%c\n", C?'C':' ', Z?'Z':' ', N?'N':' ');


    
    return 0;
}