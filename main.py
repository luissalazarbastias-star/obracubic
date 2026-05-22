import streamlit as st

# --- CONFIGURACIÓN VISUAL DE LA APP (Pestaña del navegador) ---
st.set_page_config(
    page_title="ObraCubic - Grandes Cosas Comienzan Aquí",
    page_icon="🏗️"
)

# --- DIRECCIÓN DE TU LOGOTIPO ---
# Asegúrate de que esta URL sea la que obtuvimos de GitHub (la versión "raw")
URL_DEL_LOGO = "https://raw.githubusercontent.com/luissalazarbastias-star/obracubic/refs/heads/main/263c7f73-0dfb-4f9c-ba56-a18242a3729b.jpg"

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.image(URL_DEL_LOGO, use_container_width=True)
st.sidebar.write("---")
st.sidebar.header("Módulos de Trabajo")
option = st.sidebar.radio("Ir a:", ["Panel General", "Calculadora de Hormigón"])

# --- CUERPO PRINCIPAL ---

if option == "Panel General":
    # Logo central para dar la bienvenida
    st.image(URL_DEL_LOGO, use_container_width=True)
    st.write("---")
    
    # --- FRASE INSPIRADORA PERSONALIZADA ---
    # Usamos HTML para que se vea centrada, en cursiva y con el color naranjo de la marca
    st.markdown("<h3 style='text-align: center; color: #FF6B00;'><i>“Grandes estructuras se levantan con decisiones precisas.”</i></h3>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("Estado del Proyecto")
    st.info("Aquí podrás ver el resumen de tus obras y el ahorro generado por la optimización de materiales.")
    
    # Ejemplo de métrica de impacto
    col_met1, col_met2 = st.columns(2)
    with col_met1:
        st.metric(label="Ahorro Estimado (Mes)", value="$145.000 CLP", delta="12%")
    with col_met2:
        st.metric(label="M3 Optimizados", value="14.5 m³", delta="5.2%")

elif option == "Calculadora de Hormigón":
    # Logo encabezando la calculadora principal
    st.image(URL_DEL_LOGO, use_container_width=True)
    st.write("---")
    st.subheader("Cubicación Técnica de la Obra")
    
    # --- 1. Partida: Emplantillado ---
    with st.expander("1. Emplantillado", expanded=False):
        emp1, emp2, emp3 = st.columns(3)
        with emp1:
            emp_largo = st.number_input("Largo emplantillado (m)", value=10.0, key="emp_largo")
        with emp2:
            emp_ancho = st.number_input("Ancho emplantillado (m)", value=5.0, key="emp_ancho")
        with emp3:
            emp_espesor = st.number_input("Espesor emplantillado (m)", value=0.10, key="emp_espesor")
        emp_perdida = st.slider("% Pérdida emplantillado", 0, 15, 5, key="emp_perdida")

        vol_emp = (emp_largo * emp_ancho * emp_espesor) * (1 + (emp_perdida / 100))
        st.info(f"Volumen Emplantillado: {vol_emp:.2f} m³")

    # --- 2. PARTIDA: Cimiento ---
    with st.expander("2. Cimiento", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_pilares = st.number_input("Cantidad de Pilares", value=4, step=1, key="pil_cant")
        with c2:
            seccion_pilar = st.number_input("Sección Pilar (m)", value=0.20, key="pil_sec")
        with c3:
            alto_pilar = st.number_input("Profundidad Pilar (m)", value=1.0, key="pil_alto")

        vol_pilares = (seccion_pilar * seccion_pilar * alto_pilar) * n_pilares
        st.info(f"Volumen Pilares: {vol_pilares:.2f} m³")

    # --- 3. PARTIDA: SOBRECIMIENTO ---
    with st.expander("3. Sobrecimiento (Con Descuento de Vanos)", expanded=False):
        st.write("**Dimensiones Brutas**")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sc_largo = st.number_input("Largo Total (m)", value=15.0, key="sc_largo")
        with sc2:
            sc_ancho = st.number_input("Ancho / Espesor (m)", value=0.15, key="sc_ancho")
        with sc3:
            sc_alto = st.number_input("Alto Sobrecimiento (m)", value=0.30, key="sc_alto")

        vol_sc_bruto = sc_largo * sc_ancho * sc_alto

        st.write("**Descuento de Vanos**")
        v1, v2 = st.columns(2)
        with v1:
            n_vanos = st.number_input("Cantidad de Vanos / Puertas", value=2, step=1, key="vanos_cant")
        with v2:
            ancho_vano = st.number_input("Ancho del Vano (m)", value=0.90, key="vanos_ancho")

        vol_descuento_vanos = n_vanos * ancho_vano * sc_ancho * sc_alto
        vol_sc_neto = vol_sc_bruto - vol_descuento_vanos

        st.text(f"Volumen Bruto: {vol_sc_bruto:.2f} m³")
        st.text(f"Descuento Vanos: -{vol_descuento_vanos:.2f} m³")
        st.info(f"Volumen Neto Sobrecimiento: {vol_sc_neto:.2f} m³")

    # --- 4. PARTIDA: RADIER ---
    with st.expander("4. Radier", expanded=True):
        ra1, ra2 = st.columns(2)
        with ra1:
            rad_largo = st.number_input("Largo Radier (m)", value=10.0, key="radier_largo")
            rad_ancho = st.number_input("Ancho Radier (m)", value=5.0, key="radier_ancho")
        with ra2:
            rad_espesor = st.number_input("Espesor Radier (m)", value=0.12, key="radier_espesor")
            rad_perdida = st.slider("% Pérdida Radier", 0, 15, 5, key="radier_perdida")

        vol_radier = (rad_largo * rad_ancho * rad_espesor) * (1 + (rad_perdida / 100))
        st.info(f"Volumen Radier: {vol_radier:.2f} m³")

    st.write("---")
    
    # --- TOTAL GENERAL ---
    # Al estar dentro del bloque 'elif', estas variables solo se calculan cuando entras a este módulo.
    total_hormigon = vol_emp + vol_pilares + vol_sc_neto + vol_radier
    st.success(f"### Volumen Total Neto de la Obra: {total_hormigon:.2f} m³")

