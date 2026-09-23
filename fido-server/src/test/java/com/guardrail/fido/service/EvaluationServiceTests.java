package com.guardrail.fido.service;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class EvaluationServiceTests {

    @Test
    void testGetAvailableClients() {
        EvaluationService service = new EvaluationService("http://localhost:8000");
        List<Map<String, Object>> clients = service.getAvailableClients();

        assertNotNull(clients);
        assertEquals(3, clients.size());
        assertEquals("CLI-001", clients.get(0).get("clientId"));
        assertEquals("CLI-002", clients.get(1).get("clientId"));
        assertEquals("CLI-003", clients.get(2).get("clientId"));
    }

    @Test
    void testFetchGcpIdentityTokenGracefullyFailsLocally() {
        EvaluationService service = new EvaluationService("https://guardrail-agent-service-test.run.app");
        // Fora do GCP, metadata.google.internal não responde, devendo retornar null com segurança
        String token = service.fetchGcpIdentityToken("https://guardrail-agent-service-test.run.app");
        assertNull(token);
    }
}
