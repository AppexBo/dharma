# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import pytz
from lxml import objectify
from odoo.addons.l10n_bo_bolivian_invoice.tools.utils import *
import gzip
import hashlib
import base64
import io
import tarfile
from io import BytesIO

import logging
_logger = logging.getLogger(__name__)






class AccountMove1(models.Model):
    _inherit = ['account.move']

    def _post(self, soft=True):
        _edi_actions = False
        for record in self:
            if record.edi_bo_invoice and record.move_type in ['out_invoice','out_refund']:
                res = record.prepare_invoice()
                if res:
                    return res
                    
                _edi_actions = True
            
            if not record.transaccion and _edi_actions and record.pos_id.getEmisionCode() == 1:
                raise UserError(f"OBSERVACIONES: {[error.description for error in record.messagesList_ids] if record.messagesList_ids else 'NINGUNO'} - ERRORES: {record.error if record.error else 'NINGUNO'}")
            
        res =  super(AccountMove1, self)._post(soft)

        for record in self:
            if  _edi_actions:
                record._action_post()
        return res
    
    
    def getUrl(self):
        URL = self.env['l10n.bo.wsdl'].search([('service_type','=','qr'),('environment_type','=',self.company_id.getL10nBoCodeEnvironment())], limit=1)
        if URL:
            return URL.wsdl
        raise UserError('No se encontro el servicio wsdl QR')
    
    def _action_post(self):
        self.write(
            {
                'url' : self.getUrl() + f'?nit={self.company_id.getNit()}&cuf={self.cuf}&numero={self.invoice_number}&t={self.pos_id.paper_format_type}',
                #'invoice_date_edi' : self.get_datetime(),
            }
        )
        if self.pos_id.emision_id.getCode() == 1: 
            self.write({'invoice_date_edi' : self.get_datetime(),})
        if self.is_card:
            self.write({'card' : self.getCard()})
        self.l10n_bo_send_mailing()

    def generatePdf(self):
        pdf = self.env.ref('l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo').render_qweb_pdf(self.ids)[0]
        _name_file = f'{self.pos_id.getCode()}-{self.document_type_id.getCode()}-{self.invoice_number}'
        
        attacht_id = self.env['ir.attachment'].search(
            [('res_model', '=', self._name), ('res_id', '=', self.id), ('name', '=', _name_file)], limit=1)
        if not attacht_id:
            attacht_id = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': _name_file,
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/pdf',
            })
        else:
            attacht_id.write({'datas': base64.b64encode(pdf), 'mimetype': 'application/pdf',})
        return attacht_id
    

    
    def l10n_bo_send_mailing(self):
        report = self.env.ref(f'l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo_{self.pos_id.paper_format_type}')
        email_template_obj = self.env.ref('l10n_bo_bolivian_invoice.l10n_bo_send_gmail_template')
        if report:
            email_template_obj.update(
                {
                    'report_template_ids' : [(4,report.id)]
                }
            )
        _with_context_attach = [(4,self.generate_xml().id)]
        email_values = {'attachment_ids': _with_context_attach}
        email_template_obj.send_mail(self.id, force_send=True, email_values=email_values)
        self.sudo().env['mail.mail'].process_email_queue()
        email_template_obj.write({'report_template_ids' : False})
            

    """
        Validar que el documento exista en el punto de venta
    """

    def generate_xml(self):
        if not self.edi_str:
            self.str_edi_format()
        edi_str = self.edi_str
        edi_tree = objectify.fromstring(edi_str)
        if self.company_id.getL10nBoCodeModality() == '1':
            if  "http://www.w3.org/2000/09/xmldsig#" not in self.signed_edi_str.decode('utf-8') or "Signature" not in self.signed_edi_str.decode('utf-8'):
                self.sign_edi_str()
            edi_tree_signed = self.signed_edi_str
            #raise UserError(f"{edi_tree_signed}")
        else:
            edi_tree_signed = edi_str.encode('utf-8')
        _name_file = f'{self.company_id.getNit()}-{self.name}'
        attacht_id = self.env['ir.attachment'].search(
            [('res_model', '=', self._name), ('res_id', '=', self.id), ('name', '=', _name_file)], limit=1)
        if not attacht_id:
            attacht_id = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': _name_file,
                'datas': base64.b64encode(edi_tree_signed),
                'mimetype': 'application/xml',
            })
        else:
            attacht_id.write({'datas': base64.b64encode(edi_tree_signed), 'mimetype': 'application/xml',})
        return attacht_id
    

    def checkConection(self):
        if not self.pos_id.verificarComunicacion() and self.pos_id.getEmisionCode() == 1:
            raise UserError('Sin coneccion con la base de datos del SIN')
            self.pos_id.action_offline()
            _logger.info(self.pos_id.getEmisionCode())

            
    def prepare_invoice(self, massive = None):
        for record in self:
            #raise UserError(record.document_type_id.name.getCode() in [1,2] and not massive)
            pos_code_state = record.pos_id.getEmisionCode()
            invoice_post_outline = False
            record.checkConection()
            if pos_code_state != record.pos_id.getEmisionCode():
                invoice_post_outline = True
            if record.document_type_id.name.getCode() in [24] and record.pos_id.emision_code == 2:
                raise UserError('SERVICIO NO DISPONIBLE: Para la modalidad 2 y/o sector 24, emisiones fuera de linea')
            
            record._check_partner_id()
            record.check_payment_type()

            # 1 : ESTABLECER LA FECHA DE EMISION

            if (record.pos_id and record.pos_id.emision_code == 1) or invoice_post_outline:
                record.write({'invoice_date_edi' : fields.datetime.now()})
            else:
                if record.pos_id and record.pos_id.emision_code == 2: 
                    if record.pos_id.event_id:
                        if record.pos_id.event_id.date_init:
                            if record.pos_id.event_id.date_init > record.invoice_date_edi:
                                raise UserError('La fecha de la factura no puede ser menor a la fecha de inicio del evento.')
                        else:
                            raise UserError("Su evento significativo no tiene una fecha de inicio")
                    else:
                        raise UserError(f"No se encontro un evento significativo para el {record.pos_id.name}")
                else:
                    raise UserError("Las emisiones validas son EN LINEA(1) y FUERA DE LINEA(2)")

            
            #record.write({'invoice_date' : record.get_datetime_bo()})
            #_logger.info(f"Fecha odoo: {record.invoice_date}")
            
            if record.invoice_number == 0:
                if not record.document_type_id:
                    record._set_default_document_type()
                record.write({'invoice_number': record.pos_id.getSequence(record.document_type_id)})

                #record.write({'invoice_number': record.pos_id.getSequence(record.document_type_id)})
            #raise UserError(self.invoice_date_edi)
            
            #record.write({'meridies' : 'am' if int(record.invoice_date_edi.strftime('%H')) < 12 else 'pm'})
            record.write({'meridies' : 'am' if int(self.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz')).strftime('%H')) < 12 else 'pm'})

            
            # 2 : GENERAR CUF PARA LA FACTURA
            
            #if not record.cuf:
            _cuf = record.generateCuf()
            record.write({'cuf' : _cuf})
            record.write({'edi_str' : record.str_edi_format()})
            _logger.info(f'EDI STR: {record.edi_str}')
            if record.edi_str in [None, False, '']:
                raise UserError(f'No tiene disponible una implementacion para el documento: {record.document_type_id.name.name}')
            
            if record.company_id.getL10nBoCodeModality() == '1':
                _logger.info('FIRMA')
                record.sign_edi_str()
                
            if record.pos_id.getEmisionCode() == 1:
                record.generate_zip()
                record.write({'hash'              : hashlib.sha256(record.zip_edi_str).hexdigest()})
                record.send_invoice()

            



    def check_payment_type(self):
        for record in self:
            amount_giftcard = self.getAmountGiftCard()
            amount_discount = self.getAmountDiscount()
            self.prorate_prepare()
            
            if record.is_gift_card and record.document_type_id.name.getCode() in [3,28]:
                raise UserError(f'El pago con gifcard no es valido para el documento: {self.document_type_id.name.name}')
            
            if record.is_gift_card and amount_giftcard == 0:
                raise UserError("El monto giftcard debe ser mayor a cero '0.00'")
            #elif record.is_gift_card and amount_giftcard >= self.getAmountTotal():
            #    raise UserError("El monto giftcard no debe ser mayor al monto total")
            
            
            if amount_discount >= self.getAmountSubTotal() and self.invoice_line_ids.filtered(lambda l: l.product_id.global_discount):
                raise UserError("El monto descuento no debe ser mayor o igual al subtotal")
            
            if (record.is_card and not record.card) or (record.card and len(record.card) < 16):
                raise UserError("La tarjeta debe tener 16 caracteres")
            
    
    def prorate_prepare(self):
        for line_id in self.invoice_line_ids:
            line_id.apportionment()
            

    def sign_edi_str(self):
        if  not self.company_id.getGrandParent().l10n_bo_edi_certificate_id:
            raise UserError('La compañia no tiene un certificado digital')
        success = False
        while not success:
            self.write({'signed_edi_str'    : self.company_id.getCertificate().sudo()._sign(objectify.fromstring(self.edi_str))})
            signed_str = str(self.signed_edi_str.decode('utf-8'))
            success = "http://www.w3.org/2000/09/xmldsig#" in signed_str or "Signature" in signed_str
        #raise UserError(f'{self.signed_edi_str}')
        _logger.info(f'{self.signed_edi_str}')
    
    
    def zip_edi_document(self, param):
        return gzip.compress(param)

    def generate_zip(self):
        success = False
        while not success:
            try:        
                params_src = self.generate_xml().datas
                params_src = base64.b64decode(params_src)
                self.write({'zip_edi_str': self.zip_edi_document(params_src)})
                success = True
            except:
                success = False

    def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))
        if MODALITY_TYPE:
            PARAMS.append(('modality_type','=', MODALITY_TYPE))
        
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        #raise UserError(f"{PARAMS}")
        
        if WSDL_SERVICE:
            #raise UserError(WSDL_SERVICE.getWsdl())
            return getattr(self, f"{METHOD}")(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')

    
    def send_invoice(self):
        if self.document_type_id and self.move_type in ['out_invoice', 'out_refund']:
            # SERVICIOS DE RECEPCION
            WSDL_RESPONSE = False
            if self.document_type_id.name.getCode() in [1,3,8,14]: # /|\ ADD MORE DOCUMENTS
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
                
                WSDL_RESPONSE = self.soap_service(METHOD='recepcionFactura', SERVICE_TYPE=SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
            elif self.document_type_id.name.getCode() in [24]: # /|\ ADD MORE DOCUMENTS
                WSDL_RESPONSE = self.soap_service(METHOD='recepcionDocumentoAjuste')
                
            if WSDL_RESPONSE:
                _logger.info(WSDL_RESPONSE)
                self.post_process_soap_siat(WSDL_RESPONSE)
            


    def post_process_soap_siat(self, res):
        self.write({'success': res.get('success')})
        if self.success:

            res_data = res.get('data', {})
            if res_data:
                self.write(
                    {
                        'edi_state' : res_data.codigoDescripcion,
                        'codigoEstado' : res_data.codigoEstado,
                        'codigoRecepcion' : res_data.codigoRecepcion,
                        'transaccion' : res_data.transaccion
                    }
                )
            self.setMessageList(res_data.mensajesList)
        
        try:
            
            self.write({'error' : res.get('error')})
        except:
            pass

    def setMessageList(self, _lists):
        while self.messagesList_ids:
            self.messagesList_ids[0].unlink()
        for _list in _lists:
            self.messagesList_ids.create({'code': _list.codigo, 'description': _list.descripcion, 'account_move_id': self.id  })
            
    
    def _check_partner_id(self):
        for record in self:
            if not record.force_send:    
                if record.pos_id and record.pos_id.getEmisionCode() == 1:
                    if record.partner_id.getNit() in ['99001', '99002', '99003']:
                        record.write({'force_send': True})
                        
                    elif record.partner_id.nit_state in ['NIT INEXISTENTE', 'NIT INACTIVO'] and not record.force_send:
                        raise UserError(record.partner_id.nit_state)
                else:
                    record.write({'force_send': True})
            if not record.partner_id.email:
                record.partner_id.write({'email': record.company_id.email })


    def generateCuf(self):
        _logger.info('GENERACION DEL CUF:')
        nit = self.company_id.getNit()
        nit = '0' * (13-len(nit)) + nit
        _logger.info(f'NIT : {nit}')

        fechaHora = self.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz'))
        fechaHora = self.getFechaHoraCuf(fechaHora.strftime("%Y%m%d%H%M%S%f"))
        _logger.info(f'FECHA Y HORA : {fechaHora}')
        
        sucursal = self.pos_id.branch_office_id.getCode()
        sucursal = '0' * (4-len(str(sucursal))) + str(sucursal)
        _logger.info(f'SUCURSAL : {sucursal}')

        modalidad = self.company_id.getL10nBoCodeModality()
        _logger.info(f'MODALIDAD : {modalidad}')
        

        emision = str(self.pos_id.getEmisionCode())
        _logger.info(f'TIPO EMISION : {emision}')
        
        tipoFactura = str(self.document_type_id.name.invoice_type_id.getCode())
        _logger.info(f'TIPO FACTURA : {tipoFactura}')
        
        docSector = self.document_type_id.getCode()
        docSector = '0' * (2-len(str(docSector))) + str(docSector)
        _logger.info(f'SECTOR : {docSector}')
        
        numeroFactura = '0' * (10-len(str(self.invoice_number))) + str(self.invoice_number)
        _logger.info(f'NRO. FACTURA : {numeroFactura}')
        
        pos = '0' * (4-len(str(self.pos_id.getCode()))) + str(self.pos_id.getCode())
        _logger.info(f'POS : {pos}')
        
        cadena = nit + fechaHora + sucursal + modalidad + emision + tipoFactura + docSector + numeroFactura + pos
        _logger.info(f'CONCATENADO : {cadena}')
        codAutoverificador = calculaDigitoMod11(cadena, 1, 9, False)
        cadena += str(codAutoverificador)
        _logger.info(f'MODULO 11 : {cadena}')

        _base16 = Base16(cadena) + self.pos_id.getControlCode()
        _logger.info(f'BASE 16 : {_base16}')
        return _base16
    
    def getFechaHoraCuf(self, date):
        fechaHora = ''
        if len(date) < 17:
            fechaHora = '0' * (17-len(date)) + date
        elif len(date) == 17:
            fechaHora = date
        elif len(date) > 17:
            for i in range(0,17):
                fechaHora += date[i]
        return fechaHora

    def str_edi_format(self):
        provider_modality = self.company_id.getL10nBoCodeModality()
        _str = ''
        
        if provider_modality == '1':
            _logger.info('FORMATO DE FACTURACION ELECTRONICA')
            _str = self.edi_format_electronic()
        elif provider_modality == '2':
            _logger.info('FORMATO DE FACTURACION COMPUTARIZADA')
            _str = self.edi_format_computerzed()
        return _str
    
    def edi_format_electronic(self):
        self.ensure_one()
        values = self.generate_electronic_format_srt()
        values = values.encode('utf-8')
        return values
    
    def generate_electronic_format_srt(self):
        _str = ''
        if self.document_type_id:
            if self.document_type_id.getCode() == 1:
                _str = self.purchase_sale_format_electronic()    
            elif self.document_type_id.getCode() == 3:
                _str = self.commercial_export_electronic()    
            elif self.document_type_id.getCode() == 8:
                _str = self.zero_rate_format_electronic()    
            elif self.document_type_id.getCode() == 14:
                _str = self.ice_format_electronic()    
            elif self.document_type_id.getCode() == 24:
                _str = self.credit_debit_note_format_electronic()    
            
            # others...
        return _str
    
    def edi_format_computerzed(self):
        self.ensure_one()
        values = self.generate_computerized_format_str()
        values = values.encode('utf-8')
        return values
    
    def generate_computerized_format_str(self) -> str:
        _str = ''
        if self.document_type_id:
            if self.document_type_id.getCode() == 1:
                _str = self.purchase_sale_format_computerized()
            elif self.document_type_id.getCode() == 3:
                _str = self.commercial_export_computerized()
            elif self.document_type_id.getCode() == 8:
                _str = self.zero_rate_format_computerized()
                
            elif self.document_type_id.getCode() == 14:
                _str = self.ice_format_computerized()
            elif self.document_type_id.getCode() == 24:
                _str = self.credit_debit_note_format_computerized()
            
            #others...
        return _str
    

    # CALCS
    def amountCurrency(self):
        amount_total = self.getAmountTotal() / self.currency_id.getExchangeRate() #self.tax_totals.get('amount_total', 0.00)# / self.currency_id.getExchangeRate()
        #raise UserError(f"{amount_total} - {self.amount_giftcard}")
        if self.document_type_id.getCode() == 3:
            #raise UserError(amount_total)
            pass#amount_total *= self.currency_id.getExchangeRate()#self.getAmountCostNationals()#self.getTotalNationalExpenseFob() + self.getAmountCostInternationals()
        
        #raise UserError(f'Moneda: {amount_total}')
        return round(amount_total, 2) #round(amount_total - self.amount_giftcard,2)
    
    
    def getAmountTotalExchageRate(self):
        amount_total = (self.amountCurrency() )
        return round(amount_total ,2)
    
    def getAmountTotal(self) -> float :
        if self.tax_totals:
            amount_total = 0
            for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.gif_product:
                    amount_total += line.getSubTotal()
                    if self.document_type_id.name.getCode() in [14]:
                        amount_total += line.getSpecificIce() + line.getPercentageIce()
                        amount_total = self.roundingUp(amount_total, 2)
            amount_total -= self.getAmountDiscount()
            if self.document_type_id.getCode() == 3:
                amount_total += self.getAmountCostNationals() + self.getAmountCostInternationals() 

            if self.document_type_id.getCode() in [28, 3, 4]:
                amount_total *= self.currency_id.getExchangeRate()
            
            return round(amount_total,2)
        return 0
    
    def getAmountOnIva(self) -> float:
        if self.document_type_id.name.invoice_type_id.getCode() != 2: # SOLO DOCUMENTOS CON CREDITO FISCAL
            amount = round(self.getAmountTotal() - self.getAmountGiftCard(),2)
            if self.document_type_id.getCode() in [14]:
                amount = round(amount - self.getAmountSpecificIce(5) - self.getAmountPercentageIce(), 2)
            #raise UserError(amount)
            return amount
        return 0
    

    def getAmountOnIvaExchageRate(self):
        return round(self.getAmountOnIva() / self.currency_id.getExchangeRate(), 2 )
        