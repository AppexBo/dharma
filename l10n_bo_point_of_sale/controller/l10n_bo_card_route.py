# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)



class L10nBoCardCreation(http.Controller):
    @http.route('/create_card', type="json", auth="user")
    def create_card(self, name, card, **kwargs):
        l10n_bo_card_id = request.env['l10n.bo.card'].sudo().search([('name','=', name)], limit=1)
        if l10n_bo_card_id:
            l10n_bo_card_id.write({'card':card})
            _logger.info(f"Tarjeta actualizada: {name} - {card}")
        else:
            l10n_bo_card_id = request.env['l10n.bo.card'].sudo().create(
                {
                    'name': name,
                    'card' : card
                }
            )
            if l10n_bo_card_id:
                _logger.info(f"Tarjeta creada: {name} - {card}")
