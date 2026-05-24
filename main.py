import streamlit as st

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
        "cemento_sacos": round(170 / 25),  # 7 sacos
        "gravilla_kg": 1025,
        "arena_kg": 910,
        "agua_lt": 195,
    },
    "G-10": {
        "descripcion": "Hormigón de baja resistencia",
        "cemento_sacos": round(230 / 25),  # 9 sacos
        "gravilla_kg": 1055,
        "arena_kg": 835,
        "agua_lt": 195,
    },
    "G-15": {
        "descripcion": "Emplantillado, sobrecimientos simples",
        "cemento_sacos": round(275 / 25),  # 11 sacos
        "gravilla_kg": 1070,
        "arena_kg": 800,
        "agua_lt": 195,
    },
    "G-20": {
        "descripcion": "Radier, cimientos normales",
        "cemento_sacos": round(340 / 25),  # 14 sacos
        "gravilla_kg": 1095,
        "arena_kg": 715,
        "agua_lt": 200,
    },
    "G-25": {
        "descripcion": "Losas estructurales, pilares",
        "cemento_sacos": round(380 / 25),  # 15 sacos
        "gravilla_kg": 1120,
        "arena_kg": 645,
        "agua_lt": 200,
    },
    "G-30": {
        "descripcion": "Obras especiales, alta resistencia",
        "cemento_sacos": round(440 / 25),  # 18 sacos
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
    """Muestra los materiales calculados en columnas."""
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
    "Losa":    {"ratio": 8,   "unidad": "kg/m²"},
    "Viga":    {"ratio": 120, "unidad": "kg/m³"},
    "Pilar":   {"ratio": 150, "unidad": "kg/m³"},
    "Radier":  {"ratio": 5,   "unidad": "kg/m²"},
    "Cimiento":{"ratio": 80,  "unidad": "kg/m³"},
}

# ============================
# LOGO Y SIDEBAR
# ============================
URL_DEL_LOGO = "https://raw.githubusercontent.com/luissalazarbastias-star/obracubic/refs/heads/main/Dise%C3%B1o%20sin%20t%C3%ADtulo.png"

st.sidebar.image(URL_DEL_LOGO, use_container_width=True)
st.sidebar.write("---")
st.sidebar.header("Módulos de Trabajo")
option = st.sidebar.radio("Ir a:", ["Panel General", "Cubicacion"])

# ============================
# PANEL GENERAL
# ============================
if option == "Panel General":
    st.markdown("<h3 style='text-align: center; color: #FF6B00;'><i>'Grandes estructuras se levantan con decisiones precisas.'</i></h3>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("Estado del Proyecto")
    st.info("Aquí podrás ver el resumen de tus obras y el ahorro generado por la optimización de materiales.")
    st.subheader("Radier")
    r1, r2 = st.columns(2)
    with r1:
        rad_largo = st.number_input("Largo Radier (m)", value=0.0, key="radier_largo")
        rad_ancho = st.number_input("Ancho Radier (m)", value=0.0, key="radier_ancho")
    with r2:
        rad_espesor = st.number_input("Espesor Radier (m)", value=0.0, key="radier_espesor")
        rad_perdida = st.slider("% Pérdida Radier", 0, 15, 5, key="radier_perdida")
    
    vol_radier = (rad_largo * rad_ancho * rad_espesor) * (1 + (rad_perdida / 100))
    st.info(f"Volumen Radier: {vol_radier:.2f} m³")
    
    dos_rad = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                         index=1,
                         key="dos_rad",
                         help=DOSIFICACIONES["G-20"]["descripcion"])
    mat_rad = calcular_materiales(vol_radier, dos_rad)
    mostrar_materiales(mat_rad)

