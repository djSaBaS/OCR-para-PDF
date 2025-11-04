# Importa typing para describir colecciones utilizadas en las pruebas unitarias.
from typing import List, Optional

# Importa io para simular streams de texto en procesos fingidos.
import io

# Importa pathlib para trabajar con rutas temporales generadas por pytest.
from pathlib import Path

# Importa sys para añadir la raíz del proyecto al path de importaciones.
import sys

# Importa types para crear módulos simulados cuando falten dependencias externas.
import types

# Importa pytest para aprovechar fixtures como monkeypatch y tmp_path.
import pytest

# Importa el módulo subprocess para sustituir la ejecución real de comandos externos.
import subprocess

# Crea un stub mínimo para la dependencia opcional 'fitz' si no está instalada.
if 'fitz' not in sys.modules:
    # Genera un módulo simulado con atributos neutros suficientes para las importaciones.
    sys.modules['fitz'] = types.SimpleNamespace(Matrix=lambda *_args, **_kwargs: None, open=None)

# Crea un stub mínimo para la dependencia opcional 'pypdf' si no está instalada.
if 'pypdf' not in sys.modules:
    # Define una clase ficticia que imita la interfaz básica de PdfMerger.
    class _DummyPdfMerger:
        # Define un método append sin comportamiento.
        def append(self, _path: str) -> None:
            return None

        # Define un método write sin comportamiento.
        def write(self, _fh) -> None:
            return None

        # Define un método close sin comportamiento.
        def close(self) -> None:
            return None

    # Registra el módulo simulado con la clase ficticia.
    sys.modules['pypdf'] = types.SimpleNamespace(PdfMerger=_DummyPdfMerger)

# Crea stubs básicos para los módulos de PyQt6 en entornos de testing sin la librería instalada.
if 'PyQt6' not in sys.modules:
    # Construye módulo raíz vacío para PyQt6.
    pyqt6_root = types.ModuleType('PyQt6')
    # Construye submódulo QtCore con clases y funciones mínimas.
    qtcore_module = types.ModuleType('PyQt6.QtCore')
    # Construye submódulo QtWidgets con clases mínimas.
    qtwidgets_module = types.ModuleType('PyQt6.QtWidgets')

    # Define una clase de hilo ficticia compatible con herencia.
    class _DummyThread:
        # Constructor neutro sin argumentos obligatorios.
        def __init__(self, *_args, **_kwargs) -> None:
            return None

    # Define una señal ficticia con métodos connect/emit sin efecto.
    class _DummySignal:
        # Constructor neutro.
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        # Método connect que ignora los argumentos.
        def connect(self, *_args, **_kwargs) -> None:
            return None

        # Método emit que ignora los argumentos.
        def emit(self, *_args, **_kwargs) -> None:
            return None

    # Define la función pyqtSignal que retorna la señal ficticia.
    def _dummy_pyqt_signal(*_args, **_kwargs) -> _DummySignal:
        return _DummySignal()

    # Prepara el namespace Qt con atributos utilizados en el código.
    qt_namespace = types.SimpleNamespace(
        ItemDataRole=types.SimpleNamespace(CheckStateRole=0),
        CheckState=types.SimpleNamespace(Checked=1)
    )

    # Asigna los símbolos necesarios al submódulo QtCore.
    qtcore_module.Qt = qt_namespace
    qtcore_module.QThread = _DummyThread
    qtcore_module.pyqtSignal = _dummy_pyqt_signal

    # Define una clase base vacía para los widgets.
    class _DummyWidget:
        # Constructor neutro.
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        # Define método setSizePolicy sin efecto.
        def setSizePolicy(self, *_args, **_kwargs) -> None:
            return None

        # Define método clicked con atributo connect compatible.
        @property
        def clicked(self):
            # Retorna un objeto con método connect sin efecto.
            return types.SimpleNamespace(connect=lambda *_args, **_kwargs: None)

        # Define método setText sin efecto.
        def setText(self, *_args, **_kwargs) -> None:
            return None

        # Define método setChecked sin efecto.
        def setChecked(self, *_args, **_kwargs) -> None:
            return None

        # Define método isChecked que retorna False por defecto.
        def isChecked(self) -> bool:
            return False

        # Define método text que retorna cadena vacía.
        def text(self) -> str:
            return ""

        # Define método append para QTextEdit simulado.
        def append(self, *_args, **_kwargs) -> None:
            return None

    # Mapea cada clase usada en el código a la clase ficticia.
    widget_names = [
        'QApplication', 'QMainWindow', 'QWidget', 'QFileDialog', 'QMessageBox', 'QVBoxLayout',
        'QHBoxLayout', 'QLabel', 'QLineEdit', 'QPushButton', 'QCheckBox', 'QSpinBox',
        'QTextEdit', 'QProgressBar', 'QComboBox', 'QSizePolicy', 'QStyle', 'QToolButton'
    ]

    # Asigna la clase ficticia para cada identificador requerido.
    for name in widget_names:
        setattr(qtwidgets_module, name, _DummyWidget)

    # Inserta los submódulos y el módulo raíz en sys.modules.
    sys.modules['PyQt6'] = pyqt6_root
    sys.modules['PyQt6.QtCore'] = qtcore_module
    sys.modules['PyQt6.QtWidgets'] = qtwidgets_module

