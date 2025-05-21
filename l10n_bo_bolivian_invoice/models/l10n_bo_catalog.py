# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.l10n_bo_bolivian_invoice.tools.constants import SiatSoapMethod as siatConstant
import logging
from odoo.exceptions import UserError
from datetime import datetime
from pytz import timezone, utc

_logger = logging.getLogger(__name__)


class CatalogRequest(models.Model):
    _name = 'l10n.bo.catalog.request'
    _description = 'Solicitud de catalogos'
    _order = 'id desc'

    
    name = fields.Char(
        string='Nombre',
        store=True,
        compute='_compute_name' 
    )
    
    state = fields.Selection(
        string='Estado',
        selection=[('draft', 'Borrador'),('imperfect','Imperfecto'), ('success', 'Perfecto')],
        default='draft'
    )

    def add_company(self, this_company,add_company):
        for record in self:
            for line in record.catalog_status_ids:
                line.add_company(this_company,add_company)
    
    def quit_company(self, this_company,add_company):
        for record in self:
            for line in record.catalog_status_ids:
                line.quit_company(this_company,add_company)
    
    
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            sufix = 'general'
            if record.company_id:
                sufix = record.company_id.display_name
            record.name =  f"Sincronización - {record.id} - {sufix}" 
    
    catalog_status_ids = fields.One2many(
        comodel_name='l10n.bo.request.catalog.status', 
        string='Sincronizar catalogos',
        inverse_name='request_catalog_id',
        readonly=True 
    )            

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        copy=False
    )

    
    

    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        copy=False,
    )
    

    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
        copy=False, 
    )

    
    @api.onchange('branch_office_id')
    def _onchange_branch_office_id(self):
        self.write({'pos_id' : self.branch_office_id.l10n_bo_pos_ids[0].id if self.branch_office_id else False })
    
    
    
    
    
    def get_catalogs(self):
        for record in self:
            if record.company_id:
                return record.env['l10n.bo.catalog'].search([('discriminate', '=', True)])
            return record.env['l10n.bo.catalog'].search([('discriminate', '=', False)])
    
    def get_l10n_bo_catalog_sync_ids(self):
        for record in self:
            branch_office_id = record.with_company(record.company_id.id).env['l10n.bo.branch.office'].search([], limit=1)
            if branch_office_id:
                record.catalog_status_ids = [(5, 0, 0)]
                catalogs = record.get_catalogs()
                items = []
                for catalog in catalogs:
                    items.append([
                            0, 0, {
                                'catalog_id': catalog.id,
                                'state': 'draft',
                            }
                        ]
                    )
                record.catalog_status_ids = items
                

    def button_process_all_siat(self, company_id = None):
        self.get_l10n_bo_catalog_sync_ids()
        if self.catalog_status_ids:
            self.ensure_one()
            self.write({'state' : 'success'})
            for catalog in self.catalog_status_ids:
                catalog.button_process_siat(company_id, self.pos_id if self.pos_id else None)
                if self.state != 'imperfect' and catalog.state == 'cancel':
                    self.write({'state' : 'imperfect'})

    

    @api.model
    def set_formats(self):
        records = self.env[self._name].search([])
        for record in records:
            for catalog_status_id in record.catalog_status_ids:
                catalog_status_id.set_format()
    

    @api.model # DAILY
    def update_catalogs(self):
        self = self.sudo()
        catalog_ids = self.with_company(1).env['l10n.bo.catalog.request'].search([])
        for catalog_id in catalog_ids:
            _logger.info(f"Actualizando catalogo: {catalog_id.name}")
            catalog_id.button_process_all_siat(catalog_id.company_id)
        



    


