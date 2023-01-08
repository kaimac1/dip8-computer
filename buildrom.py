# Take out.bin (output from the assembler) and generate a 64KB image
# with it placed at 0xC000 (the boot block in ROM)

# As the boot block is mapped to 0x0000, addresses in the assembled code
# do not need to change.


with open('out.bin', 'rb') as f:
    prog = f.read()

BOOT_BLOCK = 0xC000


out = b'\xff' * 65536
out = bytearray(out)
out[BOOT_BLOCK:BOOT_BLOCK+len(prog)] = prog

with open('rom.bin', 'wb') as f:
    f.write(out)