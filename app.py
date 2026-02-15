import streamlit as st
from reportlab.lib.pagesizes import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
from datetime import datetime
import babel.dates

# --- INICIALIZAÇÃO DO ESTADO ---
if 'lista_saidas' not in st.session_state:
    st.session_state.lista_saidas = []

# --- FUNÇÃO PDF TÉRMICO (RESTAURANDO LINHAS) ---
def gerar_pdf_termico_final(dados, lista_saidas):
    buffer = io.BytesIO()
    largura_papel = 72 * mm
    altura_dinamica = 160 * mm + (len(lista_saidas) * 10 * mm)
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(largura_papel, altura_dinamica),
        rightMargin=2*mm, leftMargin=2*mm, topMargin=5*mm, bottomMargin=5*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    estilo_base = ParagraphStyle('Base', fontSize=8, leading=10)
    estilo_dir = ParagraphStyle('Dir', parent=estilo_base, alignment=2)
    estilo_titulo = ParagraphStyle('Tit', fontSize=10, alignment=1, fontName='Helvetica-Bold')
    estilo_data = ParagraphStyle('Data', fontSize=9, alignment=1, spaceAfter=8)

    # Helpers para Formatação Correta (Negrito Real)
    def p_neg(t): return Paragraph(f"<b>{t}</b>", estilo_base)
    def p_val(t): return Paragraph(t, estilo_dir)
    def p_val_neg(t): return Paragraph(f"<b>{t}</b>", estilo_dir)

    # Cabeçalho
    elements.append(Paragraph("FECHAMENTO DE CAIXA", estilo_titulo))
    elements.append(Paragraph(dados['data_extenso'], estilo_data))

    # Estilo de Tabela com Linhas de Separação (GRID)
    estilo_tab = TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black), # Linha após título da seção
        ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.black), # Linha antes do total
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ])

    # 1. VENDAS
    data_v = [
        [p_neg("1. VENDAS"), ""],
        ["Delivery", p_val(f"R$ {dados['v_del']:,.2f}")],
        ["Balcão", p_val(f"R$ {dados['v_bal']:,.2f}")],
        ["Mesa", p_val(f"R$ {dados['v_mes']:,.2f}")],
        [p_neg("TOTAL VENDAS"), p_val_neg(f"R$ {dados['total_vendas']:,.2f}")]
    ]
    elements.append(Table(data_v, colWidths=[40*mm, 26*mm], style=estilo_tab))
    elements.append(Spacer(1, 5))

    # 2. RECEBIDOS
    data_r = [
        [p_neg("2. RECEBIDO"), ""],
        ["Dinheiro", p_val(f"R$ {dados['r_din']:,.2f}")],
        ["Cartão", p_val(f"R$ {dados['r_car']:,.2f}")],
        [p_neg("SOMA REC."), p_val_neg(f"R$ {dados['total_recebido']:,.2f}")]
    ]
    elements.append(Table(data_r, colWidths=[40*mm, 26*mm], style=estilo_tab))
    elements.append(Spacer(1, 5))

    # 3. SAÍDAS
    data_s = [[p_neg("3. SAÍDAS"), ""]]
    for s in lista_saidas:
        data_s.append([s['descricao'], p_val(f"R$ {s['valor']:,.2f}")])
    data_s.append([p_neg("TOTAL SAÍDAS"), p_val_neg(f"R$ {dados['total_saidas']:,.2f}")])
    elements.append(Table(data_s, colWidths=[40*mm, 26*mm], style=estilo_tab))

    # Status Final
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"<b>{dados['status']} | SALDO: R$ {dados['resultado']:,.2f}</b>", estilo_base))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFACE WEB ---
st.set_page_config(page_title="Caixa Elgin i9", layout="wide")
st.title("💰 Caixa Master Pro")

data_sel = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
data_pt = data_sel.strftime('%d/%m/%Y')
data_extenso = babel.dates.format_date(data_sel, format='full', locale='pt_BR').title()

st.subheader(f"📅 {data_pt} — {data_extenso}")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🛒 Vendas")
    v_del = st.number_input("Delivery", min_value=0.0, format="%.2f", key="v1")
    v_bal = st.number_input("Balcão", min_value=0.0, format="%.2f", key="v2")
    v_mes = st.number_input("Mesa", min_value=0.0, format="%.2f", key="v3")
    total_vendas = v_del + v_bal + v_mes
    st.info(f"Subtotal Vendas: R$ {total_vendas:,.2f}")

with col2:
    st.markdown("### 💳 Recebimentos")
    r_din = st.number_input("Dinheiro", min_value=0.0, format="%.2f", key="r1")
    r_car = st.number_input("Cartão", min_value=0.0, format="%.2f", key="r2")
    total_recebido = r_din + r_car
    st.info(f"Subtotal Recebido: R$ {total_recebido:,.2f}")

with col3:
    st.markdown("### 💸 Saídas")
    d_sai = st.text_input("Descrição", key="desc_sai")
    v_sai = st.number_input("Valor", min_value=0.0, format="%.2f", key="val_sai")
    if st.button("➕ Adicionar", use_container_width=True):
        if d_sai and v_sai > 0:
            st.session_state.lista_saidas.append({"descricao": d_sai, "valor": v_sai})
            st.rerun()
    
    total_saidas = sum(s['valor'] for s in st.session_state.lista_saidas)
    st.info(f"Subtotal Saídas: R$ {total_saidas:,.2f}")

# --- RESTAURANDO LISTA DE SAÍDAS DETALHADA NA TELA ---
if st.session_state.lista_saidas:
    with st.expander("📄 Ver Saídas Lançadas", expanded=True):
        for i, s in enumerate(st.session_state.lista_saidas):
            col_s1, col_s2 = st.columns([3, 1])
            col_s1.write(f"• {s['descricao']}")
            col_s2.write(f"R$ {s['valor']:,.2f}")
        if st.button("🗑️ Limpar Lista de Saídas"):
            st.session_state.lista_saidas = []
            st.rerun()

# --- STATUS FINAL ---
resultado = (total_recebido + total_saidas) - total_vendas
status_f = "CAIXA OK ✅" if resultado >= 0 else "CAIXA FALTANDO ❌"

st.divider()
if resultado >= 0:
    st.success(f"## {status_f}")
    st.write(f"Sobra/Equilíbrio: **R$ {resultado:,.2f}**")
else:
    st.error(f"## {status_f}")
    st.write(f"Faltam no caixa: **R$ {abs(resultado):,.2f}**")

# BOTÃO DE IMPRESSÃO
if st.button("📥 Gerar Cupom Elgin i9 (72mm)", type="primary", use_container_width=True):
    dados_p = {
        "data_extenso": data_extenso, "v_del": v_del, "v_bal": v_bal, "v_mes": v_mes,
        "total_vendas": total_vendas, "r_din": r_din, "r_car": r_car,
        "total_recebido": total_recebido, "total_saidas": total_saidas,
        "status": status_f, "resultado": resultado
    }
    pdf = gerar_pdf_termico_final(dados_p, st.session_state.lista_saidas)
    st.download_button("Baixar Cupom para Impressão", pdf, f"caixa_{data_sel.strftime('%d-%m-%Y')}.pdf")