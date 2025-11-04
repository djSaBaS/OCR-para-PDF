#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================================================================
# Aplicación GUI para realizar OCR a PDFs escaneados usando PyQt y Tesseract/OCRmyPDF
# =========================================================================
# Estilo de comentarios solicitado por el usuario:
#   - Comentario profesional y normativo ANTES de cada línea de código.
#   - Comentarios de funciones detallados con buenas prácticas.
#   - Ejemplo de estilo:  # imprime \n echo "hola";
# =========================================================================

# -----------------------------
# Importaciones estándar
# -----------------------------

# Importa typing para anotar tipos de manera clara y mantenible.
from typing import List, Optional, Tuple

# Importa os para operaciones de sistema como rutas y variables de entorno.
import os

# Importa sys para acceder a información del intérprete y salida de errores.
import sys

# Importa shutil para localizar binarios en PATH y gestionar archivos.
import shutil

# Importa subprocess para ejecutar procesos externos como 'ocrmypdf' o 'tesseract'.
import subprocess

# Importa tempfile para manejar directorios temporales seguros.
import tempfile

# Importa platform para conocer el sistema operativo y ajustar dependencias.
import platform

# Importa re para validaciones y parsing de rangos de páginas.
import re


# -----------------------------
# Importaciones de terceros
# -----------------------------

# Importa fitz (PyMuPDF) para abrir y renderizar páginas de PDF a imagen.
import fitz  # type: ignore

# Importa PdfMerger de pypdf para unir PDFs intermedios.
from pypdf import PdfMerger  # type: ignore


# -----------------------------
# Importaciones de PyQt6
# -----------------------------

# Importa el núcleo de PyQt6 para señales, ranuras y temporizadores.
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Importa widgets de PyQt6 para construir la interfaz gráfica.
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QTextEdit,
    QProgressBar,
    QComboBox,
    QSizePolicy,
    QStyle,
    QToolButton
)


# -----------------------------
# Utilidades y helpers
# -----------------------------

# Define una función para localizar un ejecutable en el PATH del sistema.
def which(cmd: str) -> Optional[str]:
    """
    Devuelve la ruta absoluta al ejecutable si se encuentra en PATH.
    :param cmd: Nombre del comando a localizar (p. ej. 'tesseract', 'ocrmypdf').
    :return: Ruta absoluta si se encuentra; None en caso contrario.
    """
    # Devuelve la ruta encontrada o None.
    return shutil.which(cmd)


# Define una función para lanzar una excepción clara cuando una precondición no se cumple.
def ensure(condition: bool, message: str) -> None:
    """
    Lanza RuntimeError si 'condition' es falsa.
    :param condition: Condición booleana que debe cumplirse.
    :param message: Mensaje explicativo de la dependencia o precondición.
    """
    # Si la condición es falsa, lanza un error con mensaje profesional.
    if not condition:
        raise RuntimeError(message)


# Define una función para convertir un string de rangos de páginas en una lista de enteros base-1.
def parse_pages(pages_str: Optional[str], total_pages: Optional[int] = None) -> List[int]:
    """
    Parsea un string de rangos de páginas (base-1) permitiendo formatos como:
      - '1-10, 15, 20-' (este último hasta el final si se conoce total_pages)
      - '-' no es válido en solitario
    :param pages_str: Cadena con rangos separados por comas.
    :param total_pages: Número total de páginas para interpretar rangos abiertos.
    :return: Lista deduplicada de páginas (enteros base-1) ordenadas ascendentemente.
    """
    # Si no se pasa cadena, retorna lista vacía que indica "todas las páginas".
    if not pages_str:
        return []
    # Separa por comas y limpia espacios.
    parts = [p.strip() for p in pages_str.split(",") if p.strip()]
    # Prepara resultado acumulado.
    result: List[int] = []
    # Recorre cada parte del rango.
    for part in parts:
        # Intenta hacer match de formato rango "a-b".
        m = re.match(r"^(\d+)?\s*-\s*(\d+)?$", part)
        # Si hay match, es un rango.
        if m:
            # Recupera valores capturados (inicio y fin).
            start_s, end_s = m.groups()
            # Si ambos son None, ignora la entrada.
            if start_s is None and end_s is None:
                continue
            # Determina inicio por defecto (1 si falta).
            start = int(start_s) if start_s else 1
            # Determina fin por defecto (total_pages si se conoce, o inicio si no).
            end = int(end_s) if end_s else (total_pages if total_pages else start)
            # Si el fin es menor que inicio, intercambia para normalizar.
            if end < start:
                start, end = end, start
            # Añade todos los enteros del rango inclusivo.
            result.extend(list(range(start, end + 1)))
        else:
            # Si no es rango, debe ser un número suelto; valida.
            if part.isdigit():
                # Convierte a entero y añade al resultado.
                result.append(int(part))
            else:
                # Lanza error en formato no reconocido.
                raise ValueError(f"Formato de páginas no reconocido: '{part}'")
    # Deduplica manteniendo el orden de aparición.
    seen = set()
    deduped: List[int] = []
    for p in result:
        if p not in seen:
            deduped.append(p)
            seen.add(p)
    # Devuelve la lista final de páginas.
    return deduped


