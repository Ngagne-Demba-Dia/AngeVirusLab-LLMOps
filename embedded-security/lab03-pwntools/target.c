#include <stdio.h>
#include <unistd.h>

void win() {
    printf(">>> FLAG : AngeVirus{pwntools_ret2win_success} <<<\n");
}

void vulnerable() {
    char buffer[64];
    printf("Input : ");
    fflush(stdout);
    read(0, buffer, 200);
}

int main() {
    vulnerable();
    return 0;
}
