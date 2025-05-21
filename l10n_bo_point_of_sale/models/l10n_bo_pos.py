# -*- coding:utf-8 -*-

from odoo import api, models, fields

class L10nBoPos(models.Model):
    _inherit = ['l10n.bo.pos']

    
    auxiliar_card = fields.Char(
        string='Tarjeta',
        copy=False,
    )