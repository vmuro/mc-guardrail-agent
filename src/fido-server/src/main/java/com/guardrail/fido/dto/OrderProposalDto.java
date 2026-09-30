package com.guardrail.fido.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderProposalDto {
    private String ticker;
    private String action; // BUY, SELL
    private Integer quantity;
    private Double unitPrice;
    private Double totalCost;
    private Double stopLossPrice;
    private String rationale;
}
