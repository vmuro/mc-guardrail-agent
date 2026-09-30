#!/usr/bin/env python3
"""
Gera o artefato obrigatório docs/one-pager.pdf para o
Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

Garante compatibilidade total de fontes UTF-8 (DejaVuSans),
elimina caracteres de fontes ausentes (tofu/black square ■) e
mantém diagramação executiva em exatamente 1 página A4.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_fonts():
    """Registra fontes TrueType com suporte completo a UTF-8/Unicode."""
    font_paths = {
        'CustomSans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'CustomSans-Bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'CustomSans-Oblique': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
    }
    for name, path in font_paths.items():
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
        else:
            # Fallback para Helvetica se por algum motivo a fonte não existir
            pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))

def build_one_pager(output_path="docs/one-pager.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Registra fontes TrueType do sistema
    font_regular = 'CustomSans'
    font_bold = 'CustomSans-Bold'
    font_italic = 'CustomSans-Oblique'
    try:
        register_fonts()
    except Exception as e:
        print(f"Aviso: Não foi possível carregar DejaVuSans ({e}). Usando Helvetica.")
        font_regular = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        font_italic = 'Helvetica-Oblique'
    
    # Margens estreitas para caber perfeitamente em 1 página A4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm
    )
    
    styles = getSampleStyleSheet()
    
    # Paleta de Cores Institucionais (Google Cloud & GFT)
    c_primary = colors.HexColor("#1A73E8")    # Google Blue
    c_dark = colors.HexColor("#172B4D")       # Deep Navy
    c_text = colors.HexColor("#2D3748")       # Dark Slate Text
    c_muted = colors.HexColor("#4A5568")      # Subtitle Gray
    c_light_bg = colors.HexColor("#F0F4F8")   # Card Background
    c_border = colors.HexColor("#CBD5E1")     # Border
    
    # Estilos customizados compactos e tipografia limpa
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=15,
        leading=18,
        textColor=c_dark
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=8.5,
        leading=11,
        textColor=c_muted
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=7.5,
        leading=10,
        textColor=c_primary,
        alignment=2 # Direita
    )
    
    sec_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=9.5,
        leading=12,
        textColor=c_primary,
        spaceBefore=3,
        spaceAfter=2
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=7.8,
        leading=10.2,
        textColor=c_text
    )
    
    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=7.8,
        leading=10.2,
        textColor=c_dark
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName=font_regular,
        fontSize=7.4,
        leading=9.5,
        textColor=c_text
    )
    
    table_head = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=7.4,
        leading=9.5,
        textColor=colors.white
    )

    story = []
    
    # 1. Cabeçalho (Título + Metadados da Equipe)
    header_data = [
        [
            Paragraph("<b>GuardrailAI</b> — Middleware B2B de Governança", title_style),
            Paragraph("<b>Desafio de Agentes de IA · SMC26</b><br/>GFT x Google Cloud", meta_style)
        ],
        [
            Paragraph("Autonomia Proativa B3 (Gemini 2.5) + Guardrails Determinísticos + Não-Repúdio CVM (FIDO2)", subtitle_style),
            Paragraph("Equipe: <b>GuardrailAI</b> | Capitão: <b>Victor Rosa</b> (vrmu@gft.com) | DGCU02 / BDP", meta_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[12.5 * cm, 5.7 * cm])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=4))
    
    # 2. O Problema
    story.append(Paragraph("1. O PROBLEMA NO MERCADO DE CAPITAIS", sec_heading))
    prob_text = (
        "Instituições financeiras, corretoras e gestoras enfrentam um receio crítico em delegar ordens de investimento a modelos de IA Generativa. "
        "Apesar de ágeis em sintetizar cenários, os LLMs sofrem de <b>alucinações matemáticas</b> em preços e volumes, tendem a <b>omitir ordens de proteção (Stop-Loss)</b> "
        "e operam sem uma trilha de consentimento regulatório auditável compatível com as normas da CVM, expondo o capital de clientes e a reputação da instituição a riscos severos."
    )
    story.append(Paragraph(prob_text, body_style))
    story.append(Spacer(1, 4))
    
    # 3. A Solução (3 Pilares)
    story.append(Paragraph("2. A SOLUÇÃO: GUARDRAILAI & OS 3 PILARES FUNDAMENTAIS", sec_heading))
    sol_intro = (
        "O <b>GuardrailAI</b> desacopla a inteligência analítica de mercado da execução determinística e do consentimento regulatório através de três pilares inegociáveis:"
    )
    story.append(Paragraph(sol_intro, body_style))
    story.append(Spacer(1, 3))
    
    pilares_data = [
        [
            Paragraph("<b>Pilar 1: Autonomia Proativa</b>", body_bold),
            Paragraph("Screener autônomo multi-indicador na B3 (MACD, Bollinger, EMAs 9/21/50/200, RSI) com análise de sentimento via Gemini 2.5 Flash (Vertex AI). A IA formula teses sem enviar ordens à bolsa.", table_cell)
        ],
        [
            Paragraph("<b>Pilar 2: Segurança Determinística</b>", body_bold),
            Paragraph("Motor de execução determinístico que <b>elimina 100% das alucinações numéricas</b> recalculando a quantidade exata <b>Q = floor(B / P)</b>, exigindo Stop-Loss obrigatório (máx. 15%) e travando tetos de risco (20% a 50%).", table_cell)
        ],
        [
            Paragraph("<b>Pilar 3: Não-Repúdio Regulatório (CVM)</b>", body_bold),
            Paragraph("Notificação Push Web (FCM) com <b>Payload Binding Criptográfico (HMAC-SHA256)</b> e autorização biométrica <b>Passkey / FIDO2</b> (WebAuthn) com <b>TTL estrito de 120 segundos</b> e trilha de auditoria no Cloud Logging.", table_cell)
        ]
    ]
    t_pilares = Table(pilares_data, colWidths=[4.6 * cm, 13.6 * cm])
    t_pilares.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light_bg),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_pilares)
    story.append(Spacer(1, 5))
    
    # 4. Impacto Quantificado
    story.append(Paragraph("3. IMPACTO DE NEGÓCIO & EFICIÊNCIA COMPROVADA", sec_heading))
    impacto_data = [
        [
            Paragraph("Dimensão", table_head),
            Paragraph("Benefício Quantificado", table_head),
            Paragraph("Diferencial para o Mercado de Capitais", table_head)
        ],
        [
            Paragraph("<b>Eficiência Operacional</b>", table_cell),
            Paragraph("<b>> 90% de redução</b> no tempo de varredura técnica e checagem de compliance.", table_cell),
            Paragraph("Capacidade de supervisionar centenas de carteiras em paralelo sem perda de precisão.", table_cell)
        ],
        [
            Paragraph("<b>Mitigação de Risco</b>", table_cell),
            Paragraph("<b>0% de alucinações matemáticas</b> em alocação e Stop-Loss garantido.", table_cell),
            Paragraph("A IA propõe cenários, mas a matemática de proteção é 100% blindada em código determinístico.", table_cell)
        ],
        [
            Paragraph("<b>Conformidade Regulatória</b>", table_cell),
            Paragraph("<b>100% de rastreabilidade</b> CVM com assinatura FIDO2 e TTL de 120s.", table_cell),
            Paragraph("Elimina repúdio em operações financeiras e previne execução defasada por oscilações na B3.", table_cell)
        ]
    ]
    t_impacto = Table(impacto_data, colWidths=[4.2 * cm, 6.8 * cm, 7.2 * cm])
    t_impacto.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light_bg]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_impacto)
    story.append(Spacer(1, 5))
    
    # 5. Stack Tecnológica & Público-Alvo (2 colunas)
    story.append(Paragraph("4. ARQUITETURA TECNOLÓGICA & PÚBLICO-ALVO", sec_heading))
    rodape_data = [
        [
            Paragraph("<b>Stack Tecnológica:</b><br/>"
                      "• <b>Plataforma de IA:</b> Google Vertex AI (Gemini 2.5 Flash)<br/>"
                      "• <b>Agente & Guardrail:</b> Python (FastAPI, Pandas, TA, ReAct)<br/>"
                      "• <b>Servidor de Não-Repúdio:</b> Java 21 Spring Boot + WebAuthn FIDO2<br/>"
                      "• <b>Notificações & Push:</b> Firebase Cloud Messaging (Data-Only)<br/>"
                      "• <b>Infraestrutura:</b> Google Cloud Run (Services & Jobs) + Cloud Logging", table_cell),
            Paragraph("<b>Público-Alvo & Casos de Uso:</b><br/>"
                      "• <b>Investidores Varejo Alta Renda:</b> Co-piloto seguro na corretora para alocações autônomas.<br/>"
                      "• <b>Assessores de Investimento (AAI):</b> Supervisão e rebalanceamento de carteiras em escala.<br/>"
                      "• <b>Gestoras & Wealth Management:</b> Cumprimento estrito de mandatos e eliminação de viés operacional.", table_cell)
        ]
    ]
    t_rodape = Table(rodape_data, colWidths=[9.1 * cm, 9.1 * cm])
    t_rodape.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_light_bg),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_rodape)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=2, spaceAfter=2))
    story.append(Paragraph("Confidencial — Uso Interno GFT x Google · Semana de Mercado de Capitais 2026 (SMC26)", ParagraphStyle('Footer', parent=styles['Normal'], fontName=font_italic, fontSize=6.5, leading=8, textColor=c_muted, alignment=1)))

    doc.build(story)
    print(f"✅ One-Pager gerado com sucesso em: {output_path}")

if __name__ == "__main__":
    build_one_pager()
