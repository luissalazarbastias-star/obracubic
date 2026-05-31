import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import io
from datetime import datetime, timezone, timedelta

# --- CONFIGURACIÓN VISUAL DE LA APP ---
st.set_page_config(
    page_title="ObraCubic - Grandes Cosas Comienzan Aquí",
    page_icon="🏗️"
)

st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# ============================
# DATOS DE DOSIFICACIÓN (CBB)
# ============================
DOSIFICACIONES = {
    "G-5": {
        "descripcion": "Hormigón de muy baja resistencia",
        "cemento_sacos": round(170 / 25),
        "gravilla_kg": 1025,
        "arena_kg": 910,
        "agua_lt": 195,
    },
    "G-10": {
        "descripcion": "Hormigón de baja resistencia",
        "cemento_sacos": round(230 / 25),
        "gravilla_kg": 1055,
        "arena_kg": 835,
        "agua_lt": 195,
    },
    "G-15": {
        "descripcion": "Emplantillado, sobrecimientos simples",
        "cemento_sacos": round(275 / 25),
        "gravilla_kg": 1070,
        "arena_kg": 800,
        "agua_lt": 195,
    },
    "G-20": {
        "descripcion": "Radier, cimientos normales",
        "cemento_sacos": round(340 / 25),
        "gravilla_kg": 1095,
        "arena_kg": 715,
        "agua_lt": 200,
    },
    "G-25": {
        "descripcion": "Losas estructurales, pilares",
        "cemento_sacos": round(380 / 25),
        "gravilla_kg": 1120,
        "arena_kg": 645,
        "agua_lt": 200,
    },
    "G-30": {
        "descripcion": "Obras especiales, alta resistencia",
        "cemento_sacos": round(440 / 25),
        "gravilla_kg": 1145,
        "arena_kg": 585,
        "agua_lt": 200,
    },
}

def calcular_materiales(volumen_m3, dosificacion):
    dos = DOSIFICACIONES[dosificacion]
    vol = volumen_m3
    return {
        "cemento_sacos": round(vol * dos["cemento_sacos"]),
        "gravilla_kg":   round(vol * dos["gravilla_kg"]),
        "arena_kg":      round(vol * dos["arena_kg"]),
        "agua_lt":       round(vol * dos["agua_lt"]),
    }

def mostrar_materiales(materiales):
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cemento",   f"{materiales['cemento_sacos']} sacos")
    m2.metric("Gravilla",  f"{materiales['gravilla_kg']} kg")
    m3.metric("Arena",     f"{materiales['arena_kg']} kg")
    m4.metric("Agua",      f"{materiales['agua_lt']} lt")

PESO_BARRAS = {
    "Ø8mm":  0.395,
    "Ø10mm": 0.617,
    "Ø12mm": 0.888,
    "Ø16mm": 1.578,
    "Ø20mm": 2.466,
    "Ø25mm": 3.854,
}
RATIO_ACERO = {
    "Losa":    {"ratio": 8,   "unidad": "kg/m2"},
    "Viga":    {"ratio": 120, "unidad": "kg/m3"},
    "Pilar":   {"ratio": 150, "unidad": "kg/m3"},
    "Radier":  {"ratio": 5,   "unidad": "kg/m2"},
    "Cimiento":{"ratio": 80,  "unidad": "kg/m3"},
}
# ============================
# MALLA ACMA
# ============================
MALLA_ACMA = {
    "C84  (Ø5,0mm c/15cm)": {"kg_m2": 1.39},
    "C92  (Ø5,5mm c/15cm)": {"kg_m2": 1.54},
    "C128 (Ø6,0mm c/15cm)": {"kg_m2": 2.13},
    "C188 (Ø6,0mm c/10cm)": {"kg_m2": 3.16},
    "C257 (Ø7,0mm c/10cm)": {"kg_m2": 4.27},
}

# ============================
# FUNCIÓN EXPORTAR PDF
# ============================
NARANJA    = colors.HexColor("#FF6B00")
GRIS_OSCURO = colors.HexColor("#1E1E1E")
GRIS_CLARO  = colors.HexColor("#F5F5F5")
BLANCO     = colors.white

