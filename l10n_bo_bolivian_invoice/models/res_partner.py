from odoo import api, models, fields, exceptions
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

"""
    Autor: Luis Fernando Hinojosa Flores
    Fecha de creacion: 9 de febrero de 2024
    Descripcion: Fichero (res_partner.py), se declaran todos los modelos respectivos para ser usados en la Facturacion electronica
"""

class ResCountry(models.Model):
    _inherit = ['res.country']
    
    l10n_bo_country_id = fields.Many2one(
        string='Pais (SIAT)',
        comodel_name='l10n.bo.origin.country',
    )

    def getCode(self):
        if self.l10n_bo_country_id:
            return self.l10n_bo_country_id.getCode()
        raise UserError(f"El pais: {self.name} no tiene un codigo SIAT establecido")  
    
    def getName(self):
        if self.l10n_bo_country_id:
            return self.l10n_bo_country_id.getName()
        raise UserError(f"El pais: {self.name} no tiene un codigo SIAT establecido")  
    


class ResCountryState(models.Model):    
    
    _inherit = ['res.country.state']
    abbreviation = fields.Char(
        string='Abreviatura',
        copy=False
    )
    
    

class ResCity(models.Model):
    _inherit = ['res.city']
    code = fields.Char(
        string='Codigo INE',
        copy=False
    )

class ResMunicipality(models.Model):
    _name = 'res.municipality'
    _description = 'Municipalidades de Bolivia'
    
    name = fields.Char(
        string='Nombre',
        copy=False
    )

    
    city_id = fields.Many2one(
        string='Provincia',
        comodel_name='res.city',
        copy=False
    )
    
    
    code = fields.Char(
        string='Codigo INE',
        copy=False
    )

    
    department_id = fields.Many2one(
        string='Departamento',
        comodel_name='res.country.state',
        copy=False
    )
    

class ResPartner(models.Model):
    _inherit = ['res.partner']

    identification_type_id = fields.Many2one(
        string='Tipo de identificación',
        comodel_name='l10n.bo.type.document.identity',
        copy=False
    )
    

    
    identification_code = fields.Integer(
        string='Codigo de identificación',
        related='identification_type_id.codigoClasificador',
        readonly=True,
        store=True
    )
    

    
    enable_bo_edi = fields.Boolean(
        string='Habilitado facturacion EDI',
        compute='_compute_enable_bo_edi' ,
    )
    
    @api.depends('company_type')
    def _compute_enable_bo_edi(self):
        for record in self:
            record.enable_bo_edi = record.env.company.enable_bo_edi
    


    def getCode(self):
        if not self.code:
            raise UserError('El cliente no tiene un codigo de cliente')
        return self.code
    

    def getIdentificationCode(self):
        if self.identification_type_id:
            return self.identification_type_id.getCode()
        else:
            raise UserError(f'El cliente {self.name} no tiene un tipo de identificacion fiscal')
    
    
    vat = fields.Char(
        string='NIT/CI', 
        copy=False,
        help='Número de Identificación Tributaria / Cédula de Identidad'
    )

    
    @api.onchange('vat','identification_type_id', 'complement')
    @api.constrains('vat')
    def _check_vat(self):
        for record in self:
            if record.identification_type_id and record.vat:
                code = record.vat
                if record.complement:
                    code += f"-{record.complement}"
                record.write({'code' : code})
        
    

    code = fields.Char(
        string='Código',
        copy=False,
        help='Código de cliente'
    )

    
    #@api.constrains('code')
    def _check_code(self):
        for record in self:
            prefix = ''
            if record.code:
                prefix = f' - {record.code}'
            record.write({'display_name' : f"{record.name} {prefix}"})
    
    

    def getNit(self):
        if self.vat:
            return self.vat
        else:
            raise UserError('El cliente no tiene un numero de identificacion NIT/CI')
    

    def getId(self):
        if self.identification_type_id:
            return self.identification_type_id.getCode()
        else:
            raise exceptions('El cliente no tiene un tipo de identificación del SIAT')
        

    
    exception = fields.Boolean(
        string='Excepción',
        copy=False,
        help='Activar para usar el codigo de exception 1 en las facturas 0 por defecto'
    )

    def getMunicipalityName(self):
        if self.municipality_id:
            return self.municipality_id.name
        else:
            raise UserError('Establezca un municipio para el contacto de la compañia')
        
    def getPhone(self):
        if self.phone:
            return self.phone
        else:
            raise UserError('Establezca un numero de Teléfono para el contacto de la compañia')
        
    
    complement = fields.Char(
        string='Complemento',
        copy=False
    )
    
        

    def getComplement(self):
        if self.complement:
            return self.complement
        return False
    
    
    nit_state = fields.Char(
        string='Estado del NIT',
        default='Por consultar',
        readonly=True 
    )
    
        
    def _get_params_verify_nit(self, branch_office, cuis_code):
        company = self.env.company
        vals = {
            'SolicitudVerificarNit': {
                'codigoAmbiente': int(company.getL10nBoCodeEnvironment()),
                'codigoModalidad': int(company.getL10nBoCodeModality()),
                'codigoSistema': company.getL10nBoCodeSystem(),
                'codigoSucursal': branch_office,
                'cuis': cuis_code,
                'nit': company.getNit(),
                'nitParaVerificacion': self.getNit(),
            }
        }
        return vals
    
    
    
    
    @api.onchange('vat', 'identification_code')
    @api.constrains('vat', 'identification_code')
    def _onchange_vat_identification_code(self):
        for record in self:
            if record.vat and record.identification_code == 5:
                record.l10n_bo_validate_nit()
            

    def prepare_process_reponse(self, res):
        if res.get('success'):
            res_data = res.get('data', {})
            res_code = res_data.mensajesList
            if res_code:
                self.write({'nit_state': res_code[0].descripcion})            

    @api.model
    def l10n_bo_validate_nit(self):
        if self.enable_bo_edi:
                self.prepare_process_reponse(self.soap_service('verificarNit'))

    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.env.company.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')

    def verificarNit(self, WSDL_SERVICE):
        _branch = self.env.company.branch_office_id.code if self.env.company.branch_office_id else 0
        _cuis = self.env['l10n.bo.pos'].search([('code','=',0),('company_id','=',self.env.company.id)]).getCuis()
        if _cuis:
            OBJECT = self._get_params_verify_nit(_branch,_cuis)
            WSDL = WSDL_SERVICE.getWsdl()
            TOKEN = self.env.company.getDelegateToken()
            WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'verificarNit')
            return WSDL_RESPONSE
        return {'success' : False}