# Define una función para convertir una lista de páginas a representación de rangos compactos.
def pages_to_ranges(nums: List[int]) -> str:
    """
    Convierte una lista de páginas (enteros base-1) en una cadena compacta de rangos.
    :param nums: Lista de páginas.
    :return: Cadena tipo '1-5,7,10-12'.
    """
    # Si la lista está vacía, retorna cadena vacía.
    if not nums:
        return ""
    # Ordena y deduplica por seguridad.
    nums = sorted(set(nums))
    # Prepara contenedores para construir rangos.
    ranges: List[str] = []
    # Inicializa inicio y anterior.
    start = prev = nums[0]
    # Recorre valores restantes.
    for n in nums[1:]:
        if n == prev + 1:
            # Si es consecutivo, avanza el final del rango.
            prev = n
        else:
            # Si se rompe la consecutividad, cierra el rango actual.
            if start == prev:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{prev}")
            # Reinicia inicio y anterior.
            start = prev = n
    # Cierra el último rango.
    if start == prev:
        ranges.append(f"{start}")
    else:
        ranges.append(f"{start}-{prev}")
    # Une con comas y devuelve.
    return ",".join(ranges)


# Define una función para renderizar una página de PDF a imagen mediante PyMuPDF.
def render_page_to_image(pdf_path: str, page_number_1based: int, dpi: int, tmpdir: str) -> str:
    """
    Renderiza una página de un PDF a PNG usando PyMuPDF (fitz).
    :param pdf_path: Ruta al PDF de entrada.
    :param page_number_1based: Número de página base-1 a renderizar.
    :param dpi: Resolución objetivo (recomendado 300-400).
    :param tmpdir: Directorio temporal donde guardar la imagen.
    :return: Ruta absoluta al PNG generado.
    """
    # Calcula la matriz de zoom en función de DPI (72 es la base de PDF).
    zoom = dpi / 72.0
    # Crea la matriz de transformación con el zoom indicado.
    mat = fitz.Matrix(zoom, zoom)
    # Abre el documento PDF con PyMuPDF.
    with fitz.open(pdf_path) as doc:
        # Valida que la página solicitada está dentro de rango.
        ensure(1 <= page_number_1based <= len(doc), f"Página fuera de rango: {page_number_1based}")
        # Obtiene el objeto página (PyMuPDF es 0-based internamente).
        page = doc[page_number_1based - 1]
        # Renderiza el contenido a un pixmap (bitmap en memoria).
        pix = page.get_pixmap(matrix=mat, alpha=False)
        # Define la ruta de salida en el directorio temporal.
        out_path = os.path.join(tmpdir, f"page_{page_number_1based:06d}.png")
        # Guarda la imagen como PNG sin canal alfa.
        pix.save(out_path)
        # Devuelve la ruta generada.
        return out_path


# Define una función para aplicar Tesseract a una imagen y producir un PDF buscable.
def tesseract_ocr_image_to_pdf(image_path: str, out_dir: str, lang: str) -> str:
    """
    Ejecuta Tesseract sobre una imagen y genera un PDF con capa de texto.
    :param image_path: Ruta a la imagen (PNG) de la página.
    :param out_dir: Directorio temporal donde depositar el resultado.
    :param lang: Códigos de idioma Tesseract (p. ej., 'spa', 'spa+eng').
    :return: Ruta absoluta al PDF generado por Tesseract.
    """
    # Asegura que el binario 'tesseract' está disponible.
    ensure(which("tesseract") is not None, "Tesseract no está instalado o no está en PATH.")
    # Construye la ruta base de salida (sin extensión) para Tesseract.
    base = os.path.join(out_dir, os.path.splitext(os.path.basename(image_path))[0])
    # Prepara el comando Tesseract con salida en PDF.
    cmd = ["tesseract", image_path, base, "-l", lang, "pdf"]
    # Ejecuta el proceso y captura salida para diagnóstico.
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Determina la ruta final esperada del PDF generado.
    pdf_path = base + ".pdf"
    # Verifica que el PDF se haya producido correctamente.
    ensure(os.path.exists(pdf_path), f"No se generó el PDF de Tesseract para {image_path}")
    # Devuelve la ruta del PDF.
    return pdf_path


# Define una función para unir múltiples PDFs en un único archivo final.
def merge_pdfs(pdf_paths: List[str], output_pdf: str) -> None:
    """
    Une una lista de PDFs (típicamente páginas OCR) en un único PDF final.
    :param pdf_paths: Rutas de PDFs a concatenar en orden.
    :param output_pdf: Ruta del PDF final generado.
    """
    # Crea el objeto PdfMerger para gestionar la concatenación.
    merger = PdfMerger()
    # Añade cada PDF al merger en el orden recibido.
    for p in pdf_paths:
        merger.append(p)
    # Abre el archivo de salida en modo binario de escritura.
    with open(output_pdf, "wb") as f:
        # Escribe el PDF combinado a disco.
        merger.write(f)
    # Cierra recursos del merger de forma explícita.
    merger.close()


