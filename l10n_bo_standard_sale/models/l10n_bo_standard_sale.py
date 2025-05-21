# -*- coding:utf-8 -*-

from odoo import api, models, fields
import xlwt
import base64
from io import BytesIO
from odoo.exceptions import UserError

class L10nBoStandardSale(models.Model):
    _name = "l10n.bo.standard.sale"
    _description = "Ventas Estándar (BO)"

    
    name = fields.Char(
        string='Nombre',
        readonly=True 
    )

    
    date_from = fields.Date(
        string='Desde',
        company_dependent=True
    )
    
    date_to = fields.Date(
        string='Hasta',
        company_dependent=True
    )
    
    
    
    standard_sale_line_ids = fields.One2many(
        string='Lineas de registro de ventas estandar',
        comodel_name='l10n.bo.standard.sale.line',
        inverse_name='standard_sale_id',
    )
    
    
    
    def unlink(self):
        raise UserError('Accion no permitida')

    def get_preview_registers(self, PARAMS):
        l10n_bo_standard_sale_line_ids =  self.env['l10n.bo.standard.sale.line'].search(PARAMS)
        for l10n_bo_standard_sale_line_id in l10n_bo_standard_sale_line_ids:
            l10n_bo_standard_sale_line_id.write({'standard_sale_id': self.id})

    def get_invoice_ids(self):
        PARAMS = [
            ('move_type','=','out_invoice'),
            ('state','!=','draft'),
            ('document_type_id','!=',False),
            ('edi_bo_invoice','=',True),
            ('edi_state','not in',[False,'',None]),
            
        ]
        preview_params = []
        if self.date_from and self.date_to:
            PARAMS.append(('invoice_date_edi','>=', self.date_from))
            PARAMS.append(('invoice_date_edi','<=', self.date_to))
            preview_params = [('invoice_date','>=', self.date_from), ('invoice_date','<=', self.date_to)]
        
        self.get_preview_registers(preview_params)
        
            
        return self.env['account.move'].search(
            PARAMS,
            order='invoice_date_edi desc'
        )

    def create_invoice_records(self, invoice_ids):
        new_l10n_bo_standard_line_records = []
        for invoice_id in invoice_ids:
            params = {
                'invoice_id'    :  invoice_id.id,
                #'name'          :  invoice_id.sequence_rv,
                'invoice_date'  :  invoice_id.invoice_date_edi,
                'invoice_number'  :  invoice_id.invoice_number,
                'autorization_code' :  invoice_id.cuf,
                'nit_ci'        :  invoice_id.getPartnerNit(),
                'complement'    :  invoice_id.getPartnerComplement(),
                'reazon_social' :  invoice_id.getNameReazonSocial(),
                'amount_total'  :  invoice_id.getAmountTotal(),
                #'amount_ice'    :  invoice_id.getAmountIce(),
                #'amount_iehd'   :  invoice_id.getAmountIehd(),
                #'amount_ipj'    :  invoice_id.getAmountIpj(),
                #'amount_rate'   :  invoice_id.getAmountRate(),
                #'amount_no_iva' :  invoice_id.getAmountNoIva(),
                #'amount_exempt' :  invoice_id.getAmountExempt(),
                #'amount_cero_rate'   :  invoice_id.getAmountCeroRate(),
                'amount_discount' : round(invoice_id.getAmountDiscount() + invoice_id.getAmountLineDiscount(), 2),
                'amount_gift_card'    :  invoice_id.getAmountGiftCard(),
                'state'         :  invoice_id.edi_state,
                'control_code'  : '0',
                'register_type' : '0',
                'standard_sale_id' : self.id,
            }
            new_l10n_bo_standard_line_records.append(params)
        if new_l10n_bo_standard_line_records:
            self.env['l10n.bo.standard.sale.line'].create(new_l10n_bo_standard_line_records)

    def clean_register_olds(self):
        for standard_sale_line_id in self.standard_sale_line_ids:
            standard_sale_line_id.write({'standard_sale_id': False})

    
    def action_update(self):
        self.clean_register_olds()
        invoice_ids = self.get_invoice_ids()
        if invoice_ids:
            new_lines = []
            l10n_bo_rv_list_ids = [ line.invoice_id.id for line in self.standard_sale_line_ids if line.invoice_id ]
            for invoice_id in invoice_ids:
                if invoice_id.id not in l10n_bo_rv_list_ids:
                    new_lines.append(invoice_id)
            
            if new_lines:
                self.create_invoice_records(new_lines)

        if self.standard_sale_line_ids:
            self.sequence_assign()

    def sequence_assign(self):
        sequence = 1
        for line_id in self.standard_sale_line_ids:
            line_id.write({'name':sequence})
            sequence += 1


    def get_column_fields(self) -> list:
        fields = []
        for field_name, field in self.standard_sale_line_ids._fields.items():
            if field_name not in ('name','specification', 'invoice_date','invoice_number','autorization_code','nit_ci','complement','reazon_social','amount_total','amount_ice','amount_iehd','amount_ipj','amount_rate','amount_no_iva','amount_exempt','amount_cero_rate','amount_subtotal','amount_discount','amount_gift_card','state','amount_gift_card','amount_fiscal_debit_base','amount_fiscal_debit','state','control_code','register_type'):
                continue
            field_label = {
                'campo': field_name,
                'string': field.string,
                'type': field.type
            }
            fields.append(field_label)
        return fields

    excel_file = fields.Binary(
        string="Archivo Excel",
        company_dependent=True
    )

    def generate_excel_file(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet('Registros de ventas')
        bold_style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        bold_style.font = font
        headers = self.get_column_fields() 
        if headers:
            for col, header in enumerate(headers):
                worksheet.write(0, col, header.get('string'), bold_style)
            row = 1
            for record in self.standard_sale_line_ids:
                for i in range(len(headers)):
                    value = getattr(record,headers[i].get('campo'))
                    if not value:
                        _type = headers[i].get('type')
                        if _type == 'float':
                            value = 0.00
                        elif _type == 'char':
                            value = ''
                    worksheet.write(row, i, value)
                row += 1
            excel_buffer = BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)
            excel_base64 = base64.b64encode(excel_buffer.getvalue())
            excel_buffer.close()
            return excel_base64
        raise UserError('No se contraron campos para las columnas')
    
    def download_excel_file(self):
        if len(self.standard_sale_line_ids)>0:
            self.write({'excel_file': False})
            excel_data = self.generate_excel_file()
            self.write({'excel_file': excel_data})
            return {
                'type': 'ir.actions.act_url',
                'url': f'web/content/?model={self._name}&id={self.id}&field=excel_file&download=true&filename=RegistroVentas.xls',
                'target': 'self',
            }