class L10nBoRequestCatalogStatus(models.Model):
    _name = 'l10n.bo.request.catalog.status'
    _description = 'Estado de solicitud de catalogos'

    catalog_id = fields.Many2one('l10n.bo.catalog', 'Catalogo')
    name = fields.Char('Sevicio SIAT', store=True, compute='_compute_name')
    error = fields.Char('Error', readonly=True)

    def add_company(self, this_company,add_company):
        for record in self:
            record.catalog_id.add_company(this_company,add_company)

    def quit_company(self, this_company,add_company):
        for record in self:
            record.catalog_id.quit_company(this_company,add_company)

    
    @api.depends('catalog_id')
    def _compute_name(self):
        for status in self:
            status.name = status.catalog_id.name

    code = fields.Selection(related='catalog_id.code')
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Sincronizado'), ('cancel', 'Cancelado')], string='Estado', default='draft')
    request_catalog_id = fields.Many2one(comodel_name='l10n.bo.catalog.request', string='Request', ondelete='cascade', copy=False)

    
    
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company',
        related='request_catalog_id.company_id',
        readonly=True,
        store=True
         
    )
    

    def set_format(self):
        for record in self:
            if record.state == 'done':
                record.catalog_id._format()
    
    def button_process_siat(self, company_id = None, pos_id = None):
        self._process_siat(company_id, pos_id)
        

    def _prepare_params_soap(self,pos_id = None):
        company_id = self.company_id if self.company_id else self.env.company

        if not pos_id:
            _pos_code = company_id.branch_office_id.l10n_bo_pos_ids[0] if company_id.branch_office_id and company_id.branch_office_id.l10n_bo_pos_ids else 0
        else:
            _pos_code = pos_id
        request_data = {
            'codigoAmbiente': int(company_id.l10n_bo_code_environment),
            'codigoPuntoVenta': int(_pos_code.getCode()),
            'codigoSistema': company_id.l10n_bo_code_system,
            'codigoSucursal': company_id.branch_office_id.code,
            'cuis': _pos_code.getCuis(),
            'nit': company_id.vat
        }
        return {'SolicitudSincronizacion': request_data}
    
    
    transaccion = fields.Boolean(
        string='Transacción',
        copy=False
    )

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
    

    def _process_siat(self, company_id = None, pos_id = None):
        #company_id = self.env.company
        if not company_id:
            company_id = self.company_id if self.company_id else self.env.company
        _logger.info(f"Sincronizando: {self.name}")
        
        

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search([
                ('name','=',self.catalog_id.code),
                ('environment_type','=', company_id.getL10nBoCodeEnvironment())
            ],limit=1)
        if WSDL_SERVICE:
            WSDL = WSDL_SERVICE.getWsdl()
            TOKEN = company_id.getDelegateToken()
            response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, self._prepare_params_soap(pos_id), self.catalog_id.code)

            #siat = SiatService(_wsdl, _delegate_token, self._prepare_params_soap(pos_id), self.catalog_id.code)
            #response = siat.process_soap_siat()
            if response.get('success'):
                res_data = response.get('data', {})
                self.write({'transaccion':res_data.transaccion})
                if self.transaccion:
                    self.catalog_id.create_records(res_data, company_id)
                    
                else:
                    self.write({'error': f'{res_data.mensajesList}'})
            else:
                self.write({'error' : response.get('error')})
            self.write({'state' : 'done' if self.transaccion else 'cancel'})
            return response
        raise UserError(f"No se encontro el servicio: {self.catalog_id.code}, ambiente: {company_id.getL10nBoCodeEnvironment()}")

'''
Creacion del Catalogo de Códigos de Leyendas Facturas
https://siatanexo.impuestos.gob.bo/index.php/implementacion-servicios-facturacion/sincronizacion-codigos-catalogos
'''

"""
Modelo representacion de todos los catalgos: FacturacionSincronizacion
"""

