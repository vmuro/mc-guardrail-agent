package com.guardrail.fido.controller;

import com.guardrail.fido.dto.EvaluationRequest;
import com.guardrail.fido.dto.EvaluationResponse;
import com.guardrail.fido.service.EvaluationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/evaluations")
@CrossOrigin(origins = "*")
public class EvaluationApiController {

    private static final Logger log = LoggerFactory.getLogger(EvaluationApiController.class);
    private final EvaluationService evaluationService;

    public EvaluationApiController(EvaluationService evaluationService) {
        this.evaluationService = evaluationService;
    }

    @PostMapping
    public ResponseEntity<?> evaluatePortfolio(@RequestBody EvaluationRequest request) {
        log.info("Recebida solicitação de avaliação via Servidor FIDO para cliente: {}", request.getClientId());
        try {
            EvaluationResponse response = evaluationService.requestEvaluation(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Erro ao solicitar avaliação ao Agente Python: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(Map.of(
                    "error", "Falha de comunicação com o Agente de Governança Python: " + e.getMessage(),
                    "clientId", request.getClientId() != null ? request.getClientId() : "N/A"
            ));
        }
    }

    @GetMapping("/clients")
    public ResponseEntity<List<Map<String, Object>>> getAvailableClients() {
        return ResponseEntity.ok(evaluationService.getAvailableClients());
    }
}
