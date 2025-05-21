# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class CancellationReason(models.TransientModel):
    _name = "cancellation.reason"
    _description ="Razón de cancelación"

    
    
    
    name = fields.Char(
        string='name',
    )

    
    account_move_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        readonly=True 
    )

    
    move_type = fields.Selection(
        string='Tipo',
        related='account_move_id.move_type',
        readonly=True,
        store=True   
    )
    
    
    
    
    def action_done(self):
        self.cancellation()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    

    purchase_sale_reason_id = fields.Many2one(
        string='Razón',
        comodel_name='l10n.bo.cancellation.reason',
        domain=[('codigoClasificador','in',[1,3])],
    )

    adjust_document_reason_id = fields.Many2one(
        string='Razón',
        comodel_name='l10n.bo.cancellation.reason',
        domain=[('codigoClasificador','in',[2,4])],
    )

    

    
    @api.onchange('account_move_id')
    def _onchange_account_move_id(self):
        self.write(
            {
                'purchase_sale_reason_id' : self.get_default_purchase_sale_reason(),
                'adjust_document_reason_id' : self.get_default_purchase_sale_reason()
            }
        )
    
    
    
    def get_default_purchase_sale_reason(self):
        reasons = self.get_cancellation_reasons(self.move_type)
        return reasons[0].id if reasons else False

    def get_cancellation_reasons(self, _type):
        _logger.info(_type)
        if _type:
            res = self.env['l10n.bo.cancellation.reason']
            _logger.info(res)
            if _type == 'out_invoice':
                return res.search([('codigoClasificador','in',[1,3])])
            
            if _type == 'out_refund':
                return res.search([('codigoClasificador','in',[2,4])])
            
        return False
    

    def cancellation(self):
        if self.account_move_id and self.account_move_id.transaccion:
            if self.move_type == 'out_invoice' and self.purchase_sale_reason_id:
                self.account_move_id.write(
                    {
                        'cancellation_reason_id' : self.purchase_sale_reason_id.id
                    }
                )
                self.account_move_id.SendCancelInvoice()
            elif self.move_type == 'out_refund' and self.adjust_document_reason_id:
                self.account_move_id.write(
                    {
                        'cancellation_reason_id' : self.adjust_document_reason_id.id
                    }
                )
            if self.account_move_id.cancellation_reason_id:
                self.account_move_id.SendCancelInvoice()
            
        else:
            raise UserError('La factura solo puede anularse posterior al envio al SIN')


