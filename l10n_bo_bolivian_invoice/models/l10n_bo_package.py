# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError
from io import BytesIO
import tarfile
import io
import hashlib
import base64
import gzip
import pytz

import logging
_logger = logging.getLogger(__name__)


class L10nBoPackage(models.Model):
    _name = 'l10n.bo.package'
    _description = 'Envio de paquetes (BO)'
    _order = 'id desc'

    
    name = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        help='La fecha de validacion de paquetes puede ser maximo hasta 48hrs despues de la fecha de finalizacion del evento.'
    )
    
    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
        required=True
    )
    
    @api.onchange('pos_id')
    def _onchange_pos_id(self):
        if self.pos_id and self.pos_id.event_id:
            self.write({'event_id' : self.pos_id.event_id.id}) 
    
    

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    document_type_id = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.document.type',
    )

    
    event_id = fields.Many2one(
        string='Evento',
        comodel_name='significant.event',
        required=True
    )
    
    
    success = fields.Boolean(
        string='Realizado',
        readonly=True 
    )
    
    
    description_code = fields.Char(
        string='Codigo descripcion',
        readonly=True 
    )

    
    state_code = fields.Integer(
        string='Codigo estado',
        readonly=True 
    )
    
    
    validation_code = fields.Char(
        string='Codigo validacion',
    )

    reception_code = fields.Char(
        string='Codigo recepcion',
    )

    

    
    transaccion = fields.Boolean(
        string='Transacción envio',
        readonly=True 
    )

    package_invoice_line_ids = fields.One2many(
        string='Lineas facturas paquetes',
        comodel_name='l10n.bo.package.invoice.line',
        inverse_name='package_id',
    )

    package_line_ids = fields.One2many(
        string='Lineas de paquete',
        comodel_name='l10n.bo.package.line',
        inverse_name='package_id',
    )
    

    def get_invoices(self):
        PARAMS = [
                ('codigoEstado','in',[0,'0',False]),
                ('state','=','posted'),
                ('pos_id.code','=',self.pos_id.getCode()),
                ('company_id','=',self.company_id.id),
                #('document_type_id','!=',False),
                ('invoice_date_edi','>=',self.event_id.date_init),
                ('invoice_date_edi','<=',self.event_id.date_end),
                ('edi_bo_invoice','=',True),
                
            ]
        invoice_ids = self.env['account.move'].search(PARAMS)
        #_logger.info(f"{invoice_ids}")

        for invoice in invoice_ids:
            #_logger.info(f"Factura: {invoice.name}, Fecha factura: {invoice.invoice_date_edi} - fecha eventi inicio: {self.event_id.date_init}")
            if invoice.id not in [line.name.id for line in self.package_invoice_line_ids]:
                self.package_invoice_line_ids.create(
                    {
                        'name' : invoice.id,
                        'package_id': self.id
                    }
                )

    def prepare_packages(self):
        self.get_invoices()
        for document_type_id in self.pos_id.sequence_ids:
            document_code = document_type_id.name
            document_type_line_ids = self.package_invoice_line_ids.filtered(lambda l: l.name.document_type_code == document_code.getCode())
            if document_type_line_ids:
                package_massive_line_ids = document_type_line_ids.filtered(lambda l: not l.package_line_id)[:500]
                while package_massive_line_ids:
                    package_line_id = self.env['l10n.bo.package.line'].create({'package_id' : self.id, 'document_type_id' : document_code.id})
                    for package_massive_line_id in package_massive_line_ids:
                        package_massive_line_id.write({'package_line_id' : package_line_id.id})
                    package_massive_line_ids = document_type_line_ids.filtered(lambda l: not l.package_line_id)[:500]

    def send_edi_documents(self):
        send = True
        package_index = 0
        while send and package_index < len(self.package_line_ids):
            if not self.package_line_ids[package_index].transaccion:
                self.package_line_ids[package_index].send_edi_documents()
            send = self.package_line_ids[package_index].transaccion
            package_index+=1

    def all_packages_send(self)->bool:
        res = True
        for line in self.package_line_ids:
            if line.state_code != 901:
                res = False
                break
        return res
    
    def parse_response_validation(self, response):
        _logger.info(f"Respuesta validacion: {response}")
        data = response.get('data')
        #raise UserError(f"{response}")
        vals = {'transaccion': data.transaccion}
        if data.transaccion:
            vals['validation_code'] = data.codigoRecepcion
            vals['state_code'] = data.codigoEstado
            vals['description_code'] = data.codigoDescripcion
            errors = False
            self.pos_id.write({'event_id' : False})

        if data.mensajesList:
                errors = ""
                for itemes in data.mensajesList:
                    errors += " | " + itemes.descripcion
        vals['error'] = errors

        
        return vals

    def validate_documents(self, from_pos = False):
        document_type = self.package_line_ids.filtered(lambda package:package.reception_code == self.reception_code)
        if document_type:
            document_type = document_type[0].document_type_id
            SERVICE_TYPE = False
            MODALITY_TYPE = False
            if document_type.getCode() in [3]:
                #SERVICE_TYPE = 'ServicioFacturacionElectronica'
                MODALITY_TYPE = self.company_id.getL10nBoCodeModality()
            if document_type.getCode() in [8,14]:
                if self.company_id.getL10nBoCodeModality() == '1':
                    SERVICE_TYPE = 'ServicioFacturacionElectronica'
                elif self.company_id.getL10nBoCodeModality() == '2':
                    SERVICE_TYPE = 'ServicioFacturacionComputarizada'
            

            response = self.soap_service(METHOD='validacionRecepcionPaqueteFactura', SERVICE_TYPE=SERVICE_TYPE, MODALITY_TYPE=MODALITY_TYPE)
            if type(response) != list:
                vals_response = self.parse_response_validation(response)
                self.write(vals_response)
                for line in self.package_invoice_line_ids:
                    line.name.post_process_soap_siat(response)
                if from_pos:
                    return self.showMessage('RESPUESTA',self.description_code)
        else:
            self.write({'error' : 'No se encontro un documento de recepcion'})
    error = fields.Char(
        string='Error',
        readonly=True 
    )


    def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))
        if MODALITY_TYPE:
            PARAMS.append(('modality_type','=', MODALITY_TYPE))
        
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        self.write({'error' : f'Servicio: {METHOD} no encontrado'})
    
    def _params_validate(self):
        document_type = self.package_line_ids.filtered(lambda package:package.reception_code == self.reception_code)
        document_type = document_type[0].document_type_id
        company = self.company_id
        vals = {
            'codigoAmbiente': int(company.getL10nBoCodeEnvironment()),
            'codigoDocumentoSector': document_type.getCode(),
            'codigoEmision': 2,
            'codigoModalidad': company.getL10nBoCodeModality(),
            'codigoPuntoVenta': self.pos_id.getCode(),
            'codigoSistema': company.getL10nBoCodeSystem(),
            'codigoSucursal': self.pos_id.branch_office_id.getCode(),
            'cufd': self.event_id.cufd_on_event,# self.pos_id.getCufd(),
            'cuis': self.pos_id.getCuis(),
            'nit': company.getNit(),
            'tipoFacturaDocumento': document_type.invoice_type_id.getCode(),
            'codigoRecepcion': self.reception_code
        }
        return {'SolicitudServicioValidacionRecepcionPaquete': vals}
    
    def validacionRecepcionPaqueteFactura(self, WSDL_SERVICE):
        if self.all_packages_send():#self.send_transaccion:
            _params_validate = self._params_validate()
            _logger.info('Parametros de validacion')
            _logger.info(f'{_params_validate}')
            OBJECT = _params_validate
            WSDL = WSDL_SERVICE.getWsdl()
            TOKEN = self.company_id.getDelegateToken()
            WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'validacionRecepcionPaqueteFactura')
            return WSDL_RESPONSE
        
        return [self.showMessage('PAQUETES', 'Tiene paquetes que aun no an sido enviados')]
    
    
    
    def showMessage(self, title, body):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'{title}',
                'message': f'{body}',
                'sticky': False,
            }
        }
    

