"""
Mantiene despierta la app de ObraCubic en Streamlit Community Cloud.

Por qué este script y no un simple "ping": Streamlit devuelve una página HTML
estática (HTTP 200) aunque la app esté dormida, así que un GET no la despierta.
Hay que abrirla con un navegador real y, si aparece el botón "Yes, get this app
back up!", hacer clic.

Nota técnica: NO se usa wait_until="networkidle" porque Streamlit mantiene un
websocket abierto y esa condición casi nunca se cumple (provocaba que el job
fallara por timeout). Se usa "domcontentloaded", que sí es fiable.
"""

import sys
from playwright.sync_api import sync_playwright

URL = "https://obracubic.streamlit.app/"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Cargar la página. Con solo abrirla ya se dispara el arranque de la app.
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            # Aunque la carga demore, la visita igual despierta la app: no fallar.
            print(f"Aviso: la carga inicial demoró ({e}). La visita igual cuenta.")

        # Dar tiempo a que renderice (despierta o con botón de 'wake up')
        page.wait_for_timeout(8000)

        # Si aparece el botón de despertar, hacer clic
        try:
            boton = page.locator("button", has_text="back up")
            if boton.count() > 0 and boton.first.is_visible():
                boton.first.click()
                print("La app estaba DORMIDA -> se hizo clic para despertarla.")
                page.wait_for_timeout(30000)  # esperar a que arranque
            else:
                print("La app ya estaba DESPIERTA.")
        except Exception as e:
            print(f"No se evaluó el botón (probablemente ya despierta): {e}")

        browser.close()

    # Siempre salir con éxito: es un mantenimiento best-effort, no debe
    # enviar correos de error si la app simplemente tardó en responder.
    return 0


if __name__ == "__main__":
    sys.exit(main())