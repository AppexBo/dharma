# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
from pytz import timezone
import pytz
_logger = logging.getLogger(__name__)

class L10nBoPos(models.Model):
    _name ="l10n.bo.pos"
    _description="Puntos de venta de sucursale"

    _order = 'priority'
    
    priority = fields.Integer(
        string='Prioridad',
    )
    

    name = fields.Char(
        string='Nombre',
        readonly=True,
        default='Punto de venta',
        copy=False
    )

    @api.model
    def create(self, vals):
        
        res = super(L10nBoPos, self).create(vals)
        
        if res.branch_office_id.l10n_bo_pos_ids.filtered(lambda pos_id : pos_id.code == res.code and pos_id.id != res.id):
            raise ValidationError('No puede tener codigos de puntos de venta iguales')
        

        if res.company_id.id != res.branch_office_id.company_id.id:
            raise ValidationError('No puede crear un punto de venta desde otra compañia, cambie de entorno de compañia.')
        
        
        res.write(
            {
                'name': f'Punto de venta {res.code}', 
                'cuis_id' : self.env['l10n.bo.cuis'].create({'pos_id' : res.id}).id,
                'cufd_id' : self.env['l10n.bo.cufd'].create({'pos_id' : res.id}).id
            }
        )
        return res
        
    
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if self.branch_office_id.l10n_bo_pos_ids.filtered(lambda pos_id : pos_id.code == record.code and pos_id.id != record.id ): # record.create_date and record.search([('code','=',record.code),('id','!=',record.id)]):
                raise ValidationError('No puede tener codigos de puntos de venta iguales')
            record.write({'name': f'Punto de venta {record.code}', })

    
    code = fields.Integer(
        string='Código',
        copy=False
    )

    def getCode(self):
        return self.code

    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        readonly=True,
        copy=False,
        required=True
        
    )
    
    cuis_id = fields.Many2one(
        string='CUIS',
        comodel_name='l10n.bo.cuis',
        readonly=True, 
        copy=False
    )
    
    def getCuis(self):
        if self.cuis_id:
            return self.cuis_id.getCode()
        return False
    
    
    cuis_active = fields.Boolean(
        string='CUIS activo',
        compute='_compute_cuis_active' 
    )
    
    def _compute_cuis_active(self):
        for record in self:
            record.cuis_active = record.cuis_id.name != '000'
    
    
    
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True 
        
    )
    
    cufd_id = fields.Many2one(
        string='CUFD',
        comodel_name='l10n.bo.cufd',
        readonly=True,
        copy=False
    )

    
    cufd_active = fields.Boolean(
        string='CUFD activo',
        compute='_compute_cufd_active' 
    )
    
    def _compute_cufd_active(self):
        for record in self:
            _today = fields.datetime.now()
            record.cufd_active = record.cufd_id.fechaVigencia and record.cufd_id.fechaVigencia > _today
    
    
    online = fields.Boolean(
        string='En linea',
        compute='_compute_online' 
    )
    
    @api.depends('emision_id')
    def _compute_online(self):
        for record in self:
            record.online = record.emision_id and record.emision_code == 1
    
    
    
    
    
    event_id = fields.Many2one(
        string='Evento',
        comodel_name='significant.event',
    )
    
    
    
    def getCufd(self, actual = False):
        if not actual:
            if self.event_id and self.event_id.cufd_on_event:
                return self.event_id.cufd_on_event
        if self.cufd_id:
            return self.cufd_id.getCode()
        
        raise UserError('El punto de venta seleccionado no tiene un cufd valid')
    
    
    address = fields.Char(
        string='Dirección',
        store=True,
        copy=False
    )

    

    
    pos_type_id = fields.Many2one(
        string='Tipo',
        comodel_name='l10n.bo.type.point.sale',
        copy=False
    )

    
    requested_cuis = fields.Boolean(
        string='CUIS activo',
        copy=False,
        readonly=True,
    )
    
    @api.constrains('cuis_id')
    def _check_cuis_id(self):
        for record in self:
            active = False
            if record.cuis_id:
                if record.cuis_id.fechaVigencia:
                    if record.cuis_id.fechaVigencia > record.getDatetimeNow() and record.name:
                        active = True
            record.requested_cuis = active
    
    
    
    
    # CUIS METHODS
    def cuis_request(self, massive = False):
        if not massive:
            if self.verificarComunicacion():
                self.ensure_one()
                if self.cuis_id:
                    self.cuis_id.unlink()
                self.write({'cuis_id' : self.env['l10n.bo.cuis'].create({'pos_id' : self.id}).id})
                self.cuis_id.soap_service('cuis')
        else:
            self.ensure_one()
            if self.cuis_id:
                self.cuis_id.unlink()
            self.write({'cuis_id' : self.env['l10n.bo.cuis'].create({'pos_id' : self.id}).id})
            self.cuis_id.soap_service('cuis')

    
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
    

    
    emision_id = fields.Many2one(
        string='Emision',
        comodel_name='l10n.bo.type.emision',
        copy=False
    )

    emision_code = fields.Integer(
        string='Codigo de emisión',
        related='emision_id.codigoClasificador',
        readonly=True,
        store=True
    )

    

    def getEmisionCode(self):
        if self.emision_id:
            return self.emision_id.getCode()
        return False
        
    def button_update_cufd(self):
        self.cufd_request()
    

    def cufd_request(self, massive = False):
        if not massive:
            if self.verificarComunicacion() and self.emision_id and self.emision_id.getCode() == 1:        
                self.write({'cufd_id' : self.env['l10n.bo.cufd'].create({'pos_id' : self.id}).id})
                self.cufd_id.soap_service('cufd')
                if len(self.cufd_ids) > self.limit_cufds:
                    self.old_cufd_delete()

        else:
            if self.cuis_id and self.emision_id and self.emision_id.getCode() == 1:
                self.write({'cufd_id' : self.env['l10n.bo.cufd'].create({'pos_id' : self.id}).id})
                self.cufd_id.soap_service('cufd')
                if len(self.cufd_ids) > self.limit_cufds:
                    self.old_cufd_delete()

        self.cuis_request()

    
    def old_cufd_delete(self):
        old_cufd_id = self.cufd_ids[0]
        for cufd_id in self.cufd_ids[1:]:
            if cufd_id.id < old_cufd_id.id:
                old_cufd_id = cufd_id
        old_cufd_id.unlink()


    def getDatetimeNow(self):
        return fields.Datetime.now().astimezone(timezone(self.branch_office_id.company_id.partner_id.tz)).astimezone(pytz.UTC).replace(tzinfo=None)


    def getFechaHora(self):
        fechaHora = fields.Datetime.now().astimezone(timezone(self.branch_office_id.company_id.partner_id.tz))
        return fechaHora
    
    def getAddress(self):
        if self.address:
            return self.address
        else:
            raise UserError(f'El {self.name} no tiene una dirrección')
        


    def verificarComunicacion(self):
        METHOD = 'verificarComunicacion'
        PARAMS = [
                ('service_type','=','FacturacionOperaciones'),
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
            ]
        _logger.info(f"Parametros de busqueda del servicio {METHOD}:{PARAMS}")
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(
            PARAMS,limit=1
        )
        if WSDL_SERVICE:
            WSDL = WSDL_SERVICE.getWsdl()
            TOKEN = self.company_id.getDelegateToken()
            response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, {},  METHOD)
            _logger.info(f"{response}")
            if response.get('success', False):
                res_data = response.get('data')
                if res_data.transaccion:
                    for obs in res_data.mensajesList:
                        if obs.codigo == 926:
                            return True
                return False
            else:
                    return False

        raise UserError(f'Servicio: {METHOD} no encontrado')
        #response = self.cuis_id.soap_service(METHOD)
        #_logger.info(f"{response}")
        #return response

    
    def test_siat_connection(self):
        if self.verificarComunicacion():
            return self.showMessage('Coneccion exitosa','Coneccion exitosa con el SIAT')
        return  self.showMessage('Coneccion fallida','No se tiene coneccion con la base de datos del SIAT') 
    
    
    transaccion = fields.Boolean(
        string='Trassacción',
        default=False
    )
    
    def wizard_l10n_bo_pos_id(self):
        return {
            'name': 'Punto de venta',
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.bo.pos',
            'view_mode': 'form',
            'target': 'new', 
            'res_id': self.id, 
        }
    
    
    def wizard_add_pos(self):
        for record in self:
            try:
                branch_office_id = record.branch_office_id.id
            except:
                branch_office_id = record.id
            
            return {
                'name': 'Punto de venta',
                'type': 'ir.actions.act_window',
                'res_model': 'l10n.bo.pos',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_branch_office_id': branch_office_id,
                }  
            }
    
    
    description = fields.Text(
        string='Descripción',
    )
    
    
    def registroPuntoVenta(self, WSDL_SERVICE):
        codigoTipoPuntoVenta = self.pos_type_id.getCode() if self.pos_type_id else False
        if not codigoTipoPuntoVenta:
            return self.showMessage('Error de usuario', 'Seleccione el tipo de punto de venta')
        if not self.description:
            return self.showMessage('Error de usuario', 'Descripción requerido')
        
        PARAMS = {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoModalidad' : int(self.company_id.getL10nBoCodeModality()),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'codigoSucursal': self.branch_office_id.getCode(),
            'codigoTipoPuntoVenta' : codigoTipoPuntoVenta,
            'cuis': self.search([('branch_office_id','=',self.branch_office_id.id),('code','=',0)], limit=1).getCuis(),
            'descripcion' : self.description,
            'nit': self.company_id.getNit(),
            'nombrePuntoVenta' : self.name
        }
        OBJECT = {'SolicitudRegistroPuntoVenta': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'registroPuntoVenta')
        return WSDL_RESPONSE
        

    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')
    

    def open_pos_request(self):
        if not self.existPos(self.code):
            res = self.soap_service('registroPuntoVenta')
            _logger.info(f"{res}")
            if res.get('success', False):
                res_data = res.get('data', {})
                if res_data.transaccion:
                    self.write({'transaccion': res_data.transaccion})
                self.setMessageList(res_data.mensajesList)
            if not self.transaccion:
                return res
        else:
            return self.showMessage('Respuesta', 'El punto de venta que intenta crear ya existe en la base de datos del SIN')
                

    def run_reponse(self, response):
        _logger.info(f"{response}")
        if response.get('success'):
            res_data = response.get('data', {})
            if res_data.transaccion:
                self.unlink()
            self.setMessageList(res_data.mensajesList)
            

    def delete_to_siat(self):
        res = self.soap_service('cierrePuntoVenta')
        self.run_reponse(res)

    def cierrePuntoVenta(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoPuntoVenta' : self.getCode(),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'codigoSucursal': self.branch_office_id.getCode(),
            'cuis': self.search([('branch_office_id','=',self.branch_office_id.id),('code','=',0)], limit=1).getCuis(),
            'nit': self.company_id.getNit()
        }
        OBJECT = {'SolicitudCierrePuntoVenta': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'cierrePuntoVenta')
        return WSDL_RESPONSE
    

    def getAllPos(self):
        poss = []
        res = self.branch_office_id.soap_service('consultaPuntoVenta')
        if res.get('success', False):
            res_data = res.get('data',{})
            if res_data:
                if res_data.transaccion:
                    poss = res_data.listaPuntosVentas
        return poss
    

    def existPos(self, code):
        exist = False
        poss = self.getAllPos()
        if poss:
            for pos in poss:
                if code == pos.codigoPuntoVenta:
                    exist = True
                    break
        return exist

    @api.model
    def update_cufd(self):
        self = self.sudo()
        pos_ids = self.with_company(1).search([])
        if pos_ids:
            if pos_ids[0].verificarComunicacion():
                for pos_id in pos_ids:
                    pos_id.cufd_request(massive=True)
            else:
                return self.showMessage('ERROR','No hay coneccion con el SIAT')


    def getControlCode(self):
        if self.event_id and self.event_id.cufd_on_event_id:
            return self.event_id.cufd_on_event_id.getControlCode()
        if self.cufd_id:
            return self.cufd_id.getControlCode()
        raise UserError('No tiene un cufd registrado')
    
    

    
    sequence_ids = fields.One2many(
        string='Secuencias',
        comodel_name='l10n.bo.pos.sequence',
        inverse_name='pos_id',
    )
    
    def generateSequence(self):
        if not self.sequence_ids:
            docs = self.env['l10n.bo.document.type'].search([('use','=',True)])
            for doc in docs:
                self.sequence_ids.create({'pos_id': self.id, 'name': doc.id})

    def getSequence(self, document_code):
        if not self.sequence_ids:
            raise UserError(f'El {self.name} no tiene generado las correlaciones')
        code = document_code.getCode()
        for sequence_id in self.sequence_ids:
            if sequence_id.getCode() == code:
                sequence = sequence_id.get_sequence()
                sequence_id.set_next_sequence()
                return sequence
        raise UserError(f'No tiene habilitado el Tipo de documento: {document_code.descripcion}, en {self.name}')
        
    

    def action_offline(self):
        _emision_id = self.env['l10n.bo.type.emision'].search([('codigoClasificador','=',2)], limit=1)
        if _emision_id:
            self.write({'emision_id': _emision_id.id})
            if self.emision_code == 2:
                _logger.info(f"{self.name} puesto en fuera de linea")
                event_id = self.event_id.create({'pos_id' : self.id, 'cufd_on_event_id' : self.cufd_id.id if self.cufd_id else False})
                if event_id:
                    self.write({'event_id' : event_id.id})

        else:
            return self.showMessage(
                'Error de sincronizacion',
                'No se encontro un tipo de emision Fuera de linea'
            )
        
    def action_online(self, massive = False):
        if not massive:
            if self.verificarComunicacion():
                emision_id = self.env['l10n.bo.type.emision'].search([('codigoClasificador','=',1)], limit=1)
                if emision_id:
                    self.write({'emision_id' : emision_id.id})
                    self.cufd_request()
                if not self.sequence_ids:
                    self.generateSequence()
                
                if self.emision_code == 1 and self.event_id:
                    self.event_id.write({'date_end' : fields.datetime.now()})
                    res = self.event_id.register_event(from_pos = True)
                    if res:
                        return res

                 
            else:
                
                return self.showMessage(
                        'Error de sincronizacion',
                        'Sin coneccion con el SIAT'
                )
        else:
            if self.cuis_id:
                        emision_id = self.env['l10n.bo.type.emision'].search([('codigoClasificador','=',1)], limit=1)
                        if emision_id:
                            self.write({'emision_id' : emision_id.id})
                        self.cufd_request(massive)
            if not self.sequence_ids:
                    self.generateSequence()
                

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
    

    # PAPEL FORMAT SETTINGS

    
    paper_format_type = fields.Selection(
        string='Tipo de formato de papel',
        selection=[('1', 'Rollo'), ('2', 'Media Página')],
        default='2', 
        required=True
    )
     
    
    limit_cufds = fields.Integer(
        string="Limite de CUFD's",
        default=30
    )
    

    cufd_ids = fields.One2many(
        string="CUFD'S",
        comodel_name='l10n.bo.cufd',
        inverse_name='pos_id',
    )
    
    
    zero_rate_type = fields.Selection(
        string='FACTURA TASA CERO',
        selection=[
            ('books', 'VENTA DE LIBROS'), 
            ('transportation', 'TRANSPORTE DE CARGA INTERNACIONAL')
        ],
        help="""
            Venta de libros = Bienes.
            Transporte de carga internacional = Servicios.
        """
        
    )
    