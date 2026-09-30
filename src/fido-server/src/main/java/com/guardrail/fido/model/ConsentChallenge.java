package com.guardrail.fido.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class ConsentChallenge {
    private String challengeId;
    private String clientId;
    private String userHandle;
    private String orderHash;
    private String canonicalPayload;
    private int ttlSeconds;
    private Instant createdAt;
    private Instant expiresAt;
    private String status; // PENDING, APPROVED, REJECTED, EXPIRED
    private String signatureId;
    private String clientDataJson;
}
