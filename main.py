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

    # Resumen total
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

        # --- 1. Canal (Solera inf. y sup.) ---
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

            st.write("---")
            st.info(f"Metros lineales necesarios: {ml_canal:.2f} ml")
            st.text(f"Cantidad de canales {largo_canal}m: {cant_piezas_canal:.0f} piezas")
            st.caption("Considera solera inferior + solera superior")

        # --- 2. Montante (Pie Derecho) ---
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

            # Montantes por tabique = (largo / separacion) + 1 (extremos)
            montantes_por_tabique = int(largo_tabique_m / sep_valor) + 1
            
            # Total montantes
            total_montantes = montantes_por_tabique * cant_tabiques_m

            # Verificar si el alto del tabique supera el largo del montante
            necesita_empalme = alto_tabique_m > largo_montante

            st.write("---")
            st.info(f"Montantes por tabique: {montantes_por_tabique} piezas")
            st.info(f"Total montantes: {total_montantes} piezas de {largo_montante}m")
            
            if necesita_empalme:
                st.warning(f"⚠️ El alto del tabique ({alto_tabique_m}m) supera el largo del montante ({largo_montante}m). Se necesita empalme.")
            else:
                st.success(f"✅ El montante de {largo_montante}m cubre el alto del tabique ({alto_tabique_m}m)")
            
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

