# -*- coding: utf-8 -*-

from odoo import api, models, fields
from zeep import Client
import requests
import logging
from zeep.exceptions import Fault
from zeep import Client, Transport
from requests.exceptions import ConnectionError as ReqConnectionError, HTTPError, ReadTimeout
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)



class L10nBoWsdl(models.Model):
    _name ="l10n.bo.wsdl"
    _description ="Wsdl (BO)"

    
    name = fields.Char(
        string='Servicio',
        readonly=True,
    )
    
    
    wsdl = fields.Char(
        string='Wsdl',
        required=True
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
    
    service_type = fields.Char(
        string='Tipo servicio',
    )
    
    

    wsdl_operation_ids = fields.One2many(
        string='Operaciones de servicio',
        comodel_name='l10n.bo.operacion.service',
        inverse_name='wsdl_id',
    )
    
    def getWsdl(self):
        return self.wsdl


    def extraer_primera_parte(self, firma):
            # Divide la firma por ':', asumiendo que el formato es "NombreOperación: TipoDatos"
            partes = firma.split(':')
            # Retorna solo la primera parte, que sería el nombre de la operación
            return partes[0].strip() if partes else firma
    
    def get_wsdl_operations(self, L10N_BO_OPERACION_SERVICE, ENVIRONMENT_TYPE, wsdl, SERVICE_TYPE):
        
        client = Client(wsdl)
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                operations = sorted(port.binding._operations.values(), key=lambda operation: operation.name)
                for operation in operations:
                
                    service_id = L10N_BO_OPERACION_SERVICE.search(
                        [
                            ('name','=',operation.name),
                            ('environment_type','=',ENVIRONMENT_TYPE),
                            ('modality_type','=',self.modality_type),
                            ('service_type','=',SERVICE_TYPE),
                            ('input','=',self.extraer_primera_parte(operation.input.signature())),
                            ('output','=',self.extraer_primera_parte(operation.output.signature())),  
                                
                        ], 
                        limit=1
                    )
                    if not service_id:
                        L10N_BO_OPERACION_SERVICE.create(
                            {
                                'name' : operation.name,
                                'input' : self.extraer_primera_parte(operation.input.signature()),
                                'output' : self.extraer_primera_parte(operation.output.signature()),  
                                'environment_type' : ENVIRONMENT_TYPE,
                                'modality_type' : self.modality_type,
                                'service_type' : SERVICE_TYPE,
                                'wsdl_id' : self.id
                            }
                        )
        
    
    

    def operation_service_soap(self):
        L10N_BO_OPERACION_SERVICE = self.env['l10n.bo.operacion.service']
        self.get_wsdl_operations(L10N_BO_OPERACION_SERVICE,self.environment_type,self.wsdl,self.service_type)

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
    





