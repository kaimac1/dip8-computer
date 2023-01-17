#define size 8191

unsigned char flags[size];

int main(void) {

    unsigned int count = 0;
    unsigned int prime;
    unsigned int k;

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
            count++;
        }
    }

    return count;

}
