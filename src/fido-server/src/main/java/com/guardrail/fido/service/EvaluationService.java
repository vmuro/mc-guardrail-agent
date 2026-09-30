package com.guardrail.fido.service;

import com.guardrail.fido.dto.EvaluationRequest;
import com.guardrail.fido.dto.EvaluationResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

@Service
public class EvaluationService {

    private static final Logger log = LoggerFactory.getLogger(EvaluationService.class);
    private final RestClient restClient;
    private final String agentPythonUrl;
    private final ConsentService consentService;

    public EvaluationService(String agentPythonUrl) {
        this(agentPythonUrl, new ConsentService());
    }

    @org.springframework.beans.factory.annotation.Autowired
    public EvaluationService(
            @Value("${agent.python.url:http://localhost:8000}") String agentPythonUrl,
            ConsentService consentService) {
        this.agentPythonUrl = agentPythonUrl.replaceAll("/+$", "");
        this.consentService = consentService;
        log.info("Inicializando EvaluationService apontando para o Agente Python em: {}", this.agentPythonUrl);
        this.restClient = RestClient.builder()
                .baseUrl(this.agentPythonUrl)
                .build();
    }

    public EvaluationResponse requestEvaluation(EvaluationRequest request) {
        log.info("Encaminhando solicitação de avaliação para o Agente Python: clientId={}, budget={}, riskProfile={}",
                request.getClientId(), request.getBudget(), request.getRiskProfile());

        var requestSpec = restClient.post()
                .uri("/api/evaluate")
                .contentType(MediaType.APPLICATION_JSON);

        // Se a chamada for via HTTPS (Cloud Run), obtém o Identity Token OIDC no GCP Metadata Server
        if (this.agentPythonUrl.startsWith("https://")) {
            String token = fetchGcpIdentityToken(this.agentPythonUrl);
            if (token != null && !token.isBlank()) {
                log.info("Identity Token obtido com sucesso. Anexando Authorization: Bearer para invocação no Cloud Run.");
                requestSpec.header("Authorization", "Bearer " + token);
            }
        }

        EvaluationResponse response = requestSpec
                .body(request)
                .retrieve()
                .body(EvaluationResponse.class);

        // Garantia Determinística: Assegura que todo desafio aprovado retornado pelo Python esteja presente no ConsentService em memória
        if (response != null && response.getApprovedOrders() != null) {
            for (Map<String, Object> ord : response.getApprovedOrders()) {
                String challengeId = (String) ord.get("challengeId");
                if (challengeId != null && consentService.getChallenge(challengeId).isEmpty()) {
                    try {
                        String canonicalPayload = ord.get("canonicalPayload") != null
                                ? String.valueOf(ord.get("canonicalPayload"))
                                : String.format("{\"action\":\"%s\",\"quantity\":%s,\"ticker\":\"%s\",\"total_cost\":%s,\"unit_price\":%s,\"rationale\":\"%s\"}",
                                        ord.get("action"), ord.get("quantity"), ord.get("ticker"), ord.get("totalCost"), ord.get("unitPrice"), ord.get("rationale"));

                        String orderHash = ord.get("orderHash") != null
                                ? String.valueOf(ord.get("orderHash"))
                                : challengeId;

                        int ttl = ord.get("ttlSeconds") instanceof Number
                                ? ((Number) ord.get("ttlSeconds")).intValue()
                                : 120;

                        com.guardrail.fido.model.ConsentChallenge challenge = com.guardrail.fido.model.ConsentChallenge.builder()
                                .challengeId(challengeId)
                                .clientId(response.getClientId() != null ? response.getClientId() : request.getClientId())
                                .userHandle("user_" + (response.getClientId() != null ? response.getClientId() : "retail").toLowerCase().replace("-", "_"))
                                .orderHash(orderHash)
                                .canonicalPayload(canonicalPayload)
                                .ttlSeconds(ttl)
                                .status("PENDING")
                                .build();

                        consentService.registerChallenge(challenge);
                        log.info("Desafio {} registrado preventivamente no ConsentService.", challengeId);
                    } catch (Exception e) {
                        log.warn("Erro ao registrar desafio preventivo {}: {}", challengeId, e.getMessage());
                    }
                }
            }
        }

        return response;
    }

    /**
     * Obtém um Identity Token (JWT) do GCP Metadata Server para chamadas autenticadas entre Cloud Run Services.
     * Funciona nativamente quando executado dentro do Google Cloud. Em ambiente local, retorna null com segurança.
     */
    protected String fetchGcpIdentityToken(String audience) {
        try {
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(2))
                    .build();

            String metadataUrl = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=" + audience;
            HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(metadataUrl))
                    .header("Metadata-Flavor", "Google")
                    .timeout(Duration.ofSeconds(3))
                    .GET()
                    .build();

            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() == 200) {
                return resp.body().trim();
            } else {
                log.warn("GCP Metadata Server retornou status {} para audience={}", resp.statusCode(), audience);
            }
        } catch (Exception e) {
            log.debug("Metadata Server indisponível (normal fora do GCP): {}", e.getMessage());
        }
        return null;
    }

    public List<Map<String, Object>> getAvailableClients() {
        return List.of(
                Map.of(
                        "clientId", "CLI-001",
                        "name", "Investidor Conservador",
                        "riskProfile", "CONSERVATIVE",
                        "budget", 5000.0,
                        "defaultWatchlist", List.of("PETR4.SA", "VALE3.SA")
                ),
                Map.of(
                        "clientId", "CLI-002",
                        "name", "Investidor Moderado",
                        "riskProfile", "MODERATE",
                        "budget", 10000.0,
                        "defaultWatchlist", List.of("PETR4.SA", "ITUB4.SA", "BBAS3.SA")
                ),
                Map.of(
                        "clientId", "CLI-003",
                        "name", "Investidor Agressivo",
                        "riskProfile", "AGGRESSIVE",
                        "budget", 20000.0,
                        "defaultWatchlist", List.of("PRIO3.SA", "VALE3.SA", "WEGE3.SA")
                )
        );
    }
}