def generar_pdf_cubicacion(
    nombre_proyecto,
    vol_emp, dos_emp, mat_emp,
    vol_pilares, dos_cim, mat_cim,
    vol_sc_neto, dos_sc, mat_sc,
    vol_radier, dos_rad, mat_rad,
    total_hormigon,
    total_sacos, total_gravilla, total_arena, total_agua,
    acero_losa_kg=None,
    acero_pilar_kg=None,
    acero_viga_kg=None,
    acero_radier_kg=None,
    canal_tipo=None, cant_piezas_canal=0, ml_canal=0, largo_canal=0,
    montante_tipo=None, total_montantes=0, largo_montante=0,
    esq_tipo=None, cant_esquinas=0, largo_esq=0,
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle("Titulo", parent=styles["Title"],
        fontSize=22, textColor=NARANJA, spaceAfter=4)
    estilo_subtitulo = ParagraphStyle("Subtitulo", parent=styles["Normal"],
        fontSize=10, textColor=GRIS_OSCURO, spaceAfter=2)
    estilo_seccion = ParagraphStyle("Seccion", parent=styles["Heading2"],
        fontSize=13, textColor=NARANJA, spaceBefore=14, spaceAfter=6)
    estilo_normal = ParagraphStyle("Normal2", parent=styles["Normal"],
        fontSize=10, textColor=GRIS_OSCURO)
    estilo_pie = ParagraphStyle("Pie", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, alignment=1)

    story = []
    zona_chile = timezone(timedelta(hours=-4))
    fecha_hoy = datetime.now(zona_chile).strftime("%d/%m/%Y %H:%M")

    # Encabezado con logo arriba a la derecha
    import urllib.request
    from reportlab.platypus import Image as RLImage
    try:
        logo_url = "https://raw.githubusercontent.com/luissalazarbastias-star/obracubic/refs/heads/main/Foto%202.png"
        logo_data = urllib.request.urlopen(logo_url).read()
        logo_buffer = io.BytesIO(logo_data)
        logo = RLImage(logo_buffer, width=2*cm, height=2*cm)
    except:
        logo = Paragraph("", estilo_normal)

    encabezado = Table(
        [[
            Paragraph("ObraCubic<br/><font size=9 color='grey'>Grandes Estructuras se Levantan con Decisiones Precisas</font>", estilo_titulo),
            logo
        ]],
        colWidths=[14.5*cm, 2.5*cm]
    )
    encabezado.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(encabezado)
    story.append(HRFlowable(width="100%", thickness=2, color=NARANJA, spaceAfter=6))

    datos_header = [
        ["Proyecto:", nombre_proyecto or "Sin nombre"],
        ["Fecha:", fecha_hoy],
        ["Volumen Total:", f"{total_hormigon:.2f} m3"],
    ]
    tabla_header = Table(datos_header, colWidths=[4*cm, 13*cm])
    tabla_header.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (0, -1), NARANJA),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tabla_header)
    story.append(Spacer(1, 10))

    # Sección Hormigón
    if total_hormigon and total_hormigon > 0:
        story.append(Paragraph("CUBICACION DE HORMIGON", estilo_seccion))

        partidas = [
            ("Emplantillado",      vol_emp,      dos_emp, mat_emp),
            ("Cimiento / Pilares", vol_pilares,  dos_cim, mat_cim),
            ("Sobrecimiento",      vol_sc_neto,  dos_sc,  mat_sc),
            ("Radier",             vol_radier,   dos_rad, mat_rad),
        ]

        for nombre_partida, vol, dos, mat in partidas:
            if vol and vol > 0:
                story.append(Paragraph(f"<b>{nombre_partida}</b>  —  Dosificacion: {dos}", estilo_normal))
                datos_p = [
                    ["Volumen", "Cemento", "Gravilla", "Arena", "Agua"],
                    [
                        f"{vol:.2f} m3",
                        f"{mat['cemento_sacos']} sacos",
                        f"{mat['gravilla_kg']} kg",
                        f"{mat['arena_kg']} kg",
                        f"{mat['agua_lt']} lt",
                    ],
                ]
                tabla_p = Table(datos_p, colWidths=[3.4*cm]*5)
                tabla_p.setStyle(TableStyle([
                    ("BACKGROUND",  (0, 0), (-1, 0), NARANJA),
                    ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
                    ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE",    (0, 0), (-1, -1), 9),
                    ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_CLARO, BLANCO]),
                    ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("TOPPADDING",  (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
                ]))
                story.append(tabla_p)
                story.append(Spacer(1, 8))

        story.append(HRFlowable(width="100%", thickness=1, color=NARANJA, spaceAfter=6))
        story.append(Paragraph("RESUMEN TOTAL DE MATERIALES", estilo_seccion))

        datos_resumen = [
            ["Volumen Total", "Cemento Total", "Gravilla Total", "Arena Total", "Agua Total"],
            [
                f"{total_hormigon:.2f} m3",
                f"{total_sacos} sacos",
                f"{total_gravilla} kg",
                f"{total_arena} kg",
                f"{total_agua} lt",
            ],
        ]
        tabla_res = Table(datos_resumen, colWidths=[3.4*cm]*5)
        tabla_res.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), GRIS_OSCURO),
            ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (0, 1), (-1, 1), NARANJA),
            ("TEXTCOLOR",   (0, 1), (-1, 1), BLANCO),
            ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 10),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING",  (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ]))
        story.append(tabla_res)
        story.append(Spacer(1, 12))

    # Sección acero (si hay datos)
    acero_datos = {
        "Losa": acero_losa_kg,
        "Pilar": acero_pilar_kg,
        "Viga": acero_viga_kg,
        "Radier": acero_radier_kg,
    }
    acero_validos = {k: v for k, v in acero_datos.items() if v and v > 0}

    if acero_validos:
        story.append(HRFlowable(width="100%", thickness=1, color=NARANJA, spaceAfter=6))
        story.append(Paragraph("ACERO ESTRUCTURAL", estilo_seccion))
        total_acero = sum(acero_validos.values())
        filas_acero = [["Elemento", "Acero (kg)"]]
        for elem, kg in acero_validos.items():
            filas_acero.append([elem, f"{kg:.1f} kg"])
        filas_acero.append(["TOTAL", f"{total_acero:.1f} kg"])
        tabla_acero = Table(filas_acero, colWidths=[9*cm, 8*cm])
        tabla_acero.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), GRIS_OSCURO),
            ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (0, -1), (-1, -1), NARANJA),
            ("TEXTCOLOR",   (0, -1), (-1, -1), BLANCO),
            ("FONTNAME",    (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 10),
            ("ALIGN",       (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [GRIS_CLARO, BLANCO]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ]))
        story.append(tabla_acero)
        story.append(Spacer(1, 12))

    # Sección Metalcon
    if cant_piezas_canal > 0 or total_montantes > 0 or cant_esquinas > 0:
        story.append(HRFlowable(width="100%", thickness=1, color=NARANJA, spaceAfter=6))
        story.append(Paragraph("ACERO NO ESTRUCTURAL - TABIQUES METALCON", estilo_seccion))

        filas_metalcon = [["Elemento", "Tipo", "Cantidad"]]
        if cant_piezas_canal > 0:
            filas_metalcon.append(["Canal / Solera", canal_tipo, f"{cant_piezas_canal:.0f} piezas de {largo_canal}m"])
        if total_montantes > 0:
            filas_metalcon.append(["Montante", montante_tipo, f"{total_montantes} piezas de {largo_montante}m"])
        if cant_esquinas > 0:
            filas_metalcon.append(["Esquinero", esq_tipo, f"{cant_esquinas} piezas de {largo_esq}m"])

        tabla_metalcon = Table(filas_metalcon, colWidths=[4*cm, 9*cm, 4*cm])
        tabla_metalcon.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), GRIS_OSCURO),
            ("TEXTCOLOR",   (0, 0), (-1, 0), BLANCO),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRIS_CLARO, BLANCO]),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ]))
        story.append(tabla_metalcon)
        story.append(Spacer(1, 12))

    # Pie de página
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generado por ObraCubic  |  {fecha_hoy}  |  obracubic.streamlit.app",
        estilo_pie
    ))
    story.append(Paragraph(
        "Este documento es una estimacion de cubicacion. Verifique los valores antes de comprar materiales.",
        estilo_pie
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Inicializar session_state
if "proyecto_creado" not in st.session_state:
    st.session_state["proyecto_creado"] = False
if "proyecto" not in st.session_state:
    st.session_state["proyecto"] = {}
if "mostrar_proyecto" not in st.session_state:
    st.session_state["mostrar_proyecto"] = False
if "vol_emp" not in st.session_state:
    st.session_state["vol_emp"] = 0.0
if "vol_pilares" not in st.session_state:
    st.session_state["vol_pilares"] = 0.0
if "vol_sc_neto" not in st.session_state:
    st.session_state["vol_sc_neto"] = 0.0
if "vol_radier" not in st.session_state:
    st.session_state["vol_radier"] = 0.0
if "mat_emp" not in st.session_state:
    st.session_state["mat_emp"] = {"cemento_sacos": 0, "gravilla_kg": 0, "arena_kg": 0, "agua_lt": 0}
if "mat_cim" not in st.session_state:
    st.session_state["mat_cim"] = {"cemento_sacos": 0, "gravilla_kg": 0, "arena_kg": 0, "agua_lt": 0}
if "mat_sc" not in st.session_state:
    st.session_state["mat_sc"] = {"cemento_sacos": 0, "gravilla_kg": 0, "arena_kg": 0, "agua_lt": 0}
if "mat_rad" not in st.session_state:
    st.session_state["mat_rad"] = {"cemento_sacos": 0, "gravilla_kg": 0, "arena_kg": 0, "agua_lt": 0}

# ============================
# LOGO Y SIDEBAR
# ============================
URL_DEL_LOGO = "https://raw.githubusercontent.com/luissalazarbastias-star/obracubic/refs/heads/main/Foto%201.png"

st.sidebar.image(URL_DEL_LOGO, use_container_width=True)
st.sidebar.write("---")
st.sidebar.header("Módulos de Trabajo")
option = st.sidebar.radio("Ir a:", ["Crear Proyecto", "Cubicacion"])

# ============================
# CREAR PROYECTO
# ============================
if option == "Crear Proyecto":
    st.subheader("Crear Nuevo Proyecto")
    st.caption("Configurá tu obra y seleccioná solo los rubros que vas a trabajar.")

    with st.container(border=True):
        nombre_proy = st.text_input("Nombre del proyecto *",
            placeholder="Ej: Casa Don Pedro - Angol",
            key="input_nombre_proy")

        col1, col2 = st.columns(2)
        with col1:
            tipo_obra = st.text_input("Tipo de obra",
                placeholder="Ej: Vivienda Unifamiliar",
                key="input_tipo_obra")
        with col2:
            profesional = st.text_input("Profesional / Empresa (opcional)",
                placeholder="Ej: Juan Pérez - Constructor",
                key="input_profesional")

        st.write("**Seleccioná los rubros de tu obra:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            usar_hormigon    = st.checkbox("Hormigón y Mov. de tierra", key="usar_hormigon")
            usar_moldajes    = st.checkbox("Moldajes", key="usar_moldajes")
            usar_pisos       = st.checkbox("Pisos y Pavimentos", key="usar_pisos")
        with col2:
            usar_acero_est   = st.checkbox("Acero estructural", key="usar_acero_est")
            usar_muros       = st.checkbox("Muros", key="usar_muros")
            usar_terminaciones = st.checkbox("Terminaciones", key="usar_terminaciones")
        with col3:
            usar_metalcon    = st.checkbox("Acero No Estructural (Metalcon)", key="usar_metalcon")
            usar_revestimientos = st.checkbox("Revestimientos", key="usar_revestimientos")

        partidas_seleccionadas = {}

        if usar_hormigon:
            st.write("---")
            st.markdown("**Hormigón — selecciona las partidas:**")
            hc1, hc2, hc3 = st.columns(3)
            with hc1:
                p_exc = st.checkbox("Excavación", key="p_exc")
                p_emp = st.checkbox("Emplantillado", key="p_emp")
            with hc2:
                p_cim = st.checkbox("Cimiento", key="p_cim")
                p_sc  = st.checkbox("Sobrecimiento", key="p_sc")
            with hc3:
                p_rad = st.checkbox("Radier", key="p_rad")
            partidas_seleccionadas["hormigon"] = {
                "excavacion": p_exc, "emplantillado": p_emp,
                "cimiento": p_cim, "sobrecimiento": p_sc, "radier": p_rad,
            }

        if usar_acero_est:
            st.write("---")
            st.markdown("**Acero estructural — selecciona las partidas:**")
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                p_losa   = st.checkbox("Losa", key="p_losa")
                p_pilar  = st.checkbox("Pilar", key="p_pilar")
            with ac2:
                p_viga   = st.checkbox("Viga", key="p_viga")
                p_rad_ac = st.checkbox("Radier", key="p_rad_ac")
            with ac3:
                p_cim_ac = st.checkbox("Cimiento", key="p_cim_ac")
            partidas_seleccionadas["acero_estructural"] = {
                "losa": p_losa, "pilar": p_pilar, "viga": p_viga,
                "radier": p_rad_ac, "cimiento": p_cim_ac,
            }

        if usar_metalcon:
            st.write("---")
            st.markdown("**Metalcon — selecciona las partidas:**")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                p_canal = st.checkbox("Canal / Solera", key="p_canal")
            with mc2:
                p_mont  = st.checkbox("Montante", key="p_mont")
            with mc3:
                p_esq   = st.checkbox("Esquinero", key="p_esq")
            partidas_seleccionadas["metalcon"] = {
                "canal": p_canal, "montante": p_mont, "esquinero": p_esq,
            }

        if usar_moldajes:
            st.write("---")
            st.markdown("**Moldajes — selecciona las partidas:**")
            mold1, mold2, mold3 = st.columns(3)
            with mold1:
                p_mold_cim  = st.checkbox("Cimiento", key="p_mold_cim")
                p_mold_muro = st.checkbox("Muro", key="p_mold_muro")
            with mold2:
                p_mold_losa = st.checkbox("Losa", key="p_mold_losa")
                p_mold_viga = st.checkbox("Viga", key="p_mold_viga")
            with mold3:
                p_mold_pilar = st.checkbox("Pilar", key="p_mold_pilar")
            partidas_seleccionadas["moldajes"] = {
                "cimiento": p_mold_cim, "muro": p_mold_muro,
                "losa": p_mold_losa, "viga": p_mold_viga, "pilar": p_mold_pilar,
            }

        if usar_muros:
            st.write("---")
            st.markdown("**Muros — selecciona las partidas:**")
            mu1, mu2, mu3 = st.columns(3)
            with mu1:
                p_muro_h = st.checkbox("Muro Hormigón", key="p_muro_h")
            with mu2:
                p_muro_l = st.checkbox("Muro Ladrillo", key="p_muro_l")
            with mu3:
                p_tab_met = st.checkbox("Tabique Metalcon", key="p_tab_met")
                p_tab_mad = st.checkbox("Tabique Madera", key="p_tab_mad")
            partidas_seleccionadas["muros"] = {
                "hormigon": p_muro_h, "ladrillo": p_muro_l,
                "tabique_metalcon": p_tab_met, "tabique_madera": p_tab_mad,
            }

        if usar_revestimientos:
            st.write("---")
            st.markdown("**Revestimientos — selecciona las partidas:**")
            re1, re2 = st.columns(2)
            with re1:
                p_rev_int = st.checkbox("Interior", key="p_rev_int")
            with re2:
                p_rev_ext = st.checkbox("Exterior", key="p_rev_ext")
            partidas_seleccionadas["revestimientos"] = {
                "interior": p_rev_int, "exterior": p_rev_ext,
            }

        if usar_pisos:
            st.write("---")
            st.markdown("**Pisos y Pavimentos — selecciona las partidas:**")
            pi1, pi2, pi3 = st.columns(3)
            with pi1:
                p_ceramico = st.checkbox("Cerámico / Porcelanato", key="p_ceramico")
                p_flotante = st.checkbox("Piso Flotante", key="p_flotante")
            with pi2:
                p_baldosa  = st.checkbox("Baldosa", key="p_baldosa")
            with pi3:
                p_deck     = st.checkbox("Deck Madera", key="p_deck")
            partidas_seleccionadas["pisos"] = {
                "ceramico": p_ceramico, "flotante": p_flotante,
                "baldosa": p_baldosa, "deck": p_deck,
            }

        if usar_terminaciones:
            st.write("---")
            st.markdown("**Terminaciones — selecciona las partidas:**")
            te1, te2, te3 = st.columns(3)
            with te1:
                p_pintura = st.checkbox("Pintura", key="p_pintura")
                p_estuco  = st.checkbox("Estuco / Revoque", key="p_estuco")
            with te2:
                p_cielos  = st.checkbox("Cielos", key="p_cielos")
            with te3:
                p_zocalos = st.checkbox("Zócalos", key="p_zocalos")
            partidas_seleccionadas["terminaciones"] = {
                "pintura": p_pintura, "estuco": p_estuco,
                "cielos": p_cielos, "zocalos": p_zocalos,
            }

        total_partidas = sum(
            v for rubro in partidas_seleccionadas.values()
            for v in rubro.values()
        )

        st.write("---")
        col_cancel, col_count, col_crear = st.columns([2, 3, 2])
        with col_cancel:
            if st.button("Cancelar", use_container_width=True):
                st.session_state["proyecto_creado"] = False
                st.session_state["proyecto"] = {}
        with col_count:
            st.caption(f"{total_partidas} partidas seleccionadas")
        with col_crear:
            crear = st.button("Crear Proyecto", type="primary",
                use_container_width=True, disabled=not nombre_proy)

        if crear and nombre_proy:
            st.session_state["proyecto_creado"] = True
            st.session_state["mostrar_proyecto"] = True
            st.session_state["proyecto"] = {
                "nombre": nombre_proy,
                "tipo_obra": tipo_obra,
                "profesional": profesional,
                "partidas": partidas_seleccionadas,
            }
            st.rerun()

    # --- Expander del proyecto creado ---
    if st.session_state.get("proyecto_creado"):
        proy = st.session_state["proyecto"]
        partidas = proy.get("partidas", {})

        with st.expander(f"Tu proyecto: {proy['nombre']}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                if proy.get("tipo_obra"):
                    st.caption(f"Tipo de obra: {proy['tipo_obra']}")
            with col2:
                if proy.get("profesional"):
                    st.caption(f"Profesional: {proy['profesional']}")

            st.write("---")
            st.markdown("**Partidas seleccionadas:**")

            NOMBRES = {
                "hormigon": "Hormigón y Mov. de tierra",
                "acero_estructural": "Acero estructural",
                "metalcon": "Acero No Estructural (Metalcon)",
                "moldajes": "Moldajes",
                "muros": "Muros",
                "revestimientos": "Revestimientos",
                "pisos": "Pisos y Pavimentos",
                "terminaciones": "Terminaciones",
            }
            NOMBRES_PARTIDAS = {
                "excavacion": "Excavación", "emplantillado": "Emplantillado",
                "cimiento": "Cimiento", "sobrecimiento": "Sobrecimiento",
                "radier": "Radier", "losa": "Losa", "pilar": "Pilar",
                "viga": "Viga", "canal": "Canal / Solera",
                "montante": "Montante", "esquinero": "Esquinero",
                "muro": "Muro", "hormigon": "Muro Hormigón",
                "ladrillo": "Muro Ladrillo", "tabique_metalcon": "Tabique Metalcon",
                "tabique_madera": "Tabique Madera", "interior": "Interior",
                "exterior": "Exterior", "ceramico": "Cerámico / Porcelanato",
                "flotante": "Piso Flotante", "baldosa": "Baldosa",
                "deck": "Deck Madera", "pintura": "Pintura",
                "estuco": "Estuco / Revoque", "cielos": "Cielos",
                "zocalos": "Zócalos",
            }

            for rubro, sub in partidas.items():
                activas = [NOMBRES_PARTIDAS.get(k, k) for k, v in sub.items() if v]
                if activas:
                    st.markdown(f"**{NOMBRES.get(rubro, rubro)}**")
                    for p in activas:
                        st.markdown(f"- {p}")

            st.write("---")
            col_ir, col_cerrar = st.columns(2)
            with col_ir:
                if st.button("Ir a cubicación", type="primary", use_container_width=True):
                    st.session_state["ir_a_cubicacion"] = True
                    st.rerun()
            with col_cerrar:
                if st.button("Cerrar proyecto", use_container_width=True):
                    st.session_state["proyecto_creado"] = False
                    st.session_state["proyecto"] = {}
                    st.rerun()

    st.info("También podés usar la Cubicación General sin crear un proyecto — está siempre disponible.")

# ============================
# CUBICACIÓN
# ============================
if option == "Cubicacion":
    # Banner proyecto activo
    if st.session_state.get("proyecto_creado") and st.session_state.get("proyecto"):
        proy = st.session_state["proyecto"]
        with st.container(border=True):
            b1, b2, b3 = st.columns([3, 2, 1])
            with b1:
                st.markdown(f"**Proyecto:** {proy['nombre']}")
                if proy.get('tipo_obra'):
                    st.caption(f"Tipo: {proy['tipo_obra']}")
            with b2:
                if proy.get('profesional'):
                    st.caption(f"Profesional: {proy['profesional']}")
            with b3:
                if st.button("Cerrar proyecto", key="cerrar_proy"):
                    st.session_state["proyecto_creado"] = False
                    st.session_state["proyecto"] = {}
                    st.rerun()
    
    st.subheader("CUBICACIONES")
    
    with st.expander("Hormigón y Movimiento de tierra", expanded=False):

        # --- 1. Excavación ---
        with st.expander("1. Excavación", expanded=False):

            if "secciones_exc" not in st.session_state:
                st.session_state.secciones_exc = [{"largo": 0.0, "ancho": 0.0, "prof": 0.0}]

            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ Agregar sección", key="add_exc"):
                    st.session_state.secciones_exc.append({"largo": 0.0, "ancho": 0.0, "prof": 0.0})
            with col_del:
                if st.button("🗑️ Eliminar última sección", key="del_exc"):
                    if len(st.session_state.secciones_exc) > 1:
                        st.session_state.secciones_exc.pop()

            vol_exc_total = 0.0
            for i, sec in enumerate(st.session_state.secciones_exc):
                st.markdown(f"**Sección {i+1}**")
                ex1, ex2, ex3 = st.columns(3)
                with ex1:
                    sec["largo"] = st.number_input(f"Largo (m)", value=sec["largo"], key=f"exc_largo_{i}")
                with ex2:
                    sec["ancho"] = st.number_input(f"Ancho (m)", value=sec["ancho"], key=f"exc_ancho_{i}")
                with ex3:
                    sec["prof"] = st.number_input(f"Profundidad (m)", value=sec["prof"], key=f"exc_prof_{i}")

                vol_sec_exc = sec["largo"] * sec["ancho"] * sec["prof"]
                st.caption(f"Volumen sección {i+1}: {vol_sec_exc:.2f} m³")
                vol_exc_total += vol_sec_exc

            exc_perdida = st.slider("% Esponjamiento", 0, 30, 20, key="exc_perdida")
            vol_exc_final = vol_exc_total * (1 + exc_perdida / 100)

            st.write("---")
            st.info(f"Volumen neto excavación: {vol_exc_total:.2f} m³")
            st.success(f"Volumen con {exc_perdida}% esponjamiento: {vol_exc_final:.2f} m³")

        # --- 2. Emplantillado ---
        with st.expander("2. Emplantillado", expanded=False):

            if "secciones_emp" not in st.session_state:
                st.session_state.secciones_emp = [{"largo": 0.0, "ancho": 0.0, "espesor": 0.0}]

            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ Agregar sección", key="add_emp"):
                    st.session_state.secciones_emp.append({"largo": 0.0, "ancho": 0.0, "espesor": 0.0})
            with col_del:
                if st.button("🗑️ Eliminar última sección", key="del_emp"):
                    if len(st.session_state.secciones_emp) > 1:
                        st.session_state.secciones_emp.pop()

            vol_emp_total = 0.0
            for i, sec in enumerate(st.session_state.secciones_emp):
                st.markdown(f"**Sección {i+1}**")
                em1, em2, em3 = st.columns(3)
                with em1:
                    sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"emp_largo_{i}")
                with em2:
                    sec["ancho"] = st.number_input("Ancho (m)", value=sec["ancho"], key=f"emp_ancho_{i}")
                with em3:
                    sec["espesor"] = st.number_input("Espesor (m)", value=sec["espesor"], key=f"emp_espesor_{i}")

                vol_sec_emp = sec["largo"] * sec["ancho"] * sec["espesor"]
                st.caption(f"Volumen sección {i+1}: {vol_sec_emp:.2f} m³")
                vol_emp_total += vol_sec_emp

            emp_perdida = st.slider("% Pérdida", 0, 15, 5, key="emp_perdida")
            vol_emp_final = vol_emp_total * (1 + emp_perdida / 100)

            dos_emp = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                    key="dos_emp",
                                    help=DOSIFICACIONES["G-15"]["descripcion"])
            mat_emp = calcular_materiales(vol_emp_final, dos_emp)

            st.write("---")
            st.info(f"Volumen neto emplantillado: {vol_emp_total:.2f} m³")
            st.success(f"Volumen con {emp_perdida}% pérdida: {vol_emp_final:.2f} m³")
            mostrar_materiales(mat_emp)

        # --- 3. Cimiento ---
        with st.expander("3. Cimiento", expanded=False):

            st.write("**Selecciona los tipos de cimiento que tiene la obra:**")

            usar_zapata_aislada   = st.checkbox("Zapata Aislada", key="usar_zapata_aislada")
            usar_zapata_corrida   = st.checkbox("Zapata Corrida", key="usar_zapata_corrida")
            usar_zapata_combinada = st.checkbox("Zapata Combinada", key="usar_zapata_combinada")
            usar_losa_cim         = st.checkbox("Losa de Cimentación", key="usar_losa_cim")

            vol_pilares = 0.0

            # --- Zapata Aislada ---
            if usar_zapata_aislada:
                st.write("---")
                st.markdown("### 📐 Zapata Aislada")

                if "secciones_zapata" not in st.session_state:
                    st.session_state.secciones_zapata = [{"cant": 0, "seccion": 0.0, "alto": 0.0}]

                col_add, col_del = st.columns(2)
                with col_add:
                    if st.button("➕ Agregar grupo", key="add_zapata"):
                        st.session_state.secciones_zapata.append({"cant": 0, "seccion": 0.0, "alto": 0.0})
                with col_del:
                    if st.button("🗑️ Eliminar último grupo", key="del_zapata"):
                        if len(st.session_state.secciones_zapata) > 1:
                            st.session_state.secciones_zapata.pop()

                vol_zapata_aislada = 0.0
                for i, sec in enumerate(st.session_state.secciones_zapata):
                    st.markdown(f"**Grupo {i+1}**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sec["cant"] = st.number_input("Cantidad zapatas", value=sec["cant"], step=1, key=f"zapata_cant_{i}")
                    with c2:
                        sec["seccion"] = st.number_input("Sección (m)", value=sec["seccion"], key=f"zapata_sec_{i}")
                    with c3:
                        sec["alto"] = st.number_input("Profundidad (m)", value=sec["alto"], key=f"zapata_alto_{i}")

                    vol_sec = (sec["seccion"] * sec["seccion"] * sec["alto"]) * sec["cant"]
                    st.caption(f"Volumen grupo {i+1}: {vol_sec:.2f} m³")
                    vol_zapata_aislada += vol_sec

                st.info(f"Volumen Zapata Aislada: {vol_zapata_aislada:.2f} m³")
                vol_pilares += vol_zapata_aislada

            # --- Zapata Corrida ---
            if usar_zapata_corrida:
                st.write("---")
                st.markdown("### 📐 Zapata Corrida")

                if "secciones_corrida" not in st.session_state:
                    st.session_state.secciones_corrida = [{"largo": 0.0, "ancho": 0.0, "prof": 0.0}]

                col_add, col_del = st.columns(2)
                with col_add:
                    if st.button("➕ Agregar sección", key="add_corrida"):
                        st.session_state.secciones_corrida.append({"largo": 0.0, "ancho": 0.0, "prof": 0.0})
                with col_del:
                    if st.button("🗑️ Eliminar última sección", key="del_corrida"):
                        if len(st.session_state.secciones_corrida) > 1:
                            st.session_state.secciones_corrida.pop()

                vol_zapata_corrida = 0.0
                for i, sec in enumerate(st.session_state.secciones_corrida):
                    st.markdown(f"**Sección {i+1}**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"corrida_largo_{i}")
                    with c2:
                        sec["ancho"] = st.number_input("Ancho/Espesor (m)", value=sec["ancho"], key=f"corrida_ancho_{i}")
                    with c3:
                        sec["prof"] = st.number_input("Profundidad (m)", value=sec["prof"], key=f"corrida_prof_{i}")

                    vol_sec = sec["largo"] * sec["ancho"] * sec["prof"]
                    st.caption(f"Volumen sección {i+1}: {vol_sec:.2f} m³")
                    vol_zapata_corrida += vol_sec

                st.info(f"Volumen Zapata Corrida: {vol_zapata_corrida:.2f} m³")
                vol_pilares += vol_zapata_corrida

            # --- Zapata Combinada ---
            if usar_zapata_combinada:
                st.write("---")
                st.markdown("### 📐 Zapata Combinada")
                st.caption("Une dos o más pilares cercanos en una sola zapata.")

                if "secciones_combinada" not in st.session_state:
                    st.session_state.secciones_combinada = [{"cant": 0, "largo": 0.0, "ancho": 0.0, "prof": 0.0}]

                col_add, col_del = st.columns(2)
                with col_add:
                    if st.button("➕ Agregar sección", key="add_combinada"):
                        st.session_state.secciones_combinada.append({"cant": 0, "largo": 0.0, "ancho": 0.0, "prof": 0.0})
                with col_del:
                    if st.button("🗑️ Eliminar última sección", key="del_combinada"):
                        if len(st.session_state.secciones_combinada) > 1:
                            st.session_state.secciones_combinada.pop()

                vol_zapata_combinada = 0.0
                for i, sec in enumerate(st.session_state.secciones_combinada):
                    st.markdown(f"**Sección {i+1}**")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        sec["cant"] = st.number_input("Cantidad zapatas", value=sec["cant"], step=1, key=f"comb_cant_{i}")
                    with c2:
                        sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"comb_largo_{i}")
                    with c3:
                        sec["ancho"] = st.number_input("Ancho (m)", value=sec["ancho"], key=f"comb_ancho_{i}")
                    with c4:
                        sec["prof"] = st.number_input("Profundidad (m)", value=sec["prof"], key=f"comb_prof_{i}")

                    vol_sec = sec["largo"] * sec["ancho"] * sec["prof"] * sec["cant"]
                    st.caption(f"Volumen sección {i+1}: {vol_sec:.2f} m³")
                    vol_zapata_combinada += vol_sec

                st.info(f"Volumen Zapata Combinada: {vol_zapata_combinada:.2f} m³")
                vol_pilares += vol_zapata_combinada

            # --- Losa de Cimentación ---
            if usar_losa_cim:
                st.write("---")
                st.markdown("### 📐 Losa de Cimentación")
                st.caption("Placa continua bajo toda la estructura. Se usa en terrenos de baja capacidad portante.")

                if "secciones_losa_cim" not in st.session_state:
                    st.session_state.secciones_losa_cim = [{"largo": 0.0, "ancho": 0.0, "esp": 0.0}]

                col_add, col_del = st.columns(2)
                with col_add:
                    if st.button("➕ Agregar sección", key="add_losa_cim"):
                        st.session_state.secciones_losa_cim.append({"largo": 0.0, "ancho": 0.0, "esp": 0.0})
                with col_del:
                    if st.button("🗑️ Eliminar última sección", key="del_losa_cim"):
                        if len(st.session_state.secciones_losa_cim) > 1:
                            st.session_state.secciones_losa_cim.pop()

                vol_losa_cim = 0.0
                for i, sec in enumerate(st.session_state.secciones_losa_cim):
                    st.markdown(f"**Sección {i+1}**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"losacim_largo_{i}")
                    with c2:
                        sec["ancho"] = st.number_input("Ancho (m)", value=sec["ancho"], key=f"losacim_ancho_{i}")
                    with c3:
                        sec["esp"] = st.number_input("Espesor (m)", value=sec["esp"], key=f"losacim_esp_{i}")

                    vol_sec = sec["largo"] * sec["ancho"] * sec["esp"]
                    st.caption(f"Volumen sección {i+1}: {vol_sec:.2f} m³")
                    vol_losa_cim += vol_sec

                st.info(f"Volumen Losa de Cimentación: {vol_losa_cim:.2f} m³")
                vol_pilares += vol_losa_cim

            # --- Resumen y Dosificación ---
            if vol_pilares > 0:
                st.write("---")
                st.success(f"### Volumen Total Cimiento: {vol_pilares:.2f} m³")
                st.caption("Para pilotes o micropilotes consulte con un ingeniero especialista.")

                dos_cim = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                       index=1, key="dos_cim",
                                       help=DOSIFICACIONES["G-20"]["descripcion"])
                mat_cim = calcular_materiales(vol_pilares, dos_cim)
                mostrar_materiales(mat_cim)
            else:
                st.caption("Selecciona al menos un tipo de cimiento para calcular.")
        # --- 4. Sobrecimiento ---
        with st.expander("4. Sobrecimiento (Con Descuento de Vanos)", expanded=False):

            if "secciones_sc" not in st.session_state:
                st.session_state.secciones_sc = [{"largo": 0.0, "ancho": 0.0, "alto": 0.0}]

            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ Agregar sección", key="add_sc"):
                    st.session_state.secciones_sc.append({"largo": 0.0, "ancho": 0.0, "alto": 0.0})
            with col_del:
                if st.button("🗑️ Eliminar última sección", key="del_sc"):
                    if len(st.session_state.secciones_sc) > 1:
                        st.session_state.secciones_sc.pop()

            vol_sc_total = 0.0
            for i, sec in enumerate(st.session_state.secciones_sc):
                st.markdown(f"**Sección {i+1}**")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"sc_largo_{i}")
                with sc2:
                    sec["ancho"] = st.number_input("Ancho/Espesor (m)", value=sec["ancho"], key=f"sc_ancho_{i}")
                with sc3:
                    sec["alto"] = st.number_input("Alto (m)", value=sec["alto"], key=f"sc_alto_{i}")

                vol_sec_sc = sec["largo"] * sec["ancho"] * sec["alto"]
                st.caption(f"Volumen bruto sección {i+1}: {vol_sec_sc:.2f} m³")
                vol_sc_total += vol_sec_sc

            st.write("**Descuento de Vanos**")
            v1, v2 = st.columns(2)
            with v1:
                n_vanos_sc = st.number_input("Cantidad de vanos/puertas", value=0, step=1, key="vanos_cant_sc")
            with v2:
                ancho_vano_sc = st.number_input("Ancho del vano (m)", value=0.0, key="vanos_ancho_sc")

            espesor_sc = st.session_state.secciones_sc[0]["ancho"] if st.session_state.secciones_sc else 0.15
            alto_sc = st.session_state.secciones_sc[0]["alto"] if st.session_state.secciones_sc else 0.30
            vol_vanos_sc = n_vanos_sc * ancho_vano_sc * espesor_sc * alto_sc
            vol_sc_neto = vol_sc_total - vol_vanos_sc

            dos_sc = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                    index=1, key="dos_sc",
                                    help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_sc = calcular_materiales(vol_sc_neto, dos_sc)

            st.write("---")
            st.text(f"Volumen bruto total: {vol_sc_total:.2f} m³")
            st.text(f"Descuento vanos: -{vol_vanos_sc:.2f} m³")
            st.info(f"Volumen neto sobrecimiento: {vol_sc_neto:.2f} m³")
            mostrar_materiales(mat_sc)

        # --- 5. Radier ---
        with st.expander("5. Radier", expanded=False):

            if "secciones_rad" not in st.session_state:
                st.session_state.secciones_rad = [{"largo": 0.0, "ancho": 0.0, "espesor": 0.0}]

            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ Agregar sección", key="add_rad"):
                    st.session_state.secciones_rad.append({"largo": 0.0, "ancho": 0.0, "espesor": 0.0})
            with col_del:
                if st.button("🗑️ Eliminar última sección", key="del_rad"):
                    if len(st.session_state.secciones_rad) > 1:
                        st.session_state.secciones_rad.pop()

            area_radier_total = 0.0
            vol_radier = 0.0
            for i, sec in enumerate(st.session_state.secciones_rad):
                st.markdown(f"**Sección {i+1}**")
                ra1, ra2, ra3 = st.columns(3)
                with ra1:
                    sec["largo"] = st.number_input("Largo (m)", value=sec["largo"], key=f"rad_largo_{i}")
                with ra2:
                    sec["ancho"] = st.number_input("Ancho (m)", value=sec["ancho"], key=f"rad_ancho_{i}")
                with ra3:
                    sec["espesor"] = st.number_input("Espesor (m)", value=sec["espesor"], key=f"rad_espesor_{i}")

                vol_sec_rad = sec["largo"] * sec["ancho"] * sec["espesor"]
                area_sec_rad = sec["largo"] * sec["ancho"]
                st.caption(f"Volumen sección {i+1}: {vol_sec_rad:.2f} m³ | Área: {area_sec_rad:.2f} m²")
                vol_radier += vol_sec_rad
                area_radier_total += area_sec_rad

            rad_perdida = st.slider("% Pérdida Radier", 0, 15, 5, key="radier_perdida")
            vol_radier_final = vol_radier * (1 + rad_perdida / 100)

            dos_rad = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                    index=1, key="dos_rad",
                                    help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_rad = calcular_materiales(vol_radier_final, dos_rad)

            # --- Malla ACMA ---
            usar_malla = st.checkbox("¿Agregar malla ACMA al radier?", key="usar_malla")
            if usar_malla:
                malla_tipo = st.selectbox("Tipo de malla ACMA", list(MALLA_ACMA.keys()), key="malla_tipo")
                desp_malla = st.slider("% Desperdicio malla", 0, 20, 10, key="desp_malla")

                kg_malla = area_radier_total * MALLA_ACMA[malla_tipo]["kg_m2"]
                kg_malla_desp = kg_malla * (1 + desp_malla / 100)
                area_plancha_malla = 14.10  # plancha 2,35x6,00m
                planchas_malla = area_radier_total / area_plancha_malla
                planchas_malla_desp = planchas_malla * (1 + desp_malla / 100)

            st.write("---")
            st.info(f"Volumen neto radier: {vol_radier:.2f} m³")
            st.info(f"Área total radier: {area_radier_total:.2f} m²")
            st.success(f"Volumen con {rad_perdida}% pérdida: {vol_radier_final:.2f} m³")
            mostrar_materiales(mat_rad)

            if usar_malla:
                st.write("---")
                st.subheader("🔩 Malla ACMA")
                st.info(f"Tipo: {malla_tipo}")
                st.info(f"Peso malla: {kg_malla:.1f} kg")
                st.success(f"Con {desp_malla}% desperdicio: {kg_malla_desp:.1f} kg")
                st.success(f"Planchas 2,35x6,00m: {planchas_malla_desp:.0f} planchas")
                st.caption(f"Área total: {area_radier_total:.2f} m² | Plancha cubre: 14,1 m²")     

    # --- Acero estructural ---
    with st.expander("Acero estructural", expanded=False):

        modo_acero = st.radio(
            "Selecciona el modo de cálculo",
            ["Modo Simple"],
            horizontal=True
        )

        with st.expander("1. Losa", expanded=False):
            modo_losa = st.radio(
                "Modo de cálculo",
                ["🔨 Modo Simple", "📐 Modo Detallado"],
                horizontal=True, key="modo_losa"
            )
            if modo_losa == "🔨 Modo Simple":
                st.caption("Estimación por ratio kg/m²")
                ls1, ls2 = st.columns(2)
                with ls1:
                    largo_losa = st.number_input("Largo losa (m)", value=0.0, key="ls_largo")
                with ls2:
                    ancho_losa = st.number_input("Ancho losa (m)", value=0.0, key="ls_ancho")
                area_losa = largo_losa * ancho_losa
                kg_acero_losa = area_losa * 8
                diametro_losa = st.selectbox("Diámetro de barra", list(PESO_BARRAS.keys()), key="diam_losa")
                largo_barra_losa = st.selectbox("Largo de barra", ["6m", "12m"], key="largo_losa")
                largo_metros_losa = float(largo_barra_losa.replace("m", ""))
                kg_por_barra_losa = PESO_BARRAS[diametro_losa] * largo_metros_losa
                cant_barras_losa = kg_acero_losa / kg_por_barra_losa if kg_por_barra_losa > 0 else 0
                st.info(f"Área losa: {area_losa:.2f} m²")
                st.text(f"Acero estimado: {kg_acero_losa:.1f} kg")
                st.text(f"Cantidad de barras {diametro_losa}: {cant_barras_losa:.0f} barras de {largo_barra_losa}")
            elif modo_losa == "📐 Modo Detallado":
                st.caption("Cálculo por barras en ambas direcciones")
                ld1, ld2 = st.columns(2)
                with ld1:
                    largo_losa_d = st.number_input("Largo losa (m)", value=0.0, key="ld_largo")
                with ld2:
                    ancho_losa_d = st.number_input("Ancho losa (m)", value=0.0, key="ld_ancho")
                st.write("**Barras dirección X (largo)**")
                dx1, dx2, dx3 = st.columns(3)
                with dx1:
                    diam_x = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_x")
                with dx2:
                    sep_x = st.selectbox("Separación (m)", [0.10, 0.15, 0.20, 0.25], key="sep_x")
                with dx3:
                    largo_barra_x = st.selectbox("Largo barra", ["6m", "12m"], key="largo_x")
                st.write("**Barras dirección Y (ancho)**")
                dy1, dy2, dy3 = st.columns(3)
                with dy1:
                    diam_y = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_y")
                with dy2:
                    sep_y = st.selectbox("Separación (m)", [0.10, 0.15, 0.20, 0.25], key="sep_y")
                with dy3:
                    largo_barra_y = st.selectbox("Largo barra", ["6m", "12m"], key="largo_y")
                cant_barras_x = ancho_losa_d / sep_x if sep_x > 0 else 0
                largo_m_x = float(largo_barra_x.replace("m", ""))
                kg_x = cant_barras_x * largo_losa_d * PESO_BARRAS[diam_x]
                barras_x = (cant_barras_x * largo_losa_d) / largo_m_x
                cant_barras_y = largo_losa_d / sep_y if sep_y > 0 else 0
                largo_m_y = float(largo_barra_y.replace("m", ""))
                kg_y = cant_barras_y * ancho_losa_d * PESO_BARRAS[diam_y]
                barras_y = (cant_barras_y * ancho_losa_d) / largo_m_y
                kg_total_losa = kg_x + kg_y
                st.write("---")
                st.info(f"Acero total losa: {kg_total_losa:.1f} kg")
                st.text(f"Dirección X: {barras_x:.0f} barras {diam_x} de {largo_barra_x}")
                st.text(f"Dirección Y: {barras_y:.0f} barras {diam_y} de {largo_barra_y}")
                st.text(f"Kg dirección X: {kg_x:.1f} kg")
                st.text(f"Kg dirección Y: {kg_y:.1f} kg")

        with st.expander("2. Pilar", expanded=False):
            modo_pilar = st.radio(
                "Modo de cálculo",
                ["🔨 Modo Simple", "📐 Modo Detallado"],
                horizontal=True, key="modo_pilar"
            )
            if modo_pilar == "🔨 Modo Simple":
                st.caption("Cálculo por barras longitudinales y estribos")
                p1, p2, p3 = st.columns(3)
                with p1:
                    cant_pilares = st.number_input("Cantidad de pilares", value=1, step=1, key="cant_pil")
                with p2:
                    alto_pilar_a = st.number_input("Alto pilar (m)", value=0.0, key="alto_pil")
                with p3:
                    barras_long = st.selectbox("Barras longitudinales", [4, 6, 8], key="barras_long")
                p4, p5, p6 = st.columns(3)
                with p4:
                    diam_long = st.selectbox("Diámetro barra long.", list(PESO_BARRAS.keys()), index=2, key="diam_long")
                with p5:
                    sep_estribo = st.selectbox("Separación estribos (m)", ["0.10", "0.15", "0.20"], key="sep_estribo")
                    sep_estribo = float(sep_estribo)
                with p6:
                    diam_estribo = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_estribo")
                p7, p8 = st.columns(2)
                with p7:
                    ancho_pilar_a = st.number_input("Ancho pilar (m)", value=0.0, key="ancho_pil")
                with p8:
                    largo_pilar_a = st.number_input("Largo pilar (m)", value=0.0, key="largo_pil")
                ml_long = barras_long * alto_pilar_a * cant_pilares
                kg_long = ml_long * PESO_BARRAS[diam_long]
                n_estribos = (alto_pilar_a / sep_estribo) * cant_pilares
                perimetro_estribo = ((ancho_pilar_a + largo_pilar_a) * 2) + 0.20
                ml_estribos = n_estribos * perimetro_estribo
                kg_estribos = ml_estribos * PESO_BARRAS[diam_estribo]
                kg_total_pilar = kg_long + kg_estribos
                st.write("---")
                st.info(f"Acero total pilares: {kg_total_pilar:.1f} kg")
                st.text(f"Barras long.: {barras_long * cant_pilares} barras {diam_long} x {alto_pilar_a}m")
                st.text(f"Estribos: {n_estribos:.0f} estribos {diam_estribo} c/{sep_estribo}m")
                st.text(f"Kg longitudinal: {kg_long:.1f} kg")
                st.text(f"Kg estribos: {kg_estribos:.1f} kg")
            elif modo_pilar == "📐 Modo Detallado":
                st.caption("Cálculo exacto por barra")
                pd1, pd2 = st.columns(2)
                with pd1:
                    cant_pil_d = st.number_input("Cantidad de pilares", value=1, step=1, key="cant_pil_d")
                with pd2:
                    alto_pil_d = st.number_input("Alto pilar (m)", value=0.0, key="alto_pil_d")
                st.write("**Barras longitudinales**")
                bl1, bl2 = st.columns(2)
                with bl1:
                    cant_bl = st.number_input("Cantidad barras", value=4, step=1, key="cant_bl")
                with bl2:
                    diam_bl = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), index=2, key="diam_bl")
                st.write("**Estribos**")
                be1, be2, be3 = st.columns(3)
                with be1:
                    ancho_p = st.number_input("Ancho pilar (m)", value=0.0, key="ancho_p_d")
                with be2:
                    largo_p = st.number_input("Largo pilar (m)", value=0.0, key="largo_p_d")
                with be3:
                    sep_be = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20"], key="sep_be")
                sep_be = float(sep_be)
                diam_be = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_be")
                ml_bl = cant_bl * alto_pil_d * cant_pil_d
                kg_bl = ml_bl * PESO_BARRAS[diam_bl]
                n_estribos_d = (alto_pil_d / sep_be) * cant_pil_d
                perimetro_d = ((ancho_p + largo_p) * 2) + 0.20
                kg_be = n_estribos_d * perimetro_d * PESO_BARRAS[diam_be]
                kg_total_d = kg_bl + kg_be
                st.write("---")
                st.info(f"Acero total pilares: {kg_total_d:.1f} kg")
                st.text(f"Barras long.: {cant_bl * cant_pil_d} barras {diam_bl} x {alto_pil_d}m → {kg_bl:.1f} kg")
                st.text(f"Estribos: {n_estribos_d:.0f} estribos {diam_be} c/{sep_be}m → {kg_be:.1f} kg")

        with st.expander("3. Viga", expanded=False):
            modo_viga = st.radio(
                "Modo de cálculo",
                ["🔨 Modo Simple", "📐 Modo Detallado"],
                horizontal=True, key="modo_viga"
            )
            if modo_viga == "🔨 Modo Simple":
                st.caption("Estimación por ratio kg/m³")
                v1, v2, v3 = st.columns(3)
                with v1:
                    cant_vigas = st.number_input("Cantidad de vigas", value=0, step=1, key="cant_vigas")
                with v2:
                    largo_viga = st.number_input("Largo viga (m)", value=0.0, key="largo_viga")
                with v3:
                    alto_viga = st.number_input("Alto viga (m)", value=0.0, key="alto_viga")
                ancho_viga = st.number_input("Ancho viga (m)", value=0.0, key="ancho_viga")
                vol_viga = cant_vigas * largo_viga * alto_viga * ancho_viga
                kg_acero_viga = vol_viga * 120
                diam_viga_s = st.selectbox("Diámetro de barra", list(PESO_BARRAS.keys()), key="diam_viga_s")
                largo_barra_viga_s = st.selectbox("Largo de barra", ["6m", "12m"], key="largo_viga_s")
                largo_metros_viga_s = float(largo_barra_viga_s.replace("m", ""))
                kg_por_barra_viga = PESO_BARRAS[diam_viga_s] * largo_metros_viga_s
                cant_barras_viga = kg_acero_viga / kg_por_barra_viga if kg_por_barra_viga > 0 else 0
                st.write("---")
                st.info(f"Acero estimado: {kg_acero_viga:.1f} kg")
                st.text(f"Cantidad de barras {diam_viga_s}: {cant_barras_viga:.0f} barras de {largo_barra_viga_s}")
                st.caption(f"Volumen vigas: {vol_viga:.2f} m³ | Ratio: 120 kg/m³")
            elif modo_viga == "📐 Modo Detallado":
                st.caption("Cálculo por barras superiores, inferiores y estribos")
                vd1, vd2, vd3 = st.columns(3)
                with vd1:
                    cant_vigas_d = st.number_input("Cantidad de vigas", value=0, step=1, key="cant_vigas_d")
                with vd2:
                    largo_viga_d = st.number_input("Largo viga (m)", value=0.0, key="largo_viga_d")
                with vd3:
                    ancho_viga_d = st.number_input("Ancho viga (m)", value=0.0, key="ancho_viga_d")
                st.write("**Barras superiores**")
                vs1, vs2 = st.columns(2)
                with vs1:
                    cant_sup = st.number_input("Cantidad barras sup.", value=0, step=1, key="cant_sup")
                with vs2:
                    diam_sup = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_sup")
                st.write("**Barras inferiores**")
                vi1, vi2 = st.columns(2)
                with vi1:
                    cant_inf = st.number_input("Cantidad barras inf.", value=0, step=1, key="cant_inf")
                with vi2:
                    diam_inf = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_inf")
                st.write("**Estribos**")
                ve1, ve2 = st.columns(2)
                with ve1:
                    sep_estribo_v = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20"], key="sep_estribo_v")
                with ve2:
                    diam_estribo_v = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_estribo_v")
                sep_estribo_v = float(sep_estribo_v)
                ml_sup = cant_sup * largo_viga_d * cant_vigas_d
                kg_sup = ml_sup * PESO_BARRAS[diam_sup]
                ml_inf = cant_inf * largo_viga_d * cant_vigas_d
                kg_inf = ml_inf * PESO_BARRAS[diam_inf]
                n_estribos_v = (largo_viga_d / sep_estribo_v) * cant_vigas_d
                perimetro_estribo_v = ((ancho_viga_d + 0.30) * 2) + 0.20
                kg_estribo_v = n_estribos_v * perimetro_estribo_v * PESO_BARRAS[diam_estribo_v]
                kg_total_viga = kg_sup + kg_inf + kg_estribo_v
                st.write("---")
                st.info(f"Acero total vigas: {kg_total_viga:.1f} kg")
                st.text(f"Barras sup.: {cant_sup * cant_vigas_d} barras {diam_sup} → {kg_sup:.1f} kg")
                st.text(f"Barras inf.: {cant_inf * cant_vigas_d} barras {diam_inf} → {kg_inf:.1f} kg")
                st.text(f"Estribos: {n_estribos_v:.0f} estribos {diam_estribo_v} c/{sep_estribo_v}m → {kg_estribo_v:.1f} kg")

        with st.expander("4. Radier", expanded=False):
            modo_radier = st.radio(
                "Modo de cálculo",
                ["🔨 Modo Simple", "📐 Modo Detallado"],
                horizontal=True, key="modo_radier"
            )
            if modo_radier == "🔨 Modo Simple":
                st.caption("Estimación por ratio kg/m²")
                rr1, rr2 = st.columns(2)
                with rr1:
                    largo_rad_a = st.number_input("Largo radier (m)", value=0.0, key="largo_rad_a")
                with rr2:
                    ancho_rad_a = st.number_input("Ancho radier (m)", value=0.0, key="ancho_rad_a")
                area_rad = largo_rad_a * ancho_rad_a
                kg_acero_rad = area_rad * 5
                diam_rad_s = st.selectbox("Diámetro de barra", list(PESO_BARRAS.keys()), key="diam_rad_s")
                largo_barra_rad = st.selectbox("Largo de barra", ["6m", "12m"], key="largo_rad_s")
                largo_metros_rad = float(largo_barra_rad.replace("m", ""))
                kg_por_barra_rad = PESO_BARRAS[diam_rad_s] * largo_metros_rad
                cant_barras_rad = kg_acero_rad / kg_por_barra_rad if kg_por_barra_rad > 0 else 0
                st.write("---")
                st.info(f"Acero estimado: {kg_acero_rad:.1f} kg")
                st.text(f"Cantidad de barras {diam_rad_s}: {cant_barras_rad:.0f} barras de {largo_barra_rad}")
                st.caption(f"Área radier: {area_rad:.2f} m² | Ratio: 5 kg/m²")
            elif modo_radier == "📐 Modo Detallado":
                st.caption("Cálculo por barras en ambas direcciones")
                rd1, rd2 = st.columns(2)
                with rd1:
                    largo_rad_d = st.number_input("Largo radier (m)", value=0.0, key="largo_rad_d")
                with rd2:
                    ancho_rad_d = st.number_input("Ancho radier (m)", value=0.0, key="ancho_rad_d")
                st.write("**Barras dirección X (largo)**")
                rx1, rx2, rx3 = st.columns(3)
                with rx1:
                    diam_rx = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_rx")
                with rx2:
                    sep_rx = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20", "0.25"], key="sep_rx")
                with rx3:
                    largo_barra_rx = st.selectbox("Largo barra", ["6m", "12m"], key="largo_rx")
                sep_rx = float(sep_rx)
                st.write("**Barras dirección Y (ancho)**")
                ry1, ry2, ry3 = st.columns(3)
                with ry1:
                    diam_ry = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_ry")
                with ry2:
                    sep_ry = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20", "0.25"], key="sep_ry")
                with ry3:
                    largo_barra_ry = st.selectbox("Largo barra", ["6m", "12m"], key="largo_ry")
                sep_ry = float(sep_ry)
                cant_barras_rx = ancho_rad_d / sep_rx if sep_rx > 0 else 0
                largo_m_rx = float(largo_barra_rx.replace("m", ""))
                kg_rx = cant_barras_rx * largo_rad_d * PESO_BARRAS[diam_rx]
                barras_rx = (cant_barras_rx * largo_rad_d) / largo_m_rx
                cant_barras_ry = largo_rad_d / sep_ry if sep_ry > 0 else 0
                largo_m_ry = float(largo_barra_ry.replace("m", ""))
                kg_ry = cant_barras_ry * ancho_rad_d * PESO_BARRAS[diam_ry]
                barras_ry = (cant_barras_ry * ancho_rad_d) / largo_m_ry
                kg_total_rad = kg_rx + kg_ry
                st.write("---")
                st.info(f"Acero total radier: {kg_total_rad:.1f} kg")
                st.text(f"Dirección X: {barras_rx:.0f} barras {diam_rx} de {largo_barra_rx} → {kg_rx:.1f} kg")
                st.text(f"Dirección Y: {barras_ry:.0f} barras {diam_ry} de {largo_barra_ry} → {kg_ry:.1f} kg")

        with st.expander("5. Cimiento", expanded=False):
    
            modo_cimiento = st.radio(
                "Modo de cálculo",
                ["🔨 Modo Simple", "📐 Modo Detallado"],
                horizontal=True,
                key="modo_cimiento"
            )
            
            if modo_cimiento == "🔨 Modo Simple":
                st.caption("Estimación por ratio kg/m³")
                
                ci1, ci2, ci3 = st.columns(3)
                with ci1:
                    cant_cim = st.number_input("Cantidad de cimientos", value=0, step=1, key="cant_cim")
                with ci2:
                    largo_cim = st.number_input("Largo cimiento (m)", value=0.0, key="largo_cim")
                with ci3:
                    ancho_cim = st.number_input("Ancho cimiento (m)", value=0.0, key="ancho_cim")
                
                alto_cim = st.number_input("Alto cimiento (m)", value=0.0, key="alto_cim")
                
                vol_cim = cant_cim * largo_cim * ancho_cim * alto_cim
                kg_acero_cim = vol_cim * 80  # ratio 80 kg/m³
                
                diam_cim_s = st.selectbox("Diámetro de barra", list(PESO_BARRAS.keys()), key="diam_cim_s")
                largo_barra_cim = st.selectbox("Largo de barra", ["6m", "12m"], key="largo_cim_s")
                largo_metros_cim = float(largo_barra_cim.replace("m", ""))
                
                kg_por_barra_cim = PESO_BARRAS[diam_cim_s] * largo_metros_cim
                cant_barras_cim = kg_acero_cim / kg_por_barra_cim if kg_por_barra_cim > 0 else 0
                
                st.write("---")
                st.info(f"Acero estimado: {kg_acero_cim:.1f} kg")
                st.text(f"Cantidad de barras {diam_cim_s}: {cant_barras_cim:.0f} barras de {largo_barra_cim}")
                st.caption(f"Volumen cimiento: {vol_cim:.2f} m³ | Ratio: 80 kg/m³")

            elif modo_cimiento == "📐 Modo Detallado":
                st.caption("Cálculo por barras longitudinales y estribos")
                
                cd1, cd2, cd3 = st.columns(3)
                with cd1:
                    cant_cim_d = st.number_input("Cantidad de cimientos", value=0, step=1, key="cant_cim_d")
                with cd2:
                    largo_cim_d = st.number_input("Largo cimiento (m)", value=0.0, key="largo_cim_d")
                with cd3:
                    ancho_cim_d = st.number_input("Ancho cimiento (m)", value=0.0, key="ancho_cim_d")

                st.write("**Barras longitudinales**")
                cl1, cl2 = st.columns(2)
                with cl1:
                    cant_bl_cim = st.number_input("Cantidad barras", value=0, step=1, key="cant_bl_cim")
                with cl2:
                    diam_bl_cim = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), key="diam_bl_cim")

                st.write("**Estribos**")
                ce1, ce2 = st.columns(2)
                with ce1:
                    sep_estribo_cim = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20", "0.25"], key="sep_estribo_cim")
                with ce2:
                    diam_estribo_cim = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_estribo_cim")
                sep_estribo_cim = float(sep_estribo_cim)

                # Cálculo barras longitudinales
                ml_bl_cim = cant_bl_cim * largo_cim_d * cant_cim_d
                kg_bl_cim = ml_bl_cim * PESO_BARRAS[diam_bl_cim]

                # Cálculo estribos
                n_estribos_cim = (largo_cim_d / sep_estribo_cim) * cant_cim_d
                perimetro_estribo_cim = ((ancho_cim_d + 0.30) * 2) + 0.20
                kg_estribo_cim = n_estribos_cim * perimetro_estribo_cim * PESO_BARRAS[diam_estribo_cim]

                kg_total_cim = kg_bl_cim + kg_estribo_cim

                st.write("---")
                st.info(f"Acero total cimientos: {kg_total_cim:.1f} kg")
                st.text(f"Barras long.: {cant_bl_cim * cant_cim_d} barras {diam_bl_cim} → {kg_bl_cim:.1f} kg")
                st.text(f"Estribos: {n_estribos_cim:.0f} estribos {diam_estribo_cim} c/{sep_estribo_cim}m → {kg_estribo_cim:.1f} kg") 
                

    # --- Acero No estructural ---       
    with st.expander(" Acero No Estructural (Tabiques Metalcon)", expanded=False):

        # ============================
        # DATOS SEGÚN MANUAL METALCON
        # ============================
        MONTANTES = {
            # Perforados
            "Montante Normal Perf. 60x38x0,5 - 2,40m":  {"largo": 2.40, "peso": 0.56},
            "Montante Normal Perf. 60x38x0,5 - 3,00m":  {"largo": 3.00, "peso": 0.56},
            # Económico (sin perforar)
            "Montante Económico 38x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.48},
            "Montante Económico 38x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.48},
        }

        CANALES = {
            "Canal Normal 61x20x0,5 - 2,40m":    {"largo": 2.40, "peso": 0.39},
            "Canal Normal 61x20x0,5 - 3,00m":    {"largo": 3.00, "peso": 0.39},
            "Canal Económico 39x20x0,5 - 2,40m": {"largo": 2.40, "peso": 0.31},
            "Canal Económico 39x20x0,5 - 3,00m": {"largo": 3.00, "peso": 0.31},
        }

        ESQUINEROS = {
            "Esquinero Perf. 30x30 - 2,40m":     {"largo": 2.40, "peso": 0.18},
            "Esquinero Perf. Eco. 25x25 - 3,00m": {"largo": 3.00, "peso": 0.15},
        }

        # --- 1. Canal / Solera ---
        with st.expander("1. Canal / Solera (inferior y superior)", expanded=False):
            st.caption("Se usa como solera en piso y cielo del tabique")

            canal_tipo = st.selectbox("Tipo de canal", list(CANALES.keys()), key="canal_tipo")

            ca1, ca2 = st.columns(2)
            with ca1:
                largo_tabique_c = st.number_input("Largo del tabique (m)", value=0.0, key="largo_tab_c")
            with ca2:
                cant_tabiques_c = st.number_input("Cantidad de tabiques", value=0, step=1, key="cant_tab_c")

            largo_canal = CANALES[canal_tipo]["largo"]

            # Solera inf + sup = largo tabique * 2 * cantidad tabiques
            ml_canal = largo_tabique_c * 2 * cant_tabiques_c
            cant_piezas_canal = ml_canal / largo_canal if largo_canal > 0 else 0

            # Desperdicio solera
            ultimo_tramo = ml_canal % largo_canal
            desperdicio_canal = (largo_canal - ultimo_tramo) if ultimo_tramo > 0 else 0
            
            # Sugerencia canal óptimo
            desperdicio_canal_240 = None
            desperdicio_canal_300 = None
            
            if largo_tabique_c > 0:
                ml_total_240 = largo_tabique_c * 2 * (cant_tabiques_c if cant_tabiques_c > 0 else 1)
                ml_total_300 = ml_total_240
                sobra_240 = ml_total_240 % 2.40
                sobra_300 = ml_total_300 % 3.00
                desperdicio_canal_240 = (2.40 - sobra_240) if sobra_240 > 0 else 0
                desperdicio_canal_300 = (3.00 - sobra_300) if sobra_300 > 0 else 0

            st.write("---")
            st.info(f"Metros lineales necesarios: {ml_canal:.2f} ml")
            st.text(f"Cantidad de canales {largo_canal}m: {cant_piezas_canal:.0f} piezas")

            if largo_tabique_c > 0:
                st.write("---")
                st.subheader("📐 Análisis de desperdicio")
                st.text(f"Desperdicio último tramo: {desperdicio_canal:.2f}m")

                st.write("**💡 Sugerencia de canal más conveniente:**")
                if desperdicio_canal_240 is not None and desperdicio_canal_300 is not None:
                    if desperdicio_canal_240 <= desperdicio_canal_300:
                        st.success(f"✅ Usa canal de 2,40m → desperdicio {desperdicio_canal_240:.2f}m")
                        st.warning(f"Con 3,00m → desperdicio {desperdicio_canal_300:.2f}m")
                    else:
                        st.success(f"✅ Usa canal de 3,00m → desperdicio {desperdicio_canal_300:.2f}m")
                        st.warning(f"Con 2,40m → desperdicio {desperdicio_canal_240:.2f}m")

            st.caption("Considera solera inferior + solera superior")

        # --- 2. Montante / Pie Derecho ---
        with st.expander("2. Montante / Pie Derecho", expanded=False):
            st.caption("Se instala cada 40 o 60 cm según revestimiento")

            montante_tipo = st.selectbox("Tipo de montante", list(MONTANTES.keys()), key="montante_tipo")

            if "Perf" in montante_tipo:
                st.caption("✅ Perforado: permite pasar instalaciones eléctricas y sanitarias por dentro")
            else:
                st.caption("⚠️ Sin perforaciones: usar cuando no pasan instalaciones por el tabique")

            mo1, mo2, mo3 = st.columns(3)
            with mo1:
                largo_tabique_m = st.number_input("Largo tabique (m)", value=0.0, key="largo_tab_m")
            with mo2:
                alto_tabique_m = st.number_input("Alto tabique (m)", value=0.0, key="alto_tab_m")
            with mo3:
                cant_tabiques_m = st.number_input("Cantidad tabiques", value=0, step=1, key="cant_tab_m")

            separacion_m = st.selectbox("Separación entre montantes",
                                        ["0,40m (recomendado)", "0,60m (máximo)"],
                                        key="sep_mont")
            sep_valor = 0.40 if "0,40" in separacion_m else 0.60

            largo_montante = MONTANTES[montante_tipo]["largo"]

            # Cálculo montantes
            montantes_por_tabique = int(largo_tabique_m / sep_valor) + 1
            total_montantes = montantes_por_tabique * cant_tabiques_m

            # Desperdicio
            corte_por_perfil = largo_montante - alto_tabique_m
            desperdicio_total = corte_por_perfil * total_montantes
            perfiles_desperdiciados = desperdicio_total / largo_montante if largo_montante > 0 else 0

            # Sugerencia de perfil óptimo
            desperdicio_240 = 2.40 - alto_tabique_m if alto_tabique_m <= 2.40 else None
            desperdicio_300 = 3.00 - alto_tabique_m if alto_tabique_m <= 3.00 else None

            st.write("---")
            st.info(f"Montantes por tabique: {montantes_por_tabique} piezas")
            st.info(f"Total montantes: {total_montantes} piezas de {largo_montante}m")

            if alto_tabique_m > 0 and largo_montante > 0:
                if corte_por_perfil < 0:
                    st.error(f"⚠️ El tabique ({alto_tabique_m}m) supera el montante ({largo_montante}m). Necesita empalme.")
                else:
                    st.write("---")
                    st.subheader("📐 Análisis de desperdicio")
                    st.text(f"Corte por perfil: {corte_por_perfil:.2f}m")
                    st.text(f"Desperdicio total: {desperdicio_total:.2f}m lineales")
                    st.text(f"Equivale a: {perfiles_desperdiciados:.1f} perfiles desperdiciados")

                    # Sugerencia perfil óptimo
                    st.write("**💡 Sugerencia de perfil más conveniente:**")
                    if desperdicio_240 is not None and desperdicio_300 is not None:
                        if desperdicio_240 <= desperdicio_300:
                            st.success(f"✅ Usa montante de 2,40m → sobran {desperdicio_240:.2f}m por perfil")
                            st.warning(f"Con 3,00m → sobrarían {desperdicio_300:.2f}m por perfil")
                        else:
                            st.success(f"✅ Usa montante de 3,00m → sobran {desperdicio_300:.2f}m por perfil")
                            st.warning(f"Con 2,40m → sobrarían {desperdicio_240:.2f}m por perfil")
                    elif desperdicio_240 is None:
                        st.success(f"✅ Usa montante de 3,00m → sobran {desperdicio_300:.2f}m por perfil")
                        st.error("❌ Montante de 2,40m no alcanza para este tabique")
                    
            st.caption(f"Separación: {sep_valor}m según manual Metalcon | +1 montante en extremo")

        # --- 3. Esquinero ---
        with st.expander("3. Esquinero", expanded=False):
            st.caption("Se usa en encuentros de muros y esquinas")

            esq_tipo = st.selectbox("Tipo de esquinero", list(ESQUINEROS.keys()), key="esq_tipo")
            cant_esquinas = st.number_input("Cantidad de esquinas/encuentros", value=0, step=1, key="cant_esq")
            
            largo_esq = ESQUINEROS[esq_tipo]["largo"]
            
            st.write("---")
            st.info(f"Cantidad de esquineros: {cant_esquinas} piezas de {largo_esq}m") 

            # Guardar en session_state para el PDF
            st.session_state["pdf_canal_tipo"] = canal_tipo
            st.session_state["pdf_cant_piezas_canal"] = cant_piezas_canal
            st.session_state["pdf_ml_canal"] = ml_canal
            st.session_state["pdf_largo_canal"] = largo_canal

            st.session_state["pdf_montante_tipo"] = montante_tipo
            st.session_state["pdf_total_montantes"] = total_montantes
            st.session_state["pdf_largo_montante"] = largo_montante

            st.session_state["pdf_esq_tipo"] = esq_tipo
            st.session_state["pdf_cant_esquinas"] = cant_esquinas
            st.session_state["pdf_largo_esq"] = largo_esq

    # ============================
    # MOLDAJES
    # ============================
    with st.expander(" Moldajes", expanded=False):

        # Datos materiales
        MATERIALES_MOLDAJE = {
            "Tabla 1\"x8\" (ancho 19cm)": {"ancho": 0.19, "largo": 3.20},
            "Tabla 1\"x10\" (ancho 24cm)": {"ancho": 0.24, "largo": 3.20},
            "Terciado Film 18mm (1,22x2,44m)": {"area_plancha": 2.98},
            "Moldaje Metálico": {"solo_m2": True},
        }

        # --- 1. Cimiento ---
        with st.expander("1. Moldaje de Cimiento", expanded=False):
            st.caption("Moldaje para caras laterales del cimiento")

            material_cim = st.selectbox(
                "Material de moldaje",
                list(MATERIALES_MOLDAJE.keys()),
                key="mat_mold_cim"
            )

            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                largo_cim_m = st.number_input("Largo cimiento (m)", value=0.0, key="largo_cim_mold")
            with mc2:
                alto_cim_m = st.number_input("Alto cimiento (m)", value=0.0, key="alto_cim_mold")
            with mc3:
                cant_cim_m = st.number_input("Cantidad cimientos", value=0, step=1, key="cant_cim_mold")

            # m² = largo * alto * 2 caras * cantidad
            m2_cimiento = largo_cim_m * alto_cim_m * 2 * cant_cim_m

            st.write("---")
            st.info(f"Superficie de moldaje: {m2_cimiento:.2f} m²")

            mat = MATERIALES_MOLDAJE[material_cim]

            if "solo_m2" in mat:
                st.text(f"Moldaje metálico requerido: {m2_cimiento:.2f} m²")

            elif "area_plancha" in mat:
                cant_planchas = m2_cimiento / mat["area_plancha"]
                st.text(f"Planchas terciado 1,22x2,44m: {cant_planchas:.0f} unidades")
                st.caption("Considera un 10% de desperdicio por cortes")
                cant_planchas_real = cant_planchas * 1.10
                st.text(f"Con 10% desperdicio: {cant_planchas_real:.0f} planchas")

            else:
                # Tabla
                ml_tabla = m2_cimiento / mat["ancho"]
                cant_tablas = ml_tabla / mat["largo"]
                st.text(f"Metros lineales de tabla: {ml_tabla:.2f} ml")
                st.text(f"Cantidad de tablas de {mat['largo']}m: {cant_tablas:.0f} unidades")
                st.caption("Considera un 10% de desperdicio por cortes")
                cant_tablas_real = cant_tablas * 1.10
                st.text(f"Con 10% desperdicio: {cant_tablas_real:.0f} tablas")   

        # --- 2. Moldaje de Muro ---
        with st.expander("2. Moldaje de Muro", expanded=False):
            st.caption("Moldaje para ambas caras del muro")

            material_muro = st.selectbox(
                "Material de moldaje",
                list(MATERIALES_MOLDAJE.keys()),
                key="mat_mold_muro"
            )

            mm1, mm2, mm3 = st.columns(3)
            with mm1:
                largo_muro_m = st.number_input("Largo muro (m)", value=0.0, key="largo_muro_mold")
            with mm2:
                alto_muro_m = st.number_input("Alto muro (m)", value=0.0, key="alto_muro_mold")
            with mm3:
                cant_muro_m = st.number_input("Cantidad de muros", value=0, step=1, key="cant_muro_mold")

            # m² = largo * alto * 2 caras * cantidad
            m2_muro = largo_muro_m * alto_muro_m * 2 * cant_muro_m

            st.write("---")
            st.info(f"Superficie de moldaje: {m2_muro:.2f} m²")

            mat_m = MATERIALES_MOLDAJE[material_muro]

            if "solo_m2" in mat_m:
                st.text(f"Moldaje metálico requerido: {m2_muro:.2f} m²")
            elif "area_plancha" in mat_m:
                cant_planchas = m2_muro / mat_m["area_plancha"]
                cant_planchas_real = cant_planchas * 1.10
                st.text(f"Planchas terciado 1,22x2,44m: {cant_planchas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_planchas_real:.0f} planchas")
            else:
                ml_tabla = m2_muro / mat_m["ancho"]
                cant_tablas = ml_tabla / mat_m["largo"]
                cant_tablas_real = cant_tablas * 1.10
                st.text(f"Metros lineales de tabla: {ml_tabla:.2f} ml")
                st.text(f"Cantidad de tablas de {mat_m['largo']}m: {cant_tablas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_tablas_real:.0f} tablas")

        # --- 3. Moldaje de Losa ---
        with st.expander("3. Moldaje de Losa", expanded=False):
            st.caption("Moldaje para cara inferior de la losa")

            material_losa = st.selectbox(
                "Material de moldaje",
                list(MATERIALES_MOLDAJE.keys()),
                key="mat_mold_losa"
            )

            ml1, ml2 = st.columns(2)
            with ml1:
                largo_losa_m = st.number_input("Largo losa (m)", value=0.0, key="largo_losa_mold")
            with ml2:
                ancho_losa_m = st.number_input("Ancho losa (m)", value=0.0, key="ancho_losa_mold")

            # m² = largo * ancho (solo cara inferior)
            m2_losa = largo_losa_m * ancho_losa_m

            st.write("---")
            st.info(f"Superficie de moldaje: {m2_losa:.2f} m²")

            mat_l = MATERIALES_MOLDAJE[material_losa]

            if "solo_m2" in mat_l:
                st.text(f"Moldaje metálico requerido: {m2_losa:.2f} m²")
            elif "area_plancha" in mat_l:
                cant_planchas = m2_losa / mat_l["area_plancha"]
                cant_planchas_real = cant_planchas * 1.10
                st.text(f"Planchas terciado 1,22x2,44m: {cant_planchas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_planchas_real:.0f} planchas")
            else:
                ml_tabla = m2_losa / mat_l["ancho"]
                cant_tablas = ml_tabla / mat_l["largo"]
                cant_tablas_real = cant_tablas * 1.10
                st.text(f"Metros lineales de tabla: {ml_tabla:.2f} ml")
                st.text(f"Cantidad de tablas de {mat_l['largo']}m: {cant_tablas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_tablas_real:.0f} tablas")

        # --- 4. Moldaje de Viga ---
        with st.expander("4. Moldaje de Viga", expanded=False):
            st.caption("Moldaje para fondo y caras laterales de la viga")

            material_viga = st.selectbox(
                "Material de moldaje",
                list(MATERIALES_MOLDAJE.keys()),
                key="mat_mold_viga"
            )

            mv1, mv2, mv3, mv4 = st.columns(4)
            with mv1:
                largo_viga_m = st.number_input("Largo viga (m)", value=0.0, key="largo_viga_mold")
            with mv2:
                alto_viga_m = st.number_input("Alto viga (m)", value=0.0, key="alto_viga_mold")
            with mv3:
                ancho_viga_m = st.number_input("Ancho viga (m)", value=0.0, key="ancho_viga_mold")
            with mv4:
                cant_viga_m = st.number_input("Cantidad vigas", value=0, step=1, key="cant_viga_mold")

            # m² = (fondo + 2 caras laterales) * largo * cantidad
            m2_viga = (ancho_viga_m + (alto_viga_m * 2)) * largo_viga_m * cant_viga_m

            st.write("---")
            st.info(f"Superficie de moldaje: {m2_viga:.2f} m²")

            mat_v = MATERIALES_MOLDAJE[material_viga]

            if "solo_m2" in mat_v:
                st.text(f"Moldaje metálico requerido: {m2_viga:.2f} m²")
            elif "area_plancha" in mat_v:
                cant_planchas = m2_viga / mat_v["area_plancha"]
                cant_planchas_real = cant_planchas * 1.10
                st.text(f"Planchas terciado 1,22x2,44m: {cant_planchas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_planchas_real:.0f} planchas")
            else:
                ml_tabla = m2_viga / mat_v["ancho"]
                cant_tablas = ml_tabla / mat_v["largo"]
                cant_tablas_real = cant_tablas * 1.10
                st.text(f"Metros lineales de tabla: {ml_tabla:.2f} ml")
                st.text(f"Cantidad de tablas de {mat_v['largo']}m: {cant_tablas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_tablas_real:.0f} tablas")

        # --- 5. Moldaje de Pilar ---
        with st.expander("5. Moldaje de Pilar", expanded=False):
            st.caption("Moldaje para las 4 caras del pilar")

            material_pilar = st.selectbox(
                "Material de moldaje",
                list(MATERIALES_MOLDAJE.keys()),
                key="mat_mold_pilar"
            )

            mp1, mp2, mp3, mp4 = st.columns(4)
            with mp1:
                ancho_pilar_m = st.number_input("Ancho pilar (m)", value=0.0, key="ancho_pilar_mold")
            with mp2:
                largo_pilar_m = st.number_input("Largo pilar (m)", value=0.0, key="largo_pilar_mold")
            with mp3:
                alto_pilar_m = st.number_input("Alto pilar (m)", value=0.0, key="alto_pilar_mold")
            with mp4:
                cant_pilar_m = st.number_input("Cantidad pilares", value=0, step=1, key="cant_pilar_mold")

            # m² = perimetro * alto * cantidad
            perimetro_pilar = (ancho_pilar_m + largo_pilar_m) * 2
            m2_pilar = perimetro_pilar * alto_pilar_m * cant_pilar_m

            st.write("---")
            st.info(f"Superficie de moldaje: {m2_pilar:.2f} m²")

            mat_p = MATERIALES_MOLDAJE[material_pilar]

            if "solo_m2" in mat_p:
                st.text(f"Moldaje metálico requerido: {m2_pilar:.2f} m²")
            elif "area_plancha" in mat_p:
                cant_planchas = m2_pilar / mat_p["area_plancha"]
                cant_planchas_real = cant_planchas * 1.10
                st.text(f"Planchas terciado 1,22x2,44m: {cant_planchas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_planchas_real:.0f} planchas")
            else:
                ml_tabla = m2_pilar / mat_p["ancho"]
                cant_tablas = ml_tabla / mat_p["largo"]
                cant_tablas_real = cant_tablas * 1.10
                st.text(f"Metros lineales de tabla: {ml_tabla:.2f} ml")
                st.text(f"Cantidad de tablas de {mat_p['largo']}m: {cant_tablas:.0f} unidades")
                st.text(f"Con 10% desperdicio: {cant_tablas_real:.0f} tablas")     

    # ============================
    # Muros
    # ============================   

    with st.expander(" Muros", expanded=False):
        # ============================
        # MURO DE HORMIGÓN
        # ============================
        with st.expander("1. Muro de Hormigón (con Enfierradura)", expanded=False):

            st.subheader("📐 Dimensiones del muro")
            mh1, mh2, mh3, mh4 = st.columns(4)
            with mh1:
                largo_muro_h = st.number_input("Largo muro (m)", value=0.0, key="largo_muro_h")
            with mh2:
                alto_muro_h = st.number_input("Alto muro (m)", value=0.0, key="alto_muro_h")
            with mh3:
                espesor_muro_h = st.number_input("Espesor muro (m)", value=0.0, key="espesor_muro_h")
            with mh4:
                cant_muros_h = st.number_input("Cantidad muros", value=0, step=1, key="cant_muros_h")

            # Vanos
            st.subheader("🚪 Vanos")
            vh1, vh2 = st.columns(2)
            with vh1:
                cant_puertas_h = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_h")
                ancho_puerta_h = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_h")
                alto_puerta_h = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_h")
            with vh2:
                cant_ventanas_h = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_h")
                ancho_ventana_h = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_h")
                alto_ventana_h = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_h")

            # Volumen neto
            vol_bruto_h = largo_muro_h * alto_muro_h * espesor_muro_h * cant_muros_h
            vol_vanos_h = ((cant_puertas_h * ancho_puerta_h * alto_puerta_h) +
                          (cant_ventanas_h * ancho_ventana_h * alto_ventana_h)) * espesor_muro_h
            vol_neto_h = vol_bruto_h - vol_vanos_h

            # Dosificación
            dos_muro_h = st.selectbox("Dosificación hormigón", list(DOSIFICACIONES.keys()),
                                      index=2, key="dos_muro_h",
                                      help=DOSIFICACIONES["G-25"]["descripcion"])
            mat_muro_h = calcular_materiales(vol_neto_h, dos_muro_h)

            st.write("---")
            st.subheader("📊 Modo de cálculo enfierradura")
            modo_muro_h = st.radio(
                "Selecciona el modo",
                ["🔨 Modo Simple (estimación)", "📐 Modo Detallado (con planos)"],
                horizontal=True,
                key="modo_muro_h"
            )

            # ============================
            # MODO SIMPLE
            # ============================
            if modo_muro_h == "🔨 Modo Simple (estimación)":
                st.caption("Valores típicos según NCh430 para muros estructurales en Chile")

                if espesor_muro_h >= 0.20:
                    st.warning("⚠️ Espesor ≥ 20cm: NCh430 exige doble malla obligatoriamente")
                    tipo_malla = "Doble"
                else:
                    st.info("ℹ️ Espesor < 20cm: Se puede usar malla simple o doble según cálculo")
                    tipo_malla = st.selectbox("Tipo de malla", ["Simple", "Doble"], key="malla_simple_h")

                ms1, ms2 = st.columns(2)
                with ms1:
                    diam_vert_s = st.selectbox("Diámetro barra vertical",
                                               ["Ø8mm", "Ø10mm", "Ø12mm"],
                                               index=1, key="diam_vert_s")
                    sep_vert_s = st.selectbox("Separación vertical (m)",
                                              ["0.15", "0.20", "0.25"],
                                              index=1, key="sep_vert_s")
                with ms2:
                    diam_horiz_s = st.selectbox("Diámetro barra horizontal",
                                                ["Ø8mm", "Ø10mm", "Ø12mm"],
                                                index=1, key="diam_horiz_s")
                    sep_horiz_s = st.selectbox("Separación horizontal (m)",
                                               ["0.15", "0.20", "0.25"],
                                               index=1, key="sep_horiz_s")

                sep_v_s = float(sep_vert_s)
                sep_h_s = float(sep_horiz_s)
                n_mallas = 2 if tipo_malla == "Doble" else 1

                # Barras verticales
                cant_barras_v_s = (largo_muro_h / sep_v_s + 1) * cant_muros_h * n_mallas
                ml_v_s = cant_barras_v_s * alto_muro_h
                kg_v_s = ml_v_s * PESO_BARRAS[diam_vert_s]

                # Barras horizontales
                cant_barras_h_s = (alto_muro_h / sep_h_s + 1) * cant_muros_h * n_mallas
                ml_h_s = cant_barras_h_s * largo_muro_h
                kg_h_s = ml_h_s * PESO_BARRAS[diam_horiz_s]

                # Barras de borde (4 barras Ø12mm en cada extremo)
                st.info("💡 NCh430: Se recomiendan barras de borde en extremos del muro")
                diam_borde = st.selectbox("Diámetro barra de borde",
                                          ["Ø12mm", "Ø16mm", "Ø20mm"],
                                          index=0, key="diam_borde_s")
                ml_borde = alto_muro_h * 4 * cant_muros_h
                kg_borde = ml_borde * PESO_BARRAS[diam_borde]

                # Refuerzo diagonal vanos
                kg_diag = 0
                if cant_puertas_h > 0 or cant_ventanas_h > 0:
                    st.info("💡 NCh430: Se requieren barras diagonales Ø12mm en esquinas de vanos")
                    ml_diag = (cant_puertas_h + cant_ventanas_h) * 4 * 0.60 * cant_muros_h
                    kg_diag = ml_diag * PESO_BARRAS["Ø12mm"]

                kg_total_h = kg_v_s + kg_h_s + kg_borde + kg_diag

                st.write("---")
                st.subheader("📦 Resultados Hormigón")
                mostrar_materiales(mat_muro_h)

                st.subheader("📦 Resultados Enfierradura")
                re1, re2 = st.columns(2)
                with re1:
                    st.info(f"Volumen neto muro: {vol_neto_h:.2f} m³")
                    st.info(f"Malla: {tipo_malla} ({n_mallas} capa/s)")
                    st.info(f"Barras verticales {diam_vert_s}: {cant_barras_v_s:.0f} barras → {kg_v_s:.1f} kg")
                    st.info(f"Barras horizontales {diam_horiz_s}: {cant_barras_h_s:.0f} barras → {kg_h_s:.1f} kg")
                with re2:
                    st.info(f"Barras de borde {diam_borde}: {ml_borde:.1f} ml → {kg_borde:.1f} kg")
                    if kg_diag > 0:
                        st.info(f"Refuerzo diagonal vanos: {kg_diag:.1f} kg")
                    st.success(f"TOTAL ACERO: {kg_total_h:.1f} kg")

            # ============================
            # MODO DETALLADO
            # ============================
            elif modo_muro_h == "📐 Modo Detallado (con planos)":
                st.caption("Ingresa los datos exactos según planos estructurales")

                if espesor_muro_h >= 0.20:
                    st.warning("⚠️ Espesor ≥ 20cm: NCh430 exige doble malla obligatoriamente")
                    tipo_malla_d = "Doble"
                else:
                    tipo_malla_d = st.selectbox("Tipo de malla", ["Simple", "Doble"], key="malla_det_h")

                n_mallas_d = 2 if tipo_malla_d == "Doble" else 1

                st.write("**Armadura vertical**")
                dv1, dv2 = st.columns(2)
                with dv1:
                    diam_vert_d = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), index=1, key="diam_vert_d")
                with dv2:
                    sep_vert_d = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20", "0.25", "0.30"], index=2, key="sep_vert_d")

                st.write("**Armadura horizontal**")
                dh1, dh2 = st.columns(2)
                with dh1:
                    diam_horiz_d = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), index=1, key="diam_horiz_d")
                with dh2:
                    sep_horiz_d = st.selectbox("Separación (m)", ["0.10", "0.15", "0.20", "0.25", "0.30"], index=2, key="sep_horiz_d")

                st.write("**Barras de borde**")
                bb1, bb2, bb3 = st.columns(3)
                with bb1:
                    cant_barras_borde_d = st.number_input("Cantidad barras borde", value=4, step=1, key="cant_bb_d")
                with bb2:
                    diam_borde_d = st.selectbox("Diámetro borde", list(PESO_BARRAS.keys()), index=3, key="diam_borde_d")
                with bb3:
                    sep_estribos_d = st.selectbox("Sep. estribos borde (m)", ["0.08", "0.10", "0.15"], key="sep_est_d")

                st.write("**Refuerzo diagonal vanos**")
                rd1, rd2 = st.columns(2)
                with rd1:
                    diam_diag_d = st.selectbox("Diámetro diagonal", list(PESO_BARRAS.keys()), index=2, key="diam_diag_d")
                with rd2:
                    largo_diag_d = st.number_input("Largo diagonal (m)", value=0.60, key="largo_diag_d")

                sep_v_d = float(sep_vert_d)
                sep_h_d = float(sep_horiz_d)

                # Cálculos
                cant_v_d = (largo_muro_h / sep_v_d + 1) * cant_muros_h * n_mallas_d
                ml_v_d = cant_v_d * alto_muro_h
                kg_v_d = ml_v_d * PESO_BARRAS[diam_vert_d]

                cant_h_d = (alto_muro_h / sep_h_d + 1) * cant_muros_h * n_mallas_d
                ml_h_d = cant_h_d * largo_muro_h
                kg_h_d = ml_h_d * PESO_BARRAS[diam_horiz_d]

                ml_borde_d = alto_muro_h * cant_barras_borde_d * cant_muros_h
                kg_borde_d = ml_borde_d * PESO_BARRAS[diam_borde_d]

                n_estribos_borde = (alto_muro_h / float(sep_estribos_d)) * cant_muros_h
                kg_estribos_borde = n_estribos_borde * (espesor_muro_h * 2 + 0.20) * PESO_BARRAS["Ø8mm"]

                ml_diag_d = (cant_puertas_h + cant_ventanas_h) * 4 * largo_diag_d * cant_muros_h
                kg_diag_d = ml_diag_d * PESO_BARRAS[diam_diag_d]

                kg_total_d = kg_v_d + kg_h_d + kg_borde_d + kg_estribos_borde + kg_diag_d

                st.write("---")
                st.subheader("📦 Resultados Hormigón")
                mostrar_materiales(mat_muro_h)

                st.subheader("📦 Resultados Enfierradura")
                rd1, rd2 = st.columns(2)
                with rd1:
                    st.info(f"Volumen neto: {vol_neto_h:.2f} m³")
                    st.info(f"Malla: {tipo_malla_d} ({n_mallas_d} capa/s)")
                    st.info(f"Barras vert. {diam_vert_d}: {cant_v_d:.0f} barras → {kg_v_d:.1f} kg")
                    st.info(f"Barras horiz. {diam_horiz_d}: {cant_h_d:.0f} barras → {kg_h_d:.1f} kg")
                with rd2:
                    st.info(f"Barras borde {diam_borde_d}: {ml_borde_d:.1f} ml → {kg_borde_d:.1f} kg")
                    st.info(f"Estribos borde Ø8mm: {n_estribos_borde:.0f} unid → {kg_estribos_borde:.1f} kg")
                    if kg_diag_d > 0:
                        st.info(f"Diagonal vanos {diam_diag_d}: {kg_diag_d:.1f} kg")
                    st.success(f"TOTAL ACERO: {kg_total_d:.1f} kg") 

        # ============================
        # MURO DE LADRILLO
        # ============================
        with st.expander("2. Muro de Ladrillo", expanded=False):

            LADRILLOS = {
                "Fiscal (29x14x5cm)": {
                    "largo": 0.29, "ancho": 0.14, "alto": 0.05,
                    "junta": 0.013,  # promedio 1,0 a 1,5cm
                    "descripcion": "Muros estructurales y de carga"
                },
                "Princesa (29x14x7,1cm)": {
                    "largo": 0.29, "ancho": 0.14, "alto": 0.071,
                    "junta": 0.010,
                    "descripcion": "Tabiques y muros no soportantes"
                },
                "Mechón/Hueco Titán (29x14x9,4cm)": {
                    "largo": 0.29, "ancho": 0.14, "alto": 0.094,
                    "junta": 0.010,
                    "descripcion": "Tabiquería interior y muros divisorios"
                },
                "Caravista (29x14x7,1cm)": {
                    "largo": 0.29, "ancho": 0.14, "alto": 0.071,
                    "junta": 0.010,
                    "descripcion": "Terminación estética, exteriores sin estuco"
                },
            }

            ladrillo_tipo = st.selectbox(
                "Tipo de ladrillo",
                list(LADRILLOS.keys()),
                key="ladrillo_tipo"
            )
            st.caption(LADRILLOS[ladrillo_tipo]["descripcion"])

            st.subheader("📐 Dimensiones del muro")
            lb1, lb2, lb3 = st.columns(3)
            with lb1:
                largo_muro_l = st.number_input("Largo muro (m)", value=0.0, key="largo_muro_l")
            with lb2:
                alto_muro_l = st.number_input("Alto muro (m)", value=0.0, key="alto_muro_l")
            with lb3:
                cant_muros_l = st.number_input("Cantidad muros", value=0, step=1, key="cant_muros_l")

            # Vanos
            st.subheader("🚪 Vanos")
            vl1, vl2 = st.columns(2)
            with vl1:
                cant_puertas_l = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_l")
                ancho_puerta_l = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_l")
                alto_puerta_l = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_l")
            with vl2:
                cant_ventanas_l = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_l")
                ancho_ventana_l = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_l")
                alto_ventana_l = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_l")

            # Desperdicio
            desp_ladrillo = st.slider("% Desperdicio ladrillos", 0, 15, 5, key="desp_ladrillo")

            lad = LADRILLOS[ladrillo_tipo]

            # Área bruta y neta
            area_bruta_l = largo_muro_l * alto_muro_l * cant_muros_l
            area_vanos_l = ((cant_puertas_l * ancho_puerta_l * alto_puerta_l) +
                           (cant_ventanas_l * ancho_ventana_l * alto_ventana_l))
            area_neta_l = area_bruta_l - area_vanos_l

            # Ladrillos por m²
            largo_con_junta = lad["largo"] + lad["junta"]
            alto_con_junta = lad["alto"] + lad["junta"]
            ladrillos_por_m2 = 1 / (largo_con_junta * alto_con_junta)

            # Total ladrillos
            total_ladrillos = area_neta_l * ladrillos_por_m2
            total_ladrillos_desp = total_ladrillos * (1 + desp_ladrillo / 100)

            # Mortero de pega (dosificación 1:4)
            # Volumen de junta aprox = 20% del volumen total del muro
            vol_mortero = area_neta_l * lad["ancho"] * 0.20
            # Dosificación 1:4 → por m³ de mortero: 0.25m³ cemento + 1m³ arena
            cemento_mortero_kg = vol_mortero * 400  # ~400 kg cemento por m³ mortero
            cemento_mortero_sacos = cemento_mortero_kg / 25
            arena_mortero_m3 = vol_mortero * 1.10

            st.write("---")
            st.subheader("📦 Resultados")

            rl1, rl2 = st.columns(2)
            with rl1:
                st.info(f"Área neta muro: {area_neta_l:.2f} m²")
                st.info(f"Ladrillos por m²: {ladrillos_por_m2:.1f} unidades")
                st.info(f"Total ladrillos: {total_ladrillos:.0f} unidades")
                st.success(f"Con {desp_ladrillo}% desperdicio: {total_ladrillos_desp:.0f} ladrillos")
            with rl2:
                st.info(f"Volumen mortero: {vol_mortero:.3f} m³")
                st.info(f"Cemento mortero: {cemento_mortero_sacos:.0f} sacos de 25kg")
                st.info(f"Arena mortero: {arena_mortero_m3:.2f} m³")

            # Advertencia caravista
            if "Caravista" in ladrillo_tipo:
                st.warning("⚠️ Ladrillo Caravista: Requiere mortero especial de color y junta vista. Considerar maestro especializado.")

            st.write("---")
            st.subheader("💡 Datos técnicos")
            st.text(f"Dimensiones ladrillo: {lad['largo']*100:.0f}x{lad['ancho']*100:.0f}x{lad['alto']*100:.1f}cm")
            st.text(f"Junta de mortero: {lad['junta']*10:.0f}mm")
            st.text(f"Dosificación mortero: 1:4 (cemento:arena)") 

        # ============================
        # TABIQUE METALCON
        # ============================
        with st.expander("1. Tabique Metalcon", expanded=False):

                    MONTANTES_MU = {
                        "Montante Normal Perf. 60x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.56},
                        "Montante Normal Perf. 60x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.56},
                        "Montante Económico Perf. 38x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.48},
                        "Montante Económico Perf. 38x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.48},
                        "Montante Normal 60x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.56},
                        "Montante Normal 60x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.56},
                        "Montante Económico 38x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.48},
                        "Montante Económico 38x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.48},
                    }

                    CANALES_MU = {
                        "Canal Normal 61x20x0,5 - 3,00m":    {"largo": 3.00, "peso": 0.39},
                        "Canal Económico 39x20x0,5 - 3,00m": {"largo": 3.00, "peso": 0.31},
                    }

                    st.subheader("📐 Dimensiones del tabique")
                    tm1, tm2, tm3 = st.columns(3)
                    with tm1:
                        largo_tab_mu = st.number_input("Largo tabique (m)", value=0.0, key="largo_tab_mu")
                    with tm2:
                        alto_tab_mu = st.number_input("Alto tabique (m)", value=0.0, key="alto_tab_mu")
                    with tm3:
                        cant_tab_mu = st.number_input("Cantidad tabiques", value=0, step=1, key="cant_tab_mu")

                    sep_mu = st.selectbox("Separación montantes", 
                                        ["0,40m (recomendado)", "0,60m (máximo)"], 
                                        key="sep_mu")
                    sep_valor_mu = 0.40 if "0,40" in sep_mu else 0.60

                    canal_tipo_mu = st.selectbox("Tipo de canal", list(CANALES_MU.keys()), key="canal_mu")

                    # Dos selectbox separados para montantes
                    st.write("**Tipo de montantes**")
                    mt1, mt2 = st.columns(2)
                    with mt1:
                        montante_medio = st.selectbox(
                            "Montante central (perforado)",
                            [k for k in MONTANTES_MU.keys() if "Perf" in k],
                            key="mont_medio_mu"
                        )
                        st.caption("✅ Va en el medio - permite paso de instalaciones")
                    with mt2:
                        montante_esquina = st.selectbox(
                            "Montante esquinas y encuentros (normal)",
                            [k for k in MONTANTES_MU.keys() if "Perf" not in k],
                            key="mont_esq_mu"
                        )
                        st.caption("⚠️ Va en esquinas y encuentros")

                    st.subheader("🚪 Vanos")
                    v1, v2 = st.columns(2)
                    with v1:
                        cant_puertas_mu = st.number_input("Cantidad de puertas", value=0, step=1, key="cant_puertas_mu")
                        ancho_puerta_mu = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_mu")
                    with v2:
                        cant_ventanas_mu = st.number_input("Cantidad de ventanas", value=0, step=1, key="cant_ventanas_mu")
                        ancho_ventana_mu = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_mu")

                    st.subheader("🔲 Esquinas y Encuentros")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        cant_esquinas_mu = st.number_input("Cantidad de esquinas", value=0, step=1, key="cant_esq_mu")
                    with ec2:
                        cant_encuentros_mu = st.number_input("Cantidad de encuentros", value=0, step=1, key="cant_enc_mu")

                    largo_canal_mu = CANALES_MU[canal_tipo_mu]["largo"]
                    largo_mont_medio = MONTANTES_MU[montante_medio]["largo"]
                    largo_mont_esq = MONTANTES_MU[montante_esquina]["largo"]

                    # Cálculo canales (solera inf + sup)
                    ml_canal_mu = largo_tab_mu * 2 * cant_tab_mu
                    cant_canales_mu = ml_canal_mu / largo_canal_mu if largo_canal_mu > 0 else 0

                    # Montantes del medio (perforados) - los corrientes
                    # Se descuentan los 2 extremos que son normales
                    montantes_medio_por_tab = max(0, int(largo_tab_mu / sep_valor_mu) - 1)
                    total_mont_medio = montantes_medio_por_tab * cant_tab_mu

                    # Montantes normales
                    # 2 extremos por tabique + 3 por esquina + 4 por encuentro
                    mont_extremos = 2 * cant_tab_mu
                    mont_esquinas = cant_esquinas_mu * 3
                    mont_encuentros = cant_encuentros_mu * 4
                    mont_vanos = (cant_puertas_mu + cant_ventanas_mu) * 2
                    total_mont_normal = mont_extremos + mont_esquinas + mont_encuentros + mont_vanos

                    # Canales extra por vanos
                    canales_extra_vanos = (cant_puertas_mu + cant_ventanas_mu) * 2
                    total_canales_final = cant_canales_mu + canales_extra_vanos

                    # Diagonales (2 por tabique)
                    total_diagonales = cant_tab_mu * 2

                    # Pletinas por esquina
                    total_pletinas = cant_esquinas_mu

                    # Tornillos autoperforantes
                    tornillos = ((total_mont_medio + total_mont_normal) * 4) + (total_canales_final * 2)

                    # Aislación lana de vidrio
                    m2_aislacion = largo_tab_mu * alto_tab_mu * cant_tab_mu
                    m2_vanos_mu = ((cant_puertas_mu * ancho_puerta_mu * alto_tab_mu) +
                                (cant_ventanas_mu * ancho_ventana_mu * alto_tab_mu))
                    m2_aislacion_neta = m2_aislacion - m2_vanos_mu

                    st.write("---")
                    st.subheader("📦 Resultados")

                    r1, r2 = st.columns(2)
                    with r1:
                        st.info(f"Canales totales: {total_canales_final:.0f} piezas de {largo_canal_mu}m")
                        st.info(f"Montantes perforados (medio): {total_mont_medio:.0f} piezas de {largo_mont_medio}m")
                        st.info(f"Montantes normales (esquinas/extremos): {total_mont_normal:.0f} piezas de {largo_mont_esq}m")
                        st.info(f"Total montantes: {total_mont_medio + total_mont_normal:.0f} piezas")
                    with r2:
                        st.info(f"Diagonales: {total_diagonales} piezas")
                        st.info(f"Pletinas esquinas: {total_pletinas} unidades")
                        st.info(f"Tornillos autoperf.: {tornillos:.0f} unidades")
                        st.info(f"Lana de vidrio: {m2_aislacion_neta:.2f} m²")

                    st.write("---")
                    st.subheader("🔧 Herramientas necesarias")
                    st.markdown("""
                    - 🔩 Atornillador
                    - 🔧 Alicates
                    - ⚙️ Amoladora (para cortar perfiles)
                    - 🔨 Taladro
                    - 📏 Nivel
                    - 📐 Huincha de medir
                    """)

        # ============================
        # TABIQUE DE MADERA
        # ============================
        with st.expander("4. Tabique de Madera", expanded=False):

            MADERA_TIPOS = {
                "2x2 Pino Dimensionado Verde 3,2m":      {"largo": 3.20, "ancho": 0.038, "alto": 0.038},
                "2x3 Pino Dimensionado Verde 3,2m":      {"largo": 3.20, "ancho": 0.038, "alto": 0.063},
                "1x2 Pino Certificado Seco Cepillado 3,2m": {"largo": 3.20, "ancho": 0.025, "alto": 0.038},
            }

            st.subheader("📐 Dimensiones del tabique")
            tw1, tw2, tw3 = st.columns(3)
            with tw1:
                largo_tab_ma = st.number_input("Largo tabique (m)", value=0.0, key="largo_tab_ma")
            with tw2:
                alto_tab_ma = st.number_input("Alto tabique (m)", value=0.0, key="alto_tab_ma")
            with tw3:
                cant_tab_ma = st.number_input("Cantidad tabiques", value=0, step=1, key="cant_tab_ma")

            madera_tipo = st.selectbox("Tipo de madera", list(MADERA_TIPOS.keys()), key="madera_tipo")

            sep_ma = st.selectbox("Separación entre montantes", ["0,40m", "0,60m"], key="sep_ma")
            sep_valor_ma = 0.40 if "0,40" in sep_ma else 0.60

            cant_cad = st.selectbox("Filas de cadenetas", ["1 fila (cada 80cm)", "2 filas (cada 60cm)", "3 filas (cada 50cm)"], key="cant_cad")
            n_cadenetas = int(cant_cad[0])

            st.subheader("🚪 Vanos")
            vw1, vw2 = st.columns(2)
            with vw1:
                cant_puertas_ma = st.number_input("Cantidad de puertas", value=0, step=1, key="cant_puertas_ma")
                ancho_puerta_ma = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_ma")
            with vw2:
                cant_ventanas_ma = st.number_input("Cantidad de ventanas", value=0, step=1, key="cant_ventanas_ma")
                ancho_ventana_ma = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_ma")

            st.subheader("🔲 Esquinas")
            cant_esq_ma = st.number_input("Cantidad de esquinas", value=0, step=1, key="cant_esq_ma")

            largo_mad = MADERA_TIPOS[madera_tipo]["largo"]

            # Soleras y carreras (inf + sup)
            ml_solera_ma = largo_tab_ma * 2 * cant_tab_ma
            cant_soleras_ma = ml_solera_ma / largo_mad if largo_mad > 0 else 0

            # Montantes
            montantes_por_tab_ma = int(largo_tab_ma / sep_valor_ma) + 1
            total_mont_ma = montantes_por_tab_ma * cant_tab_ma

            # Diagonales (2 por tabique)
            total_diag_ma = cant_tab_ma * 2

            # Cadenetas
            ml_cadenetas = largo_tab_ma * n_cadenetas * cant_tab_ma
            cant_cadenetas = ml_cadenetas / largo_mad if largo_mad > 0 else 0

            # Vanos puertas (1/4 pieza = 0,8m aprox)
            piezas_puertas = cant_puertas_ma * 1
            # Vanos ventanas (dintel y peana = 2 piezas)
            piezas_ventanas = cant_ventanas_ma * 2

            # Esquinas (1 pieza cuadrada 10x10cm por esquina)
            piezas_esquinas = cant_esq_ma

            # Total listones
            total_listones = cant_soleras_ma + total_mont_ma + total_diag_ma + cant_cadenetas + piezas_puertas + piezas_ventanas + piezas_esquinas

            # Clavos (aprox 2 por unión)
            clavos = total_listones * 4

            # Papel kraft (m²)
            m2_papel = largo_tab_ma * alto_tab_ma * cant_tab_ma
            m2_vanos_ma = (cant_puertas_ma * ancho_puerta_ma * alto_tab_ma) + (cant_ventanas_ma * ancho_ventana_ma * alto_tab_ma)
            m2_papel_neto = m2_papel - m2_vanos_ma

            # Aislante (m²)
            m2_aislante_ma = m2_papel_neto

            st.write("---")
            st.subheader("📦 Resultados")

            rm1, rm2 = st.columns(2)
            with rm1:
                st.info(f"Soleras y carreras: {cant_soleras_ma:.0f} piezas de {largo_mad}m")
                st.info(f"Montantes: {total_mont_ma:.0f} piezas de {largo_mad}m")
                st.info(f"Diagonales: {total_diag_ma} piezas de {largo_mad}m")
                st.info(f"Cadenetas: {cant_cadenetas:.0f} piezas de {largo_mad}m")
            with rm2:
                st.info(f"Vanos puertas: {piezas_puertas} piezas")
                st.info(f"Vanos ventanas: {piezas_ventanas} piezas")
                st.info(f"Esquinas: {piezas_esquinas} piezas")
                st.info(f"Total listones: {total_listones:.0f} piezas")

            st.write("---")
            rm3, rm4 = st.columns(2)
            with rm3:
                st.info(f"Papel kraft: {m2_papel_neto:.2f} m²")
                st.info(f"Aislante: {m2_aislante_ma:.2f} m²")
            with rm4:
                st.info(f"Clavos aprox.: {clavos:.0f} unidades")

            st.write("---")
            st.subheader("🔧 Herramientas necesarias")
            st.markdown("""
            - 🔨 Martillo
            - 🪚 Sierra circular
            - 🪚 Serrucho
            - 📏 Nivel
            - 📐 Huincha de medir
            """)

    # ============================
    # REVESTIMIENTOS
    # ============================
    with st.expander("Revestimientos", expanded=False):

        # ============================
        # DATOS
        # ============================
        YESO_CARTON = {
            "ST Estándar 10mm (Zonas secas)":        {"espesor": 10,   "area": 2.88, "tipo": "ST"},
            "ST Estándar 12,5mm (Zonas secas)":      {"espesor": 12.5, "area": 2.88, "tipo": "ST"},
            "RH Humedad 12,5mm (Baños/Cocinas)":     {"espesor": 12.5, "area": 2.88, "tipo": "RH"},
            "RH Humedad 15mm (Baños/Cocinas)":       {"espesor": 15,   "area": 2.88, "tipo": "RH"},
            "RF Fuego 12,5mm (Shaft/Bodegas)":       {"espesor": 12.5, "area": 2.88, "tipo": "RF"},
            "RF Fuego 15mm (Shaft/Bodegas)":         {"espesor": 15,   "area": 2.88, "tipo": "RF"},
        }
        TERCIADO_RANURADO = {
            "Terciado Ranurado 5,5-6mm (Colonial liviano)": {"area": 2.98},
            "Terciado Ranurado 9mm (Uso general)":          {"area": 2.98},
            "Terciado Ranurado 12mm (Alta resistencia)":    {"area": 2.98},
        }
        OSB_TIPOS = {
            "OSB 9,5mm":  {"area": 2.98},
            "OSB 11,1mm": {"area": 2.98},
            "OSB 15,1mm": {"area": 2.98},
        }
        FIBROCEMENTO = {
            "Lisa 4mm (Sobre tablero madera)":      {"area": 2.88},
            "Lisa 5mm (Cielos y aleros húmedos)":   {"area": 2.88},
            "Simplísima 6mm (Fachada)":             {"area": 2.88},
            "Textura Madera 6mm (Fachada)":         {"area": 2.88},
        }
        TERCIADO_ESTRUCTURAL = {
            "Terciado Estructural 9mm":  {"area": 2.98},
            "Terciado Estructural 12mm": {"area": 2.98},
            "Terciado Estructural 15mm": {"area": 2.98},
            "Terciado Estructural 18mm": {"area": 2.98},
        }

        def calcular_planchas(area_neta, area_plancha, desperdicio):
            cant_exacta = area_neta / area_plancha if area_plancha > 0 else 0
            cant_con_desp = cant_exacta * (1 + desperdicio / 100)
            sobra_ultima = (cant_exacta % 1) * area_plancha
            desperdicio_m2 = (cant_con_desp - cant_exacta) * area_plancha
            return cant_exacta, cant_con_desp, sobra_ultima, desperdicio_m2

        def calcular_tornillos_plancha(cant_planchas, area_plancha, sep_borde, sep_centro):
            """Calcula tornillos para planchas rectangulares"""
            # Perímetro plancha 1,22x2,44 aprox
            perimetro = (1.22 + 2.44) * 2
            apoyos_internos = area_plancha / (sep_centro * 1.22)
            torn_borde = (perimetro / sep_borde) * cant_planchas
            torn_centro = apoyos_internos * cant_planchas
            return round(torn_borde + torn_centro)

        # ============================
        # INTERIOR
        # ============================
        with st.expander("1. Revestimiento Interior", expanded=False):

            # --- Yeso Cartón ---
            with st.expander("1.1 Yeso Cartón", expanded=False):

                yeso_tipo = st.selectbox("Tipo de Yeso Cartón", list(YESO_CARTON.keys()), key="yeso_tipo")

                if YESO_CARTON[yeso_tipo]["tipo"] == "ST":
                    st.caption("🏠 Uso: dormitorios, living, zonas secas")
                elif YESO_CARTON[yeso_tipo]["tipo"] == "RH":
                    st.caption("💧 Uso: baños, cocinas - color verde")
                else:
                    st.caption("🔥 Uso: shaft, bodegas, vías escape - color rojo/rosado")

                estructura_yc = st.selectbox("Tipo de estructura",
                                                ["Metalcon", "Madera"],
                                                key="estructura_yc")

                if estructura_yc == "Metalcon":
                    tornillo_yc = "Autoperforante Punta Fina (Trompeta)"
                    medida_yc = "6x1\" o 6x1 1/4\""
                else:
                    tornillo_yc = "Tornillo Clavex (hilo grueso)"
                    medida_yc = "6x1\" o 6x1 1/4\""

                yc1, yc2, yc3 = st.columns(3)
                with yc1:
                    largo_yc = st.number_input("Largo muro/tabique (m)", value=0.0, key="largo_yc")
                with yc2:
                    alto_yc = st.number_input("Alto muro/tabique (m)", value=0.0, key="alto_yc")
                with yc3:
                    cant_yc = st.number_input("Cantidad muros/tabiques", value=0, step=1, key="cant_yc")

                caras_yc = st.selectbox("Cantidad de caras", ["1 cara", "2 caras"], key="caras_yc")
                n_caras_yc = 1 if "1" in caras_yc else 2

                yv1, yv2 = st.columns(2)
                with yv1:
                    cant_puertas_yc = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_yc")
                    ancho_puerta_yc = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_yc")
                    alto_puerta_yc = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_yc")
                with yv2:
                    cant_ventanas_yc = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_yc")
                    ancho_ventana_yc = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_yc")
                    alto_ventana_yc = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_yc")

                desp_yc = st.slider("% Desperdicio", 0, 20, 10, key="desp_yc")

                area_bruta_yc = largo_yc * alto_yc * cant_yc * n_caras_yc
                area_vanos_yc = ((cant_puertas_yc * ancho_puerta_yc * alto_puerta_yc) +
                                (cant_ventanas_yc * ancho_ventana_yc * alto_ventana_yc)) * n_caras_yc
                area_neta_yc = area_bruta_yc - area_vanos_yc

                area_plancha_yc = YESO_CARTON[yeso_tipo]["area"]
                cant_exacta_yc, cant_desp_yc, sobra_yc, desp_m2_yc = calcular_planchas(
                    area_neta_yc, area_plancha_yc, desp_yc)

                tornillos_yc = calcular_tornillos_plancha(cant_desp_yc, area_plancha_yc, 0.30, 0.40)

                st.write("---")
                st.info(f"Área neta: {area_neta_yc:.2f} m²")
                st.info(f"Planchas exactas: {cant_exacta_yc:.1f} unidades")
                st.success(f"Planchas con {desp_yc}% desperdicio: {cant_desp_yc:.0f} unidades")
                st.text(f"Sobra última plancha: {sobra_yc:.2f} m²")
                st.text(f"Desperdicio estimado: {desp_m2_yc:.2f} m²")
                st.write("---")
                st.info(f"🔩 Tornillo: {tornillo_yc} {medida_yc}")
                st.info(f"Separación: bordes cada 30cm / centro cada 40cm")
                st.success(f"Total tornillos: {tornillos_yc} unidades")

            # --- Terciado Ranurado ---
            with st.expander("1.2 Terciado Ranurado", expanded=False):
                st.caption("Revestimiento muros y cielos interiores")

                tr_tipo = st.selectbox("Tipo", list(TERCIADO_RANURADO.keys()), key="tr_tipo")
                estructura_tr = st.selectbox("Tipo de estructura", ["Metalcon", "Madera"], key="estructura_tr")

                if estructura_tr == "Madera":
                    tornillo_tr = "Clavo sin cabeza (punta) o Tornillo madera"
                    medida_tr = "2\""
                else:
                    tornillo_tr = "Tornillo Kover o Lenteja Punta Fina"
                    medida_tr = "8x1 1/4\""

                tr1, tr2, tr3 = st.columns(3)
                with tr1:
                    largo_tr = st.number_input("Largo muro (m)", value=0.0, key="largo_tr")
                with tr2:
                    alto_tr = st.number_input("Alto muro (m)", value=0.0, key="alto_tr")
                with tr3:
                    cant_tr = st.number_input("Cantidad muros", value=0, step=1, key="cant_tr")

                tv1, tv2 = st.columns(2)
                with tv1:
                    cant_puertas_tr = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_tr")
                    ancho_puerta_tr = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_tr")
                    alto_puerta_tr = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_tr")
                with tv2:
                    cant_ventanas_tr = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_tr")
                    ancho_ventana_tr = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_tr")
                    alto_ventana_tr = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_tr")

                desp_tr = st.slider("% Desperdicio", 0, 20, 10, key="desp_tr")

                area_bruta_tr = largo_tr * alto_tr * cant_tr
                area_vanos_tr = ((cant_puertas_tr * ancho_puerta_tr * alto_puerta_tr) +
                                (cant_ventanas_tr * ancho_ventana_tr * alto_ventana_tr))
                area_neta_tr = area_bruta_tr - area_vanos_tr

                area_plancha_tr = TERCIADO_RANURADO[tr_tipo]["area"]
                cant_exacta_tr, cant_desp_tr, sobra_tr, desp_m2_tr = calcular_planchas(
                    area_neta_tr, area_plancha_tr, desp_tr)

                tornillos_tr = calcular_tornillos_plancha(cant_desp_tr, area_plancha_tr, 0.15, 0.30)

                st.write("---")
                st.info(f"Área neta: {area_neta_tr:.2f} m²")
                st.info(f"Planchas exactas: {cant_exacta_tr:.1f} unidades")
                st.success(f"Planchas con {desp_tr}% desperdicio: {cant_desp_tr:.0f} unidades")
                st.text(f"Sobra última plancha: {sobra_tr:.2f} m²")
                st.text(f"Desperdicio estimado: {desp_m2_tr:.2f} m²")
                st.write("---")
                st.info(f"🔩 Fijación: {tornillo_tr} {medida_tr}")
                st.info(f"Separación: perímetro cada 15cm / apoyos internos cada 30cm")
                st.success(f"Total fijaciones: {tornillos_tr} unidades")
                st.caption("⚠️ Distancia mínima al borde: 1cm")

        # ============================
        # EXTERIOR
        # ============================
        with st.expander("2. Revestimiento Exterior", expanded=False):

            # --- OSB ---
            with st.expander("2.1 OSB", expanded=False):
                st.caption("Tablero estructural - 1,22x2,44m")

                osb_tipo = st.selectbox("Espesor OSB", list(OSB_TIPOS.keys()), key="osb_tipo")
                estructura_osb = st.selectbox("Tipo de estructura", ["Metalcon", "Madera"], key="estructura_osb")

                if estructura_osb == "Madera":
                    tornillo_osb = "Clavo Anillado Galvanizado"
                    medida_osb = "2 1/2\" o 3\""
                else:
                    tornillo_osb = "Tornillo Punta Broca con aletas (Wafer)"
                    medida_osb = "8x1 1/4\""

                ob1, ob2, ob3 = st.columns(3)
                with ob1:
                    largo_osb = st.number_input("Largo muro (m)", value=0.0, key="largo_osb")
                with ob2:
                    alto_osb = st.number_input("Alto muro (m)", value=0.0, key="alto_osb")
                with ob3:
                    cant_osb = st.number_input("Cantidad muros", value=0, step=1, key="cant_osb")

                ov1, ov2 = st.columns(2)
                with ov1:
                    cant_puertas_osb = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_osb")
                    ancho_puerta_osb = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_osb")
                    alto_puerta_osb = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_osb")
                with ov2:
                    cant_ventanas_osb = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_osb")
                    ancho_ventana_osb = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_osb")
                    alto_ventana_osb = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_osb")

                desp_osb = st.slider("% Desperdicio", 0, 20, 10, key="desp_osb")
                fibro_encima = st.checkbox("¿Agregar fibrocemento encima del OSB?", key="fibro_encima")
                if fibro_encima:
                    fibro_osb_tipo = st.selectbox("Tipo fibrocemento", list(FIBROCEMENTO.keys()), key="fibro_osb_tipo")

                area_bruta_osb = largo_osb * alto_osb * cant_osb
                area_vanos_osb = ((cant_puertas_osb * ancho_puerta_osb * alto_puerta_osb) +
                                    (cant_ventanas_osb * ancho_ventana_osb * alto_ventana_osb))
                area_neta_osb = area_bruta_osb - area_vanos_osb

                area_plancha_osb = OSB_TIPOS[osb_tipo]["area"]
                cant_exacta_osb, cant_desp_osb, sobra_osb, desp_m2_osb = calcular_planchas(
                    area_neta_osb, area_plancha_osb, desp_osb)

                tornillos_osb = calcular_tornillos_plancha(cant_desp_osb, area_plancha_osb, 0.15, 0.30)

                st.write("---")
                st.info(f"Área neta: {area_neta_osb:.2f} m²")
                st.info(f"Planchas exactas: {cant_exacta_osb:.1f} unidades")
                st.success(f"Planchas con {desp_osb}% desperdicio: {cant_desp_osb:.0f} unidades")
                st.text(f"Sobra última plancha: {sobra_osb:.2f} m²")
                st.text(f"Desperdicio estimado: {desp_m2_osb:.2f} m²")
                st.write("---")
                st.info(f"🔩 Fijación: {tornillo_osb} {medida_osb}")
                st.info(f"Separación: perímetro cada 15cm / apoyos internos cada 30cm")
                st.success(f"Total fijaciones: {tornillos_osb} unidades")
                st.caption("⚠️ Dejar holgura de 3mm entre planchas para dilatación")

                if fibro_encima:
                    area_plancha_fo = FIBROCEMENTO[fibro_osb_tipo]["area"]
                    cant_exacta_fo, cant_desp_fo, sobra_fo, desp_m2_fo = calcular_planchas(
                        area_neta_osb, area_plancha_fo, desp_osb)
                    tornillos_fo = calcular_tornillos_plancha(cant_desp_fo, area_plancha_fo, 0.175, 0.275)
                    st.write("---")
                    st.subheader("Fibrocemento sobre OSB")
                    st.info(f"Planchas: {cant_desp_fo:.0f} unidades")
                    st.info(f"🔩 Tornillo Autoperforante Punta Broca 8x1\"")
                    st.success(f"Total tornillos fibrocemento: {tornillos_fo} unidades")
                    st.caption("⚠️ Distancia mínima al borde horizontal: 1,5cm / vertical: 1cm")

            # --- Fibrocemento ---
            with st.expander("2.2 Fibrocemento", expanded=False):
                st.caption("Placa fibrocemento exterior - 1,20x2,40m")

                fc_tipo = st.selectbox("Tipo de Fibrocemento", list(FIBROCEMENTO.keys()), key="fc_tipo")

                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    largo_fc = st.number_input("Largo muro (m)", value=0.0, key="largo_fc")
                with fc2:
                    alto_fc = st.number_input("Alto muro (m)", value=0.0, key="alto_fc")
                with fc3:
                    cant_fc = st.number_input("Cantidad muros", value=0, step=1, key="cant_fc")

                fv1, fv2 = st.columns(2)
                with fv1:
                    cant_puertas_fc = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_fc")
                    ancho_puerta_fc = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_fc")
                    alto_puerta_fc = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_fc")
                with fv2:
                    cant_ventanas_fc = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_fc")
                    ancho_ventana_fc = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_fc")
                    alto_ventana_fc = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_fc")

                desp_fc = st.slider("% Desperdicio", 0, 20, 10, key="desp_fc")

                area_bruta_fc = largo_fc * alto_fc * cant_fc
                area_vanos_fc = ((cant_puertas_fc * ancho_puerta_fc * alto_puerta_fc) +
                                (cant_ventanas_fc * ancho_ventana_fc * alto_ventana_fc))
                area_neta_fc = area_bruta_fc - area_vanos_fc

                area_plancha_fc = FIBROCEMENTO[fc_tipo]["area"]
                cant_exacta_fc, cant_desp_fc, sobra_fc, desp_m2_fc = calcular_planchas(
                    area_neta_fc, area_plancha_fc, desp_fc)

                tornillos_fc = calcular_tornillos_plancha(cant_desp_fc, area_plancha_fc, 0.175, 0.275)

                st.write("---")
                st.info(f"Área neta: {area_neta_fc:.2f} m²")
                st.info(f"Planchas exactas: {cant_exacta_fc:.1f} unidades")
                st.success(f"Planchas con {desp_fc}% desperdicio: {cant_desp_fc:.0f} unidades")
                st.text(f"Sobra última plancha: {sobra_fc:.2f} m²")
                st.text(f"Desperdicio estimado: {desp_m2_fc:.2f} m²")
                st.write("---")
                st.info("🔩 Tornillo Autoperforante Punta Broca con aletas 8x1\"")
                st.info("Separación: perímetro cada 15-20cm / apoyos internos cada 25-30cm")
                st.success(f"Total tornillos: {tornillos_fc} unidades")
                st.caption("⚠️ Distancia mínima borde horizontal: 1,5cm / vertical: 1cm")

            # --- Terciado Estructural ---
            with st.expander("2.3 Terciado Estructural", expanded=False):
                st.caption("Placa estructural exterior - 1,22x2,44m")

                te_tipo = st.selectbox("Espesor", list(TERCIADO_ESTRUCTURAL.keys()), key="te_tipo")
                estructura_te = st.selectbox("Tipo de estructura", ["Metalcon", "Madera"], key="estructura_te")

                if estructura_te == "Madera":
                    tornillo_te = "Clavo Anillado Galvanizado"
                    medida_te = "2 1/2\""
                else:
                    tornillo_te = "Tornillo Wafer Punta Broca"
                    medida_te = "8x1 1/4\" o 8x1 1/2\""

                te1, te2, te3 = st.columns(3)
                with te1:
                    largo_te = st.number_input("Largo muro (m)", value=0.0, key="largo_te")
                with te2:
                    alto_te = st.number_input("Alto muro (m)", value=0.0, key="alto_te")
                with te3:
                    cant_te = st.number_input("Cantidad muros", value=0, step=1, key="cant_te")

                tev1, tev2 = st.columns(2)
                with tev1:
                    cant_puertas_te = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_te")
                    ancho_puerta_te = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_te")
                    alto_puerta_te = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_te")
                with tev2:
                    cant_ventanas_te = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_te")
                    ancho_ventana_te = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_te")
                    alto_ventana_te = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_te")

                desp_te = st.slider("% Desperdicio", 0, 20, 10, key="desp_te")

                area_bruta_te = largo_te * alto_te * cant_te
                area_vanos_te = ((cant_puertas_te * ancho_puerta_te * alto_puerta_te) +
                                (cant_ventanas_te * ancho_ventana_te * alto_ventana_te))
                area_neta_te = area_bruta_te - area_vanos_te

                area_plancha_te = TERCIADO_ESTRUCTURAL[te_tipo]["area"]
                cant_exacta_te, cant_desp_te, sobra_te, desp_m2_te = calcular_planchas(
                    area_neta_te, area_plancha_te, desp_te)

                tornillos_te = calcular_tornillos_plancha(cant_desp_te, area_plancha_te, 0.15, 0.30)

                st.write("---")
                st.info(f"Área neta: {area_neta_te:.2f} m²")
                st.info(f"Planchas exactas: {cant_exacta_te:.1f} unidades")
                st.success(f"Planchas con {desp_te}% desperdicio: {cant_desp_te:.0f} unidades")
                st.text(f"Sobra última plancha: {sobra_te:.2f} m²")
                st.text(f"Desperdicio estimado: {desp_m2_te:.2f} m²")
                st.write("---")
                st.info(f"🔩 Fijación: {tornillo_te} {medida_te}")
                st.info("Separación: perímetro cada 15cm / apoyos internos cada 30cm")
                st.success(f"Total fijaciones: {tornillos_te} unidades")
                st.caption("⚠️ Instalar fibra perpendicular a los apoyos para mayor resistencia")

            # --- Siding Fibrocemento ---
            with st.expander("2.4 Siding Fibrocemento", expanded=False):
                st.caption("Volcan, Pizarreño Cedral, Nativa - 19cm x 3,66m")

                estructura_sid = st.selectbox("Tipo de estructura", ["Metalcon", "Madera"], key="estructura_sid")

                if estructura_sid == "Metalcon":
                    tornillo_sid = "Tornillo Cabeza Lenteja (Wafer) Punta Fina"
                    medida_sid = "8x1 1/4\""
                else:
                    tornillo_sid = "Clavo Galvanizado Cabeza Plana"
                    medida_sid = "1 1/2\" o 2\""

                sd1, sd2, sd3 = st.columns(3)
                with sd1:
                    largo_sid = st.number_input("Largo muro (m)", value=0.0, key="largo_sid")
                with sd2:
                    alto_sid = st.number_input("Alto muro (m)", value=0.0, key="alto_sid")
                with sd3:
                    cant_sid = st.number_input("Cantidad muros", value=0, step=1, key="cant_sid")

                sv1, sv2 = st.columns(2)
                with sv1:
                    cant_puertas_sid = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_sid")
                    ancho_puerta_sid = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_sid")
                    alto_puerta_sid = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_sid")
                with sv2:
                    cant_ventanas_sid = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_sid")
                    ancho_ventana_sid = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_sid")
                    alto_ventana_sid = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_sid")

                traslape_sid = st.selectbox("Traslape", ["25mm", "30mm"], key="traslape_sid")
                sep_mont_sid = st.selectbox("Separación montantes", ["0,40m", "0,60m"], key="sep_mont_sid")
                sep_valor_sid = 0.40 if "0,40" in sep_mont_sid else 0.60
                desp_sid = st.slider("% Desperdicio", 0, 20, 10, key="desp_sid")

                rend_tabla = 0.70 if "25" in traslape_sid else 0.44

                area_bruta_sid = largo_sid * alto_sid * cant_sid
                area_vanos_sid = ((cant_puertas_sid * ancho_puerta_sid * alto_puerta_sid) +
                                    (cant_ventanas_sid * ancho_ventana_sid * alto_ventana_sid))
                area_neta_sid = area_bruta_sid - area_vanos_sid

                cant_tablas_sid = area_neta_sid / rend_tabla if rend_tabla > 0 else 0
                cant_tablas_desp = cant_tablas_sid * (1 + desp_sid / 100)
                ml_tablas_sid = cant_tablas_desp * 3.66

                # Tornillos siding: 1 por montante por tabla
                tornillos_sid = (largo_sid / sep_valor_sid) * cant_tablas_desp * cant_sid
                tornillos_sid = round(tornillos_sid * (1 + desp_sid / 100))

                st.write("---")
                st.info(f"Área neta: {area_neta_sid:.2f} m²")
                st.info(f"Rendimiento por tabla: {rend_tabla} m² (traslape {traslape_sid})")
                st.info(f"Tablas exactas: {cant_tablas_sid:.0f} unidades")
                st.success(f"Tablas con {desp_sid}% desperdicio: {cant_tablas_desp:.0f} unidades")
                st.text(f"Metros lineales totales: {ml_tablas_sid:.2f} ml")
                st.write("---")
                st.info(f"🔩 Fijación: {tornillo_sid} {medida_sid}")
                st.info(f"1 fijación por montante cada {sep_mont_sid}")
                st.success(f"Total fijaciones: {tornillos_sid} unidades")
                st.caption("⚠️ Fijación a 2cm del borde superior, quedará tapada por la tabla siguiente")

    # ============================
    # PISOS Y PAVIMENTOS
    # ============================
    with st.expander(" Pisos y Pavimentos", expanded=False):

        # ============================
        # DATOS
        # ============================
        CERAMICO_MEDIDAS = {
            "30x30 cm":   {"largo": 0.30, "ancho": 0.30, "area": 0.09, "doble_pegado": False},
            "45x45 cm":   {"largo": 0.45, "ancho": 0.45, "area": 0.2025, "doble_pegado": False},
            "60x60 cm":   {"largo": 0.60, "ancho": 0.60, "area": 0.36, "doble_pegado": False},
            "80x80 cm":   {"largo": 0.80, "ancho": 0.80, "area": 0.64, "doble_pegado": False},
            "60x120 cm":  {"largo": 0.60, "ancho": 1.20, "area": 0.72, "doble_pegado": True},
        }

        PISO_FLOTANTE = {
            "7mm - Tránsito Residencial (AC3)":  {"espesor": 7},
            "8mm - Tránsito Residencial (AC4)":  {"espesor": 8},
            "10mm - Tránsito Comercial (AC5)":   {"espesor": 10},
            "12mm - Tránsito Comercial (AC5)":   {"espesor": 12},
        }

        MADERA_DECK = {
            "Pino Impregnado CCA":  {"precio_ref": "económico"},
            "Lenga":                {"precio_ref": "premium"},
            "Raulí":                {"precio_ref": "premium"},
            "Ipé":                  {"precio_ref": "alta gama"},
            "Coigüe":               {"precio_ref": "alta gama"},
        }

        # ============================
        # 1. CERÁMICO / PORCELANATO
        # ============================
        with st.expander("1. Cerámico / Porcelanato", expanded=False):

            cer_medida = st.selectbox("Medida", list(CERAMICO_MEDIDAS.keys()), key="cer_medida")
            cer = CERAMICO_MEDIDAS[cer_medida]

            if cer["doble_pegado"]:
                st.warning("⚠️ Formato grande (60x120cm): Requiere doble pegado y pegamento de mayor adherencia (tipo AC o Flex)")

            ce1, ce2 = st.columns(2)
            with ce1:
                largo_cer = st.number_input("Largo área (m)", value=0.0, key="largo_cer")
            with ce2:
                ancho_cer = st.number_input("Ancho área (m)", value=0.0, key="ancho_cer")

            # Vanos
            cv1, cv2 = st.columns(2)
            with cv1:
                cant_vanos_cer = st.number_input("Cantidad de vanos", value=0, step=1, key="cant_vanos_cer")
            with cv2:
                area_vano_cer = st.number_input("Área por vano (m²)", value=0.0, key="area_vano_cer")

            junta_cer = st.selectbox("Ancho de junta (cantería)", ["2mm", "3mm", "5mm"], key="junta_cer")
            desp_cer = st.slider("% Desperdicio", 0, 20, 10, key="desp_cer")

            area_bruta_cer = largo_cer * ancho_cer
            area_vanos_cer = cant_vanos_cer * area_vano_cer
            area_neta_cer = area_bruta_cer - area_vanos_cer

            # Cerámicos
            ceramicos_exactos = area_neta_cer / cer["area"] if cer["area"] > 0 else 0
            ceramicos_desp = ceramicos_exactos * (1 + desp_cer / 100)

            # Pegamento
            rend_pega = 4.5  # promedio 4-5 kg/m²
            if cer["doble_pegado"]:
                rend_pega = 8.0  # doble pegado
            kg_pegamento = area_neta_cer * rend_pega
            bolsas_pegamento = kg_pegamento / 25

            # Fragüe según junta
            junta_val = float(junta_cer.replace("mm", ""))
            if junta_val <= 2:
                rend_frag = 0.30
            elif junta_val <= 3:
                rend_frag = 0.40
            else:
                rend_frag = 0.50
            kg_frag = area_neta_cer * rend_frag
            bolsas_frag = kg_frag / 5  # bolsas de 5kg

            st.write("---")
            st.info(f"Área neta: {area_neta_cer:.2f} m²")
            st.info(f"Piezas por m²: {1/cer['area']:.1f} unidades")
            st.info(f"Cerámicos exactos: {ceramicos_exactos:.0f} unidades")
            st.success(f"Con {desp_cer}% desperdicio: {ceramicos_desp:.0f} unidades")

            st.write("---")
            st.subheader("🧴 Pegamento")
            if cer["doble_pegado"]:
                st.caption("Doble pegado: en el piso y en la trasera de la palmeta")
            st.info(f"Pegamento necesario: {kg_pegamento:.1f} kg")
            st.success(f"Bolsas de 25kg: {bolsas_pegamento:.0f} bolsas")
            st.caption(f"Rendimiento: {rend_pega} kg/m² | Rinde aprox. {25/rend_pega:.1f} m² por bolsa")

            st.write("---")
            st.subheader("🪣 Fragüe")
            st.info(f"Fragüe necesario: {kg_frag:.1f} kg")
            st.success(f"Bolsas de 5kg: {bolsas_frag:.0f} bolsas")
            st.caption(f"Rendimiento: {rend_frag} kg/m² para junta de {junta_cer}")

        # ============================
        # 2. PISO FLOTANTE
        # ============================
        with st.expander("2. Piso Flotante / Parquet", expanded=False):

            pf_tipo = st.selectbox("Tipo de piso flotante", list(PISO_FLOTANTE.keys()), key="pf_tipo")

            pf1, pf2 = st.columns(2)
            with pf1:
                largo_pf = st.number_input("Largo área (m)", value=0.0, key="largo_pf")
            with pf2:
                ancho_pf = st.number_input("Ancho área (m)", value=0.0, key="ancho_pf")

            pfv1, pfv2 = st.columns(2)
            with pfv1:
                cant_vanos_pf = st.number_input("Cantidad de vanos", value=0, step=1, key="cant_vanos_pf")
            with pfv2:
                area_vano_pf = st.number_input("Área por vano (m²)", value=0.0, key="area_vano_pf")

            sobre_losa = st.checkbox("¿Va sobre losa de hormigón (primer piso)?", key="sobre_losa")
            desp_pf = st.slider("% Desperdicio", 0, 20, 10, key="desp_pf")

            area_bruta_pf = largo_pf * ancho_pf
            area_vanos_pf = cant_vanos_pf * area_vano_pf
            area_neta_pf = area_bruta_pf - area_vanos_pf

            area_pf_desp = area_neta_pf * (1 + desp_pf / 100)

            st.write("---")
            st.info(f"Área neta: {area_neta_pf:.2f} m²")
            st.success(f"Piso flotante con {desp_pf}% desperdicio: {area_pf_desp:.2f} m²")

            st.write("---")
            st.subheader("🧸 Espuma Niveladora (Manta Polietileno)")
            st.info(f"Espuma 2-3mm necesaria: {area_neta_pf:.2f} m²")
            st.caption("1 m² de espuma por 1 m² de piso flotante")

            if sobre_losa:
                st.write("---")
                st.subheader("💧 Barrera de Humedad (Buna/Film Polietileno)")
                st.warning("⚠️ Instalación sobre losa: Se requiere barrera de humedad bajo la espuma")
                st.info(f"Film polietileno necesario: {area_neta_pf:.2f} m²")
                st.caption("Traslapar 20cm en uniones y subir 10cm por los muros")

        # ============================
        # 3. BALDOSA
        # ============================
        with st.expander("3. Baldosa", expanded=False):
            st.caption("Microvibrada o calcárea 2-4cm espesor - Mortero de pega tradicional")

            ba1, ba2, ba3, ba4 = st.columns(4)
            with ba1:
                largo_bal = st.number_input("Largo baldosa (cm)", value=0.0, key="largo_bal")
            with ba2:
                ancho_bal = st.number_input("Ancho baldosa (cm)", value=0.0, key="ancho_bal")
            with ba3:
                largo_area_bal = st.number_input("Largo área (m)", value=0.0, key="largo_area_bal")
            with ba4:
                ancho_area_bal = st.number_input("Ancho área (m)", value=0.0, key="ancho_area_bal")

            bv1, bv2 = st.columns(2)
            with bv1:
                cant_vanos_bal = st.number_input("Cantidad de vanos", value=0, step=1, key="cant_vanos_bal")
            with bv2:
                area_vano_bal = st.number_input("Área por vano (m²)", value=0.0, key="area_vano_bal")

            espesor_bal = st.selectbox("Espesor baldosa", ["2cm", "3cm", "4cm"], key="espesor_bal")
            junta_bal = st.selectbox("Ancho de junta", ["5mm", "8mm", "10mm"], key="junta_bal")
            desp_bal = st.slider("% Desperdicio", 0, 20, 10, key="desp_bal")

            area_baldosa = (largo_bal / 100) * (ancho_bal / 100)
            area_bruta_bal = largo_area_bal * ancho_area_bal
            area_vanos_bal = cant_vanos_bal * area_vano_bal
            area_neta_bal = area_bruta_bal - area_vanos_bal

            baldosas_exactas = area_neta_bal / area_baldosa if area_baldosa > 0 else 0
            baldosas_desp = baldosas_exactas * (1 + desp_bal / 100)

            # Mortero de pega (dosificación 1:3 arena:cemento)
            # Espesor cama mortero aprox 3cm
            espesor_mort = 0.03
            vol_mortero_bal = area_neta_bal * espesor_mort
            cemento_bal_kg = vol_mortero_bal * 400
            cemento_bal_sacos = cemento_bal_kg / 25
            arena_bal_m3 = vol_mortero_bal * 1.20

            st.write("---")
            st.info(f"Área neta: {area_neta_bal:.2f} m²")
            st.info(f"Baldosas por m²: {1/area_baldosa:.1f} unidades" if area_baldosa > 0 else "Ingresa dimensiones")
            st.info(f"Baldosas exactas: {baldosas_exactas:.0f} unidades")
            st.success(f"Con {desp_bal}% desperdicio: {baldosas_desp:.0f} unidades")

            st.write("---")
            st.subheader("🧱 Mortero de Pega (1:3 cemento:arena)")
            st.info(f"Cemento: {cemento_bal_sacos:.0f} sacos de 25kg")
            st.info(f"Arena: {arena_bal_m3:.2f} m³")
            st.caption(f"Espesor cama mortero: 3cm | Volumen mortero: {vol_mortero_bal:.3f} m³")
            st.warning("⚠️ Baldosa puede requerir pulido o sellado posterior según tipo")

        # ============================
        # 4. DECK DE MADERA
        # ============================
        with st.expander("4. Deck de Madera Exterior", expanded=False):

            dk_madera = st.selectbox("Tipo de madera", list(MADERA_DECK.keys()), key="dk_madera")

            if MADERA_DECK[dk_madera]["precio_ref"] == "económico":
                st.caption("✅ Pino Impregnado CCA: Resistente a humedad y termitas de fábrica")
            elif MADERA_DECK[dk_madera]["precio_ref"] == "premium":
                st.warning("⚠️ Requiere tratamiento con impregnante protector (Cerestain o Sipasol)")
            else:
                st.caption("🌟 Madera de alta gama - Mayor dureza y durabilidad")

            dk1, dk2 = st.columns(2)
            with dk1:
                ancho_tabla_dk = st.selectbox("Ancho tabla", ["4\" (90mm)", "5\" (120mm)"], key="ancho_tabla_dk")
            with dk2:
                largo_tabla_dk = st.selectbox("Largo tabla", ["3,20m", "4,00m"], key="largo_tabla_dk")

            ancho_val_dk = 0.090 if "4\"" in ancho_tabla_dk else 0.120
            largo_val_dk = 3.20 if "3,20" in largo_tabla_dk else 4.00

            espesor_dk = st.selectbox("Espesor tabla", ["1\" (19mm)", "1 1/2\" (32mm)"], key="espesor_dk")
            sep_dk = st.selectbox("Separación entre tablas", ["5mm", "8mm", "10mm"], key="sep_dk")
            sep_val_dk = float(sep_dk.replace("mm", "")) / 1000

            dk3, dk4 = st.columns(2)
            with dk3:
                largo_deck = st.number_input("Largo área deck (m)", value=0.0, key="largo_deck")
            with dk4:
                ancho_deck = st.number_input("Ancho área deck (m)", value=0.0, key="ancho_deck")

            desp_dk = st.slider("% Desperdicio", 0, 20, 10, key="desp_dk")

            area_neta_dk = largo_deck * ancho_deck

            # Tablas necesarias
            ancho_util_dk = ancho_val_dk + sep_val_dk
            tablas_por_ml = 1 / ancho_util_dk
            ml_tablas_dk = area_neta_dk * tablas_por_ml
            cant_tablas_dk = ml_tablas_dk / largo_val_dk
            cant_tablas_desp_dk = cant_tablas_dk * (1 + desp_dk / 100)

            # Tornillos deck (2 por tabla por vigueta, viguetas cada 40cm)
            viguetas_dk = largo_deck / 0.40
            tornillos_dk = cant_tablas_desp_dk * viguetas_dk * 2

            st.write("---")
            st.info(f"Área deck: {area_neta_dk:.2f} m²")
            st.info(f"Tablas exactas: {cant_tablas_dk:.0f} unidades de {largo_val_dk}m")
            st.success(f"Con {desp_dk}% desperdicio: {cant_tablas_desp_dk:.0f} tablas")
            st.text(f"Metros lineales totales: {cant_tablas_desp_dk * largo_val_dk:.2f} ml")

            st.write("---")
            st.subheader("🔩 Fijaciones")
            st.info(f"Tornillos galvanizados: {tornillos_dk:.0f} unidades")
            st.caption("2 tornillos por tabla en cada vigueta (viguetas cada 40cm)")

            if dk_madera != "Pino Impregnado CCA":
                st.write("---")
                st.subheader("🪵 Tratamiento recomendado")
                st.warning(f"⚠️ {dk_madera}: Aplicar impregnante protector tipo Cerestain o Sipasol antes de instalar")

    # ============================
    # TERMINACIONES
    # ============================
    with st.expander("Terminaciones", expanded=False):

        # ============================
        # DATOS
        # ============================
        PINTURAS = {
            "Látex Interior": {
                "rendimiento": 10,  # m² por litro por mano
                "descripcion": "Dormitorios, living, zonas secas"
            },
            "Látex Exterior": {
                "rendimiento": 8,
                "descripcion": "Fachadas y muros exteriores"
            },
            "Esmalte": {
                "rendimiento": 12,
                "descripcion": "Puertas, ventanas, metales"
            },
            "Anticorrosivo": {
                "rendimiento": 8,
                "descripcion": "Superficies metálicas expuestas"
            },
        }

        ESTUCOS = {
            "Premezclado Exterior (Sika/Melón/Weber)": {
                "rendimiento_saco": 1.5,  # m² por saco de 25kg a 15mm
                "peso_saco": 25,
                "tipo": "premezclado"
            },
            "Premezclado Antihumedad (Hidrófugo)": {
                "rendimiento_saco": 1.5,
                "peso_saco": 25,
                "tipo": "premezclado"
            },
            "Tradicional (Cemento+Arena+Cal)": {
                "rendimiento_saco": None,
                "tipo": "tradicional"
            },
            "Fino (Maquillaje/Terminación)": {
                "rendimiento_saco": 3.0,  # m² por saco a 5mm
                "peso_saco": 25,
                "tipo": "fino"
            },
        }

        CIELOS_TIPOS = {
            "Yeso Cartón ST 10mm":   {"area_plancha": 2.88, "tipo": "plancha"},
            "Yeso Cartón ST 12,5mm": {"area_plancha": 2.88, "tipo": "plancha"},
            "Volcanita 10mm":        {"area_plancha": 2.88, "tipo": "plancha"},
            "MDF 3mm":               {"area_plancha": 2.98, "tipo": "plancha"},
            "MDF 6mm":               {"area_plancha": 2.98, "tipo": "plancha"},
            "Madera Machihembrada":  {"area_plancha": None, "tipo": "madera"},
        }

        ZOCALOS = {
            "MDF 7cm":    {"alto": 0.07, "tipo": "MDF"},
            "MDF 10cm":   {"alto": 0.10, "tipo": "MDF"},
            "MDF 15cm":   {"alto": 0.15, "tipo": "MDF"},
            "Madera 7cm": {"alto": 0.07, "tipo": "Madera"},
            "Madera 10cm":{"alto": 0.10, "tipo": "Madera"},
            "Madera 15cm":{"alto": 0.15, "tipo": "Madera"},
            "PVC 7cm":    {"alto": 0.07, "tipo": "PVC"},
            "PVC 10cm":   {"alto": 0.10, "tipo": "PVC"},
            "PVC 15cm":   {"alto": 0.15, "tipo": "PVC"},
        }

        # ============================
        # 1. PINTURA
        # ============================
        with st.expander("1. Pintura", expanded=False):

            pintura_tipo = st.selectbox("Tipo de pintura", list(PINTURAS.keys()), key="pintura_tipo")
            st.caption(PINTURAS[pintura_tipo]["descripcion"])

            p1, p2, p3 = st.columns(3)
            with p1:
                largo_pin = st.number_input("Largo muro (m)", value=0.0, key="largo_pin")
            with p2:
                alto_pin = st.number_input("Alto muro (m)", value=0.0, key="alto_pin")
            with p3:
                cant_pin = st.number_input("Cantidad muros", value=0, step=1, key="cant_pin")

            pv1, pv2 = st.columns(2)
            with pv1:
                cant_puertas_pin = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_pin")
                ancho_puerta_pin = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_pin")
                alto_puerta_pin = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_pin")
            with pv2:
                cant_ventanas_pin = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_pin")
                ancho_ventana_pin = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_pin")
                alto_ventana_pin = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_pin")

            cant_manos = st.selectbox("Cantidad de manos", ["1 mano", "2 manos", "3 manos"], index=1, key="cant_manos")
            n_manos = int(cant_manos[0])

            area_bruta_pin = largo_pin * alto_pin * cant_pin
            area_vanos_pin = ((cant_puertas_pin * ancho_puerta_pin * alto_puerta_pin) +
                                (cant_ventanas_pin * ancho_ventana_pin * alto_ventana_pin))
            area_neta_pin = area_bruta_pin - area_vanos_pin

            rend_pin = PINTURAS[pintura_tipo]["rendimiento"]
            litros_pin = (area_neta_pin * n_manos) / rend_pin

            # Pasta muro
            st.write("---")
            st.subheader("🪣 Pasta Muro (Masilla/Compuesto para Juntas)")
            st.caption("Se aplica antes del sellador para rellenar juntas e imperfecciones")
            kg_pasta = area_neta_pin * 0.30  # 300g por m²
            st.info(f"Pasta muro necesaria: {kg_pasta:.1f} kg")
            st.success(f"Sacos de 25kg: {kg_pasta/25:.0f} sacos")

            # Cinta para juntas
            st.write("---")
            st.subheader("📏 Cinta para Juntas")
            st.caption("Se aplica sobre las juntas entre planchas antes de la pasta")
            ml_cinta = area_neta_pin / 2.88 * 4.84  # metros lineales de juntas por plancha
            st.info(f"Metros lineales de cinta: {ml_cinta:.1f} ml")
            st.success(f"Rollos de 75m: {ml_cinta/75:.0f} rollos")

            # Sellador/Imprimante
            st.write("---")
            st.subheader("🖌️ Sellador / Imprimante Base")
            st.caption("Se aplica antes de la pintura para mejorar adherencia")
            litros_sellador = area_neta_pin / 10  # 1 litro por 10m²
            st.info(f"Sellador necesario: {litros_sellador:.1f} litros")
            st.success(f"Galones de 4 litros: {litros_sellador/4:.0f} galones")

            # Pintura
            st.write("---")
            st.subheader(f"🎨 {pintura_tipo}")
            st.info(f"Área neta: {area_neta_pin:.2f} m²")
            st.info(f"Manos: {n_manos} | Rendimiento: {rend_pin} m²/litro")
            st.info(f"Litros necesarios: {litros_pin:.1f} litros")
            st.success(f"Galones de 4 litros: {litros_pin/4:.0f} galones")
            st.success(f"Tarros de 1 litro: {litros_pin:.0f} litros")

        # ============================
        # 2. ESTUCO / REVOQUE
        # ============================
        with st.expander("2. Estuco / Revoque", expanded=False):

            estuco_tipo = st.selectbox("Tipo de estuco", list(ESTUCOS.keys()), key="estuco_tipo")
            est = ESTUCOS[estuco_tipo]

            es1, es2, es3 = st.columns(3)
            with es1:
                largo_est = st.number_input("Largo muro (m)", value=0.0, key="largo_est")
            with es2:
                alto_est = st.number_input("Alto muro (m)", value=0.0, key="alto_est")
            with es3:
                cant_est = st.number_input("Cantidad muros", value=0, step=1, key="cant_est")

            ev1, ev2 = st.columns(2)
            with ev1:
                cant_puertas_est = st.number_input("Cantidad puertas", value=0, step=1, key="cant_puertas_est")
                ancho_puerta_est = st.number_input("Ancho puerta (m)", value=0.0, key="ancho_puerta_est")
                alto_puerta_est = st.number_input("Alto puerta (m)", value=0.0, key="alto_puerta_est")
            with ev2:
                cant_ventanas_est = st.number_input("Cantidad ventanas", value=0, step=1, key="cant_ventanas_est")
                ancho_ventana_est = st.number_input("Ancho ventana (m)", value=0.0, key="ancho_ventana_est")
                alto_ventana_est = st.number_input("Alto ventana (m)", value=0.0, key="alto_ventana_est")

            espesor_est = st.selectbox("Espesor de aplicación",
                                        ["5mm (fino)", "10mm (estándar)", "15mm (máximo por capa)", "20mm (2 capas)", "25mm (2 capas)"],
                                        key="espesor_est")
            espesor_val = float(espesor_est.split("mm")[0]) / 1000

            area_bruta_est = largo_est * alto_est * cant_est
            area_vanos_est = ((cant_puertas_est * ancho_puerta_est * alto_puerta_est) +
                                (cant_ventanas_est * ancho_ventana_est * alto_ventana_est))
            area_neta_est = area_bruta_est - area_vanos_est

            if espesor_val > 0.015:
                n_capas = 2
                st.warning(f"⚠️ Espesor mayor a 15mm: Se requieren {n_capas} capas. Esperar secado entre capas.")
            else:
                n_capas = 1

            if espesor_val >= 0.030:
                st.error("⚠️ Espesor mayor a 30mm: Requiere malla de refuerzo obligatoriamente")

            st.write("---")
            st.info(f"Área neta: {area_neta_est:.2f} m²")
            st.info(f"Capas necesarias: {n_capas}")

            if est["tipo"] == "premezclado" or est["tipo"] == "fino":
                sacos_est = (area_neta_est / est["rendimiento_saco"]) * n_capas
                st.success(f"Sacos de {est['peso_saco']}kg: {sacos_est:.0f} sacos")
                st.caption(f"Rendimiento: {est['rendimiento_saco']} m² por saco a {espesor_est}")

            elif est["tipo"] == "tradicional":
                vol_est = area_neta_est * espesor_val * n_capas
                cemento_est = vol_est * 300  # kg cemento por m³
                arena_est = vol_est * 1.20
                cal_est = vol_est * 100  # kg cal por m³
                sacos_cemento_est = cemento_est / 25
                sacos_cal_est = cal_est / 25

                st.info(f"Volumen mortero: {vol_est:.3f} m³")
                st.success(f"Cemento: {sacos_cemento_est:.0f} sacos de 25kg")
                st.success(f"Arena: {arena_est:.2f} m³")
                st.success(f"Cal: {sacos_cal_est:.0f} sacos de 25kg")
                st.caption("Dosificación: 1 cemento : 4 arena : 1 cal")

        # ============================
        # 3. CIELOS
        # ============================
        with st.expander("3. Cielos", expanded=False):

            cielo_tipo = st.selectbox("Tipo de cielo", list(CIELOS_TIPOS.keys()), key="cielo_tipo")
            ci = CIELOS_TIPOS[cielo_tipo]

            ci1, ci2 = st.columns(2)
            with ci1:
                largo_ci = st.number_input("Largo habitación (m)", value=0.0, key="largo_ci")
            with ci2:
                ancho_ci = st.number_input("Ancho habitación (m)", value=0.0, key="ancho_ci")

            cant_ci = st.number_input("Cantidad de habitaciones", value=0, step=1, key="cant_ci")
            desp_ci = st.slider("% Desperdicio", 0, 20, 10, key="desp_ci")

            area_ci = largo_ci * ancho_ci * cant_ci

            st.write("---")
            st.info(f"Área total cielo: {area_ci:.2f} m²")

            if ci["tipo"] == "plancha":
                cant_planchas_ci = area_ci / ci["area_plancha"]
                cant_planchas_desp_ci = cant_planchas_ci * (1 + desp_ci / 100)
                st.info(f"Planchas exactas: {cant_planchas_ci:.1f} unidades")
                st.success(f"Con {desp_ci}% desperdicio: {cant_planchas_desp_ci:.0f} planchas")

            elif ci["tipo"] == "madera":
                ancho_tabla_ci = st.selectbox("Ancho tabla machihembrada", ["10cm", "15cm", "20cm"], key="ancho_tabla_ci")
                ancho_val_ci = float(ancho_tabla_ci.replace("cm", "")) / 100
                largo_tabla_ci = st.selectbox("Largo tabla", ["3,20m", "4,00m"], key="largo_tabla_ci")
                largo_val_ci = 3.20 if "3,20" in largo_tabla_ci else 4.00
                ml_ci = area_ci / ancho_val_ci
                tablas_ci = ml_ci / largo_val_ci
                tablas_desp_ci = tablas_ci * (1 + desp_ci / 100)
                st.info(f"Metros lineales: {ml_ci:.1f} ml")
                st.success(f"Tablas con {desp_ci}% desperdicio: {tablas_desp_ci:.0f} tablas de {largo_tabla_ci}")

            # Estructura de cielo (Perfiles AT)
            st.write("---")
            st.subheader("🔩 Estructura de Cielo (Perfiles AT)")
            st.caption("Perfil AT en todo el perímetro + largueros cada 40cm")

            # Perfil AT perímetro
            perimetro_ci = (largo_ci + ancho_ci) * 2 * cant_ci
            largo_perfil_at = st.selectbox("Largo perfil AT", ["2,40m", "3,00m"], key="largo_at")
            largo_val_at = 2.40 if "2,40" in largo_perfil_at else 3.00

            cant_perfiles_at = perimetro_ci / largo_val_at
            cant_perfiles_at_desp = cant_perfiles_at * 1.10

            # Largueros Portante 40R cada 40cm
            cant_largueros = (ancho_ci / 0.40) * cant_ci
            largo_larguero = st.selectbox("Largo Portante 40R", ["2,40m", "3,00m"], key="largo_larguero")
            largo_val_larg = 2.40 if "2,40" in largo_larguero else 3.00
            cant_largueros_desp = cant_largueros * 1.10

            # Conectores
            cant_conectores = cant_largueros * (largo_ci / 1.20)

            # Tornillos
            tornillos_ci = (cant_perfiles_at_desp + cant_largueros_desp) * 4

            st.info(f"Perfiles AT perímetro: {cant_perfiles_at_desp:.0f} piezas de {largo_val_at}m")
            st.info(f"Portante 40R: {cant_largueros_desp:.0f} piezas de {largo_val_larg}m")
            st.info(f"Conectores TF: {cant_conectores:.0f} unidades")
            st.success(f"Tornillos: {tornillos_ci:.0f} unidades")
            st.caption("Largueros cada 40cm | Conectores cada 1,20m")

        # ============================
        # 4. ZÓCALOS Y GUARDAPOLVOS
        # ============================
        with st.expander("4. Zócalos y Guardapolvos", expanded=False):

            zocalo_tipo = st.selectbox("Tipo de zócalo", list(ZOCALOS.keys()), key="zocalo_tipo")
            zoc = ZOCALOS[zocalo_tipo]

            zo1, zo2 = st.columns(2)
            with zo1:
                largo_zoc = st.number_input("Metros lineales totales (m)", value=0.0, key="largo_zoc")
            with zo2:
                cant_vanos_zoc = st.number_input("Cantidad de vanos/puertas", value=0, step=1, key="cant_vanos_zoc")

            ancho_vano_zoc = st.number_input("Ancho vano promedio (m)", value=0.90, key="ancho_vano_zoc")
            largo_pieza_zoc = st.selectbox("Largo por pieza", ["2,40m", "3,00m", "3,20m"], key="largo_pieza_zoc")
            largo_val_zoc = {"2,40m": 2.40, "3,00m": 3.00, "3,20m": 3.20}[largo_pieza_zoc]
            desp_zoc = st.slider("% Desperdicio", 0, 20, 10, key="desp_zoc")

            # Descuento vanos
            ml_vanos_zoc = cant_vanos_zoc * ancho_vano_zoc
            ml_neto_zoc = largo_zoc - ml_vanos_zoc

            # Piezas
            cant_piezas_zoc = ml_neto_zoc / largo_val_zoc
            cant_piezas_desp_zoc = cant_piezas_zoc * (1 + desp_zoc / 100)

            # Fijaciones según material
            if zoc["tipo"] == "MDF":
                fijacion_zoc = "Pegamento para MDF + Clavo sin cabeza"
                cant_fijaciones_zoc = round(ml_neto_zoc / 0.40)  # cada 40cm
                medida_fijacion = "Clavo 1 1/2\""
            elif zoc["tipo"] == "Madera":
                fijacion_zoc = "Clavo sin cabeza galvanizado"
                cant_fijaciones_zoc = round(ml_neto_zoc / 0.40)
                medida_fijacion = "Clavo 1 1/2\" o 2\""
            else:  # PVC
                fijacion_zoc = "Pegamento PVC o clip de fijación"
                cant_fijaciones_zoc = round(ml_neto_zoc / 0.50)
                medida_fijacion = "Clip cada 50cm"

            st.write("---")
            st.info(f"Metros lineales netos: {ml_neto_zoc:.2f} ml")
            st.info(f"Piezas exactas: {cant_piezas_zoc:.1f} unidades")
            st.success(f"Con {desp_zoc}% desperdicio: {cant_piezas_desp_zoc:.0f} piezas de {largo_val_zoc}m")

            st.write("---")
            st.subheader("🔩 Fijaciones")
            st.info(f"Tipo: {fijacion_zoc}")
            st.info(f"Medida: {medida_fijacion}")
            st.success(f"Cantidad: {cant_fijaciones_zoc} fijaciones")
            st.caption("Distancia mínima al borde: 2cm")                
