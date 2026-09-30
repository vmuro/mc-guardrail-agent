package com.guardrail.fido.controller;

import com.guardrail.fido.dto.EvaluationRequest;
import com.guardrail.fido.dto.EvaluationResponse;
import com.guardrail.fido.service.EvaluationService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class EvaluationApiControllerTests {

    @Mock
    private EvaluationService evaluationService;

    @InjectMocks
    private EvaluationApiController controller;

    @Test
    void testGetAvailableClients() {
        when(evaluationService.getAvailableClients()).thenReturn(List.of(
                Map.of("clientId", "CLI-001", "name", "Investidor Conservador")
        ));

        ResponseEntity<List<Map<String, Object>>> response = controller.getAvailableClients();
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().size());
        assertEquals("CLI-001", response.getBody().get(0).get("clientId"));
    }

    @Test
    void testEvaluatePortfolioSuccess() {
        EvaluationRequest request = EvaluationRequest.builder()
                .clientId("CLI-001")
                .budget(5000.0)
                .riskProfile("CONSERVATIVE")
                .watchlist(List.of("PETR4.SA"))
                .build();

        EvaluationResponse mockResponse = EvaluationResponse.builder()
                .evaluationId("eval-test-123")
                .clientId("CLI-001")
                .isValid(true)
                .summary("Aprovado com sucesso")
                .build();

        when(evaluationService.requestEvaluation(any(EvaluationRequest.class))).thenReturn(mockResponse);

        ResponseEntity<?> response = controller.evaluatePortfolio(request);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertInstanceOf(EvaluationResponse.class, response.getBody());
        EvaluationResponse body = (EvaluationResponse) response.getBody();
        assertEquals("eval-test-123", body.getEvaluationId());
    }

    @Test
    void testEvaluatePortfolioError() {
        EvaluationRequest request = EvaluationRequest.builder()
                .clientId("CLI-001")
                .budget(5000.0)
                .build();

        when(evaluationService.requestEvaluation(any(EvaluationRequest.class)))
                .thenThrow(new RuntimeException("Connection refused to Python agent"));

        ResponseEntity<?> response = controller.evaluatePortfolio(request);
        assertEquals(HttpStatus.BAD_GATEWAY, response.getStatusCode());
        assertTrue(response.getBody() instanceof Map);
    }
}
