import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
from datetime import datetime
import babel.dates

# --- INICIALIZAÇÃO DO ESTADO ---
if 'lista_saidas' not in st.session_state:
    st.session_state.lista_saidas = []

# --- FUNÇÃO PDF COM DATA POR EXTENSO EM DESTAQUE ---
def gerar_pdf_profissional(dados, lista_saidas):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo para a Data em Destaque
    estilo_data_destaque = ParagraphStyle(
        'DataDestak',
        parent=styles['Normal'],
        fontSize=14,
        leading=18,
        alignment=1, # Centralizado
        spaceAfter=20,
        textColor=colors.black
    )

    estilo_status = styles['Heading2'].clone('status')
    estilo_status.alignment = 0 
    estilo_status.textColor = colors.whitesmoke

    # 1. Título Principal
    elements.append(Paragraph("<b>RELATÓRIO DE FECHAMENTO DE CAIXA</b>", styles['Title']))
    
    # 2. DATA EM DESTAQUE 
    elements.append(Paragraph(f"<b>{dados['data_extenso']}</b>", estilo_data_destaque))
    elements.append(Spacer(1, 10))

    # --- TABELAS (Layout Mantido) ---
    # Seção Vendas
    data_vendas = [
        [Paragraph("<b>1. DETALHAMENTO DE VENDAS</b>", styles['Normal']), ""],
        ["Delivery", f"R$ {dados['v_del']:,.2f}"],
        ["Balcão", f"R$ {dados['v_bal']:,.2f}"],
        ["Mesa", f"R$ {dados['v_mes']:,.2f}"],
        [Paragraph("<b>SOMA TOTAL VENDAS</b>", styles['Normal']), Paragraph(f"<b>R$ {dados['total_vendas']:,.2f}</b>", styles['Normal'])]
    ]
    t_vendas = Table(data_vendas, colWidths=[350, 100])
    t_vendas.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke), ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black)]))
    elements.append(t_vendas)
    elements.append(Spacer(1, 15))

    # Seção Recebimentos
    data_rec = [
        [Paragraph("<b>2. RECEBIMENTOS (EM MÃOS)</b>", styles['Normal']), ""],
        ["Dinheiro", f"R$ {dados['r_din']:,.2f}"],
        ["Cartão", f"R$ {dados['r_car']:,.2f}"],
        [Paragraph("<b>SOMA TOTAL RECEBIMENTOS</b>", styles['Normal']), Paragraph(f"<b>R$ {dados['total_recebido']:,.2f}</b>", styles['Normal'])]
    ]
    t_rec = Table(data_rec, colWidths=[350, 100])
    t_rec.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke), ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black)]))
    elements.append(t_rec)
    elements.append(Spacer(1, 15))

    # Seção Saídas
    data_sai = [[Paragraph("<b>3. SAÍDAS DETALHADAS</b>", styles['Normal']), ""]]
    for s in lista_saidas:
        data_sai.append([s['descricao'], f"R$ {s['valor']:,.2f}"])
    data_sai.append([Paragraph("<b>SOMA TOTAL SAÍDAS</b>", styles['Normal']), Paragraph(f"<b>R$ {dados['total_saidas']:,.2f}</b>", styles['Normal'])])
    
    t_sai = Table(data_sai, colWidths=[350, 100])
    t_sai.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke), ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black)]))
    elements.append(t_sai)
    elements.append(Spacer(1, 20))

    # Banner Status Final
    cor_fundo = colors.darkgreen if dados['resultado'] >= 0 else colors.darkred
    data_status = [[Paragraph(f"<b>STATUS FINAL: {dados['status']}</b>", estilo_status), 
                    Paragraph(f"<b>R$ {dados['resultado']:,.2f}</b>", estilo_status)]]
    t_status = Table(data_status, colWidths=[350, 100])
    t_status.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), cor_fundo), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('PADDING', (0, 0), (-1, -1), 10)]))
    elements.append(t_status)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- INTERFACE (LAYOUT DE 3 COLUNAS) ---
st.set_page_config(page_title="Caixa Master Pro", layout="wide")
st.title("💰 Gestão de Caixa")

data_sel = st.date_input("Data do Fechamento", datetime.now(), format="DD/MM/YYYY")
data_pt = data_sel.strftime('%d/%m/%Y')
# Gerar data por extenso: Sábado, 14 de Fevereiro de 2026
data_extenso = babel.dates.format_date(data_sel, format='full', locale='pt_BR').title()

st.subheader(f"📅 {data_pt} — {data_extenso}")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🛒 Vendas")
    v_del = st.number_input("Delivery", min_value=0.0, format="%.2f")
    v_bal = st.number_input("Balcão", min_value=0.0, format="%.2f")
    v_mes = st.number_input("Mesa", min_value=0.0, format="%.2f")
    total_vendas = v_del + v_bal + v_mes
    st.info(f"**Subtotal Vendas:** R$ {total_vendas:,.2f}")

with col2:
    st.markdown("### 💳 Recebimentos")
    r_din = st.number_input("Dinheiro", min_value=0.0, format="%.2f")
    r_car = st.number_input("Cartão", min_value=0.0, format="%.2f")
    total_recebido = r_din + r_car
    st.info(f"**Subtotal Recebido:** R$ {total_recebido:,.2f}")

with col3:
    st.markdown("### 💸 Saídas")
    d_sai = st.text_input("Descrição")
    v_sai = st.number_input("Valor", min_value=0.0, format="%.2f")
    if st.button("➕ Adicionar Saída"):
        if d_sai and v_sai > 0:
            st.session_state.lista_saidas.append({"descricao": d_sai, "valor": v_sai})
            st.rerun()

total_saidas = sum(s['valor'] for s in st.session_state.lista_saidas)
if st.session_state.lista_saidas:
    with st.expander("Resumo das Saídas", expanded=True):
        for s in st.session_state.lista_saidas:
            st.write(f"• {s['descricao']}: R$ {s['valor']:,.2f}")
        st.markdown(f"**Total Saídas:** R$ {total_saidas:,.2f}")
        st.button("Limpar Lista", on_click=lambda: st.session_state.update({"lista_saidas": []}))

# Cálculos
resultado = (total_recebido + total_saidas) - total_vendas
status_f = "CAIXA OK ✅" if resultado >= 0 else "CAIXA FALTANDO ❌"

st.divider()
if st.button("📥 Gerar Relatório PDF Profissional", type="primary", use_container_width=True):
    dados_pdf = {
        "data_extenso": data_extenso,
        "v_del": v_del, "v_bal": v_bal, "v_mes": v_mes,
        "total_vendas": total_vendas, "r_din": r_din, "r_car": r_car,
        "total_recebido": total_recebido, "total_saidas": total_saidas,
        "status": status_f, "resultado": resultado
    }
    pdf_out = gerar_pdf_profissional(dados_pdf, st.session_state.lista_saidas)
    st.download_button("Clique para Baixar", pdf_out, f"caixa_{data_sel.strftime('%d-%m-%Y')}.pdf")