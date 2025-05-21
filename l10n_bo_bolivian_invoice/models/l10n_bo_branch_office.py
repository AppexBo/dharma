# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class L10nBoBranchOffice(models.Model):
    _name = 'l10n.bo.branch.office'
    _description = 'Sucursales'

    
    name = fields.Char(
        string='Nombre',
        copy=False,
        readonly=True 
    )
    
    
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('unique_company', 'unique(company_id)', 'Solo se permite un registro por compañía.')
    ]

    @api.model
    def create(self, vals):
        existing_record = self.search([('company_id', '=', vals.get('company_id'))])
        if existing_record:
            raise ValidationError('Ya existe un registro para esta compañía.')
        
        res = super(L10nBoBranchOffice, self).create(vals)
        return res

    def wizard_add_pos(self):
        for record in self:
            return {
                'name': 'Punto de venta',
                'type': 'ir.actions.act_window',
                'res_model': 'l10n.bo.pos',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_branch_office_id': record.id,
                }  
            }
    
    @api.constrains('company_id')
    def _check_company_id(self):
        for record in self:
            company_id = record.company_id.id if record.company_id else False
            for pos_id in record.l10n_bo_pos_ids:
                pos_id.write({'company_id' : company_id})
        
    
    
    code = fields.Integer(
        string='Código',
        required=True,
        copy=False
    )

    
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            record.write(
                {
                    'name' : 'CASA MATRIZ' if record.code == 0 else 'Sucursal '+str(record.code)
                }
            )

   
    
    address = fields.Text(
        string='Dirección',
        copy=False
    )


    l10n_bo_pos_ids = fields.One2many(
        string='Puntos de venta',
        comodel_name='l10n.bo.pos',
        inverse_name='branch_office_id', 
        copy=False
    )

    
    def getCode(self):
        return self.code
    
    
    def update_pos_from_siat(self):
        pos = self.l10n_bo_pos_ids.filtered(lambda pos_id : pos_id.code == 0 and pos_id.getCuis())[:1]
        if pos:
            res = self.soap_service('consultaPuntoVenta')
            _logger.info(f"{res}")
            self.createPosS(res)
        else:
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Respuesta',
                    'message': 'Debe registrar y obtener el cuis del Punto de venta 0, en primera instancia',
                    'sticky': False,
                }
            }
    
    def consultaPuntoVenta(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoSucursal': self.code,
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'cuis': self.env['l10n.bo.pos'].search([('branch_office_id','=',self.id),('code','=',0)], limit=1).getCuis(),
        }
        OBJECT = {'SolicitudConsultaPuntoVenta': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'consultaPuntoVenta')
        return WSDL_RESPONSE
    

    def createPosS(self, res):
        if res.get('success', False):
            res_data = res.get('data',{})
            if res_data:
                if res_data.transaccion:
                    for pos in res_data.listaPuntosVentas:
                        pos_id = self.env['l10n.bo.pos'].search([('code','=',pos.codigoPuntoVenta)], limit=1)
                        if not pos_id:
                            type_id = self.env['l10n.bo.type.point.sale'].search([('descripcion','=',pos.tipoPuntoVenta)], limit=1)

                            self.env['l10n.bo.pos'].create(
                                {
                                    'code' : pos.codigoPuntoVenta,
                                    'pos_type_id' : type_id.id if type_id else False,
                                    'branch_office_id' : self.id
                                }
                            )
                else:
                    pass

    
    def cuis_massive_request(self):
        res = self.soap_service('cuisMasivo')
        if res.get('success', False):
            res_data = res.get('data',{})
            if res_data and res_data.transaccion:
                listaRespuestasCuis = res_data.listaRespuestasCuis
                for RespuestasCuis in listaRespuestasCuis:
                    pos_id = self.l10n_bo_pos_ids.filtered(lambda pos: pos.code == RespuestasCuis.codigoPuntoVenta)
                    if pos_id:
                        pos_id.cuis_id.prepare_wsdl_reponse({'success': True, 'data': RespuestasCuis})
        
    
    def cuisMasivo(self, WSDL_SERVICE):
        codigo_pos_list = []

        for pos_id in self.l10n_bo_pos_ids:
                codigo_pos_list.append({
                    'codigoPuntoVenta': pos_id.getCode(),
                    'codigoSucursal': self.getCode(),
                })

        PARAMS = {
            'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
            'codigoModalidad': self.company_id.getL10nBoCodeModality(),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'datosSolicitud': codigo_pos_list,
        }

        OBJECT = {'SolicitudCuisMasivoSistemas': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'cuisMasivo')
        return WSDL_RESPONSE
    
    def cufdMasivo(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
            'codigoModalidad': self.company_id.getL10nBoCodeModality(),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'datosSolicitud': [
                {
                    'codigoPuntoVenta': pos_id.getCode(),
                    'codigoSucursal': self.getCode(),
                    'cuis': pos_id.getCuis()
                }
                for pos_id in self.l10n_bo_pos_ids if pos_id.getCuis() and pos_id.getEmisionCode() == 1
            ],
        }
        OBJECT = {'SolicitudCufdMasivo': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'cufdMasivo')
        return WSDL_RESPONSE
    
    


    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.l10n_bo_code_environment)
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            WSDL_RESPONSE = getattr(self, METHOD)(WSDL_SERVICE)
            return WSDL_RESPONSE
        raise UserError(f'Servicio: {METHOD} no encontrado')
    
    
    def cufd_massive_request(self):
        if self.l10n_bo_pos_ids.filtered(lambda pos: pos.emision_code == 1 and pos.getCuis()):
            res = self.soap_service('cufdMasivo')
            if res.get('success', False):
                res_data = res.get('data',{})
                if res_data and res_data.transaccion:
                    listaRespuestasCufd = res_data.listaRespuestasCufd
                    for RespuestasCufd in listaRespuestasCufd:
                        pos_id = self.l10n_bo_pos_ids.filtered(lambda pos: pos.code == RespuestasCufd.codigoPuntoVenta)
                        if pos_id:
                            pos_id.cufd_id.prepare_wsdl_reponse({'success': True, 'data': RespuestasCufd})

    
    
    def test_server_cominication(self):
        raise UserError(self.soap_service('verificarComunicacion','FacturacionOperaciones'))
    
    def verificarComunicacion(self, WSDL_SERVICE):
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.l10n_bo_delegate_token
        response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, {},  'verificarComunicacion')
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
    