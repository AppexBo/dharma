from odoo import api, fields, models


import logging
_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _get_pos_ui_l10n_bo_type_document_identity(self, params):
        return self.env['l10n.bo.type.document.identity'].search_read(**params['search_params'])
    
    def _loader_params_l10n_bo_type_document_identity(self):
        return {'search_params': {'domain': [], 'fields': ['name', 'codigoClasificador', 'descripcion']}}

    def _loader_params_res_partner(self):
        res = super(PosSession, self)._loader_params_res_partner()
        add_list = ["identification_type_id", 'complement', 'nit_state', 'complement','exception']
        res['search_params']['fields'] += add_list
        return res

    @api.model
    def _pos_ui_models_to_load(self):
        res = super(PosSession, self)._pos_ui_models_to_load()
        models_to_load = [
            'l10n.bo.type.document.identity',
            #'l10n.bo.card',
            'pos.payment',
        ]
        res+= models_to_load
        return res
    
        
    #def _loader_params_l10n_bo_card(self):
    #    return {
    #        'search_params': {'fields': ['name','card'],},}

    #def _get_pos_ui_l10n_bo_card(self, params):
    #    return self.env['l10n.bo.card'].search_read(**params['search_params'])
    


    def _loader_params_pos_payment(self):
        return {'search_params': {'domain': [],'fields': ['card','order']}}

    def _get_pos_ui_pos_payment(self, params):
        return self.env['pos.payment'].search_read(**params['search_params'])