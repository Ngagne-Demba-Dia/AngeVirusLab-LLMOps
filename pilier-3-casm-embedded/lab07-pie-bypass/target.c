#include <stdio.h>
#include <unistd.h>

// Gadget explicite : pop rdi ; ret
__asm__(".global pop_rdi\npop_rdi:\n\tpop %rdi\n\tret\n");

int main();  // declaration anticipee pour l'utiliser comme pointeur dans vulnerable()

void vulnerable() {
    char buffer[64];

    // PIE leak : affiche l'adresse reelle de main → permet de calculer la base PIE
    printf("main @ %p\n", main);
    puts("Input :");
    fflush(stdout);
    read(0, buffer, 200);
}

int main() {
    vulnerable();
    return 0;
}
