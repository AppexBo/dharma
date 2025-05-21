# -*- coding: utf-8 -*-

class SiatSoapMethod:
    # Metodos para Sincronizar el CUFD Y CUIS
    CUIS = 'cuis'
    CUFD = 'cufd'
    MASSIVE_CUIS = 'cuisMasivo'
    MASSIVE_CUFD = 'cufdMasivo'
    VERIFY_NIT = 'verificarNit'
    CREATE_POS = 'registroPuntoVenta'
    SELECT_POS = 'consultaPuntoVenta'
    DELETE_POS = 'cierrePuntoVenta'


    # Metodos para Sincronizar los Catalogos
    SYNC_ACTIVITIES = ('sincronizarActividades', 'Códigos de Actividades')
    SYNC_DATETIME = ('sincronizarFechaHora', 'Fecha y Hora')
    SYNC_ACTIVITIES_DOCUMENT_SECTOR = (
        'sincronizarListaActividadesDocumentoSector', 'Códigos de Actividades Documento Sector')
    SYNC_LEGEND_CODE_INVOICES = ('sincronizarListaLeyendasFactura', 'Códigos de Leyendas Facturas')
    SYNC_MESSAGES_SERVICE = ('sincronizarListaMensajesServicios', 'Códigos de Mensajes Servicios')
    SYNC_PRODUCT_SERVICE = ('sincronizarListaProductosServicios', 'Códigos de Productos y Servicios')
    SYNC_EVENT_SIGNIFICANT = ('sincronizarParametricaEventosSignificativos', 'Códigos de Eventos Significativos')
    SYNC_REASON_CANCELLATION = ('sincronizarParametricaMotivoAnulacion', 'Códigos de Motivos Anulación')
    SYNC_ORIGIN_COUNTRY = ('sincronizarParametricaPaisOrigen', 'Códigos de País Origen')
    SYNC_TYPE_DOCUMENT_IDENTITY = (
        'sincronizarParametricaTipoDocumentoIdentidad', 'Códigos de Tipo Documento Identidad')
    SYNC_TYPE_DOCUMENT_SECTOR = ('sincronizarParametricaTipoDocumentoSector', 'Códigos de Tipo Documento Sector')
    SYNC_TYPE_EMISION = ('sincronizarParametricaTipoEmision', 'Códigos de Tipo Emisión')
    SYNC_TYPE_ROOM = ('sincronizarParametricaTipoHabitacion', 'Códigos de Tipo Habitación')
    SYNC_TYPE_METHOD_PAYMENT = ('sincronizarParametricaTipoMetodoPago', 'Códigos de Tipo Método Pago')
    SYNC_TYPE_CURRENCY = ('sincronizarParametricaTipoMoneda', 'Códigos de Tipo Moneda')
    SYNC_TYPE_POINT_SALE = ('sincronizarParametricaTipoPuntoVenta', 'Códigos de Tipo Punto de Venta')
    SYNC_TYPE_INVOICE = ('sincronizarParametricaTiposFactura', 'Códigos de Tipo Factura')
    SYNC_UNIT_MEASUREMENT = ('sincronizarParametricaUnidadMedida', 'Códigos de Unidad de Medida')
    
    SYNC_ALL_TUPLE = [
        SYNC_ACTIVITIES,
        SYNC_DATETIME,
        SYNC_ACTIVITIES_DOCUMENT_SECTOR,
        SYNC_LEGEND_CODE_INVOICES,
        SYNC_MESSAGES_SERVICE,
        SYNC_PRODUCT_SERVICE,
        SYNC_EVENT_SIGNIFICANT,
        SYNC_REASON_CANCELLATION,
        SYNC_ORIGIN_COUNTRY,
        SYNC_TYPE_DOCUMENT_IDENTITY,
        SYNC_TYPE_DOCUMENT_SECTOR,
        SYNC_TYPE_EMISION,
        SYNC_TYPE_ROOM,
        SYNC_TYPE_METHOD_PAYMENT,
        SYNC_TYPE_CURRENCY,
        SYNC_TYPE_POINT_SALE,
        SYNC_TYPE_INVOICE,
        SYNC_UNIT_MEASUREMENT
    ]

    
    # Version del SIAT Electronico
    SIAT_VERSION = 'bo_siat'
    # Recepcion de Factura
    RECEPTION_INVOICE = 'recepcionFactura'
    # Anulacion de Factura
    CANCEL_INVOICE = 'anulacionFactura'
    # Recepcion de Ajuste , Nota de Credito o Debito
    RECEPTION_CREDIT_DEBIT = 'recepcionDocumentoAjuste'
    # Recepcion de Ajuste , Nota de Credito o Debito
    CANCEL_CREDIT_DEBIT = 'anulacionDocumentoAjuste'
    # Recepcion de Evento Significativo
    ADD_SIGNIFICABT_EVENT = 'registroEventoSignificativo'

       # Metodos de Obtencion de WSDL
    WSDLS = {
        '1': {
            '1': 'get_wsdl_invoicing_binding',
            '2': 'get_wsdl_invoicing_binding',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reversion': 'reversionAnulacionFactura',
            'method_reception_masive': 'recepcionMasivaFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive': 'validacionRecepcionMasivaFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            'name_field': 'SolicitudServicioRecepcionFactura',

        },
        '2': {
            '1': 'get_wsdl_electronic_invoice',
            '2': 'get_wsdl_electronic_invoice',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reversion': 'reversionAnulacionFactura',
            'method_reception_masive': 'recepcionMasivaFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive': 'validacionRecepcionMasivaFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            'name_field': 'SolicitudServicioRecepcionFactura',

        },
        '3': {
            '1': 'get_wsdl_commercial_export',
            '2': 'get_wsdl_commercial_export_computerized',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reception_masive': 'recepcionMasivaFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive': 'validacionRecepcionMasivaFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            'name_field': 'SolicitudServicioRecepcionFactura'

        },
        '8': {
            '1': 'get_wsdl_electronic_invoice',
            '2': 'get_wsdl_electronic_invoice',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reversion': 'reversionAnulacionFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            
        },
        '11': {
            '1': 'get_wsdl_electronic_invoice',
            '2': 'get_wsdl_electronic_invoice',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reversion': 'reversionAnulacionFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            
        },
        '24': {
            '1': 'get_wsdl_credit_debit',
            '2': 'get_wsdl_credit_debit',
            'method_reception': RECEPTION_CREDIT_DEBIT,
            'method_cancel': CANCEL_CREDIT_DEBIT,
            'method_reversion': 'reversionAnulacionDocumentoAjuste',
        },
        '28': {
            '1': 'get_wsdl_electronic_invoice',
            '2': 'get_wsdl_electronic_invoice',
            'method_reception': RECEPTION_INVOICE,
            'method_cancel': CANCEL_INVOICE,
            'method_reversion': 'reversionAnulacionFactura',
            'method_reception_masive_package': 'recepcionPaqueteFactura',
            'method_validation_masive_package': 'validacionRecepcionPaqueteFactura',
            
        },
        
        '29': {
            '1': 'get_wsdl_credit_debit',
            '2': 'get_wsdl_credit_debit',
            'method_reception': RECEPTION_CREDIT_DEBIT,
            'method_cancel': CANCEL_CREDIT_DEBIT,
            'name_field': 'SolicitudServicioRecepcionDocumentoAjuste'
        },
        'significant.event': {
            '1': 'get_wsdl_operations',
            '2': 'get_wsdl_operations',
            'method_reception': ADD_SIGNIFICABT_EVENT,
            'method_cancel': '',
            'name_field': 'SolicitudEventoSignificativo'
        },
        'server.verification': {
            '1': 'get_wsdl_operations',
            '2': 'get_wsdl_operations',
            'method_verification': 'verificarComunicacion'
        }
    }
