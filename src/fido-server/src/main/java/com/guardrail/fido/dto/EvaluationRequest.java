package com.guardrail.fido.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EvaluationRequest {
    private String clientId;
    private Double budget;
    private String riskProfile;
    private List<String> watchlist;
    private List<OrderProposalDto> orders;
    private String clientName;
    private String segment;
    private String deviceToken;
}