class AccountMove(models.Model):
    
    _inherit = ['account.move']

    
    cancellation_reason_id = fields.Many2one(
        string='Motivo de cancelación',
        comodel_name='l10n.bo.cancellation.reason',
        ondelete='restrict',
    )

    def SendCancelInvoice(self):
        if self.move_type == 'out_invoice':
            SERVICE_TYPE = None
            MODALITY_TYPE = None
            if self.document_type_id.name.getCode() in [1]:
                    SERVICE_TYPE = 'ServicioFacturacionCompraVenta'
            
            if self.document_type_id.name.getCode() in [8,14]:
                if self.company_id.getL10nBoCodeModality() == '1':
                    SERVICE_TYPE = 'ServicioFacturacionElectronica'
                elif self.company_id.getL10nBoCodeModality() == '2':
                    SERVICE_TYPE = 'ServicioFacturacionComputarizada'
                
            if self.document_type_id.name.getCode() in [3]:
                    #SERVICE_TYPE = 'ServicioFacturacionElectronica'
                    MODALITY_TYPE = self.company_id.getL10nBoCodeModality()
                
            WSDL_RESPONSE = self.soap_service(METHOD='anulacionFactura', SERVICE_TYPE= SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
        elif self.move_type == 'out_refund':
            WSDL_RESPONSE = self.soap_service(METHOD = 'anulacionDocumentoAjuste', SERVICE_TYPE='ServicioFacturacionDocumentoAjuste')

        _logger.info(f"{WSDL_RESPONSE}")
        self.cancel_response(WSDL_RESPONSE)
        _logger.info(f"Verificacion de anucalion: {self.anulation_transaction}")
        if self.anulation_transaction:
            _logger.info('Reestableciendo a asiento a borrador')
            self.button_draft()
            if self.state == 'draft':
                _logger.info('Asiento reestablecido a borrador')
                _logger.info('Cancelando el asiento')
                self.button_cancel()
                if self.state == 'cancel':
                    _logger.info('Asiento cancelado')
                    _logger.info('Enviando correo al cliente')
                    self.l10n_bo_send_mailing_cancel()
                else:
                    _logger.info('No se cancelo el asiento')
            else:
                _logger.info('No se reestablecio a borrador el asiento')

    
    anulation_transaction = fields.Boolean(
        string='Anulado',
    )
    

    def cancel_response(self, res):
        self.write({'success': res.get('success')})
        if self.success:

            res_data = res.get('data', {})
            if res_data:
                self.write(
                    {
                        'edi_state' : res_data.codigoDescripcion,
                        'codigoEstado' : res_data.codigoEstado,
                        'codigoRecepcion' : res_data.codigoRecepcion,
                        'anulation_transaction' : res_data.transaccion
                    }
                )
            #self.setMessageList(res_data.mensajesList)
        if self.success == False:
            self.write({'error' : res.get('error')})

    def l10n_bo_send_mailing_cancel(self):
        report = self.env.ref(f'l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo_{self.pos_id.paper_format_type}')
        email_template_obj = self.env.ref('l10n_bo_bolivian_invoice.l10n_bo_cancel_gmail_template')
        if report:
            email_template_obj.update(
                {
                    'report_template_ids' : [(4,report.id)]
                }
            )
        email_template_obj.send_mail(self.id, force_send=True)
        self.sudo().env['mail.mail'].process_email_queue()
        email_template_obj.write({'report_template_ids' : False})
        

    """
        {
            'success': False, 
            'error': TypeError("{https://siat.impuestos.gob.bo/}anulacionFactura() got an unexpected keyword argument 'SolicitudServicioReversionAnulacionFactura'. Signature: `SolicitudServicioAnulacionFactura: {https://siat.impuestos.gob.bo/}solicitudAnulacion`")} 
    """

    def anulacionFactura(self, WSDL_SERVICE):
        _name_field = 'SolicitudServicioAnulacionFactura'
        method_name = 'anulacionFactura'
        if self.document_type_id.name.getCode() in [24,29]:
            _name_field = 'SolicitudServicioAnulacionDocumentoAjuste'
            method_name = 'anulacionDocumentoAjuste'
        #raise UserError(_name_field)
        request_data = {
            _name_field: {
                'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
                'codigoPuntoVenta': int(self.pos_id.getCode()),
                'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                'codigoSucursal': self.pos_id.branch_office_id.getCode(),
                'nit': self.company_id.getNit(),
                'codigoDocumentoSector': self.document_type_id.getCode(),
                'codigoEmision': 1,
                'codigoModalidad': int(self.company_id.getL10nBoCodeModality()),
                'cufd': self.pos_id.getCufd(True),
                'cuis': self.pos_id.getCuis(),
                'tipoFacturaDocumento': self.document_type_id.name.invoice_type_id.getCode(),
                'codigoMotivo': self.getReason(),
                'cuf': self.cuf
            }
        }

        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, request_data, method_name)
        return WSDL_RESPONSE
    

    def anulacionDocumentoAjuste(self, WSDL_SERVICE):
        _name_field = 'SolicitudServicioAnulacionDocumentoAjuste'
        method_name = 'anulacionDocumentoAjuste'
        #raise UserError(_name_field)
        request_data = {
            _name_field: {
                'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
                'codigoPuntoVenta': int(self.pos_id.getCode()),
                'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                'codigoSucursal': self.pos_id.branch_office_id.getCode(),
                'nit': self.company_id.getNit(),
                'codigoDocumentoSector': self.document_type_id.getCode(),
                'codigoEmision': 1,
                'codigoModalidad': int(self.company_id.getL10nBoCodeModality()),
                'cufd': self.pos_id.getCufd(True),
                'cuis': self.pos_id.getCuis(),
                'tipoFacturaDocumento': self.document_type_id.name.invoice_type_id.getCode(),
                'codigoMotivo': self.getReason(),
                'cuf': self.cuf
            }
        }

        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, request_data, method_name)
        return WSDL_RESPONSE
    
    
    def getReason(self):
        if self.cancellation_reason_id:
            return self.cancellation_reason_id.getCode()
        else:
            raise UserError('Debe seleccionar una razon para cancelar la factura')
        

    def cancellation_reazon_wizard(self):
        return {
            'name': 'Cancelar factura',
            'type': 'ir.actions.act_window',
            'res_model': 'cancellation.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': "Factura de venta",
                'default_account_move_id': self.id
            }
        }
    