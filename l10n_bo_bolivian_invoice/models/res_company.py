# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'
    

    
    enable_bo_edi = fields.Boolean(
        string='Habilitar la facturación (BO)',
        copy=False
    )

    
    edi_company_adm_user = fields.Boolean(
        string='Permiso de compañia (BO)',
        compute='_compute_edi_company_adm_user' 
    )
        
    @api.depends('enable_bo_edi','parent_company_id')
    def _compute_edi_company_adm_user(self):
        for record in self:
            record.edi_company_adm_user = record.get_id() == record.env.company.id

    
    parent_company_id = fields.Boolean(
        string='Tiene compañia padre',
        compute='_compute_parent_company_id' 
    )

    
    @api.depends('enable_bo_edi')
    def _compute_parent_company_id(self):
        for record in self:
            parent = record.parent_id
            while parent and parent.parent_id:
                parent = parent.parent_id
            record.parent_company_id = parent.enable_bo_edi

    
    
    
    
        
    
    def getGrandParent(self):
        for record in self:
            parent = record.sudo().parent_id if record.sudo().parent_id else record
            while parent and parent.sudo().parent_id:
                parent = parent.sudo().parent_id
            #raise UserError(parent)
            return parent
    
    
    
    user_admin_bo = fields.Boolean(
        string='Usuario de ajustes (BO)',
        compute='_compute_user_admin_bo' 
    )
    
    def _compute_user_admin_bo(self):
        for record in self:
            user_admin_bo = False
            group = self.env.ref('l10n_bo_bolivian_invoice.group_adm_invoice_edi')
            if group and record.env.user in group.users:
                user_admin_bo = True
            record.user_admin_bo = user_admin_bo
    
    
    
    

    
    
    pos_ids = fields.One2many(
        string='Puntos de venta (BO)',
        comodel_name='l10n.bo.pos',
        inverse_name='company_id',
    )    
    
    
    l10n_bo_code_environment = fields.Selection(
        string='Tipo de entorno',
        selection=[
            ('1', 'Producción'), 
            ('2', 'Prueba')
        ] 
    )
    l10n_bo_code_modality = fields.Selection(
        string='Tipo de modalidad',
        selection=[
            ('1', 'Electronica en linea'), 
            ('2', 'Computarizada en linea')
        ],
    )

    l10n_bo_code_system = fields.Char(
        string='Codigo de sistema',
        copy=False,
    )
    l10n_bo_delegate_token = fields.Text(
        string='Token delegado',
        copy=False
        
    )
    
    
    
    l10n_bo_edi_certificate_id = fields.Many2one(
        string="Certificado (BO)",
        comodel_name='l10n.bo.edi.certificate',
        company_dependent=True
    )
    
    vat = fields.Char(
        string='NIT',
    )
    
    
    state_id = fields.Many2one(
        string='Departamento',
        comodel_name='res.country.state'
    )

    province_id = fields.Many2one(
        string='Provincia',
        comodel_name='res.city',
        copy=False
    )
    
    
    
    

    municipality_id = fields.Many2one(
        string='Municipio',
        comodel_name='res.municipality',
        copy=False
    )    

    def getMunicipalityName(self):
        if self.municipality_id:
            return self.municipality_id.name
        raise UserError('Su compañia no tiene un municipo asignado.')



    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office'
    )

    def add_company(self, company_id):
        for record in self:
            catalog = record.sudo().with_company(1).env['l10n.bo.catalog.request'].search([('company_id','=',record.id)])
            if catalog:
                catalog.add_company(record, company_id)


    def quit_company(self, company_id):
        for record in self:
            catalog = self.sudo().with_company(1).env['l10n.bo.catalog.request'].search([('company_id','=',record.id)])
            if catalog:
                catalog.quit_company(record, company_id)
    
    
    #@api.onchange('branch_office_id')
    @api.constrains('branch_office_id')
    def _check_branch_office_id(self):
        for record in self:
            if record.branch_office_id:
                
                record.branch_office_id.write({'company_id' : record.id})
                _parent_id = record.getGrandParent()
                if _parent_id.id != record.id:
                    _parent_id.add_company(record)
                    record.inherit_bo_edi_settings()
                    #record.write({'enable_bo_edi' : True})
            else:
                _parent_id = record.getGrandParent()
                if _parent_id.id != record.id:
                    _parent_id.quit_company(record)


    
    # GETTERS
    def getL10nBoCodeEnvironment(self):
        COMPANY_ID = self.getGrandParent()
        #raise UserError(COMPANY_ID)
        if COMPANY_ID and not COMPANY_ID.l10n_bo_code_environment:
            raise UserError('Defina el tipo de entorno')
        return COMPANY_ID.l10n_bo_code_environment
    
    def getL10nBoCodeSystem(self):
        COMPANY_ID = self.getGrandParent()
        if not COMPANY_ID.l10n_bo_code_system:
            raise UserError('Defina el codigo de sistema')
        return COMPANY_ID.l10n_bo_code_system
    
    def getNit(self):
        COMPANY_ID = self.getGrandParent()
        if not COMPANY_ID.vat:
            raise UserError('Defina el nit de la compañia')
        return COMPANY_ID.vat
    
    def getL10nBoCodeModality(self):
        COMPANY_ID = self.getGrandParent()
        if not COMPANY_ID.l10n_bo_code_modality:
            raise UserError('Defina el tipo de modalidad')
        return COMPANY_ID.l10n_bo_code_modality
    
    def getDelegateToken(self):
        COMPANY_ID = self.getGrandParent()
        if not COMPANY_ID.l10n_bo_delegate_token:
            raise UserError('Defina el token delegado')
        return COMPANY_ID.l10n_bo_delegate_token
    
    def getCertificate(self):
        COMPANY_ID = self.getGrandParent()
        if not COMPANY_ID.l10n_bo_edi_certificate_id:
            raise UserError(f'La compañia:{COMPANY_ID.name}, no tiene un certificado digital')
        return COMPANY_ID.l10n_bo_edi_certificate_id
    

    
    def get_id(self):
        for record in self:
            try:
                _id = int(record.id)
                return _id
            except:
                try:
                    return int(str(record.id)[6:])
                except:
                    return False
                
    
    @api.onchange('enable_bo_edi')
    def _onchange_enable_bo_edi(self):
        self.partner_id.write({'tz': 'America/La_Paz'})
        if self.enable_bo_edi:        
            self.inherit_bo_edi_settings()
    
    

    @api.constrains('enable_bo_edi')
    def _check_enable_bo_edi(self):
        for record in self:
            if record.enable_bo_edi:
                if not record.parent_id:
                    wsdl_model_ids = self.env['l10n.bo.wsdl'].search([('service_type','!=', 'qr')])
                    for wsdl_id in wsdl_model_ids:
                        wsdl_id.operation_service_soap()
                record.partner_id.write({'tz': 'America/La_Paz'})
                
                if not record.parent_id:
                    _branch_office_id = record.branch_office_create()
                    if _branch_office_id:
                            record.write(
                                {
                                    'branch_office_id' : _branch_office_id.id
                                }
                            ) 
                            record.point_of_sale_create()

    '''
        Compra y venta
        Educativo
        Alquiler
        Taza cero
        Transporte
        Exportacion
        '''

    
    def branch_office_create(self):
        for record in self:
            branch_office_id = record.env['l10n.bo.branch.office'].search([('code','=',0),('company_id','=', record.id)], limit=1)
            if not branch_office_id:
                branch_office_id = record.env['l10n.bo.branch.office'].create(
                    {
                        'code' : 0,
                        'address' : record.street,
                        'company_id' : record.id
                    }
                )
            return branch_office_id
        
    def point_of_sale_create(self):
        for record in self:
            pos_id = record.env['l10n.bo.pos'].search([('code','=',0),('company_id','=',record.id)], limit=1)
            if not pos_id:
                pos_id = record.env['l10n.bo.pos'].create(
                    {
                        'code' : 0,
                        'branch_office_id' : record.branch_office_id.id,
                        'address' : record.branch_office_id.address,
                        'company_id' : record.id
                    }
                )
            if pos_id and not record.parent_company_id:
                    pos_id.cuis_request()
                    if pos_id.getCuis():
                        record.catalog_request_udpate()
                    if pos_id.emision_id:
                        pos_id.cufd_request()
                        if pos_id.cufd_id:
                            pos_id.generateSequence()

    def set_formats(self):
        self.env['l10n.bo.catalog.request'].set_formats()
        decimal_precision_id = self.env['decimal.precision'].search([('id','=',3)])
        if decimal_precision_id and decimal_precision_id.digits!=4:
            decimal_precision_id.update({'digits' : 4})


    def catalog_request_udpate(self):
        for record in self:
            l10n_bo_catalog_request_company_id = record.env['l10n.bo.catalog.request'].search([('company_id','=',record.id)], limit=1)
            if not l10n_bo_catalog_request_company_id:
                l10n_bo_catalog_request_company_id = record.env['l10n.bo.catalog.request'].create({'company_id': record.id})
            
            if l10n_bo_catalog_request_company_id:
                    l10n_bo_catalog_request_company_id.button_process_all_siat()

            l10n_bo_catalog_request_id = record.env['l10n.bo.catalog.request'].search([('company_id','=',False)], limit=1)
            if not l10n_bo_catalog_request_id:
                l10n_bo_catalog_request_id = record.env['l10n.bo.catalog.request'].create({})
            
            if l10n_bo_catalog_request_id:
                    l10n_bo_catalog_request_id.button_process_all_siat()
                        
    
    def inherit_bo_edi_settings(self):
        for record in self:
            PARENT_ID = record.getGrandParent()
            if PARENT_ID and PARENT_ID.id != record.id:
                record.write(
                    {
                        'l10n_bo_code_environment'  : PARENT_ID.l10n_bo_code_environment,
                        'l10n_bo_code_modality'     : PARENT_ID.l10n_bo_code_modality,
                        'l10n_bo_code_system'       : PARENT_ID.l10n_bo_code_system,
                        'l10n_bo_delegate_token'    : PARENT_ID.l10n_bo_delegate_token,
                        #'l10n_bo_edi_certificate_id': PARENT_ID.l10n_bo_edi_certificate_id.id if PARENT_ID.l10n_bo_edi_certificate_id else False,
                        'vat' : PARENT_ID.vat
                    }    
                )
    


#-----------------------------------------------------------------------------------------------------------------------------

