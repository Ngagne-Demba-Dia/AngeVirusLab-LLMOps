#include <stdio.h>
#include <unistd.h>

void win() {
    printf(">>> FLAG : AngeVirus{stack_canary_bypassed} <<<\n");
}

void vulnerable() {
    char buffer[64];

    // Stage 1 : format string → leak canary
    printf("Leak     : ");
    fflush(stdout);
    read(0, buffer, 64);
    printf(buffer);           // VULNERABLE : format string
    fflush(stdout);

    // Stage 2 : overflow avec canary connu
    printf("Overflow : ");
    fflush(stdout);
    read(0, buffer, 200);     // overflow volontaire
}

int main() {
    vulnerable();
    return 0;
}
