import xml.etree.ElementTree as ET
import os
from datetime import datetime

class CFDIExtractor:
    """Extractor robusto para CFDI que maneja casos reales"""
    
    def __init__(self):
        self.namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'cfdi33': 'http://www.sat.gob.mx/cfd/3',  # Para CFDI 3.3
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
            'pago20': 'http://www.sat.gob.mx/Pagos20',
            'pago10': 'http://www.sat.gob.mx/Pagos',  # Versión anterior
            'nomina12': 'http://www.sat.gob.mx/nomina12',
            'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31'
        }
    
    def cargar_cfdi(self, archivo_path):
        """Carga un CFDI desde archivo con validaciones"""
        try:
            if not os.path.exists(archivo_path):
                raise FileNotFoundError(f"No se encontró el archivo: {archivo_path}")
            
            tree = ET.parse(archivo_path)
            root = tree.getroot()
            
            # Detectar versión automáticamente
            version = self.detectar_version(root)
            print(f"📄 CFDI Versión {version} cargado correctamente")
            
            return root
            
        except ET.ParseError as e:
            print(f"❌ Error al parsear XML: {e}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None
    
    def detectar_version(self, root):
        """Detecta automáticamente la versión del CFDI"""
        version = root.get('Version') or root.get('version')
        if version:
            return version
        
        # Si no tiene atributo version, detectar por namespace
        if 'cfd/4' in root.tag:
            return "4.0"
        elif 'cfd/3' in root.tag:
            return "3.3"
        else:
            return "Desconocida"
    
    def extraer_datos_generales(self, root):
        """Extrae información básica del comprobante"""
        datos = {
            'version': root.get('Version'),
            'serie': root.get('Serie', 'Sin Serie'),
            'folio': root.get('Folio', 'Sin Folio'),
            'fecha': root.get('Fecha'),
            'subtotal': float(root.get('SubTotal', 0)),
            'total': float(root.get('Total', 0)),
            'moneda': root.get('Moneda', 'MXN'),
            'tipo_comprobante': self.traducir_tipo_comprobante(root.get('TipoDeComprobante')),
            'metodo_pago': root.get('MetodoPago', 'No especificado'),
            'lugar_expedicion': root.get('LugarExpedicion')
        }
        return datos
    
    def traducir_tipo_comprobante(self, tipo):
        """Traduce los códigos de tipo de comprobante"""
        tipos = {
            'I': 'Ingreso (Factura)',
            'E': 'Egreso (Nota de Crédito)',
            'P': 'Pago',
            'N': 'Nómina',
            'T': 'Traslado'
        }
        return tipos.get(tipo, f'Desconocido ({tipo})')
    
    def extraer_emisor(self, root):
        """Extrae datos del emisor con validaciones"""
        emisor = root.find('cfdi:Emisor', self.namespaces)
        if emisor is None:
            # Intentar con versión 3.3
            emisor = root.find('cfdi33:Emisor', self.namespaces)
        
        if emisor is not None:
            return {
                'rfc': emisor.get('Rfc'),
                'nombre': emisor.get('Nombre', 'Sin Nombre'),
                'regimen_fiscal': emisor.get('RegimenFiscal')
            }
        return {'rfc': None, 'nombre': None, 'regimen_fiscal': None}
    
    def extraer_receptor(self, root):
        """Extrae datos del receptor"""
        receptor = root.find('cfdi:Receptor', self.namespaces)
        if receptor is None:
            receptor = root.find('cfdi33:Receptor', self.namespaces)
        
        if receptor is not None:
            return {
                'rfc': receptor.get('Rfc'),
                'nombre': receptor.get('Nombre', 'Sin Nombre'),
                'uso_cfdi': receptor.get('UsoCFDI'),
                'regimen_fiscal': receptor.get('RegimenFiscalReceptor'),
                'domicilio_fiscal': receptor.get('DomicilioFiscalReceptor')
            }
        return {}
    
    def extraer_conceptos(self, root):
        """Extrae todos los conceptos con sus detalles"""
        conceptos = root.findall('cfdi:Conceptos/cfdi:Concepto', self.namespaces)
        if not conceptos:
            conceptos = root.findall('cfdi33:Conceptos/cfdi33:Concepto', self.namespaces)
        
        lista_conceptos = []
        for concepto in conceptos:
            concepto_data = {
                'clave_prod_serv': concepto.get('ClaveProdServ'),
                'cantidad': float(concepto.get('Cantidad', 0)),
                'clave_unidad': concepto.get('ClaveUnidad'),
                'descripcion': concepto.get('Descripcion'),
                'valor_unitario': float(concepto.get('ValorUnitario', 0)),
                'importe': float(concepto.get('Importe', 0)),
                'descuento': float(concepto.get('Descuento', 0)),
                'objeto_imp': concepto.get('ObjetoImp')
            }
            
            # Extraer impuestos del concepto
            concepto_data['impuestos'] = self.extraer_impuestos_concepto(concepto)
            lista_conceptos.append(concepto_data)
        
        return lista_conceptos
    
    def extraer_impuestos_concepto(self, concepto):
        """Extrae impuestos específicos de un concepto"""
        impuestos = {'traslados': [], 'retenciones': []}
        
        # Buscar impuestos trasladados
        traslados = concepto.findall('.//cfdi:Traslado', self.namespaces)
        for traslado in traslados:
            impuestos['traslados'].append({
                'base': float(traslado.get('Base', 0)),
                'impuesto': traslado.get('Impuesto'),
                'tipo_factor': traslado.get('TipoFactor'),
                'tasa_cuota': float(traslado.get('TasaOCuota', 0)),
                'importe': float(traslado.get('Importe', 0))
            })
        
        # Buscar retenciones (si las hay)
        retenciones = concepto.findall('.//cfdi:Retencion', self.namespaces)
        for retencion in retenciones:
            impuestos['retenciones'].append({
                'base': float(retencion.get('Base', 0)),
                'impuesto': retencion.get('Impuesto'),
                'tipo_factor': retencion.get('TipoFactor'),
                'tasa_cuota': float(retencion.get('TasaOCuota', 0)),
                'importe': float(retencion.get('Importe', 0))
            })
        
        return impuestos
    
    def extraer_timbre(self, root):
        """Extrae información del timbre fiscal digital"""
        timbre = root.find('.//tfd:TimbreFiscalDigital', self.namespaces)
        if timbre is not None:
            return {
                'uuid': timbre.get('UUID'),
                'fecha_timbrado': timbre.get('FechaTimbrado'),
                'rfc_prov_certif': timbre.get('RfcProvCertif'),
                'no_certificado_sat': timbre.get('NoCertificadoSAT')
            }
        return {}
    
    def extraer_complementos(self, root):
        """Detecta y extrae diferentes tipos de complementos"""
        complementos = {}
        
        # Complemento de Pagos
        pagos = root.find('.//pago20:Pagos', self.namespaces)
        if not pagos:
            pagos = root.find('.//pago10:Pagos', self.namespaces)
        
        if pagos is not None:
            complementos['pagos'] = self.extraer_complemento_pagos(pagos)
        
        # Aquí puedes agregar otros complementos como:
        # - Nómina
        # - Comercio Exterior  
        # - Carta Porte
        # etc. 
        
        return complementos
    
    def extraer_complemento_pagos(self, pagos):
        """Extrae detalles del complemento de pagos"""
        datos_pagos = []
        
        # Buscar todos los pagos
        lista_pagos = pagos.findall('.//pago20:Pago', self.namespaces)
        if not lista_pagos:
            lista_pagos = pagos.findall('.//pago10:Pago', self.namespaces)
        
        for pago in lista_pagos:
            pago_data = {
                'fecha_pago': pago.get('FechaPago'),
                'forma_pago': pago.get('FormaDePagoP'),
                'moneda': pago.get('MonedaP'),
                'monto': float(pago.get('Monto', 0)),
                'documentos_relacionados': []
            }
            
            # Documentos relacionados con este pago
            docs = pago.findall('.//pago20:DoctoRelacionado', self.namespaces)
            if not docs:
                docs = pago.findall('.//pago10:DoctoRelacionado', self.namespaces)
            
            for doc in docs:
                pago_data['documentos_relacionados'].append({
                    'id_documento': doc.get('IdDocumento'),
                    'serie': doc.get('Serie'),
                    'folio': doc.get('Folio'),
                    'moneda': doc.get('MonedaDR'),
                    'imp_saldo_ant': float(doc.get('ImpSaldoAnt', 0)),
                    'imp_pagado': float(doc.get('ImpPagado', 0)),
                    'imp_saldo_insoluto': float(doc.get('ImpSaldoInsoluto', 0))
                })
            
            datos_pagos.append(pago_data)
        
        return datos_pagos
    
    def procesar_cfdi_completo(self, archivo_path):
        """Procesa un CFDI completo y retorna toda la información"""
        print(f"🔍 Procesando: {archivo_path}")
        print("=" * 50)
        
        root = self.cargar_cfdi(archivo_path)
        if root is None:
            return None
        
        resultado = {
            'archivo': archivo_path,
            'fecha_procesamiento': datetime.now().isoformat(),
            'datos_generales': self.extraer_datos_generales(root),
            'emisor': self.extraer_emisor(root),
            'receptor': self.extraer_receptor(root),
            'conceptos': self.extraer_conceptos(root),
            'timbre': self.extraer_timbre(root),
            'complementos': self.extraer_complementos(root)
        }
        
        # Mostrar resumen
        self.mostrar_resumen(resultado)
        
        return resultado
    
    def mostrar_resumen(self, datos):
        """Muestra un resumen amigable de los datos extraídos"""
        print(f"📊 RESUMEN DEL CFDI")
        print(f"UUID: {datos['timbre'].get('uuid', 'No disponible')}")
        print(f"Tipo: {datos['datos_generales']['tipo_comprobante']}")
        print(f"Serie-Folio: {datos['datos_generales']['serie']}-{datos['datos_generales']['folio']}")
        print(f"Total: ${datos['datos_generales']['total']:,.2f} {datos['datos_generales']['moneda']}")
        print(f"Emisor: {datos['emisor']['nombre']} ({datos['emisor']['rfc']})")
        print(f"Receptor: {datos['receptor'].get('nombre', 'Sin nombre')} ({datos['receptor'].get('rfc')})")
        print(f"Conceptos: {len(datos['conceptos'])} artículos/servicios")
        
        if datos['complementos']:
            print(f"Complementos: {', '.join(datos['complementos'].keys())}")
        
        print("✅ Procesamiento completado\n")