# Añade la carpeta raíz del proyecto al sys.path para resolver importaciones relativas.
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Importa el módulo principal de la aplicación para acceder a la función bajo prueba.
import ocr_gui


# Define una prueba que garantiza que la limpieza se omite cuando falta 'unpaper'.
def test_run_ocrmypdf_cli_omite_limpieza_sin_unpaper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verifica que run_ocrmypdf_cli evita '--clean' si 'unpaper' no está disponible."""
    # Prepara una lista mutable para almacenar el comando emitido por la función.
    captured_cmd: List[str] = []
    # Prepara una lista para recopilar los mensajes de log enviados desde run_ocrmypdf_cli.
    logs: List[str] = []

    # Define un sustituto de subprocess.Popen que capture el comando sin ejecutarlo.
    class FakeProcess:
        # Constructor que almacena el comando y prepara un stream vacío.
        def __init__(self, cmd, stdout, stderr, text, bufsize, universal_newlines):
            # Registra cada elemento del comando para comprobaciones posteriores.
            captured_cmd.extend(cmd)
            # Expone un stream sin contenido para iterar sin errores.
            self.stdout = io.StringIO("")

        # Define wait para simular finalización correcta.
        def wait(self) -> int:
            return 0

    # Reemplaza subprocess.Popen dentro del módulo con la clase simulada.
    monkeypatch.setattr(ocr_gui.subprocess, "Popen", FakeProcess)

    # Define un sustituto de which que retorna rutas simuladas salvo para 'unpaper'.
    def fake_which(name: str) -> Optional[str]:
        # Si se solicita 'unpaper', se devuelve None para emular su ausencia.
        if name == "unpaper":
            return None
        # Para el resto de dependencias, se devuelve una ruta ficticia válida.
        return f"/usr/bin/{name}"

    # Reemplaza la función which del módulo por el sustituto previamente definido.
    monkeypatch.setattr(ocr_gui, "which", fake_which)

    # Ejecuta la función con limpieza activada y captura el comportamiento resultante.
    ocr_gui.run_ocrmypdf_cli(
        input_pdf=str(tmp_path / "entrada.pdf"),
        output_pdf=str(tmp_path / "salida.pdf"),
        lang="spa",
        rotate=True,
        deskew=True,
        clean=True,
        jobs=2,
        pages=[1, 2],
        log_callback=lambda message: logs.append(message)
    )

    # Comprueba que el comando no incluye las opciones '--clean' ni '--remove-background'.
    assert "--clean" not in captured_cmd
    assert "--remove-background" not in captured_cmd
    # Verifica que se registró un mensaje avisando de la ausencia de 'unpaper'.
    assert any("unpaper" in entry for entry in logs)


# Define una prueba que verifica la propagación del progreso desde OCRmyPDF.
def test_run_ocrmypdf_cli_reporta_progreso(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Comprueba que run_ocrmypdf_cli interpreta las líneas de progreso y emite porcentajes."""
    # Prepara listas para capturar comando, logs y porcentaje de progreso.
    captured_cmd: List[str] = []
    logs: List[str] = []
    progress: List[int] = []

    # Genera un stream con líneas similares a las que emite OCRmyPDF.
    sample_output = """    1: page 1 of 4\n    2: page 2 of 4\n    3: page 3 of 4\n    4: page 4 of 4\n"""

    # Define un proceso simulado que produce el stream anterior.
    class FakeProcess:
        # Constructor que almacena el comando y ofrece el stream.
        def __init__(self, cmd, stdout, stderr, text, bufsize, universal_newlines):
            # Registra el comando para su inspección.
            captured_cmd.extend(cmd)
            # Usa StringIO para emular stdout textual línea a línea.
            self.stdout = io.StringIO(sample_output)

        # Define wait para indicar finalización correcta.
        def wait(self) -> int:
            return 0

    # Sustituye subprocess.Popen por la clase simulada.
    monkeypatch.setattr(ocr_gui.subprocess, "Popen", FakeProcess)

    # Define un which simulado que declara disponibles todas las dependencias.
    monkeypatch.setattr(ocr_gui, "which", lambda name: f"/usr/bin/{name}")

    # Ejecuta la función capturando logs y progreso.
    ocr_gui.run_ocrmypdf_cli(
        input_pdf=str(tmp_path / "entrada.pdf"),
        output_pdf=str(tmp_path / "salida.pdf"),
        lang="spa",
        rotate=False,
        deskew=False,
        clean=False,
        jobs=1,
        pages=[1, 2, 3, 4],
        log_callback=lambda message: logs.append(message),
        progress_callback=lambda value: progress.append(value)
    )

    # Asegura que el comando emitido contiene la ruta de entrada y salida esperada.
    assert str(tmp_path / "entrada.pdf") in captured_cmd
    assert str(tmp_path / "salida.pdf") in captured_cmd
    # Comprueba que los logs incluyen las líneas del stream simulado.
    assert any("page 3 of 4" in entry for entry in logs)
    # Verifica que se recibió al menos un valor de progreso y que finaliza al 100%.
    assert progress, "Se esperaba recibir actualizaciones de progreso"
    assert progress[-1] == 100