# Define una función para ejecutar OCR con OCRmyPDF si está disponible.
def run_ocrmypdf_cli(input_pdf: str, output_pdf: str, lang: str, rotate: bool, deskew: bool,
                     clean: bool, jobs: int, pages: List[int]) -> None:
    """
    Ejecuta el proceso OCR mediante la utilidad de línea de comandos 'ocrmypdf'.
    :param input_pdf: Ruta al PDF de entrada (escaneado).
    :param output_pdf: Ruta al PDF de salida (con OCR).
    :param lang: Idiomas Tesseract (p. ej., 'spa' o 'spa+eng').
    :param rotate: Si es True, intenta auto-rotar páginas.
    :param deskew: Si es True, intenta enderezar páginas.
    :param clean: Si es True, aplica limpieza de fondo/ruido.
    :param jobs: Número de hilos para paralelizar.
    :param pages: Lista de páginas base-1 a procesar (vacío = todas).
    """
    # Asegura que 'ocrmypdf' está disponible en PATH.
    ensure(which("ocrmypdf") is not None, "ocrmypdf no está instalado o no está en PATH.")
    # Asegura que 'tesseract' está disponible, ya que OCRmyPDF lo utiliza.
    ensure(which("tesseract") is not None, "Tesseract no está instalado o no está en PATH.")
    # Verifica Ghostscript según el sistema operativo.
    if platform.system() == "Windows":
        ensure(which("gswin64c") or which("gswin32c"),
               "Ghostscript no está instalado o no está en PATH (gswin64c/gswin32c).")
    else:
        ensure(which("gs") is not None, "Ghostscript no está instalado o no está en PATH (gs).")
    # Verifica 'qpdf', requerido por OCRmyPDF para saneamiento de PDFs.
    ensure(which("qpdf") is not None, "qpdf no está instalado o no está en PATH.")

    # Construye la línea de comandos con parámetros.
    cmd = ["ocrmypdf", "--language", lang, "--output-type", "pdfa"]
    # Añade rotación si procede.
    if rotate:
        cmd += ["--rotate-pages", "--rotate-pages-threshold", "15.0"]
    # Añade enderezado si procede.
    if deskew:
        cmd += ["--deskew"]
    # Añade limpieza/optimización si procede.
    if clean:
        cmd += ["--clean", "--remove-background"]
    # Añade paralelización si se indica.
    if jobs and jobs > 1:
        cmd += ["--jobs", str(jobs)]
    # Si se especifican páginas, conviértelas a formato compacto 'a-b,c'.
    if pages:
        cmd += ["--pages", pages_to_ranges(pages)]
    # Añade rutas de entrada y salida al final.
    cmd += [input_pdf, output_pdf]
    # Ejecuta el comando y espera a que termine.
    subprocess.run(cmd, check=True)


