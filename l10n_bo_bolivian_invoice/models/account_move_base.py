# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import random
import pytz
from datetime import datetime, timedelta
from num2words import num2words
import qrcode
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    
    edi_bo_invoice = fields.Boolean(
        string='Factura (BO)',
        related='journal_id.bo_edi',
        readonly=True,
        store=True
    )
    
    
    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        ondelete='restrict',
        default= lambda self : self.get_branch_office_default()
    )


    @api.model
    def create(self, values):
        account_move_id = super(AccountMove, self).create(values)
        account_move_id.prepare_fields()
        return account_move_id
    

    
    @api.onchange('move_type')
    @api.constrains('move_type')
    def prepare_fields(self):
        for record in self:
            if record.edi_bo_invoice:
                record.write(
                    {
                        'branch_office_id' : record.get_branch_office_default(),
                        'legend_id' : record.get_legend_default(record.company_id.getGrandParent().id if record.company_id else None )
                    }
                )
                record._set_default_document_type()
                
    def get_branch_office_default(self):
        branch_office_id = self.env['l10n.bo.branch.office'].search([('company_id','=',self.company_id.id)], limit=1)
        if branch_office_id:
            _logger.info(f"Sucursal por defecto:{branch_office_id.name}")
            return branch_office_id.id
        _logger.info("No se encontro una sucursal:")
        return False
    
    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
    )

    
    emision_type_id = fields.Many2one(
        string='Tipo emisión',
        comodel_name='l10n.bo.type.emision',
        related='pos_id.emision_id',
        readonly=True,
        store=True
    )
    
    
    many_pos = fields.Boolean(
        string='Muchas puntos de venta',
        compute='_compute_many_pos', 
    )
    
    def _compute_many_pos(self):
        for record in self:
            record.many_pos = True if len(record.env['l10n.bo.pos'].search([])) > 1 else False
    
    
    @api.onchange('branch_office_id')    
    @api.constrains('branch_office_id')
    def _check_branch_office_id(self):
        for record in self:
            if record.branch_office_id and not record.pos_id:
                record.write(
                    {
                        'pos_id' :  record.branch_office_id.l10n_bo_pos_ids[0].id if record.branch_office_id and record.branch_office_id.l10n_bo_pos_ids else False
                    }
                ) 
                self._set_default_document_type()
                #if self.pos_id:
                #    
        
    
    meridies = fields.Selection(
        string='Meridiano',
        selection=[('am', 'AM'), ('pm', 'PM')]
    )
    

    
    invoice_date_edi = fields.Datetime(
        string='Fecha de la factura',
        default=fields.Datetime.now,
        copy=False
    )
    
    
    @api.constrains('invoice_date_edi')
    def _check_invoice_date_edi(self):
        for record in self:
            if record.edi_bo_invoice and record.move_type in ['out_invoice','out_refund']:
                record.write({'invoice_date' : record.invoice_date_edi})
    
    def get_formatted_datetime(self):
        if self.invoice_date_edi:
            emision_date_utc = self.invoice_date_edi.replace(tzinfo=None).astimezone(pytz.UTC)
            # Restar 4 horas a la fecha y hora
            emision_date_minus_4_hours = emision_date_utc - timedelta(hours=4)
            return emision_date_minus_4_hours.strftime("%d/%m/%Y %I:%M")
        else:
            return ''

    
    document_type_id = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.pos.sequence',
    )

    

    document_type_code = fields.Integer(
        string='Código de documento',
        related='document_type_id.name.codigoClasificador',
        readonly=True,
        store=True   
    )
    

    invoice_type_code = fields.Integer(
        string='Codigo tipo tipo documento',
        related='document_type_id.name.invoice_type_id.codigoClasificador',
        readonly=True,
        store=True
        
    )
    

    
    #@api.onchange('move_type', 'edi_bo_invoice')
    def _set_default_document_type(self):
        for record in self:
            if record.edi_bo_invoice:
                doc_type_id = False
            
                #raise UserError(record.move_type)
                if record.move_type == 'out_invoice':
                    dt = record.pos_id.sequence_ids.filtered(lambda document_type_sequence : document_type_sequence.getCode() == 1)[:1]
                    if dt:
                        doc_type_id = dt.id
                
                elif record.move_type == 'out_refund':
                    dt = record.pos_id.sequence_ids.filtered(lambda document_type_sequence : document_type_sequence.getCode() == 24)[:1]
                    if dt and record.document_type_id and record.document_type_id.name.invoice_type_id.getCode() != 3 :
                        doc_type_id = dt.id
                        record.write({'document_type_id' : doc_type_id})
                if doc_type_id and not record.document_type_id:
                    record.write({'document_type_id' : doc_type_id})
        

    
    payment_type_id = fields.Many2one(
        string='Tigo pago',
        comodel_name='l10n.bo.type.payment',
        ondelete='restrict',
        default= lambda self : self.get_payment_type_default()
    )
    
    def get_payment_type_default(self):
        payment_type = self.env['l10n.bo.type.payment'].search([('codigoClasificador','=',1)], limit=1)
        return payment_type.id if payment_type  else False
    

    
    error = fields.Text(
        string='Error',
        copy=False,
        readonly=True
    )
    
    
    legend_id = fields.Many2one(
        string='Leyenda',
        comodel_name='l10n.bo.legend.code',
        ondelete='restrict',
        default= lambda self : self.get_legend_default()
    )
    
    
    @api.onchange('company_id')
    @api.constrains('company_id')
    def _check_company_id(self):
        for record in self:
            _logger.info(f"Compañia: {record.company_id.getGrandParent().name}")
            if not record.legend_id and record.company_id:
                record.write({'legend_id' : record.get_legend_default(record.company_id.getGrandParent().id)})
    
    
    def get_legend_default(self, company_id = None):
        if not self.legend_id:
            legends = self.env['l10n.bo.legend.code'].search([('company_id','=',self.company_id.id if not company_id else company_id)])            
            return legends[random.randint(0,len(legends)-1)].id if legends else False
    
    
    amount_giftcard = fields.Float(
        string='Monto Giftcard',
        copy=False
    )

    def getAmountGiftCard(self):
        if self.is_gift_card:
            ld = self.invoice_line_ids.filtered(lambda l: l.product_id.gift_card_product)
            if not ld:
                self.write({'amount_giftcard' : 0.0})
            elif ld and self.amount_giftcard == 0:
                self.write({'amount_giftcard' : ld[0].price_unit * -1})
            
            amount = round(self.amount_giftcard * self.currency_id.getExchangeRate() , 2)

            return  amount
        return 0
        
    

    is_gift_card = fields.Boolean(
        string='¿Es gift card?',
    )
    
    @api.onchange('payment_type_id')
    def _compute_is_gift_card(self):
        for record in self:
            is_gift_card = False
            if record.payment_type_id and 'GIFT' in record.payment_type_id.descripcion:
                is_gift_card = True
            record.write({'is_gift_card' :  is_gift_card})
    
    card = fields.Char(
        string='Tarjeta',
        size=16
    )
    

    is_card = fields.Boolean(string='¿Es tarjeta?' )
    
    @api.onchange('payment_type_id')
    @api.constrains('payment_type_id')
    def _onchange_payment_type_id(self):
        for record in self:
            is_card = False
            if record.payment_type_id and 'TARJETA' in record.payment_type_id.descripcion:
                is_card = True
            record.write({'is_card':is_card}) 
    
    
    invoice_number = fields.Integer(
        string='Nro. Factura',
        copy=False,
        readonly=True 
    )
    
    
    force_send = fields.Boolean(
        string='Forzar envio',
        copy=False,
        help='Activar para enviar factura con codigo de excepción 1'
    )

    
    nit_state = fields.Char(
        string='Estado del nit',
        related='partner_id.nit_state',
        readonly=True,
        store=True
    )
    
    
    
    
    cuf = fields.Char(
        string='Cuf',
        help='Codigo unico de facturación.',
        copy=False,
        readonly=True 
    )

    edi_str = fields.Text(
        string='Formato edi',
        copy=False,
        readonly=True 
    )
    
    
    sector_document_id = fields.Many2one(
        string='Documento sector',
        comodel_name='l10n.bo.activity.document.sector',
        related='document_type_id.name.sector_document_id',
        readonly=True,
        store=True,
        company_dependent=True,
    )
    
    signed_edi_str = fields.Binary(
        string='Formato edi firmado',
        copy=False,
        readonly=True 
    )

    zip_edi_str = fields.Binary(
        string='Documento ZIP',
        copy=False,
        readonly=True 
    )

    
    
    hash = fields.Binary(
        string = 'HASH',
        copy=False,
        readonly=True 
    )


    
    url = fields.Char(
        string='url',
        copy=False,
        readonly=True 
    )
    
    edi_state = fields.Char(
        string='Estado edi',
        copy=False,
        readonly=True 
    )
    
    
    transaccion = fields.Boolean(
        string='Transacción',
        readonly=True,
        copy=False
    )
    
    
    codigoEstado = fields.Integer(
        string='Codigo de estado',
        copy=False
    )
    
    
    codigoRecepcion = fields.Char(
        string='Codigo recepción',
        copy=False
    )
    
    messagesList_ids = fields.One2many(
        string='Lista de mensajes',
        comodel_name='message.code',
        inverse_name='account_move_id',
        copy=False
    )


    
    code_environment = fields.Selection(
        string='Codigo de entorno',
        related='company_id.l10n_bo_code_environment',
        readonly=True,
        store=True
    )
    
    def getLiteral(self):
        parte_entera = int(self.getAmountTotalExchageRate())
        parte_decimal = int( round((self.getAmountTotalExchageRate() - parte_entera),2) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        return num2words(parte_entera, lang='es') + parte_decimal +'/100'
    
    def getBolivianLiteral(self):
           
        amount_total = self.getAmountOnIva() if self.document_type_code not in [28, 8, 3] else self.getAmountTotal() # * self.currency_id.getExchangeRate()
        
        if self.document_type_code in [14]:
            amount_total += self.getAmountSpecificIce() + self.getAmountPercentageIce()

        parte_entera = int(amount_total)
        parte_decimal = int( round((amount_total - parte_entera),2) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        return num2words(parte_entera, lang='es') + parte_decimal +'/100'
    
    
    def getAmountSubTotal(self):
        if self.document_type_id.getCode() not in [28]:
            return round(self.getAmountTotal() + self.getAmountDiscount(), 2)
        return round(self.tax_totals.get('amount_total', 0.00) + self.getAmountDiscount(), 2)
    
    

    def generate_qr(self):
            image = qrcode.make(
                f"{self.url}"
            ).get_image()
            buff = BytesIO()
            image.save(buff, format="PNG")
            return base64.b64encode(buff.getvalue()).decode('utf-8')
    

    
    success = fields.Boolean(
        string='Realizado',
        copy=False,
        readonly=True 
    )
    
    def showMessage(self, title, body):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'{title}',
                'message': f'{body}',
                'sticky': False,
            }
        }

    @api.model
    def get_datetime_bo(self):
        # Realizar la consulta SQL
        self.env.cr.execute("""
            SELECT current_timestamp AT TIME ZONE 'America/La_Paz'
        """)
        
        # Obtener el resultado de la consulta
        result = self.env.cr.fetchone()

        # El resultado estará en el índice 0
        datetime_bo = result[0] if result else None

        return datetime_bo
    
    def get_datetime(self):
        # Obtener la fecha y hora actual en la zona horaria de Bolivia (America/La_Paz)
        tz_bolivia = pytz.timezone('America/La_Paz')
        current_datetime = datetime.now(tz_bolivia)

        # Convertir el objeto datetime a UTC antes de asignarlo al campo
        current_datetime_utc = current_datetime.astimezone(pytz.UTC)

        # Eliminar la información de la zona horaria (convierte el objeto a "ingenuo")
        current_datetime_naive = current_datetime_utc.replace(tzinfo=None)

        return current_datetime_naive
    
    