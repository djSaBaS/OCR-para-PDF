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

- La barra de progreso de la interfaz refleja el avance real reportado por OCRmyPDF, mostrando el porcentaje según las páginas procesadas.
- Se habilitó el arrastre y suelta de archivos PDF directamente sobre la ventana para acelerar la selección del documento de entrada.
- Se añadieron pruebas automatizadas que verifican la omisión de limpieza sin `unpaper` y la nueva interpretación de progreso.

## Uso básico

1. Ejecuta `python ocr_gui.py` para abrir la interfaz gráfica.
2. Selecciona un PDF de entrada y define el nombre del archivo OCR de salida (puedes arrastrar el PDF sobre la ventana para rellenar el campo automáticamente).
3. Marca los idiomas necesarios y las opciones deseadas (rotación, enderezado, limpieza, etc.).
4. Si no tienes instalado `unpaper`, deja desmarcada la limpieza o confía en la desactivación automática que ahora realiza la aplicación.
5. Pulsa **Iniciar OCR** y espera a que finalice el proceso.

## Automatización y pruebas

Este repositorio incorpora un flujo de GitHub Actions (`.github/workflows/tests.yml`) que ejecuta `pytest` para validar las utilidades críticas. Asegúrate de mantener los tests actualizados cuando introduzcas cambios relevantes.

## Licencia

Este proyecto se distribuye bajo la licencia MIT incluida en `LICENSE`.