class CatalogRequest(models.Model):
    _name = 'l10n.bo.catalog'
    _description = 'Catalogos'
    name = fields.Char(
        'Nombre', 
        readonly=True 
    )
    code = fields.Selection(
        selection=siatConstant.SYNC_ALL_TUPLE, 
        string='Tipo codigo',
        readonly=True 
    )
    description = fields.Char(
        'Description', 
        readonly=True 
    )
    
    model = fields.Char(
        string='Modelo de actividad',
        readonly=True 
        
    )
    def create_records(self, request, company_id = None):
        self.env[self.model].create_records(request, company_id)

    
    discriminate = fields.Boolean(
        string='Discriminar',
        readonly=True
    )

    
    required_format = fields.Boolean(
        string='Formatear',
        readonly=True
    )
    


    def _format(self):
        for record in self:
            if record.required_format:
                record.env[record.model]._format()

    def add_company(self, this_company,add_company):
        for record in self:
            if record.discriminate:
                _record_ids = record.env[record.model].search([('company_id','=',this_company.id)])
                for _record_id in _record_ids:
                    _record_id.write({'company_ids': [(4, add_company.id, 0)]})
    
    def quit_company(self, this_company,add_company):
        for record in self:
            if record.discriminate:
                _record_ids = record.env[record.model].search([('company_id','=',this_company.id)])
                for _record_id in _record_ids:
                    _record_id.write({'company_ids': [(3, add_company.id, 0)]})
    


class L10nBoActivity(models.Model):
    _name = 'l10n.bo.activity'
    _description = 'Codigos de actividad'
    _order = 'codigoCaeb ASC'

    codigoCaeb = fields.Char(
        string='Codigo CAEB',
        readonly=True 
    )
    descripcion = fields.Char(
        string='Descripcion',
        readonly=True 
    )
    tipoActividad = fields.Char(
        string='Tipo de actividad',
        readonly=True 
    )
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )

    def getCode(self):
        if self.codigoCaeb:
            return self.codigoCaeb
        else:
            raise UserError('La actividad economica no tiene un codigo')

    @api.depends('codigoCaeb', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoCaeb or '', leg.descripcion or '')
    
    def create_records(self, res_data, company_id = None):
        _logger.info(f"Sincronizando catalogo: {self._description}, en: {company_id.name if company_id else self.company_id.name}")
        if not company_id:
            company_id = self.company_id
        for activity in res_data.listaActividades:
            activity_exist = self.search(
                [
                    ('codigoCaeb', '=', activity.codigoCaeb),
                    ('company_id','=', company_id.id)
                ], 
                limit=1
            )
            if activity_exist:
                activity_exist.write(
                    {
                        'tipoActividad' : activity.tipoActividad,
                        'descripcion' : activity.descripcion
                    }
                )
            else:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoCaeb' : activity.codigoCaeb,
                        'descripcion' : activity.descripcion,
                        'tipoActividad' : activity.tipoActividad,
                        'company_id' : company_id.id
                    }
                )

import pytz

class L10nBoDatetime(models.Model):
    _name = 'l10n.bo.datetime'
    _description = 'Fecha de sincronización'
    _order = 'id desc'

    name = fields.Char(
        string='Fecha y hora', 
        readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    def create_records(self, res, company_id = None):
        _logger.info(f"Fecha y hora de actualizacion de catalogos: {res.fechaHora}")
        
        self.create(
            {
                'name': f"{res.fechaHora}"
            }
        )



class L10nBoActivityDocumentSector(models.Model):
    _name = 'l10n.bo.activity.document.sector'
    _description = 'Códigos de Tipo Documento Sector'
    _order = 'codigoDocumentoSector ASC'
    
    codigoActividad = fields.Char(
        string='Codigo de actividad', 
        #readonly=True 
    )
    
    codigoDocumentoSector = fields.Integer(
        string='Codigo documento sector',
        #readonly=True 
    )
    
    tipoDocumentoSector = fields.Char(
        string='Tipo documento sector',
        #readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    @api.depends('codigoActividad', 'codigoDocumentoSector', 'tipoDocumentoSector')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s - %s' % (
            leg.codigoActividad or '', leg.codigoDocumentoSector or '', leg.tipoDocumentoSector or '')

    def getCode(self):
        return self.codigoDocumentoSector

    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        
        for activity in res.listaActividadesDocumentoSector:
            activity_exist = self.search([('codigoDocumentoSector', '=', activity.codigoDocumentoSector),('company_id','=', company_id.id)], limit=1)
            if activity_exist:
                
                activity_exist.write(
                    {
                        'codigoActividad' : activity.codigoActividad,
                        'tipoDocumentoSector' : activity.tipoDocumentoSector
                    }
                )
            else:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'codigoDocumentoSector': activity.codigoDocumentoSector,
                        'tipoDocumentoSector': activity.tipoDocumentoSector,
                        'company_id' : company_id.id
                    }
                )