# ============================
# EXPORTAR A PDF
# ============================
st.write("---")
st.subheader("📄 Exportar Cubicación")
nombre_proyecto = st.text_input(
    "Nombre del proyecto (opcional)",
    placeholder="Ej: Casa Don Pedro - Angol",
    key="nombre_proyecto"
)

if st.button("📄 Generar PDF", type="primary"):
    pdf_buffer = generar_pdf_cubicacion(
                nombre_proyecto=nombre_proyecto,
                vol_emp=vol_emp, dos_emp=dos_emp, mat_emp=mat_emp,
                vol_pilares=vol_pilares, dos_cim=dos_cim, mat_cim=mat_cim,
                vol_sc_neto=vol_sc_neto, dos_sc=dos_sc, mat_sc=mat_sc,
                vol_radier=vol_radier, dos_rad=dos_rad, mat_rad=mat_rad,
                total_hormigon=total_hormigon,
                total_sacos=total_sacos,
                total_gravilla=total_gravilla,
                total_arena=total_arena,
                total_agua=total_agua,
                canal_tipo=st.session_state.get("pdf_canal_tipo", ""),
                cant_piezas_canal=st.session_state.get("pdf_cant_piezas_canal", 0),
                ml_canal=st.session_state.get("pdf_ml_canal", 0),
                largo_canal=st.session_state.get("pdf_largo_canal", 0),
                montante_tipo=st.session_state.get("pdf_montante_tipo", ""),
                total_montantes=st.session_state.get("pdf_total_montantes", 0),
                largo_montante=st.session_state.get("pdf_largo_montante", 0),
                esq_tipo=st.session_state.get("pdf_esq_tipo", ""),
                cant_esquinas=st.session_state.get("pdf_cant_esquinas", 0),
                largo_esq=st.session_state.get("pdf_largo_esq", 0),
            )
    nombre_archivo = f"ObraCubic_{nombre_proyecto or 'cubicacion'}.pdf".replace(" ", "_")
    st.download_button(
        label="⬇️ Descargar PDF",
        data=pdf_buffer,
        file_name=nombre_archivo,
        mime="application/pdf",
    )                

