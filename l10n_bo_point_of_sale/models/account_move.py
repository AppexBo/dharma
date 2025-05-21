# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    def check_payment_type(self):
        for record in self:
            CARD = record.getOrdenCard()
            if CARD:
                record.write({'card':CARD})
        res = super(AccountMove, self).check_payment_type()
        return res

    def getOrdenCard(self, ofuscate = False):
        for record in self:
            _logger.info('Definiendo si es un existe una tarjeta')
            if record.invoice_origin:
                if ofuscate:
                    record.pos_id.write({'auxiliar_card':False})
                else: 
                    pos_order_id = record.env['pos.order'].search([('name','=',record.invoice_origin)], limit=1)
                    if pos_order_id:
                        l10n_bo_card_id = record.env['l10n.bo.card'].search([('name','=',pos_order_id.pos_reference)], limit=1)
                        if l10n_bo_card_id:
                            _logger.info(f'Se ha encontrado una tarjeta: {l10n_bo_card_id.card}')
                            return l10n_bo_card_id.card
                        else:
                            _logger.info(f"No se encontro una tarjeta en pedido: {pos_order_id.pos_reference}, devolviendo la tarjeta auxiliar")
                            return record.pos_id.auxiliar_card

                    else:
                        _logger.info(f"No se encontro un pedido: {record.invoice_origin}")
            else:
                _logger.info(f"No se encontro un origen de factura")
            return False
    
    def _action_post(self):
        res = super(AccountMove, self)._action_post()
        self.getOrdenCard(ofuscate=True)
        return res


    def _check_partner_id(self):
        self.write({'force_send' : self.partner_id.exception})
        return super(AccountMove, self)._check_partner_id()
        
    def is_pos_invoice(self)->bool:
        pos_order_id = self.env['pos.order'].search([('name','=', self.ref)], limit=1)
        return True if pos_order_id else False
    
    def l10n_bo_send_mailing(self):
        if not self.is_pos_invoice():
            return super(AccountMove, self).l10n_bo_send_mailing()
        else:
            pass

    def is_pos_bo(self):
        origin_pos = self.is_pos_invoice()
        pos_order_id = self.env['pos.order'].search([('name','=', self.ref)], limit=1)
        return True if pos_order_id and pos_order_id.config_id.enable_bo_edi and origin_pos else False
        
        

    def _get_mail_template(self):
        pos_order_id = self.env['pos.order'].search([('name','=', self.ref)], limit=1)
        if not pos_order_id.config_id.enable_bo_edi:
            return (
                'account.email_template_edi_credit_note'
                if all(move.move_type == 'out_refund' for move in self)
                else 'account.email_template_edi_invoice'
            )
        return ('l10n_bo_bolivian_invoice.l10n_bo_send_gmail_template')