class LegendCodesInvoices(models.Model):
    _name = 'l10n.bo.legend.code'
    _description = 'Códigos de Leyendas Facturas'
    _order = 'codigoActividad ASC'

    codigoActividad = fields.Char(
        string='Codigo de actividad',
        readonly=True 
    )
    
    descripcionLeyenda = fields.Text(
        string='Leyenda',
        readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    @api.depends('codigoActividad', 'descripcionLeyenda')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoActividad or '', leg.descripcionLeyenda or '')

    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        for activity in res.listaLeyendas:
            activity_exist = self.search([('codigoActividad','=',activity.codigoActividad), ('descripcionLeyenda', '=', activity.descripcionLeyenda), ('company_id','=', company_id.id) ], limit=1)
            if not activity_exist:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'descripcionLeyenda': activity.descripcionLeyenda,
                        'company_id' : company_id.id
                    }
                )



class MessageService(models.Model):
    _name = 'l10n.bo.message.service'
    _description = 'Códigos de Mensajes Servicios'

    _order = 'codigoClasificador ASC'

    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )
    name = fields.Char(string='Nombre', store=True, compute='_compute_name')

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )



class ProductService(models.Model):
    _name = 'l10n.bo.product.service'
    _description = 'Productos de servicio SIAT'
    _order = 'codigoProducto ASC'
    
    codigoActividad = fields.Char(
        string='Codigo de actividad',
        readonly=True 
    )

    codigoProducto = fields.Integer(
        string='Codigo de producto',
        readonly=True 
    )
    
    descripcionProducto = fields.Text(
        string='Descripcion',
        readonly=True 
    )    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True 
    )

    
    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )

    
    @api.constrains('company_ids')
    def _check_company_ids(self):
        for record in self:
            for nandina_id in record.manytowmany_nandina_ids:
                nandina_id.write({'company_ids' : record.company_ids})
    
    
    
    
    manytowmany_nandina_ids = fields.Many2many('l10n.bo.product.service.nandina',string="Codigos nandina",readonly=True)
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    def getAe(self):
        return self.codigoActividad
    
    def getCode(self):
        return self.codigoProducto

    @api.depends('codigoActividad', 'codigoProducto', 'descripcionProducto')
    def _compute_name(self):
        for record in self:
            record.name = '%s - %s - %s' % (
            record.codigoActividad or '', record.codigoProducto or '', record.descripcionProducto or '')
    
    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        for activity in res.listaCodigos:
            record_exist = self.search(['&','&',('codigoActividad','=',activity.codigoActividad), ('codigoProducto','=',activity.codigoProducto),('company_id','=', company_id.id)], limit=1)
            if not record_exist:
                record_exist = self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'codigoProducto': activity.codigoProducto,
                        'descripcionProducto' : activity.descripcionProducto,
                        'company_id' : company_id.id
                    }
                )
            if activity.nandina:
                for nandina in activity.nandina:
                    nandina_id = self.env['l10n.bo.product.service.nandina'].search([('name','=',nandina),('company_id','=', company_id.id)])
                    if not nandina_id:
                        nandina_ids = [registro_id.id for registro_id in record_exist.manytowmany_nandina_ids]
                        nandina_ids.append(self.with_company(company_id.id).env['l10n.bo.product.service.nandina'].create({'name': nandina,'l10n_bo_product_service_id':record_exist.id, 'company_id' : company_id.id}).id)
                        record_exist.write({'manytowmany_nandina_ids': [(6,0,nandina_ids)]})
                        
class ProductServiceNandina(models.Model):
    _name = 'l10n.bo.product.service.nandina'
    _description = 'Codigos de producto servicio nandina'
    
    name = fields.Char(
        string='Nandina',
        readonly=True 
    )

    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    
    l10n_bo_product_service_id = fields.Many2one(
        string='Producto servicio',
        comodel_name='l10n.bo.product.service',
        readonly=True 
    )

    def getCode(self):
        return self.name
    
    
    
    fixed_rate = fields.Float(
        string='ICE Espesifico (BS)',
        min_value = 0,
        company_dependent=True
    )

    def get_fixed_rate(self):
        return self.fixed_rate

    percentage_rate = fields.Float(
        string='ICE Porcentual (%)',
        company_dependent=True
    )

    def get_percentage_rate(self):
        return self.percentage_rate

    
    ratio = fields.Float(
        string='Factor',
        company_dependent=True
    )
    
    
    

    