class L10nBoPackageLine(models.Model):
    _name = 'l10n.bo.package.line'
    _description = 'Linea de paquete (BO)'

    
    name = fields.Char(
        string='Nombre',
        readonly=True 
    )
    
    
    @api.model
    def create(self, values):
        result = super(L10nBoPackageLine, self).create(values)
        result.write({'name' : f'Paquete {result.id}'})
        return result
    
    
    package_id = fields.Many2one(
        string='Paquete (BO)',
        comodel_name='l10n.bo.package',
    )
    
    

    
    invoice_line_ids = fields.One2many(
        string='Lineas de facturas',
        comodel_name='l10n.bo.package.invoice.line',
        inverse_name='package_line_id',
    )

    
    document_type_id = fields.Many2one(
        string='Tipo de documento',
        comodel_name='l10n.bo.document.type',
        required=True
    )
    
    
    success = fields.Boolean(
        string='Realizado',
        readonly=True 
    )
    
    
    description_code = fields.Char(
        string='Codigo descripcion',
        readonly=True 
    )

    
    state_code = fields.Integer(
        string='Codigo estado',
        readonly=True 
    )
    
    
    reception_code = fields.Char(
        string='Codigo recepcion',
    )

    
    transaccion = fields.Boolean(
        string='Transacción',
        readonly=True
    ) 
    
    error = fields.Char(
        string='Error',
        readonly=True 
    )

    
    fechaEnvio = fields.Datetime(
        string='Fecha envio',
        default=fields.Datetime.now,
        required=True,
        help='La fecha de envio de paquetes debe ser la fecha-hora actual y debe estar dentro de las 48hras despues de el envio del evento significativo.'
    )

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )


    def send_edi_documents(self):
        if not self.transaccion:
            SERVICE_TYPE = False
            MODALITY_TYPE = False
            if self.document_type_id.getCode() in [3]:
                #SERVICE_TYPE = 'ServicioFacturacionElectronica'
                MODALITY_TYPE = self.company_id.getL10nBoCodeModality()
            if self.document_type_id.getCode() in [8,14]:
                if self.company_id.getL10nBoCodeModality() == '1':
                    SERVICE_TYPE = 'ServicioFacturacionElectronica'
                elif self.company_id.getL10nBoCodeModality() == '2':
                    SERVICE_TYPE = 'ServicioFacturacionComputarizada'
            

            res = self.soap_service(METHOD='recepcionPaqueteFactura', SERVICE_TYPE=SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
            _logger.info("Respuesta recepcion de paquetes")
            _logger.info(res)
            self.parse_response(res)
        else:
            self.write({'error': 'El paquete ya esta registrado'})
        
    
    def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))
        if MODALITY_TYPE:
            PARAMS.append(('modality_type','=', MODALITY_TYPE))
        

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        self.write({'error' : f'Servicio: {METHOD} no encontrado'})
    
    def _prepare_params(self):
        company = self.company_id
        fechaEnvio = self.fechaEnvio.astimezone(pytz.timezone('America/La_Paz'))
        vals = {
            'codigoAmbiente': int(company.getL10nBoCodeEnvironment()),
            'codigoPuntoVenta': self.package_id.pos_id.getCode(),
            'codigoSistema': company.getL10nBoCodeSystem(),
            'codigoSucursal': self.package_id.pos_id.branch_office_id.getCode(),
            'nit': company.getNit(),
            'codigoDocumentoSector': self.document_type_id.getCode(),
            'codigoEmision': 2,
            'codigoModalidad': int(company.getL10nBoCodeModality()),
            'cufd': self.package_id.pos_id.getCufd(actual = True),
            'cuis': self.package_id.pos_id.getCuis(),
            'tipoFacturaDocumento': int(self.document_type_id.invoice_type_id.getCode()),
            'archivo': '',
            'fechaEnvio': fechaEnvio.strftime("%Y-%m-%dT%H:%M:%S.000"),
            'hashArchivo': '',
            'cafc': '', #self.document_type_id.getCafc() if self.package_massive_id.event_id.getCode() in [5,6,7] else '',
            'cantidadFacturas': '',
            'codigoEvento': self.package_id.event_id.codeRecepcion,
        }
        return {'SolicitudServicioRecepcionPaquete': vals}
    

    def recepcionPaqueteFactura(self, WSDL_SERVICE):
        zip_file_bk = io.BytesIO()
        with tarfile.open(fileobj=zip_file_bk, mode="w") as tar_file:
            for line in self.invoice_line_ids:
                    params_src = line.name.generate_xml().datas
                    params_src = base64.b64decode(params_src)
                    params_sio = io.BytesIO(params_src)
                    info = tarfile.TarInfo(name=line.name.name + '.xml')
                    info.size = len(params_src)
                    tar_file.addfile(tarinfo=info, fileobj=params_sio)
        zip_file_bk.seek(0)
        if zip_file_bk:
            _prepare_vals = self._prepare_params()
            
            file_compress = gzip.compress(zip_file_bk.getvalue())
            if file_compress:
                hash_string = hashlib.sha256(file_compress).hexdigest()
                _prepare_vals['SolicitudServicioRecepcionPaquete']['archivo'] = file_compress
                _prepare_vals['SolicitudServicioRecepcionPaquete']['hashArchivo'] = hash_string
                _prepare_vals['SolicitudServicioRecepcionPaquete']['cantidadFacturas'] = len(self.invoice_line_ids)
            
            _logger.info(f"Parametros de envio: {_prepare_vals}")

            OBJECT = _prepare_vals
            WSDL = WSDL_SERVICE.getWsdl()
            _logger.info(WSDL)
            TOKEN = self.company_id.getDelegateToken()
            WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'recepcionPaqueteFactura')
            return WSDL_RESPONSE
            
    def parse_response(self, response):
        if response.get('success'):
            self.write({'success': response.get('success')})
            data = response.get('data')
            if self.success:
                self.write({'transaccion': data.transaccion}) 
                self.write(
                        {
                            'description_code' : data.codigoDescripcion,
                            'state_code' : data.codigoEstado,
                            'reception_code' : data.codigoRecepcion,
                        }
                )
                if self.transaccion:
                    self.package_id.write({'reception_code' : self.reception_code})
            error = ''
            for message in data.mensajesList:
                error += " - " + message.descripcion
            self.write({'error' : error if error != '' else False})
        else:
            self.write({'error' : response.get('error')})
    
    
class L10nBoInvoiceLine(models.Model):
    _name = 'l10n.bo.package.invoice.line'
    _description = 'Lineas factura de paquete (BO)'

    
    name = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
    )
    
    
    package_id = fields.Many2one(
        string='Paquete (BO)',
        comodel_name='l10n.bo.package',
    )

    
    package_line_id = fields.Many2one(
        string='Linea paquete',
        comodel_name='l10n.bo.package.line',
    )
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    