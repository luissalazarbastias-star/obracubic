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
        "cemento_sacos": round(170 / 25),  # 7 sacos
        "gravilla_kg": 1025,
        "arena_kg": 910,
        "agua_lt": 195,
    },
    "G-10":{
        "cemento_sacos": round(230 / 25),  # 9 sacos
        "gravilla_kg": 1055,
        "arena_kg": 835,
        "agua_lt": 195, 
   },
    "G-15": {
        "cemento_sacos": round(275 / 25),  # 11 sacos
        "gravilla_kg": 1070,
        "arena_kg": 800,
        "agua_lt": 195,
    },
    "G-20": {
        "cemento_sacos": round(340 / 25),  # 14 sacos
        "gravilla_kg": 1095,
        "arena_kg": 715,
        "agua_lt": 200,
    },
    "G-25": {
        "cemento_sacos": round(380 / 25),  # 15 sacos
        "gravilla_kg": 1120,
        "arena_kg": 645,
        "agua_lt": 200,
    },
    "G-30": {
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

# ============================
# LOGO Y SIDEBAR
# ============================
URL_DEL_LOGO = "https://raw.githubusercontent.com/luissalazarbastias-star/obracubic/refs/heads/main/Dise%C3%B1o%20sin%20t%C3%ADtulo.png"

st.sidebar.image(URL_DEL_LOGO, use_container_width=True)
st.sidebar.write("---")
st.sidebar.header("Módulos de Trabajo")
option = st.sidebar.radio("Ir a:", ["Panel General", "Calculadora de Obra"])

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
                         help=DOSIFICACIONES["G-20"])
    mat_rad = calcular_materiales(vol_radier, dos_rad/ 100)
    mostrar_materiales(mat_rad)

# ============================
# CALCULADORA DE HORMIGÓN
# ============================
elif option == "Calculadora de Obra":
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
                                   help=DOSIFICACIONES["G-15"])
            mat_emp = calcular_materiales(vol_emp, dos_emp / 100)
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
                                   help=DOSIFICACIONES["G-20"])
            mat_cim = calcular_materiales(vol_pilares, dos_cim / 100)
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
                                  help=DOSIFICACIONES["G-20"])
            mat_sc = calcular_materiales(vol_sc_neto, dos_sc / 100)
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
                                   help=DOSIFICACIONES["G-20"])
            mat_rad = calcular_materiales(vol_radier, dos_rad / 100)
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