class SignificantEvent(models.Model):
    _name = 'l10n.bo.significant.event'
    _description = 'Códigos de Eventos Significativos'
    _order = 'codigoClasificador ASC'
    codigoClasificador = fields.Integer('Codigo')
    descripcion = fields.Text('Descripcion')

    """
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    """
    name = fields.Char('Name', store=True, compute='_compute_name')

    def getCode(self):
        return self.codigoClasificador

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def complete_name(self):
        for leg in self.search([]):
            leg._compute_name()

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class CancellationReason(models.Model):
    _name = 'l10n.bo.cancellation.reason'
    _description = 'Códigos de Motivos Anulación'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    def getCode(self):
        return self.codigoClasificador

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class OriginCountry(models.Model):
    _name = 'l10n.bo.origin.country'
    _description = 'Códigos de País'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo', 
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def getCode(self):
        return self.codigoClasificador
    
    def getName(self):
        return self.descripcion


class TypeDocumentIdentity(models.Model):
    _name = 'l10n.bo.type.document.identity'
    _description = 'Códigos de Tipo Documento Identidad'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    
    def complete_name(self):
        for leg in self.search([]):
            leg._compute_name()

    def getCode(self):
        if self.codigoClasificador == 0:
            raise UserError('Error de codigo documento identidad')
        return self.codigoClasificador


    name = fields.Char(
        string='Name', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

xsd_names = {
    '1-1': 'facturaElectronicaCompraVenta.xsd',
    '1-24': ''
}


class L10nLatamDocumentType(models.Model):
    _name = 'l10n.bo.document.type'
    _description = 'Codigos de tipo documento'
    _order = 'codigoClasificador ASC'
    
    name = fields.Char(
        string='Nombre',
        store=True,
        compute='_compute_name'
    )

    codigoClasificador = fields.Integer(
        string='Código',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    
    use = fields.Boolean(
        string='Activo',
        company_dependent=True,
    )
    
    
    def getCode(self):
        return self.codigoClasificador
    
    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    
    invoice_type_id = fields.Many2one(
        string='Tipo factura',
        comodel_name='l10n.bo.type.invoice',
        copy=False
    )

    
    sector_document_id = fields.Many2one(
        string='Documento sector',
        comodel_name='l10n.bo.activity.document.sector',
        company_dependent=True,
    )
    



    def _format(self):
        # INVOICE TYPE
        with_tax_credit_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',1)], limit=1)
        document_type_with_tax_credit_ids = self.search(
            [
                ('codigoClasificador','in',[1,2,11,12,13,14,15,16,17,18,19,21,22,23,31,34,35,37,38,39,41,44,51,53])
            ]
        )
        if with_tax_credit_id and document_type_with_tax_credit_ids:
            for document_id in document_type_with_tax_credit_ids:
                document_id.write({'invoice_type_id':with_tax_credit_id.id})
        
        without_tax_credit_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',2)], limit=1)
        document_type_without_tax_credit_ids = self.search(
            [
                ('codigoClasificador','in',[3,4,5,6,7,8,9,10,20,28,33,36,40,42,43,45,46,49,50,52])
            ]
        )
        if without_tax_credit_id and document_type_without_tax_credit_ids:
            for document_id in document_type_without_tax_credit_ids:
                document_id.write({'invoice_type_id':without_tax_credit_id.id})
        
        adjustment_document_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',3)], limit=1)
        document_type_adjustment_document_ids = self.search(
            [
                ('codigoClasificador','in',[24,29,47,48])
            ]
        )
        if adjustment_document_id and document_type_adjustment_document_ids:
            for document_id in document_type_adjustment_document_ids:
                document_id.write({'invoice_type_id':adjustment_document_id.id})


        equivalent_document_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',4)], limit=1)
        document_type_equivalent_document_ids = self.search(
            [
                ('codigoClasificador','in',[30])
            ]
        )
        if equivalent_document_id and document_type_equivalent_document_ids:
            for document_id in document_type_equivalent_document_ids:
                document_id.write({'invoice_type_id':equivalent_document_id.id})


        # SET SECTOR DOCUMENTS
        sector_document_ids = self.env['l10n.bo.activity.document.sector'].search([])
        for sector_document_id in sector_document_ids:
            document_type_id = self.search([('codigoClasificador','=',sector_document_id.getCode())], limit=1)
            if document_type_id:
                document_type_id.write({'sector_document_id' : sector_document_id.id, 'use' : True})

class TypeEmision(models.Model):
    _name = 'l10n.bo.type.emision'
    _description = 'Códigos de Tipo Emisión'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo', 
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    legend = fields.Text(
        string='Leyenda'
    )
    
    

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    def _format(self):
        emision_online = self.search([('codigoClasificador','=',1)], limit=1)
        if emision_online:
            emision_online.write({'legend': """“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”."""})
            
            pos_ids = self.env['l10n.bo.pos'].search([('company_id','=',self.env.company.id)])
            _logger.info('Obteniendo la lista de puntos de venta')
            for pos_id in pos_ids:
                _logger.info('Recoriendo la lista de puntos de venta')
                if not pos_id.emision_id:
                    pos_id.action_online(True)


        emision_offline = self.search([('codigoClasificador','=',2)], limit=1)
        if emision_offline:
            emision_offline.write({'legend': """“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido fuera de línea, verifique su envío con su proveedor o en la página web www.impuestos.gob.bo"."""})
            

class TypeRoom(models.Model):
    _name = 'l10n.bo.type.room'
    _description = 'Codigos tipo de habitación'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )


    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class TypePayment(models.Model):
    _name = 'l10n.bo.type.payment'
    _description = 'Códigos de Tipo Método Pago'
    _order = 'codigoClasificador ASC'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )



