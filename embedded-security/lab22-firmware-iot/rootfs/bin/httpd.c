/* AngeRouter httpd — binaire embarqué MIPSEL
 * Vulnérabilité : stack overflow dans parse_auth()
 * Mot de passe hardcodé : AngeVirus{hardcoded_in_binary}
 */
#include <stdio.h>
#include <string.h>

static const char SECRET[] = "AngeVirus{hardcoded_in_binary}";
static const char PASS[]   = "AngeRouter2024!";

void parse_auth(const char *input) {
    char buf[64];
    strcpy(buf, input);   /* overflow intentionnel */
}

int main() {
    printf("AngeRouter httpd v2.1\n");
    printf("Auth key: %s\n", SECRET);
    return 0;
}
