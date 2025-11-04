# OCR para PDF

Aplicación de escritorio en Python y PyQt6 que permite aplicar OCR a documentos PDF utilizando OCRmyPDF o un flujo alternativo basado en Tesseract. Incluye un registro detallado y opciones avanzadas como selección de idiomas, rotación automática, enderezado y limpieza.

## Requisitos

- Python 3.10 o superior.
- Dependencias listadas en `requirements_gui.txt`.
- Binarios externos sugeridos:
  - `ocrmypdf`
  - `tesseract`
  - `ghostscript` (`gs`, `gswin64c` o `gswin32c` según sistema operativo)
  - `qpdf`
  - `unpaper` (solo necesario si se desea emplear la limpieza automática)

Instala las dependencias de Python ejecutando:

```bash
pip install -r requirements_gui.txt
```

## Novedades recientes

- La interfaz ahora informa cuando la opción de limpieza se omite porque `unpaper` no está disponible. De esta forma se evita el error de salida 3 de OCRmyPDF en Windows y se mantiene el resto del procesamiento.
- Se añadieron pruebas automatizadas que verifican el comportamiento anterior.

## Uso básico

1. Ejecuta `python ocr_gui.py` para abrir la interfaz gráfica.
2. Selecciona un PDF de entrada y define el nombre del archivo OCR de salida.
3. Marca los idiomas necesarios y las opciones deseadas (rotación, enderezado, limpieza, etc.).
4. Si no tienes instalado `unpaper`, deja desmarcada la limpieza o confía en la desactivación automática que ahora realiza la aplicación.
5. Pulsa **Iniciar OCR** y espera a que finalice el proceso.

## Automatización y pruebas

Este repositorio incorpora un flujo de GitHub Actions (`.github/workflows/tests.yml`) que ejecuta `pytest` para validar las utilidades críticas. Asegúrate de mantener los tests actualizados cuando introduzcas cambios relevantes.

## Licencia

Este proyecto se distribuye bajo la licencia MIT incluida en `LICENSE`.
