#include <stdio.h>
#include <unistd.h>

// Gadget explicite : pop rdi ; ret
// Necessaire pour respecter la convention d'appel x86-64 (1er arg dans RDI)
// En prod, on cherche ce gadget dans la libc
__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");

void vulnerable() {
    char buffer[64];
    puts("Input :");
    fflush(stdout);        // force le flush en mode pipe
    read(0, buffer, 200);
}

int main() {
    vulnerable();
    return 0;
}