# ============================
# CALCULADORA DE HORMIGÓN
# ============================
elif option == "Cubicacion":
    st.subheader("CUBICACIONES")
    with st.expander("Hormigón y Movimiento de tierra", expanded=False):

        # --- 1. Excavacion---
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
                                   key="dos_emp",
                                   help=DOSIFICACIONES["G-15"]["descripcion"])
            mat_emp = calcular_materiales(vol_emp, dos_emp)
            mostrar_materiales(mat_emp)

        # --- 3. Cimiento ---
        with st.expander("3. Cimiento", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_pilares = st.number_input("Cantidad de Pilares", value=4, step=1, key="pil_cant")
            with c2:
                seccion_pilar = st.number_input("Sección Pilar (m)", value=0.0, key="pil_sec")
            with c3:
                alto_pilar = st.number_input("Profundidad Pilar (m)", value=0.0, key="pil_alto")

            vol_pilares = (seccion_pilar * seccion_pilar * alto_pilar) * n_pilares
            st.info(f"Volumen Pilares: {vol_pilares:.2f} m³")

            dos_cim = st.selectbox("Dosificación", list(DOSIFICACIONES.keys()),
                                   index=1,
                                   key="dos_cim",
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
                                  index=1,
                                  key="dos_sc",
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
                                   index=1,
                                   key="dos_rad",
                                   help=DOSIFICACIONES["G-20"]["descripcion"])
            mat_rad = calcular_materiales(vol_radier, dos_rad)
            mostrar_materiales(mat_rad)

        # --- Total general ---
        st.write("---")
        total_hormigon = vol_emp + vol_pilares + vol_sc_neto + vol_radier
        st.success(f"### Volumen Total Neto de la Obra: {total_hormigon:.2f} m³")

        st.subheader("Resumen Total de Materiales")
        st.caption("Suma de todas las partidas con sus respectivas dosificaciones y desperdicios")

        total_sacos    = mat_emp["cemento_sacos"] + mat_cim["cemento_sacos"] + mat_sc["cemento_sacos"] + mat_rad["cemento_sacos"]
        total_gravilla = mat_emp["gravilla_kg"]   + mat_cim["gravilla_kg"]   + mat_sc["gravilla_kg"]   + mat_rad["gravilla_kg"]
        total_arena    = mat_emp["arena_kg"]      + mat_cim["arena_kg"]      + mat_sc["arena_kg"]      + mat_rad["arena_kg"]
        total_agua     = mat_emp["agua_lt"]       + mat_cim["agua_lt"]       + mat_sc["agua_lt"]       + mat_rad["agua_lt"]

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Cemento Total",  f"{total_sacos} sacos")
        r2.metric("Gravilla Total", f"{total_gravilla} kg")
        r3.metric("Arena Total",    f"{total_arena} kg")
        r4.metric("Agua Total",     f"{total_agua} lt")
        
        #--- Acero estructural --- 
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
                    horizontal=True,
                    key="modo_losa"
                )
                
                if modo_losa == "🔨 Modo Simple":
                    st.caption("Estimación por ratio kg/m²")
                    ls1, ls2 = st.columns(2)
                    with ls1:
                        largo_losa = st.number_input("Largo losa (m)", value=0.0, key="ls_largo")
                    with ls2:
                        ancho_losa = st.number_input("Ancho losa (m)", value=0.0, key="ls_ancho")
                        
                    area_losa = largo_losa * ancho_losa
                    kg_acero_losa = area_losa * 8  # ratio 8 kg/m²
                    
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
                        
                    # Cálculo dirección X
                    cant_barras_x = ancho_losa_d / sep_x if sep_x > 0 else 0
                    largo_m_x = float(largo_barra_x.replace("m", ""))
                    kg_x = cant_barras_x * largo_losa_d * PESO_BARRAS[diam_x]
                    barras_x = (cant_barras_x * largo_losa_d) / largo_m_x

                    # Cálculo dirección Y
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
                    horizontal=True,
                    key="modo_pilar"
                    )
                if modo_pilar == "🔨 Modo Simple":
                        st.caption("Cálculo por barras longitudinales y estribos")
                            
                        p1, p2, p3 = st.columns(3)
                        with p1:
                            cant_pilares = st.number_input("Cantidad de pilares", value=1, step=1, key="cant_pil")
                        with p2:
                            alto_pilar = st.number_input("Alto pilar (m)", value=2.20, key="alto_pil")
                        with p3:
                            barras_long = st.selectbox("Barras longitudinales", [4, 6, 8], key="barras_long")
                        p4, p5, p6 = st.columns(3)
                        with p4:
                            diam_long = st.selectbox("Diámetro barra long.", list(PESO_BARRAS.keys()), index=2, key="diam_long")
                        with p5:
                            sep_estribo = st.selectbox("Separación estribos (m)", [0.10, 0.15, 0.20], key="sep_estribo")                            with p6:
                        diam_estribo = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_estribo")
                         p7, p8 = st.columns(2)
                        with p7:
                            ancho_pilar = st.number_input("Ancho pilar (m)", value=0.30, key="ancho_pil")
                        with p8:
                            largo_pilar = st.number_input("Largo pilar (m)", value=0.30, key="largo_pil")
                            
                        # Barras longitudinales
                        ml_long = barras_long * alto_pilar * cant_pilares
                        kg_long = ml_long * PESO_BARRAS[diam_long]
                            
                        # Estribos
                        n_estribos = (alto_pilar / sep_estribo) * cant_pilares
                        perimetro_estribo = ((ancho_pilar + largo_pilar) * 2) + 0.20  # +20cm ganchos
                        ml_estribos = n_estribos * perimetro_estribo 
                        kg_estribos = ml_estribos * PESO_BARRAS[diam_estribo]
                            
                        kg_total_pilar = kg_long + kg_estribos
                            
                        st.write("---")
                        st.info(f"Acero total pilares: {kg_total_pilar:.1f} kg")
                        st.text(f"Barras long.: {barras_long * cant_pilares} barras {diam_long} x {alto_pilar}m")
                        st.text(f"Estribos: {n_estribos:.0f} estribos {diam_estribo} c/{sep_estribo}m")
                        st.text(f"Kg longitudinal: {kg_long:.1f} kg")
                        st.text(f"Kg estribos: {kg_estribos:.1f} kg")
                            
                elif modo_pilar == "📐 Modo Detallado":
                        st.caption("Cálculo exacto por barra")
                            
                        pd1, pd2 = st.columns(2)
                        with pd1:
                            cant_pil_d = st.number_input("Cantidad de pilares", value=1, step=1, key="cant_pil_d")
                        with pd2:
                                alto_pil_d = st.number_input("Alto pilar (m)", value=2.20, key="alto_pil_d")
                           
                        st.write("**Barras longitudinales**")
                        bl1, bl2 = st.columns(2)
                        with bl1:
                            cant_bl = st.number_input("Cantidad barras", value=4, step=1, key="cant_bl")
                        with bl2:
                            diam_bl = st.selectbox("Diámetro", list(PESO_BARRAS.keys()), index=2, key="diam_bl")
                            
                        st.write("**Estribos**")
                        be1, be2, be3 = st.columns(3)
                        with be1:
                              ancho_p = st.number_input("Ancho pilar (m)", value=0.30, key="ancho_p_d")
                        with be2:
                            largo_p = st.number_input("Largo pilar (m)", value=0.30, key="largo_p_d")
                        with be3:
                            sep_be = st.selectbox("Separación (m)", [0.10, 0.15, 0.20], key="sep_be")
                            
                       diam_be = st.selectbox("Diámetro estribo", list(PESO_BARRAS.keys()), index=0, key="diam_be")

                       # Cálculo
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
                
