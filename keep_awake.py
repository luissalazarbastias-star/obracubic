"""
Mantiene despierta la app de ObraCubic en Streamlit Community Cloud.

Por qué este script y no un simple "ping": Streamlit devuelve una página HTML
estática (HTTP 200) aunque la app esté dormida, así que un GET no la despierta.
Hay que abrirla con un navegador real y, si aparece el botón "Yes, get this app
back up!", hacer clic. Eso es justo lo que hace Playwright aquí.
"""

import sys
from playwright.sync_api import sync_playwright

URL = "https://obracubic.streamlit.app/"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"No se pudo cargar la app: {e}")
            browser.close()
            return 1

        # Dar un momento a que renderice la pantalla (despierta o dormida)
        page.wait_for_timeout(5000)

        # Buscar el botón de "despertar" por su texto (tolerante a mayúsculas)
        boton = page.locator("button", has_text="back up")
        try:
            if boton.count() > 0 and boton.first.is_visible():
                boton.first.click()
                print("La app estaba DORMIDA -> se hizo clic para despertarla.")
                # Esperar a que arranque la app Python
                page.wait_for_timeout(30000)
            else:
                print("La app ya estaba DESPIERTA.")
        except Exception as e:
            print(f"No se encontró el botón de despertar (probablemente ya despierta): {e}")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
