# Historial de versiones

- 0.01.001
  - Desactivación automática de la limpieza cuando falta `unpaper` para evitar fallos de OCRmyPDF.
  - Incorporación de pruebas automatizadas que validan la construcción del comando de OCRmyPDF.
  - Añadido flujo de GitHub Actions para ejecutar los tests.
  - Documentación inicial del proyecto en `README.md`.
- 0.02.001
  - Visualización del progreso emitido por OCRmyPDF directamente en la barra de progreso de la aplicación.
  - Soporte de arrastrar y soltar archivos PDF sobre la ventana para completar la ruta de entrada.
  - Nuevas pruebas unitarias que validan la interpretación del progreso y el comportamiento sin `unpaper` usando el nuevo flujo.
