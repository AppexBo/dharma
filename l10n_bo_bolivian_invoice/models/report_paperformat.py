# -*- coding: utf-8 -*-
from odoo import api, models, fields

class ReportPaperformat(models.Model):
    _inherit = ['report.paperformat']
    
    
    
    code = fields.Char(
        string='Código',
        size=1
    )
    