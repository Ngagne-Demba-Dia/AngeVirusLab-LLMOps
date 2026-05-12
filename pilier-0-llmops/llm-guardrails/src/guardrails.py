import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RailDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass
class RailResult:
    decision: RailDecision
    reason: Optional[str] = None
    threat_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Input rail — prompt injection patterns
# ---------------------------------------------------------------------------

INJECTION_PATTERNS = [
    (r"ignore\s+(tes|les|vos|previous|your|all)\s+(instructions|directives|règles|rules)", "instruction_override"),
    (r"(tu es|you are|vous êtes)\s+maintenant", "identity_override"),
    (r"\bDAN\b", "dan_jailbreak"),
    (r"(oublie|forget|ignore)\s+(tout|everything|all|previous)", "context_wipe"),
    (r"(pretend|fais semblant|act as|agis comme).{0,40}(no restriction|sans restriction|unrestricted)", "persona_jailbreak"),
    (r"(system|système)\s*:", "system_prompt_injection"),
    (r"<\s*(system|assistant|user)\s*>", "role_tag_injection"),
    (r"\[\s*(system|SYSTEM|INST)\s*\]", "instruction_tag_injection"),
    (r"(réponds|respond|answer).{0,30}(sans restriction|without restriction|ignoring\s+rule)", "behavior_override"),
    (r"(new\s+instructions?|nouvelles?\s+instructions?)\s*:", "instruction_hijack"),
]

# ---------------------------------------------------------------------------
# Input rail — contenu dangereux / requêtes malveillantes
# ---------------------------------------------------------------------------

HARMFUL_CONTENT_PATTERNS = [
    (r"(crée|créer|développer|coder|écrire|fabriquer|construire).{0,40}(virus|malware|ransomware|cheval de troie|trojan|keylogger|botnet|worm|ver informatique)", "malware_creation"),
    (r"(pirater|hacker|hack|compromettre|accéder sans autorisation).{0,50}(wifi|réseau|serveur|base de données|compte|système|mot de passe)", "unauthorized_hacking"),
    (r"(comment|how to|étapes pour|guide pour|tutoriel).{0,30}(pirater|hacker|cracker|exploiter|bypass|contourner).{0,40}(sans autorisation|illegalement|sans permission)", "hacking_tutorial"),
    (r"(bombe|explosif|détonateur|nitrate|TNT|IED|engin explosif|dispositif explosif)", "explosive_device"),
    (r"(synthèse|fabriquer|créer|produire).{0,40}(drogue|stupéfiant|méthamphétamine|fentanyl|héroïne|cocaine|poison)", "illegal_substance"),
    (r"(injection sql|sql injection).{0,40}(voler|extraire|dump|exfiltrer).{0,30}(données|password|mot de passe|users|table)", "sql_attack"),
    (r"(comment|how).{0,20}(tuer|assassiner|empoisonner).{0,30}(personne|quelqu'un|someone|une cible)", "violence"),
    (r"(ransomware|cryptolocker).{0,40}(déployer|lancer|distribuer|propager|créer)", "ransomware_deployment"),
    (r"(ddos|déni de service|denial of service).{0,30}(lancer|attaquer|cibler|flooder)", "ddos_attack"),
    (r"(phishing|hameçonnage).{0,40}(créer|monter|configurer|déployer|campagne)", "phishing_campaign"),
    (r"(scanner|scan).{0,30}(ports?|vulnerabilit|services).{0,40}(ip|cible|adresse|reseau)", "port_scanner"),
    (r"(brute\s*force|force brute|automatiser).{0,40}(connexion|login|mot de passe|password|tentatives)", "brute_force"),
    (r"(keylogger|key\s*logger|capturer.{0,20}touches|enregistrer.{0,20}frappe)", "keylogger"),
    (r"(fausse page|fake.{0,10}page|page.{0,20}phishing).{0,40}(connexion|login|bancaire|identifiant)", "phishing_page"),
    (r"(capture|capturer|voler|recuperer).{0,30}(identifiants|credentials|mots de passe|logins).{0,30}(victime|utilisateur|saisi)", "credential_harvesting"),
]

# ---------------------------------------------------------------------------
# Output rail — dangerous content patterns
# ---------------------------------------------------------------------------

DANGEROUS_OUTPUT_PATTERNS = [
    (r"\brm\s+-rf\b", "destructive_command"),
    (r"\bsudo\b.{0,30}\b(rm|chmod|chown|kill|shutdown)\b", "privileged_command"),
    (r"\b(DELETE|DROP|TRUNCATE)\s+(FROM|TABLE|DATABASE)\b", "sql_destructive"),
    (r"\b(sk-|pk-lf-|ghp_|AKIA)[A-Za-z0-9]{10,}", "api_key_leak"),
    (r"(password|mot de passe|passwd)\s*[:=]\s*\S{4,}", "credential_leak"),
    (r"wget\s+.{0,60}\|\s*(sh|bash|python)", "remote_execution"),
    (r"\b(eval|exec)\s*\(.{0,100}\)", "code_injection"),
    (r"os\.system\s*\(", "os_command_injection"),
]


class InputRail:
    def check(self, user_input: str) -> RailResult:
        for pattern, threat_type in INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return RailResult(
                    decision=RailDecision.BLOCK,
                    reason=f"Injection détectée : {threat_type}",
                    threat_type=threat_type,
                )
        for pattern, threat_type in HARMFUL_CONTENT_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return RailResult(
                    decision=RailDecision.BLOCK,
                    reason=f"Contenu dangereux : {threat_type}",
                    threat_type=threat_type,
                )
        return RailResult(decision=RailDecision.ALLOW)


class OutputRail:
    def check(self, llm_output: str) -> RailResult:
        for pattern, threat_type in DANGEROUS_OUTPUT_PATTERNS:
            if re.search(pattern, llm_output, re.IGNORECASE):
                return RailResult(
                    decision=RailDecision.BLOCK,
                    reason=f"Contenu dangereux : {threat_type}",
                    threat_type=threat_type,
                )
        return RailResult(decision=RailDecision.ALLOW)


class GuardedAgent:
    def __init__(self, llm, langfuse_handler=None):
        self.llm = llm
        self.input_rail = InputRail()
        self.output_rail = OutputRail()
        self.langfuse_handler = langfuse_handler

    def invoke(self, user_input: str, run_name: str = "guarded_call") -> dict:
        # Stage 1 — input rail
        input_result = self.input_rail.check(user_input)
        if input_result.decision == RailDecision.BLOCK:
            return {
                "status": "BLOCKED",
                "stage": "input",
                "threat": input_result.threat_type,
                "reason": input_result.reason,
                "response": "⛔ Requête bloquée : tentative de manipulation détectée.",
            }

        # Stage 2 — LLM call (only reached if input is clean)
        config = {"run_name": run_name}
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]

        response = self.llm.invoke(user_input, config=config)

        # Stage 3 — output rail
        output_result = self.output_rail.check(response)
        if output_result.decision == RailDecision.BLOCK:
            return {
                "status": "BLOCKED",
                "stage": "output",
                "threat": output_result.threat_type,
                "reason": output_result.reason,
                "response": "⛔ Réponse bloquée : contenu dangereux dans l'output du LLM.",
            }

        return {
            "status": "ALLOWED",
            "response": response,
        }
