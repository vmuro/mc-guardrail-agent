package com.guardrail.fido.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EvaluationResponse {
    private String evaluationId;
    private String clientId;
    private String clientName;
    private String riskProfile;
    private Double budget;
    private Double totalAllocated;
    private Double remainingBudget;
    private Boolean isValid;
    private String summary;
    private String portfolioRationale;
    private List<Map<String, Object>> approvedOrders;
    private List<Map<String, Object>> rejectedOrders;
    private List<Map<String, Object>> regulatoryConsents;
    private Integer ttlSeconds;
    private Boolean notificationsSent;
}
