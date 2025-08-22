import pandas as pd

def exportar_a_excel(lista_datos_cfdi, ruta_salida):
    """
    Toma una lista con los datos de varios CFDI y la exporta a un
    archivo Excel con dos hojas: una para datos generales y otra para conceptos.
    """
    print(f"\n--- Iniciando la exportación a Excel ---")
    print(f"Se exportarán datos de {len(lista_datos_cfdi)} CFDI.")

    filas_general = []
    filas_conceptos = []
    filas_documentos_relacionados = []

    for datos in lista_datos_cfdi:
        # --- Fila para la hoja de datos generales ---
        uuid = datos.get('timbre', {}).get('uuid', 'SIN_UUID')
        
        fila_gen = {
            'UUID': uuid,
            'Archivo': datos.get('archivo'),
            'Fecha': datos.get('datos_generales', {}).get('fecha'),
            'Tipo Comprobante': datos.get('datos_generales', {}).get('tipo_comprobante'),
            'Serie': datos.get('datos_generales', {}).get('serie'),
            'Folio': datos.get('datos_generales', {}).get('folio'),
            'Subtotal': datos.get('datos_generales', {}).get('subtotal'),
            'Total': datos.get('datos_generales', {}).get('total'),
            'Moneda': datos.get('datos_generales', {}).get('moneda'),
            'Emisor RFC': datos.get('emisor', {}).get('rfc'),
            'Emisor Nombre': datos.get('emisor', {}).get('nombre'),
            'Receptor RFC': datos.get('receptor', {}).get('rfc'),
            'Receptor Nombre': datos.get('receptor', {}).get('nombre'),
            'Uso CFDI': datos.get('receptor', {}).get('uso_cfdi')
        }
        filas_general.append(fila_gen)

        # --- Filas para la hoja de conceptos ---
        for concepto in datos.get('conceptos', []):
            fila_con = {
                'UUID_CFDI': uuid, # Para relacionar con la factura principal
                'ClaveProdServ': concepto.get('clave_prod_serv'),
                'Cantidad': concepto.get('cantidad'),
                'ClaveUnidad': concepto.get('clave_unidad'),
                'Descripcion': concepto.get('descripcion'),
                'ValorUnitario': concepto.get('valor_unitario'),
                'Importe': concepto.get('importe'),
                'Descuento': concepto.get('descuento')
            }
            filas_conceptos.append(fila_con)

        # --- Filas para la hoja de documentos relacionados (complemento de pagos) ---
        if 'pagos' in datos.get('complementos', {}):
            for pago in datos['complementos']['pagos']:
                uuid_pago = pago.get('uuid', uuid) # Usar UUID del CFDI si el pago no tiene uno propio
                for doc_rel in pago.get('documentos_relacionados', []):
                    fila_doc_rel = {
                        'UUID_CFDI': uuid, # UUID del CFDI principal
                        'UUID_Pago': uuid_pago, # UUID del pago si aplica
                        'IdDocumento': doc_rel.get('id_documento'),
                        'Serie': doc_rel.get('serie'),
                        'Folio': doc_rel.get('folio'),
                        'MonedaDR': doc_rel.get('moneda'),
                        'ImpSaldoAnt': doc_rel.get('imp_saldo_ant'),
                        'ImpPagado': doc_rel.get('imp_pagado'),
                        'ImpSaldoInsoluto': doc_rel.get('imp_saldo_insoluto')
                    }
                    filas_documentos_relacionados.append(fila_doc_rel)

    if not filas_general:
        print("No hay datos generales para exportar.")
        return

    try:
        # Crear los DataFrames de pandas
        df_general = pd.DataFrame(filas_general)
        df_conceptos = pd.DataFrame(filas_conceptos)
        df_documentos_relacionados = pd.DataFrame(filas_documentos_relacionados)

        # Escribir a Excel usando ExcelWriter para crear múltiples hojas
        with pd.ExcelWriter(ruta_salida, engine='openpyxl') as writer:
            df_general.to_excel(writer, sheet_name='CFDI_General', index=False)
            df_conceptos.to_excel(writer, sheet_name='Conceptos', index=False)
            if not df_documentos_relacionados.empty:
                df_documentos_relacionados.to_excel(writer, sheet_name='Documentos Relacionados', index=False)
        
        print(f"✅ ¡Éxito! Archivo guardado en: {ruta_salida}")

    except Exception as e:
        print(f"❌ Error al escribir el archivo Excel: {e}")
