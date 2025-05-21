from odoo import api, models, fields

class L10nBoPosSequence(models.Model):
    _name = 'l10n.bo.pos.sequence'
    _description = 'Secuencia de Punto de venta'

    name = fields.Many2one(string='Tipo de documento',comodel_name='l10n.bo.document.type',ondelete='restrict',)
    
    sequence = fields.Integer(string='Secuencia', default=1)
    pos_id = fields.Many2one(string='Punto de venta',comodel_name='l10n.bo.pos',ondelete='cascade')

    def getCode(self):
        return self.name.getCode()

    def get_sequence(self):
        return self.sequence
    
    def set_next_sequence(self):
        self.write({'sequence': self.sequence + 1})