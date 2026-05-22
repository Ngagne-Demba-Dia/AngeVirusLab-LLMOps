#include <stdio.h>
#include <unistd.h>

// Gadget pop rdi ; ret pour les ROP chains
__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");

int main();

void vulnerable() {
    char buffer[64];

    printf("main @ %p\n", main);   // PIE leak automatique

    puts("Leak :");                 // force puts dans PLT (necessaire pour leak libc)
    fflush(stdout);
    read(0, buffer, 64);
    printf(buffer);                 // VULNERABLE : format string → canary leak
    fflush(stdout);

    puts("Overflow :");
    fflush(stdout);
    read(0, buffer, 200);          // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