# Define una clase QThread para ejecutar el OCR en segundo plano y no bloquear la GUI.
class OCRWorker(QThread):
    """
    Hilo de trabajo que ejecuta el OCR con la estrategia adecuada (OCRmyPDF o Tesseract por página).
    Emite señales para actualizar el log y el progreso en la interfaz.
    """
    # Señal para emitir mensajes de log en texto plano.
    log_signal = pyqtSignal(str)
    # Señal para actualizar el progreso (0-100).
    progress_signal = pyqtSignal(int)
    # Señal que indica finalización con éxito (ruta de salida).
    done_signal = pyqtSignal(str)
    # Señal que indica error con mensaje explicativo.
    error_signal = pyqtSignal(str)

    # Constructor del hilo con parámetros de ejecución.
    def __init__(self,
                 input_pdf: str,
                 output_pdf: str,
                 lang: str,
                 rotate: bool,
                 deskew: bool,
                 clean: bool,
                 jobs: int,
                 dpi: int,
                 pages_expr: str,
                 force_tesseract: bool):
        # Inicializa la superclase QThread.
        super().__init__()
        # Almacena rutas y parámetros de OCR.
        self.input_pdf = input_pdf
        self.output_pdf = output_pdf
        self.lang = lang
        self.rotate = rotate
        self.deskew = deskew
        self.clean = clean
        self.jobs = jobs
        self.dpi = dpi
        self.pages_expr = pages_expr
        self.force_tesseract = force_tesseract

    # Método principal del hilo: decide estrategia y ejecuta OCR.
    def run(self) -> None:
        """
        Selecciona el motor de OCR (OCRmyPDF si está disponible y no forzado el fallback) o
        usa Tesseract por página como alternativa. Actualiza progreso y logs.
        """
        try:
            # Emite log del inicio.
            self.log_signal.emit("Iniciando OCR...")
            # Intenta abrir el documento para contar páginas.
            with fitz.open(self.input_pdf) as doc:
                total_pages = len(doc)
            # Emite log con total de páginas.
            self.log_signal.emit(f"Total de páginas detectadas: {total_pages}")

            # Parsea expresión de páginas a lista (vacío será interpretado como 'todas').
            pages = parse_pages(self.pages_expr, total_pages=total_pages) if self.pages_expr else []
            # Si la lista está vacía, genera todas.
            if not pages:
                pages = list(range(1, total_pages + 1))

            # Calcula si usaremos OCRmyPDF, sujeto a disponibilidad y preferencia del usuario.
            use_ocrmypdf = (not self.force_tesseract) and (which("ocrmypdf") is not None)
            # Rama de ejecución según motor.
            if use_ocrmypdf:
                # Emite log informando del motor seleccionado.
                self.log_signal.emit("Usando OCRmyPDF (limpieza, rotación y PDF/A).")
                # Ejecuta OCRmyPDF como proceso externo.
                run_ocrmypdf_cli(
                    input_pdf=self.input_pdf,
                    output_pdf=self.output_pdf,
                    lang=self.lang,
                    rotate=self.rotate,
                    deskew=self.deskew,
                    clean=self.clean,
                    jobs=self.jobs,
                    pages=pages
                )
                # Reporta progreso al 100%.
                self.progress_signal.emit(100)
                # Emite señal de finalización.
                self.done_signal.emit(self.output_pdf)
                # Finaliza el método.
                return

            # Si no se usa OCRmyPDF, recurre al modo Tesseract por página.
            self.log_signal.emit("Usando fallback: Tesseract por página (PyMuPDF + Tesseract).")
            # Crea un directorio temporal para imágenes y PDFs intermedios.
            with tempfile.TemporaryDirectory(prefix="ocr_pages_") as tmpdir:
                # Lista para almacenar rutas a PDFs generados por Tesseract.
                part_pdfs: List[str] = []
                # Recorre páginas solicitadas con índice para progreso.
                for idx, pn in enumerate(pages, start=1):
                    # Renderiza la página a imagen PNG con el DPI indicado.
                    img = render_page_to_image(self.input_pdf, pn, self.dpi, tmpdir)
                    # Emite log por página renderizada.
                    self.log_signal.emit(f"Página {pn} renderizada → {os.path.basename(img)}")
                    # Aplica Tesseract a la imagen para generar PDF con texto.
                    pdf_part = tesseract_ocr_image_to_pdf(img, tmpdir, self.lang)
                    # Emite log por página OCR completada.
                    self.log_signal.emit(f"Página {pn} OCR completada → {os.path.basename(pdf_part)}")
                    # Añade la ruta del PDF parcial a la lista.
                    part_pdfs.append(pdf_part)
                    # Calcula y emite el progreso aproximado.
                    progress = int(idx * 100 / max(1, len(pages)))
                    self.progress_signal.emit(progress)

                # Una vez procesadas todas las páginas, une los PDFs parciales.
                merge_pdfs(part_pdfs, self.output_pdf)
                # Emite log final indicando la ruta del PDF de salida.
                self.log_signal.emit(f"PDF final generado: {self.output_pdf}")
                # Asegura que el progreso queda al 100%.
                self.progress_signal.emit(100)
                # Emite señal de finalización con éxito.
                self.done_signal.emit(self.output_pdf)

        except Exception as e:
            # En caso de error, emite el mensaje para mostrar al usuario.
            self.error_signal.emit(str(e))


