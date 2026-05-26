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
option = st.sidebar.radio("Ir a:", ["Cubicacion"])

# ============================
# CUBICACIÓN
# ============================
if option == "Cubicacion":
    st.subheader("CUBICACIONES")
    with st.expander("Hormigón y Movimiento de tierra", expanded=False):

        # --- 1. Excavación ---
        with st.expander("1. Excavación", expanded=False):
            ex1, ex2, ex3 = st.columns(3)
            with ex1:
                exc_largo = st.number_input("Largo excavación (m)", value=0.0, key="exc_largo")
            with ex2:
                exc_ancho = st.number_input("Ancho excavación (m)", value=0.0, key="exc_ancho")
            with ex3:
                exc_profundidad = st.number_input("Profundidad (m)", value=0.0, key="exc_prof")
            exc_perdida = st.slider("% Esponjamiento", 0, 30, 20, key="exc_perdida")
            vol_exc = (exc_largo * exc_ancho * exc_profundidad) * (1 + (exc_perdida / 100))
            st.info(f"Volumen Excavación: {vol_exc:.2f} m³")

        # --- 2. Emplantillado ---
        with st.expander("2. Emplantillado", expanded=False):
            emp1, emp2, emp3 = st.columns(3)
            with emp1:
                emp_largo = st.number_input("Largo emplantillado (m)", value=0.0, key="emp_largo")
            with emp2:
                emp_ancho = st.number_input("Ancho emplantillado (m)", value=0.0, key="emp_ancho")
            with emp3:
                emp_espesor = st.number_input("Espesor emplantillado (m)", value=0.0, key="emp_espesor")
            emp_perdida = st.slider("% Pérdida emplantillado", 0, 15, 5, key="emp_perdida")
            vol_emp = (emp_largo * emp_ancho * emp_espesor) * (1 + (emp_perdida / 100))
            st.info(f"Volumen Emplantillado: {vol_emp:.2f} m³")
            dos_emp = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                   key="dos_emp", help=DOSIFICACIONES["G-15"]["descripcion"])
            mat_emp = calcular_materiales(vol_emp, dos_emp)
            mostrar_materiales(mat_emp)

        # --- 3. Cimiento ---
        with st.expander("3. Cimiento", expanded=False):
            tipo_cimiento = st.radio(
                "Tipo de cimiento",
                ["Zapata Aislada", "Zapata Corrida", "Zapata Combinada", "Losa de Cimentación"],
                horizontal=True,
                key="tipo_cimiento"
            )

            if tipo_cimiento == "Zapata Aislada":
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_pilares = st.number_input("Cantidad de Zapatas", value=4, step=1, key="pil_cant")
                with c2:
                    seccion_pilar = st.number_input("Sección (m)", value=0.0, key="pil_sec")
                with c3:
                    alto_pilar = st.number_input("Profundidad (m)", value=0.0, key="pil_alto")
                vol_pilares = (seccion_pilar * seccion_pilar * alto_pilar) * n_pilares
                st.info(f"Volumen Zapata Aislada: {vol_pilares:.2f} m³")

            elif tipo_cimiento == "Zapata Corrida":
                c1, c2, c3 = st.columns(3)
                with c1:
                    largo_cim = st.number_input("Largo total (m)", value=0.0, key="cim_largo")
                with c2:
                    ancho_cim = st.number_input("Ancho / Espesor (m)", value=0.0, key="cim_ancho")
                with c3:
                    prof_cim = st.number_input("Profundidad (m)", value=0.0, key="cim_prof")
                vol_pilares = largo_cim * ancho_cim * prof_cim
                st.info(f"Volumen Zapata Corrida: {vol_pilares:.2f} m³")

            elif tipo_cimiento == "Zapata Combinada":
                st.caption("Une dos o más pilares cercanos en una sola zapata.")
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_zapatas_comb = st.number_input("Cantidad de zapatas combinadas", value=1, step=1, key="comb_cant")
                with c2:
                    largo_comb = st.number_input("Largo zapata (m)", value=0.0, key="comb_largo")
                with c3:
                    ancho_comb = st.number_input("Ancho zapata (m)", value=0.0, key="comb_ancho")
                prof_comb = st.number_input("Profundidad (m)", value=0.0, key="comb_prof")
                vol_pilares = largo_comb * ancho_comb * prof_comb * n_zapatas_comb
                st.info(f"Volumen Zapata Combinada: {vol_pilares:.2f} m³")

            elif tipo_cimiento == "Losa de Cimentación":
                st.caption("Placa continua bajo toda la estructura. Se usa en terrenos de baja capacidad portante.")
                c1, c2, c3 = st.columns(3)
                with c1:
                    largo_losa_cim = st.number_input("Largo (m)", value=0.0, key="losacim_largo")
                with c2:
                    ancho_losa_cim = st.number_input("Ancho (m)", value=0.0, key="losacim_ancho")
                with c3:
                    esp_losa_cim = st.number_input("Espesor (m)", value=0.0, key="losacim_esp")
                vol_pilares = largo_losa_cim * ancho_losa_cim * esp_losa_cim
                st.info(f"Volumen Losa de Cimentación: {vol_pilares:.2f} m³")

            st.caption("Para pilotes o micropilotes consulte con un ingeniero especialista.")

            dos_cim = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                index=1, key="dos_cim",
                                help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_cim = calcular_materiales(vol_pilares, dos_cim)
            mostrar_materiales(mat_cim)

        # --- 4. Sobrecimiento ---
        with st.expander("4. Sobrecimiento (Con Descuento de Vanos)", expanded=False):
            st.write("**Dimensiones Brutas**")
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sc_largo = st.number_input("Largo Total (m)", value=0.0, key="sc_largo")
            with sc2:
                sc_ancho = st.number_input("Ancho / Espesor (m)", value=0.0, key="sc_ancho")
            with sc3:
                sc_alto = st.number_input("Alto Sobrecimiento (m)", value=0.0, key="sc_alto")
            vol_sc_bruto = sc_largo * sc_ancho * sc_alto
            st.write("**Descuento de Vanos**")
            v1, v2 = st.columns(2)
            with v1:
                n_vanos = st.number_input("Cantidad de Vanos / Puertas", value=2, step=1, key="vanos_cant")
            with v2:
                ancho_vano = st.number_input("Ancho del Vano (m)", value=0.0, key="vanos_ancho")
            vol_descuento_vanos = n_vanos * ancho_vano * sc_ancho * sc_alto
            vol_sc_neto = vol_sc_bruto - vol_descuento_vanos
            st.text(f"Volumen Bruto: {vol_sc_bruto:.2f} m³")
            st.text(f"Descuento Vanos: -{vol_descuento_vanos:.2f} m³")
            st.info(f"Volumen Neto Sobrecimiento: {vol_sc_neto:.2f} m³")
            dos_sc = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                  index=1, key="dos_sc",
                                  help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_sc = calcular_materiales(vol_sc_neto, dos_sc)
            mostrar_materiales(mat_sc)

        # --- 5. Radier ---
        with st.expander("5. Radier", expanded=False):
            ra1, ra2 = st.columns(2)
            with ra1:
                rad_largo = st.number_input("Largo Radier (m)", value=0.0, key="radier_largo")
                rad_ancho = st.number_input("Ancho Radier (m)", value=0.0, key="radier_ancho")
            with ra2:
                rad_espesor = st.number_input("Espesor Radier (m)", value=0.0, key="radier_espesor")
                rad_perdida = st.slider("% Pérdida Radier", 0, 15, 5, key="radier_perdida")
            vol_radier = (rad_largo * rad_ancho * rad_espesor) * (1 + (rad_perdida / 100))
            st.info(f"Volumen Radier: {vol_radier:.2f} m³")
            dos_rad = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                   index=1, key="dos_rad",
                                   help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_rad = calcular_materiales(vol_radier, dos_rad)
            mostrar_materiales(mat_rad)

        # --- Resumen total hormigón ---
        st.write("---")
        total_hormigon = vol_emp + vol_pilares + vol_sc_neto + vol_radier
        st.success(f"### Volumen Total Neto de la Obra: {total_hormigon:.2f} m³")

        st.subheader("Resumen Total de Materiales")
        st.caption("Suma de todas las partidas con sus respectivas dosificaciones y desperdicios")

        total_sacos    = mat_emp["cemento_sacos"] + mat_cim["cemento_sacos"] + mat_sc["cemento_sacos"] + mat_rad["cemento_sacos"]
        total_gravilla = mat_emp["gravilla_kg"]   + mat_cim["gravilla_kg"]   + mat_sc["gravilla_kg"]   + mat_rad["gravilla_kg"]
        total_arena    = mat_emp["arena_kg"]      + mat_cim["arena_kg"]      + mat_sc["arena_kg"]      + mat_rad["arena_kg"]
        total_agua     = mat_emp["agua_lt"]       + mat_cim["agua_lt"]       + mat_sc["agua_lt"]       + mat_rad["agua_lt"]

        st.session_state["vol_emp"] = vol_emp
        st.session_state["vol_pilares"] = vol_pilares
        st.session_state["vol_sc_neto"] = vol_sc_neto
        st.session_state["vol_radier"] = vol_radier
        st.session_state["total_sacos"] = total_sacos
        st.session_state["total_gravilla"] = total_gravilla
        st.session_state["total_arena"] = total_arena
        st.session_state["total_agua"] = total_agua

        st.session_state["mat_emp"] = mat_emp
        st.session_state["mat_cim"] = mat_cim
        st.session_state["mat_sc"] = mat_sc
        st.session_state["mat_rad"] = mat_rad

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
        with st.expander("3. Tabique Metalcon", expanded=False):

            MONTANTES_MU = {
                "Montante Normal Perf. 60x38x0,5 - 2,40m": {"largo": 2.40, "peso": 0.56},
                "Montante Normal Perf. 60x38x0,5 - 3,00m": {"largo": 3.00, "peso": 0.56},
                "Montante Económico 38x38x0,5 - 2,40m":    {"largo": 2.40, "peso": 0.48},
                "Montante Económico 38x38x0,5 - 3,00m":    {"largo": 3.00, "peso": 0.48},
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

            sep_mu = st.selectbox("Separación montantes", ["0,40m (recomendado)", "0,60m (máximo)"], key="sep_mu")
            sep_valor_mu = 0.40 if "0,40" in sep_mu else 0.60

            canal_tipo_mu = st.selectbox("Tipo de canal", list(CANALES_MU.keys()), key="canal_mu")
            montante_tipo_mu = st.selectbox("Tipo de montante", list(MONTANTES_MU.keys()), key="montante_mu")

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
                cant_encuentros_mu = st.number_input("Cantidad de encuentros de muros", value=0, step=1, key="cant_enc_mu")

            largo_canal_mu = CANALES_MU[canal_tipo_mu]["largo"]
            largo_mont_mu = MONTANTES_MU[montante_tipo_mu]["largo"]

            # Cálculo canales (solera inf + sup)
            ml_canal_mu = largo_tab_mu * 2 * cant_tab_mu
            cant_canales_mu = ml_canal_mu / largo_canal_mu if largo_canal_mu > 0 else 0

            # Cálculo montantes
            montantes_por_tab = int(largo_tab_mu / sep_valor_mu) + 1
            total_montantes_mu = montantes_por_tab * cant_tab_mu

            # Montantes extra por vanos (2 por cada vano)
            mont_extra_vanos = (cant_puertas_mu + cant_ventanas_mu) * 2

            # Montantes extra por esquinas (3 por esquina)
            mont_extra_esq = cant_esquinas_mu * 3

            # Montantes extra por encuentros (4 por encuentro)
            mont_extra_enc = cant_encuentros_mu * 4

            total_montantes_final = total_montantes_mu + mont_extra_vanos + mont_extra_esq + mont_extra_enc

            # Diagonales (2 por tabique)
            total_diagonales = cant_tab_mu * 2

            # Canales extra por vanos (1 canal por cada lado del vano)
            canales_extra_vanos = (cant_puertas_mu + cant_ventanas_mu) * 2
            total_canales_final = cant_canales_mu + canales_extra_vanos

            # Tornillos autoperforantes
            tornillos = (total_montantes_final * 4) + (total_canales_final * 2)

            # Aislación lana de vidrio
            m2_aislacion = largo_tab_mu * alto_tab_mu * cant_tab_mu
            m2_vanos = (cant_puertas_mu * ancho_puerta_mu * alto_tab_mu) + (cant_ventanas_mu * ancho_ventana_mu * alto_tab_mu)
            m2_aislacion_neta = m2_aislacion - m2_vanos

            st.write("---")
            st.subheader("📦 Resultados")

            r1, r2 = st.columns(2)
            with r1:
                st.info(f"Canales totales: {total_canales_final:.0f} piezas de {largo_canal_mu}m")
                st.info(f"Montantes totales: {total_montantes_final:.0f} piezas de {largo_mont_mu}m")
                st.info(f"Diagonales: {total_diagonales} piezas")
            with r2:
                st.info(f"Pletinas esquinas: {cant_esquinas_mu} unidades")
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

