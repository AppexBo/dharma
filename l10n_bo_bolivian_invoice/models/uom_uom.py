from odoo import api, models, fields
from odoo.exceptions import UserError

class UomUom(models.Model):
    _inherit = ['uom.uom']

    enable_bo_edi = fields.Boolean(
        string='Habilitado facturacion EDI',
        compute='_compute_enable_bo_edi' ,
    )

    @api.model
    def getProduct(self):
        return self.env['uom.uom'].sudo().with_company(self.env.company.getGrandParent().id).browse(self.id)

    
    @api.depends('active')
    def _compute_enable_bo_edi(self):
        for record in self:
            record.enable_bo_edi = record.env.company.enable_bo_edi
    
    siat_udm_id = fields.Many2one(
        string='Udm SIAT',
        comodel_name='l10n.bo.type.unit.measurement',
        copy=False,
        company_dependent=True,
    )

    def getCode(self):
        if self.siat_udm_id:
            return self.siat_udm_id.getCode()
        if self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getCode()
        raise UserError(f'La unidad de medida {self.name} no tiene una UDM del SIAT')
