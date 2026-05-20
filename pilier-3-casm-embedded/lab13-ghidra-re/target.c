#include <stdio.h>
#include <string.h>

void win() {
    printf(">>> FLAG : AngeVirus{ghidra_reverse_engineering} <<<\n");
}

// Mot de passe encode XOR 0x13 — invisible dans strings
// Defi : retrouver le mot de passe par analyse statique/dynamique
int check(const char* input) {
    unsigned char encoded[] = {
        0x40, 0x7b, 0x72, 0x77, 0x7c, 0x64,  // S h a d o w
        0x51, 0x6a, 0x67, 0x76, 0x60,         // B y t e s
        0x00
    };
    char decoded[12];
    for (int i = 0; i < 11; i++)
        decoded[i] = encoded[i] ^ 0x13;
    decoded[11] = '\0';

    return strcmp(input, decoded) == 0;
}

int main() {
    char input[64];
    printf("Password : ");
    fgets(input, sizeof(input), stdin);
    input[strcspn(input, "\n")] = 0;

    if (check(input))
        win();
    else
        printf("Wrong password.\n");

    return 0;
}
