# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class PosOrder(models.Model):
    _inherit = ['pos.order']

    def get_payment_type_default(self):
        pos_payment_ids = self.payment_ids.filtered(lambda line: line.payment_method_id.payment_type_id != False)
        _payment_type_ids = False
        _descripcion = False
        if pos_payment_ids:
            _payment_type_ids = self.env['l10n.bo.type.payment'].search([])
            _descripcion = ''
            for pos_payment_id in pos_payment_ids:
                _descripcion += pos_payment_id.payment_method_id.payment_type_id.descripcion+'-'
                _payment_type_ids = _payment_type_ids.filtered(lambda line: pos_payment_id.payment_method_id.payment_type_id.descripcion in line.descripcion)
            _descripcion = _descripcion[:-1]
            _descripcion = _descripcion.replace('–','-')
            _desc = _descripcion.split('-')
            for pos_payment_id in _payment_type_ids:
                SEPARATOR, DESCRIPTION = '–' , pos_payment_id.descripcion    
                if SEPARATOR in DESCRIPTION:
                    DESCRIPTION = DESCRIPTION.replace(SEPARATOR, '-')
                
                DESCRIPTION = DESCRIPTION.split('-')
                DESCRIPTION = [palabra.strip() for palabra in DESCRIPTION]
                if sorted(_desc) == sorted(DESCRIPTION):
                    _logger.info(f"TIPO DE PAGO SIAT: {pos_payment_id.descripcion}")
                    return pos_payment_id.id

    
    def action_pos_order_invoice(self):
        res = super(PosOrder, self).action_pos_order_invoice()
        return res
    
    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        if self.config_id.enable_bo_edi:
            if  self.config_id.branch_office_id:
                if self.config_id.pos_id:
                    if self.config_id.branch_office_id.company_id.id == self.config_id.pos_id.company_id.id:
                        vals['payment_type_id'] = self.get_payment_type_default()
                        vals['branch_office_id'] = self.config_id.branch_office_id.id
                        vals['pos_id'] = self.config_id.pos_id.id
                        vals['document_type_id'] = self.config_id.document_type_id.id
                    else:
                        raise UserError('Las compañias de sucursal (BO) y punto de venta (BO) no coinciden')
                else:
                    raise UserError('No se encontro un punto de venta (BO) configurado en el POS fiscal.')
            else:
                raise UserError('No se encontro una sucursal (BO) configurado en el POS fiscal.')
        return vals
    


    # PAYMENTS
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order,ui_paymentline)
        return res
    
    def add_payment(self, data):
        res = super(PosOrder, self).add_payment(data)
        return res