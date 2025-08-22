import os
from cfdi_tool.extractor import CFDIExtractor
from cfdi_tool.excel_writer import exportar_a_excel # Usaremos esto después

# Rutas relativas al script main.py
CARPETA_INPUT = 'input_cfdi'
CARPETA_OUTPUT = 'output_excel'

def main():
    """
    Función principal que orquesta el proceso de extracción.
    """
    print("--- Iniciando el proceso de extracción de CFDI ---")
    
    # Construir rutas absolutas basadas en la ubicación de este script
    script_dir = os.path.dirname(__file__)
    input_dir = os.path.abspath(os.path.join(script_dir, CARPETA_INPUT))
    output_dir = os.path.abspath(os.path.join(script_dir, CARPETA_OUTPUT))

    if not os.path.isdir(input_dir):
        print(f"Error: La carpeta de entrada '{input_dir}' no existe o no es un directorio.")
        return

    if not os.path.exists(output_dir):
        print(f"La carpeta de salida '{output_dir}' no existe. Creándola...")
        os.makedirs(output_dir)

    # Encontrar todos los archivos XML
    archivos_xml = [f for f in os.listdir(input_dir) if f.lower().endswith('.xml')]
    
    if not archivos_xml:
        print(f"No se encontraron archivos .xml en '{input_dir}'.")
        return

    print(f"Se encontraron {len(archivos_xml)} CFDI para procesar.")

    extractor = CFDIExtractor()
    todos_los_datos = []

    for nombre_archivo in archivos_xml:
        ruta_completa = os.path.join(input_dir, nombre_archivo)
        datos_cfdi = extractor.procesar_cfdi_completo(ruta_completa)
        if datos_cfdi:
            todos_los_datos.append(datos_cfdi)
    
    if not todos_los_datos:
        print("No se pudo extraer información de ningún archivo CFDI.")
        return

    print(f"\n✅ Se procesaron {len(todos_los_datos)} CFDI con éxito.")
    
    # --- Guardar en Excel ---
    nombre_excel = "reporte_cfdi.xlsx"
    ruta_salida_excel = os.path.join(output_dir, nombre_excel)
    exportar_a_excel(todos_los_datos, ruta_salida_excel)

if __name__ == '__main__':
    main()
