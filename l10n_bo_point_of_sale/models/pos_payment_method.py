# -*- coding:utf-8 -*-

from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    _inherit = ['pos.payment']
    card = fields.Char(
        string='Tarjeta',
        readonly=True,
        help='Campo comodin, no usado para guardar la tarjeta',
        copy=False
    )
    
    order = fields.Char(
        string='Nro de orden',
        copy=False
    )
    
    

class PosPaymentMethod(models.Model):
    _inherit = ['pos.payment.method']
    payment_type_id = fields.Many2one(
        string='Tipo de pago (BO)',
        comodel_name='l10n.bo.type.payment',
        help='Tipo de pago en SIAT'
    )