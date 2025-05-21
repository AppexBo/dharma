# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
import pytz
_logger = logging.getLogger(__name__)



class SignificantEvent(models.Model):
    _name = "significant.event"
    _description ="Registro de eventos significativo (BO)"
    _order = 'id desc'
    
    name = fields.Char(
        string='Nombre',
        readonly=True,
        copy=False
    )

    
    @api.model
    def create(self, values):
    
        result = super(SignificantEvent, self).create(values)
        result.write({'name' : f"Evento {result.id}",})
        return result
    

    
    state = fields.Selection(
        string='Estado',
        selection=[('draft', 'Borrador'), ('send', 'Enviado'), ('cancel', 'Cancelado')],
        default='draft',
        readonly=True 
    )

    
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    
    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
        ondelete='restrict',
        required=True
    )

    
    @api.onchange('pos_id')
    @api.constrains('pos_id')
    def _onchange_pos_id(self):
        for record in self:
            record.cufd = record.pos_id.getCufd(actual = True) if record.pos_id else False
    
    
    
    
    event_id = fields.Many2one(
        string='Evento',
        comodel_name='l10n.bo.significant.event',
        ondelete='restrict',
        required=True,    
        default= lambda self: self.getDefaultEvent()
    )

    def getDefaultEvent(self):
        EVENT_IDS = self.env['l10n.bo.significant.event'].search([])
        if EVENT_IDS:
            event = EVENT_IDS.filtered(lambda event_id: event_id.codigoClasificador == 2)[:1]
            if event: return event.id
            return EVENT_IDS[0].id
        return False
    

    
    
    cufd_on_event_id = fields.Many2one(
        string='CUFD en evento',
        comodel_name='l10n.bo.cufd',
    )
    
    cufd_on_event = fields.Char(
        string='CUFD evento',
    )
    
    cufd = fields.Char(
        string='CUFD',
    )
    
    
    
    
    date_init = fields.Datetime(
        string='Fecha de inicio',
        default=fields.Datetime.now,
        required=True
    )
    
    
    date_end = fields.Datetime(
        string='Fecha de finalización',
    )
    
    success = fields.Boolean(
        string='Realizado',
    )
    
    codeRecepcion = fields.Char(
        string='Codigo de recepción', 
        readonly=True  
    )
    
    transaccion = fields.Boolean(
        string='Transacción',    
        readonly=True 
    )

    
    @api.onchange('cufd_on_event_id')
    @api.constrains('cufd_on_event_id')
    def _onchange_cufd_on_event_id(self):
        for record in self:
            record.cufd_on_event = record.cufd_on_event_id.getCode() if record.cufd_on_event_id else False
    
    

    def soap_service(self, METHOD, SERVICE_TYPE = None):
        PARAMS = [
            ('name','=',METHOD),
            ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))
        _logger.info(f"{PARAMS}")
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            WSDL_RESPONSE = getattr(self, METHOD)(WSDL_SERVICE)
            return WSDL_RESPONSE
        self.write({'error' : f'Servicio: {METHOD} no encontrado'})

    def getDatetimeInit(self):
        if self.date_init:
            date_init = self.date_init.astimezone(pytz.timezone('America/La_Paz'))
            return date_init.strftime("%Y-%m-%dT%H:%M:%S.000")
        raise UserError("Su evento significativo no tiene fecha de inicio.")
    
    def getDatetimeEnd(self):
        if self.date_end:
            date_end = self.date_end.astimezone(pytz.timezone('America/La_Paz'))
            return date_end.strftime("%Y-%m-%dT%H:%M:%S.000")
        raise UserError("Su evento significativo no tiene fecha de finalización.")
    
    
    error = fields.Text(
        string='Error',
        readonly=True 
    )
    
    
    messagesList = fields.Many2many(
        string='Lista de mensajes',
        comodel_name='l10n.bo.message.service',
        readonly=True ,
        copy=False
    )

    def setMessageList(self, _lists):
        _message_ids = []
        for _list in _lists:
            _message_id = self.env['l10n.bo.message.service'].search([('codigoClasificador','=', _list.codigo)],limit=1)
            if _message_id:
                _message_ids.append(_message_id.id)
        self.write({'messagesList': [(6,0,_message_ids)] if _message_ids else False})

    def stable_communication(self) -> bool:
        WSDL_RESPONSE = self.soap_service('verificarComunicacion', 'FacturacionOperaciones')
        if WSDL_RESPONSE.get('success', False):
            res_data = WSDL_RESPONSE.get('data')
            if res_data.transaccion:
                for obs in res_data.mensajesList:
                    if obs.codigo == 926:
                        return True
            return False
        else:
                return False

    def verificarComunicacion(self, WSDL_SERVICE):
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, {},  'verificarComunicacion')
        _logger.info(f"{WSDL_RESPONSE}")
        return WSDL_RESPONSE
        
    

    def prepare_soap_response(self, SOAP_RESPONSE, from_pos = False):
        res = None
        if SOAP_RESPONSE and SOAP_RESPONSE.get('success'):
                res_data = SOAP_RESPONSE.get('data', {})
                if res_data.transaccion:
                    self.write(
                        {
                            'error' : False,
                            'codeRecepcion':res_data.codigoRecepcionEventoSignificativo,
                            'transaccion':res_data.transaccion,
                            'state':'send',
                            'messagesList' : False
                        }
                    )
                else:
                    self.setMessageList(res_data.mensajesList if res_data.mensajesList else []) 
                    self.write({'state': 'cancel'})

                #if self.transaccion and from_pos:
                #    res = self.create_package_massive()
        else:
            self.write({'error' : SOAP_RESPONSE.get('error'),'state': 'cancel'})
        return res

    def registroEventoSignificativo(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente'    : int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoSistema'     : self.company_id.getL10nBoCodeSystem(),
            'nit'               : int(self.company_id.getNit()),
            'cuis'              : self.pos_id.getCuis(),
            'cufd'              : self.cufd,
            'codigoSucursal'    : int(self.pos_id.branch_office_id.getCode()),
            'codigoPuntoVenta'  : int(self.pos_id.getCode()),
            'descripcion'       : self.event_id.descripcion,
            'codigoMotivoEvento'    : self.event_id.getCode(),
            'cufdEvento'        : self.cufd_on_event,
            'fechaHoraInicioEvento' : self.getDatetimeInit(),
            'fechaHoraFinEvento'    : self.getDatetimeEnd()
        }
        OBJECT = {'SolicitudEventoSignificativo' : PARAMS}
        _logger.info(f"Parametros de evento: {PARAMS}")
        WSDL =  WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'registroEventoSignificativo')
        _logger.info(f"RESPUESTA REGISTO DE EVENTO SIGNIFICATIVO: {WSDL_RESPONSE}")
        self.prepare_soap_response(WSDL_RESPONSE)

    def register_event(self, from_pos = False):
        if not self.codeRecepcion:
            STABLE_COMUNICATION = False
            if from_pos:
                STABLE_COMUNICATION = True
            else:
                STABLE_COMUNICATION = self.stable_communication()
            if STABLE_COMUNICATION:
                self.write({'cufd' : self.pos_id.getCufd(actual = True)})
                self.soap_service('registroEventoSignificativo')
                if from_pos and self.codeRecepcion:
                    package_id = self.env['l10n.bo.package'].create({'name' : fields.datetime.now(), 'pos_id' : self.pos_id.id, 'event_id': self.id})
                    if package_id:
                        package_id.prepare_packages()
                        if package_id.package_line_ids:
                            package_id.send_edi_documents()
                            res = package_id.validate_documents()
                            if res:
                                return res
        else:
            return self.showMessage('EVENTO REGISTADO', f'El {self.name} ya fue enviado y registrado')

    def wizard_significant_event_form(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new', 
            'res_id': self.id, 
        }
    
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