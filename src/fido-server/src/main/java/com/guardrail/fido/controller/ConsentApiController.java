package com.guardrail.fido.controller;

import com.guardrail.fido.model.ConsentChallenge;
import com.guardrail.fido.service.ConsentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/consent")
@CrossOrigin(origins = "*") // Permite chamadas do WebApp mobile
public class ConsentApiController {

    private final ConsentService consentService;

    public ConsentApiController(ConsentService consentService) {
        this.consentService = consentService;
    }

    @PostMapping("/challenges")
    public ResponseEntity<ConsentChallenge> createChallenge(@RequestBody ConsentChallenge request) {
        ConsentChallenge challenge = consentService.registerChallenge(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(challenge);
    }

    @GetMapping("/status/{challengeId}")
    public ResponseEntity<?> getStatus(@PathVariable String challengeId) {
        return consentService.getChallenge(challengeId)
                .<ResponseEntity<?>>map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Challenge não encontrado")));
    }

    @PostMapping("/verify")
    public ResponseEntity<?> verifyConsent(@RequestBody Map<String, String> payload) {
        String challengeId = payload.get("challengeId");
        String signature = payload.get("signature");
        String clientDataJson = payload.get("clientDataJson");

        boolean approved = consentService.verifyAndApprove(challengeId, signature, clientDataJson);
        if (approved) {
            return ResponseEntity.ok(Map.of("status", "APPROVED", "message", "Assinatura biométrica validada com sucesso!"));
        } else {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("status", "REJECTED", "message", "Desafio expirado ou inválido."));
        }
    }
}