class TypeCurrency(models.Model):
    _name = 'l10n.bo.type.currency'
    _description = 'Códigos de Tipo Moneda'

    codigoClasificador = fields.Integer(
        string='Codigo',    
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador
    
    def getName(self):
        return self.descripcion

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def _format(self):
        base_bo, base_usd = self.env['res.currency'].search([('id','=',62)], limit=1), self.env['res.currency'].search([('id','=',1)], limit=1)
        siat_bo, siat_usd = self.search([('codigoClasificador','=',1)], limit=1), self.search([('codigoClasificador','=',2)], limit=1)
        
        if base_bo and siat_bo:
            base_bo.write(
                {
                    'siat_currency_id' : siat_bo.id
                }
            )
        if base_usd and siat_usd:
            base_usd.write(
                {
                    'siat_currency_id' : siat_usd.id
                }
            )
        
        




class TypePos(models.Model):
    _name = 'l10n.bo.type.point.sale'
    _description = 'Códigos tipo de punto de venta'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class TypeInvoice(models.Model):
    _name = 'l10n.bo.type.invoice'
    _description = 'Códigos de Tipo Factura'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )     
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador
    
    
    

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    
    def _format(self):
        pass


class TypeUnitMeasurement(models.Model):
    _name = 'l10n.bo.type.unit.measurement'
    _description = 'Códigos de Unidad de Medida'
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def getCode(self):
        return self.codigoClasificador

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def _format(self):
        siat_unit, siat_dozen = self.search([('codigoClasificador','=',58)], limit=1), self.search([('codigoClasificador','=',14)], limit=1)
        uom_unit, uom_dozen = self.env['uom.uom'].search([('id','=',1)], limit=1), self.env['uom.uom'].search([('id','=',2)], limit=1)

        if uom_unit and siat_unit:
            uom_unit.write(
                {
                    'siat_udm_id' : siat_unit.id
                }
            )

        if uom_dozen and siat_dozen:
            uom_dozen.write(
                {
                    'siat_udm_id' : siat_dozen.id
                }
            )