# Define una clase principal de ventana que contiene todos los controles de la UI.
class OCRWindow(QMainWindow):
    """
    Ventana principal de la aplicación de OCR.
    Permite configurar archivo de entrada/salida, idiomas, opciones de limpieza/rotación,
    rango de páginas, DPI, número de hilos y motor de OCR.
    """
    # Constructor de la ventana con inicialización de widgets y layout.
    def __init__(self) -> None:
        # Inicializa la superclase QMainWindow.
        super().__init__()
        # Establece el título de la ventana de la aplicación.
        self.setWindowTitle("OCR PDF – GUI (PyQt)")
        # Crea el contenedor central tipo QWidget.
        central = QWidget(self)
        # Crea un layout vertical principal para apilar secciones.
        layout = QVBoxLayout(central)

        # ---------------- Archivo de entrada ----------------
        # Crea un layout horizontal para la selección del archivo PDF de entrada.
        in_row = QHBoxLayout()
        # Crea etiqueta para indicar el campo del PDF de entrada.
        in_label = QLabel("PDF de entrada:")
        # Crea un QLineEdit para mostrar/editar la ruta del archivo de entrada.
        self.in_edit = QLineEdit()
        # Permite que el campo de entrada se expanda horizontalmente.
        self.in_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Crea el botón para abrir el diálogo de selección de archivo.
        self.in_btn = QPushButton("Adjuntar archivo")
        # Conecta el clic del botón a la función que abre el diálogo de archivo.
        self.in_btn.clicked.connect(self.browse_input)
        # Añade widgets al layout horizontal.
        in_row.addWidget(in_label)
        in_row.addWidget(self.in_edit)
        in_row.addWidget(self.in_btn)
        # Añade la fila al layout principal.
        layout.addLayout(in_row)

        # ---------------- Archivo de salida ----------------
        # Crea un layout horizontal para la selección del archivo de salida.
        out_row = QHBoxLayout()
        # Crea etiqueta para el campo de salida.
        out_label = QLabel("PDF de salida:")
        # Crea un QLineEdit para mostrar/editar la ruta del archivo de salida.
        self.out_edit = QLineEdit()
        # Permite expansión horizontal también en salida.
        self.out_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Crea el botón para abrir diálogo "Guardar como".
        self.out_btn = QPushButton("Seleccionar…")
        # Conecta el clic del botón a la función de guardar.
        self.out_btn.clicked.connect(self.browse_output)
        # Añade widgets a la fila de salida.
        out_row.addWidget(out_label)
        out_row.addWidget(self.out_edit)
        out_row.addWidget(self.out_btn)
        # Añade la fila al layout principal.
        layout.addLayout(out_row)

        # ---------------- Idiomas (multiselección) ----------------
        # Crea una fila horizontal para el selector de idiomas.
        lang_row = QHBoxLayout()
        # Crea etiqueta para el selector de idiomas.
        lang_label = QLabel("Idioma(s) OCR:")
        # Crea un QComboBox para mostrar opciones de idiomas con check.
        self.lang_combo = QComboBox()
        # Permite que el combo se expanda horizontalmente.
        self.lang_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Inserta elementos con checkboxes (español, inglés, alemán, francés).
        for text, code in [("Español", "spa"), ("Inglés", "eng"), ("Alemán", "deu"), ("Francés", "fra")]:
            self.lang_combo.addItem(text, userData=code)
        # Itera y marca por defecto Español.
        for i in range(self.lang_combo.count()):
            # Obtiene el modelo subyacente y marca el rol de check.
            self.lang_combo.setItemData(i, Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        # Marca español por defecto.
        self.lang_combo.setItemData(0, Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole)
        # Conecta el evento de activación para alternar checks al hacer clic.
        self.lang_combo.activated[int].connect(self.toggle_lang_check)
        # Crea una nota explicativa sobre multiselección.
        self.lang_note = QLabel("Nota: elige varios marcándolos del desplegable (puedes abrir y marcar varias veces).")
        # Establece estilo de la nota para que sea menos intrusiva.
        self.lang_note.setStyleSheet("color: gray; font-size: 11px;")
        # Añade widgets a la fila de idiomas.
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.lang_combo)
        # Crea un pequeño botón de ayuda con icono de interrogación.
        self.help_btn = QToolButton()
        # Asigna un icono estándar de ayuda si está disponible.
        self.help_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
        # Establece un texto accesible para lectores de pantalla.
        self.help_btn.setToolTip("Ayuda / Manual de usuario")
        # Conecta el clic del botón a la función que muestra el manual.
        self.help_btn.clicked.connect(self.show_manual)
        # Añade el botón de ayuda a la fila de idiomas.
        lang_row.addWidget(self.help_btn)
        # Añade la fila y la nota al layout principal.
        layout.addLayout(lang_row)
        layout.addWidget(self.lang_note)

        # ---------------- Opciones de limpieza y rotación ----------------
        # Crea una fila horizontal para las opciones booleanas.
        opt_row = QHBoxLayout()
        # Crea checkbox para limpieza de fondo/ruido.
        self.clean_chk = QCheckBox("Limpiar fondo/ruido")
        # Activa por defecto la limpieza.
        self.clean_chk.setChecked(True)
        # Crea checkbox para auto-rotado de páginas.
        self.rotate_chk = QCheckBox("Rotar páginas automáticamente")
        # Activa por defecto el rotado.
        self.rotate_chk.setChecked(True)
        # Crea checkbox para enderezar (deskew).
        self.deskew_chk = QCheckBox("Enderezar (deskew)")
        # Activa por defecto el enderezado.
        self.deskew_chk.setChecked(True)
        # Crea checkbox para forzar el uso de Tesseract por página.
        self.force_tesseract_chk = QCheckBox("Forzar Tesseract por página (sin OCRmyPDF)")
        # Por defecto, no forzar (dejar que use OCRmyPDF si existe).
        self.force_tesseract_chk.setChecked(False)
        # Añade todos los checkboxes al layout horizontal.
        opt_row.addWidget(self.clean_chk)
        opt_row.addWidget(self.rotate_chk)
        opt_row.addWidget(self.deskew_chk)
        opt_row.addWidget(self.force_tesseract_chk)
        # Añade la fila al layout principal.
        layout.addLayout(opt_row)

        # ---------------- Parámetros numéricos ----------------
        # Crea una fila horizontal para DPI y Jobs.
        num_row = QHBoxLayout()
        # Crea etiqueta para DPI.
        dpi_label = QLabel("DPI (fallback Tesseract):")
        # Crea un QSpinBox para DPI con valores razonables.
        self.dpi_spin = QSpinBox()
        # Establece el mínimo de DPI (150).
        self.dpi_spin.setMinimum(150)
        # Establece el máximo de DPI (600).
        self.dpi_spin.setMaximum(600)
        # Establece el valor por defecto (300).
        self.dpi_spin.setValue(300)
        # Crea etiqueta para número de hilos.
        jobs_label = QLabel("Hilos (jobs):")
        # Crea un QSpinBox para número de hilos.
        self.jobs_spin = QSpinBox()
        # Establece mínimo de 1 hilo.
        self.jobs_spin.setMinimum(1)
        # Establece máximo razonable (32).
        self.jobs_spin.setMaximum(32)
        # Establece valor por defecto en función de CPU disponible.
        default_jobs = max(1, (os.cpu_count() or 2) // 2)
        self.jobs_spin.setValue(default_jobs)
        # Añade widgets al layout de parámetros numéricos.
        num_row.addWidget(dpi_label)
        num_row.addWidget(self.dpi_spin)
        num_row.addSpacing(20)
        num_row.addWidget(jobs_label)
        num_row.addWidget(self.jobs_spin)
        # Añade la fila al layout principal.
        layout.addLayout(num_row)

        # ---------------- Rango de páginas ----------------
        # Crea una fila horizontal para especificar páginas.
        pages_row = QHBoxLayout()
        # Crea etiqueta para el campo de páginas.
        pages_label = QLabel("Nº de páginas / rangos:")
        # Crea QLineEdit para introducir rangos.
        self.pages_edit = QLineEdit()
        # Establece un placeholder aclaratorio.
        self.pages_edit.setPlaceholderText("Ej.: 1-100,150,200- (vacío = todas)")
        # Añade widgets a la fila de páginas.
        pages_row.addWidget(pages_label)
        pages_row.addWidget(self.pages_edit)
        # Añade la fila al layout principal.
        layout.addLayout(pages_row)

        # ---------------- Botón de ejecución ----------------
        # Crea el botón que inicia el proceso de OCR.
        self.run_btn = QPushButton("Iniciar OCR")
        # Conecta el clic a la función de validación y lanzamiento del hilo.
        self.run_btn.clicked.connect(self.start_ocr)
        # Añade el botón al layout principal.
        layout.addWidget(self.run_btn)

        # ---------------- Progreso y log ----------------
        # Crea una barra de progreso para feedback del avance.
        self.progress = QProgressBar()
        # Inicializa el progreso en 0%.
        self.progress.setValue(0)
        # Añade la barra al layout principal.
        layout.addWidget(self.progress)
        # Crea un área de texto para mostrar logs y mensajes del proceso.
        self.log_edit = QTextEdit()
        # Establece el área de logs como solo lectura.
        self.log_edit.setReadOnly(True)
        # Define una altura mínima razonable para el área de log.
        self.log_edit.setMinimumHeight(180)
        # Añade el área de logs al layout principal.
        layout.addWidget(self.log_edit)

        # ---------------- Estado de motores disponibles ----------------
        # Crea una etiqueta para mostrar qué motores están disponibles.
        self.status_label = QLabel("Estado motores: ...")
        # Añade la etiqueta al layout principal.
        layout.addWidget(self.status_label)

        # ---------------- Finaliza configuración de la ventana ----------------
        # Establece el widget central de la ventana.
        self.setCentralWidget(central)
        # Ajusta un tamaño inicial amigable.
        self.resize(900, 640)
        # Actualiza el estado de motores disponibles.
        self.refresh_engine_status()

    # Define una función para alternar el check de un idioma cuando el usuario lo selecciona en el combo.
    def toggle_lang_check(self, index: int) -> None:
        """
        Alterna (marca/desmarca) el estado de check del elemento seleccionado en el combo de idiomas.
        :param index: Índice del elemento activado.
        """
        # Obtiene el estado actual.
        state = self.lang_combo.itemData(index, Qt.ItemDataRole.CheckStateRole)
        # Calcula el nuevo estado (checked ↔ unchecked).
        new_state = Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked
        # Aplica el nuevo estado al elemento.
        self.lang_combo.setItemData(index, new_state, Qt.ItemDataRole.CheckStateRole)

    # Define una función para actualizar la etiqueta de estado de motores disponibles.
    def refresh_engine_status(self) -> None:
        """
        Refresca la información de disponibilidad de motores y dependencias del sistema.
        Muestra si están presentes 'ocrmypdf', 'tesseract', 'ghostscript' y 'qpdf'.
        """
        # Detecta disponibilidad de binarios clave.
        have_ocrmypdf = which("ocrmypdf") is not None
        have_tesseract = which("tesseract") is not None
        have_qpdf = which("qpdf") is not None
        # Ghostscript varía en Windows vs Unix.
        have_gs = which("gswin64c") or which("gswin32c") if platform.system() == "Windows" else which("gs")
        # Construye un texto de estado claro.
        text = (f"ocrmypdf: {'✔' if have_ocrmypdf else '✖'}   "
                f"tesseract: {'✔' if have_tesseract else '✖'}   "
                f"ghostscript: {'✔' if have_gs else '✖'}   "
                f"qpdf: {'✔' if have_qpdf else '✖'}")
        # Actualiza la etiqueta en la UI.
        self.status_label.setText(text)

    # Define una función para abrir un diálogo de selección de archivo de entrada.
    def browse_input(self) -> None:
        """
        Abre un diálogo para seleccionar el PDF de entrada. Al elegirlo, sugiera automáticamente
        una ruta de salida con sufijo '_OCR.pdf' en el mismo directorio si no se ha rellenado.
        """
        # Muestra un diálogo para escoger archivo PDF.
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona PDF de entrada", "", "PDF (*.pdf)")
        # Si el usuario cancela, no hace nada.
        if not path:
            return
        # Coloca la ruta seleccionada en el QLineEdit correspondiente.
        self.in_edit.setText(path)
        # Si no hay salida definida, sugiere una con sufijo "_OCR".
        if not self.out_edit.text().strip():
            base, ext = os.path.splitext(path)
            self.out_edit.setText(base + "_OCR.pdf")

    # Define una función para abrir un diálogo "Guardar como..." para la salida.
    def browse_output(self) -> None:
        """
        Abre un diálogo para seleccionar la ruta del PDF de salida (guardar como).
        """
        # Muestra diálogo para seleccionar o escribir la ruta de salida.
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF OCR como", self.out_edit.text(), "PDF (*.pdf)")
        # Si hay ruta elegida, actualiza el campo de salida.
        if path:
            self.out_edit.setText(path)

    # Define una función para mostrar el manual de usuario detallado en un mensaje modal.
    def show_manual(self) -> None:
        """
        Muestra un manual de usuario con explicación detallada de cada opción y recomendaciones.
        """
        # Redacta el texto del manual con formato simple.
        manual = (
            "Manual de usuario – OCR PDF GUI\n\n"
            "1) PDF de entrada: Selecciona el archivo PDF escaneado que deseas convertir.\n"
            "2) PDF de salida: Ubicación y nombre del PDF con OCR que se generará.\n"
            "3) Idioma(s) OCR: Despliegue y marca uno o varios idiomas (puedes abrir y marcar "
            "varias veces). Códigos: Español(spa), Inglés(eng), Alemán(deu), Francés(fra). "
            "Selecciona los que se correspondan con el idioma del documento para mejorar la precisión.\n"
            "4) Limpiar fondo/ruido: Con OCRmyPDF elimina ruido y fondos grises; mejora legibilidad.\n"
            "5) Rotar páginas automáticamente: Detecta y corrige orientación incorrecta.\n"
            "6) Enderezar (deskew): Corrige inclinaciones leves derivadas del escaneo.\n"
            "7) Forzar Tesseract por página: Si marcas esto, ignorará OCRmyPDF y usará el modo fallback "
            "(renderizado de páginas + Tesseract). Útil si no tienes OCRmyPDF instalado.\n"
            "8) DPI (fallback): Resolución de renderizado para el modo Tesseract por página. 300–400 "
            "suele equilibrar calidad y tamaño.\n"
            "9) Hilos (jobs): Paraleliza el proceso (OCRmyPDF y fallback). No abuses si tu equipo va justo.\n"
            "10) Nº de páginas / rangos: Puedes limitar a un subset. Formatos válidos: '1-100,150,200-'. "
            "Vacío = todas las páginas. Los rangos abiertos (como '200-') usan el total detectado.\n\n"
            "Motores y dependencias:\n"
            "- OCRmyPDF (recomendado): requiere 'tesseract', 'ghostscript' y 'qpdf'.\n"
            "- Fallback Tesseract por página: requiere 'tesseract' y PyMuPDF.\n\n"
            "Buenas prácticas:\n"
            "- Si el documento es muy antiguo o con latinismos, combina idiomas, p. ej. 'spa+lat' "
            "(debes tener el idioma instalado en Tesseract). En la app, los idiomas predefinidos son spa/eng/deu/fra.\n"
            "- Empieza con un rango pequeño para validar calidad antes de procesar todo.\n"
            "- Conserva siempre el PDF original sin OCR como respaldo.\n"
        )
        # Muestra el texto en un cuadro informativo modal.
        QMessageBox.information(self, "Ayuda / Manual", manual)

    # Define una función para recoger opciones de UI y lanzar el OCR en un hilo.
    def start_ocr(self) -> None:
        """
        Valida entradas de usuario, compone el string de idiomas y lanza el proceso OCR en un hilo
        de trabajo no bloqueante, conectando las señales de log, progreso y finalización.
        """
        # Obtiene la ruta de entrada desde la UI.
        in_path = self.in_edit.text().strip()
        # Valida que se haya proporcionado ruta de entrada.
        if not in_path:
            QMessageBox.warning(self, "Falta archivo", "Selecciona un PDF de entrada.")
            return
        # Valida que el archivo existe físicamente.
        if not os.path.exists(in_path):
            QMessageBox.critical(self, "Archivo no encontrado", "La ruta del PDF de entrada no existe.")
            return

        # Obtiene la ruta de salida.
        out_path = self.out_edit.text().strip()
        # Si no hay salida, sugiere una en el mismo directorio con sufijo _OCR.
        if not out_path:
            base, ext = os.path.splitext(in_path)
            out_path = base + "_OCR.pdf"
            self.out_edit.setText(out_path)

        # Construye el string de idiomas según items marcados (combina con '+').
        langs: List[str] = []
        for i in range(self.lang_combo.count()):
            state = self.lang_combo.itemData(i, Qt.ItemDataRole.CheckStateRole)
            if state == Qt.CheckState.Checked:
                langs.append(self.lang_combo.itemData(i))
        # Si no hay ninguno marcado, por seguridad establece 'spa'.
        if not langs:
            langs = ["spa"]
        # Une los códigos con el separador '+' que entiende Tesseract.
        lang_str = "+".join(langs)

        # Lee flags booleanos de la UI.
        clean = self.clean_chk.isChecked()
        rotate = self.rotate_chk.isChecked()
        deskew = self.deskew_chk.isChecked()
        force_tesseract = self.force_tesseract_chk.isChecked()

        # Lee parámetros numéricos de la UI.
        dpi = int(self.dpi_spin.value())
        jobs = int(self.jobs_spin.value())

        # Obtiene la expresión de páginas tal como la introdujo el usuario.
        pages_expr = self.pages_edit.text().strip()

        # Limpia el área de logs y resetea la barra de progreso.
        self.log_edit.clear()
        self.progress.setValue(0)

        # Crea el trabajador OCR en un hilo independiente con los parámetros elegidos.
        self.worker = OCRWorker(
            input_pdf=in_path,
            output_pdf=out_path,
            lang=lang_str,
            rotate=rotate,
            deskew=deskew,
            clean=clean,
            jobs=jobs,
            dpi=dpi,
            pages_expr=pages_expr,
            force_tesseract=force_tesseract
        )

        # Conecta las señales del worker a las funciones de actualización de UI.
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.done_signal.connect(self.ocr_done)
        self.worker.error_signal.connect(self.ocr_error)

        # Deshabilita el botón mientras se procesa para evitar duplicados.
        self.run_btn.setEnabled(False)
        # Inicia el hilo de trabajo.
        self.worker.start()

    # Define una función para añadir mensajes al área de logs con salto de línea.
    def append_log(self, text: str) -> None:
        """
        Añade una línea al log visible para el usuario.
        :param text: Mensaje de información o avance.
        """
        # Inserta el texto seguido de un salto de línea.
        self.log_edit.append(text)

    # Define una función para gestionar la finalización correcta del OCR.
    def ocr_done(self, out_path: str) -> None:
        """
        Maneja la señal de finalización del proceso OCR.
        :param out_path: Ruta al PDF generado con OCR.
        """
        # Rehabilita el botón de ejecución.
        self.run_btn.setEnabled(True)
        # Actualiza el estado de motores (por si se instalaron durante la sesión).
        self.refresh_engine_status()
        # Muestra un cuadro informativo de éxito con la ruta de salida.
        QMessageBox.information(self, "OCR completado", f"Se generó el PDF con OCR:\n{out_path}")

    # Define una función para gestionar errores ocurridos durante el proceso OCR.
    def ocr_error(self, message: str) -> None:
        """
        Maneja la señal de error del proceso OCR.
        :param message: Texto del error producido.
        """
        # Rehabilita el botón de ejecución.
        self.run_btn.setEnabled(True)
        # Añade el error al área de logs para diagnóstico.
        self.append_log(f"[ERROR] {message}")
        # Muestra un cuadro de diálogo crítico con el mensaje de error.
        QMessageBox.critical(self, "Error en OCR", message)


# Punto de entrada principal de la aplicación.
def main() -> int:
    """
    Crea la aplicación Qt, instancia la ventana principal y entra en el loop de eventos.
    :return: Código de salida del proceso (0 = OK).
    """
    # Crea la instancia de QApplication con argumentos de línea de comandos.
    app = QApplication(sys.argv)
    # Crea la ventana principal de OCR.
    win = OCRWindow()
    # Muestra la ventana en pantalla.
    win.show()
    # Ejecuta el bucle principal de eventos de Qt y captura el código de salida.
    code = app.exec()
    # Devuelve el código de salida a sistema.
    return code


# Ejecuta la función main si el archivo se ejecuta como script principal.
if __name__ == "__main__":
    # Llama a la función main y sale con su código de retorno.
    sys.exit(main())
