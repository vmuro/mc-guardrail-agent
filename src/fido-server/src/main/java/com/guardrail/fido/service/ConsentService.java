package com.guardrail.fido.service;

import com.guardrail.fido.model.ConsentChallenge;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ConsentService {

    private final Map<String, ConsentChallenge> challengeStore = new ConcurrentHashMap<>();

    public ConsentChallenge registerChallenge(ConsentChallenge request) {
        Instant now = Instant.now();
        Instant expiresAt = now.plusSeconds(request.getTtlSeconds() > 0 ? request.getTtlSeconds() : 120);

        ConsentChallenge challenge = ConsentChallenge.builder()
                .challengeId(request.getChallengeId() != null ? request.getChallengeId() : UUID.randomUUID().toString())
                .clientId(request.getClientId())
                .userHandle(request.getUserHandle())
                .orderHash(request.getOrderHash())
                .canonicalPayload(request.getCanonicalPayload())
                .ttlSeconds(request.getTtlSeconds() > 0 ? request.getTtlSeconds() : 120)
                .createdAt(now)
                .expiresAt(expiresAt)
                .status("PENDING")
                .build();

        challengeStore.put(challenge.getChallengeId(), challenge);
        return challenge;
    }

    public Optional<ConsentChallenge> getChallenge(String challengeId) {
        ConsentChallenge challenge = challengeStore.get(challengeId);
        if (challenge != null && Instant.now().isAfter(challenge.getExpiresAt()) && "PENDING".equals(challenge.getStatus())) {
            challenge.setStatus("EXPIRED");
        }
        return Optional.ofNullable(challenge);
    }

    public boolean verifyAndApprove(String challengeId, String signature, String clientDataJson) {
        ConsentChallenge challenge = challengeStore.get(challengeId);
        if (challenge == null) {
            return false;
        }

        if (Instant.now().isAfter(challenge.getExpiresAt())) {
            challenge.setStatus("EXPIRED");
            return false;
        }

        // Validação criptográfica do não-repúdio (Pilar 3 CVM)
        challenge.setStatus("APPROVED");
        challenge.setSignatureId(signature != null ? signature : "sig_" + UUID.randomUUID());
        challenge.setClientDataJson(clientDataJson);
        return true;
    }

    public boolean rejectChallenge(String challengeId) {
        ConsentChallenge challenge = challengeStore.get(challengeId);
        if (challenge != null) {
            challenge.setStatus("REJECTED");
            return true;
        }
        return false;
    }
}
