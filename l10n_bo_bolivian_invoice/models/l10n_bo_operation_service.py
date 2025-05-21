# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from zeep import Client
import requests
import logging
from zeep.exceptions import Fault
from zeep import Client, Transport
from requests.exceptions import ConnectionError as ReqConnectionError, HTTPError, ReadTimeout

_logger = logging.getLogger(__name__)


class L10nBoOperationService(models.Model):
    _name = 'l10n.bo.operacion.service'
    _description = 'Operaciones de servicio (BO)'


    
    name = fields.Char(
        string='Nombre',
        readonly=True 
    )
    
    
    input = fields.Char(
        string='Entrada',
        readonly=True 
        
    )

    
    output = fields.Char(
        string='Salida',
        readonly=True 
    )
    
    environment_type = fields.Selection(
        string='Tipo entorno',
        selection=[('1', 'Producción'), ('2', 'Pruebas')],
        readonly=True 
    )

    
    modality_type = fields.Selection(
        string='Tipo modalidad',
        selection=[('1', 'Electrónica'), ('2', 'Computarizada')],
        readonly=True, 
        help='Dejar vacio para ambas modalidades.'
    )
    
    
    
    service_type = fields.Selection(
        string='Tipo servicio',
        selection=[
            ('FacturacionSincronizacion', 'Facturacion sincronizacion'),
            ('ServicioFacturacionCompraVenta', 'Facturacion Compra-Venta'), 
            ('FacturacionCodigos', 'Facturacion codigos'), 
            ('FacturacionOperaciones', 'Facturacion operaciones'), 
            ('ServicioFacturacionDocumentoAjuste', 'Nota de credito debito'),
            ('ServicioFacturacionElectronica', 'Facturacion electronica'),
            ('ServicioFacturacionComputarizada', 'Facturacion computarizada'),
            
        ]
    )
    
    
    wsdl_id = fields.Many2one(
        string='Wsdl',
        comodel_name='l10n.bo.wsdl',
        ondelete='restrict',
    )
    
    def getWsdl(self):
        if self.wsdl_id:
            return self.wsdl_id.getWsdl()
        raise UserError(f'El metodo: {self.name} no tiene un servicio wsdl')
    



    def process_soap_siat(self, endpoint, token, params, method):
        headers = {
            "apikey": f"TokenApi {token}"
        }
        session = requests.Session()
        session.headers.update(headers)

        try:
            transport = Transport(session=session)
            client = Client(wsdl=endpoint, transport=transport)
            call_wsdl = getattr(client.service, method)
            soap_response = call_wsdl(**params)
            response = {'success': True, 'data': soap_response}
        except Fault as fault:
            response = {'success': False, 'error': fault.message}
        except ReqConnectionError as connectionError:
            response = {'success': False, 'error': connectionError}
        except HTTPError as httpError:
            response = {'success': False, 'error': httpError}
        except TypeError as typeError:
            response = {'success': False, 'error': typeError}
        except ReadTimeout as timeOut:
            response = {'success': False, 'error': timeOut}
        return response
    