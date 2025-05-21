# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools import (is_html_empty)
import logging
_logger = logging.getLogger(__name__)




class AccountMove(models.Model):
    _inherit = ['account.move']
       
    
    def commercial_export_format(self):
        cabecera = """<cabecera>"""
        cabecera += f"""<nitEmisor>{self.company_id.getNit()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getCompanyName()}</razonSocialEmisor>"""
        cabecera += f"""<municipio>{self.getMunicipality()}</municipio>"""
        cabecera += f"""<telefono>{self.getPhone()}</telefono>"""
        cabecera += f"""<numeroFactura>{self.invoice_number}</numeroFactura>"""
        cabecera += f"""<cuf>{self.getCuf()}</cuf>"""
        cabecera += f"""<cufd>{self.getCufd()}</cufd>"""
        cabecera += f"""<codigoSucursal>{self.getBranchCode()}</codigoSucursal>"""
        cabecera += f"""<direccion>{self.getAddress()}</direccion>"""
        cabecera += f"""<codigoPuntoVenta>{self.getPosCode()}</codigoPuntoVenta>"""
        cabecera += f"""<fechaEmision>{self.getEmisionDate()}</fechaEmision>"""
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial()}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.getPartnerNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.getPartnerComplement()}</complemento>""" if self.getPartnerComplement() else """<complemento xsi:nil="true"/>"""
        
        cabecera += f"""<direccionComprador>{self.getDestinationAddress()}</direccionComprador>"""
        
        cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""

        cabecera += f"""<incoterm>{self.getIncoterm()}</incoterm>"""
        cabecera += f"""<incotermDetalle>{self.getDetailedIncoterm()}</incotermDetalle>"""
        cabecera += f"""<puertoDestino>{self.getDestinationPort()}</puertoDestino>"""
        cabecera += f"""<lugarDestino>{self.getDestinationPlace()}</lugarDestino>"""
        cabecera += f"""<codigoPais>{self.getCountryCode()}</codigoPais>"""

        cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
        cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
        cabecera += f"""<montoTotal>{self.getAmountTotal()}</montoTotal>"""
        
        cabecera += f"""<costosGastosNacionales>{self.getCostExpenseNational()}</costosGastosNacionales>""" if self.getCostExpenseNational() else """<costosGastosNacionales xsi:nil="true"/>"""
        cabecera += f"""<totalGastosNacionalesFob>{self.getTotalNationalExpenseFob()}</totalGastosNacionalesFob>""" if self.getTotalNationalExpenseFob()>0 else """<totalGastosNacionalesFob xsi:nil="true"/>"""
        
        cabecera += f"""<costosGastosInternacionales>{self.getCostExpenseInternational()}</costosGastosInternacionales>""" if self.getCostExpenseInternational() else """<costosGastosInternacionales xsi:nil="true"/>"""
        cabecera += f"""<totalGastosInternacionales>{self.getAmountCostInternationals()}</totalGastosInternacionales>""" if self.getAmountCostInternationals()>0 else """<totalGastosInternacionales xsi:nil="true"/>"""
        cabecera += f"""<montoDetalle>{self.getAmountDetailed()}</montoDetalle>""" 
        
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva()}</montoTotalSujetoIva>"""
        cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
        cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
        cabecera += f"""<montoTotalMoneda>{self.amountCurrency()}</montoTotalMoneda>"""
        
        cabecera += f"""<numeroDescripcionPaquetesBultos>{self.getDescriptionPaquetesBulk()}</numeroDescripcionPaquetesBultos>""" if self.aditional_description else """<numeroDescripcionPaquetesBultos xsi:nil="true"/>"""
        cabecera += f"""<informacionAdicional>{self.getNarration()}</informacionAdicional>""" if not is_html_empty(self.narration) else """<informacionAdicional xsi:nil="true"/>"""
        
        cabecera += f"""<descuentoAdicional>{self.getAmountDiscount()}</descuentoAdicional>""" if self.amount_discount > 0 else """<descuentoAdicional xsi:nil="true"/>"""
        cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        cabecera += f"""<cafc>{self.getCafc()}</cafc>""" if self.getCafc() else """<cafc xsi:nil="true"/>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        cabecera += f"""<codigoDocumentoSector>{self.getDocumentSector()}</codigoDocumentoSector>"""
        cabecera += """</cabecera>"""
        
        detalle  = """"""
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode()}</codigoProducto>"""
                detalle += f"""<codigoNandina>{line.product_id.getNandinaCode()}</codigoNandina>"""
                detalle += f"""<descripcion>{line.name}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
                detalle += """</detalle>"""
        return cabecera + detalle    

    def commercial_export_computerized(self):
        commercial_export_format = f"""<facturaComputarizadaComercialExportacion xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="facturaComputarizadaComercialExportacion.xsd">"""
        commercial_export_format += self.commercial_export_format()
        commercial_export_format += f"""</facturaComputarizadaComercialExportacion>"""
        return commercial_export_format
    
    def commercial_export_electronic(self):
        commercial_export_format = f"""<facturaElectronicaComercialExportacion xsi:noNamespaceSchemaLocation="facturaElectronicaComercialExportacion.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        commercial_export_format += self.commercial_export_format()
        commercial_export_format += f"""</facturaElectronicaComercialExportacion>"""
        return commercial_export_format
    
    destination_address = fields.Char(
        string='Dirección destino',
    )
    
    def getDestinationAddress(self):
        if self.destination_address:
            return self.destination_address
        raise UserError("Establesca una direccion de entrega")
    
    def getDestinationPlace(self):
        if self.country_id:
                return self.country_id.getName()
        raise UserError(f"El cliente: {self.partner_id.name} no tiene un pais establecido")
        
    country_id = fields.Many2one(
        string='Pais',
        comodel_name='res.country',
        ondelete='restrict',
        domain=[('l10n_bo_country_id','!=',False)]
    )

    def getNarration(self):
        _narration = str(self.narration)
        _narration = _narration.replace('<br>','').replace("&nbsp;", " ").replace('<p>','').replace('</p>',' ')
        return _narration
    

    def getCountryCode(self):
        if self.country_id:
                return self.country_id.getCode()
        raise UserError(f"El Cliente: {self.partner_id.name} no tiene un pais establecido.")
    
    def getIncoterm(self):
        if self.invoice_incoterm_id:
            return self.invoice_incoterm_id.code
        raise UserError('Necesita establecer un Código de términos de comercio internacional - INCOTERM')
    
    def getDetailedIncoterm(self):
        if self.invoice_incoterm_id:
            return self.invoice_incoterm_id.name
        raise UserError('Necesita establecer un Código de términos de comercio internacional - INCOTERM')
    
    def getDestinationPort(self):
        if self.country_state_id:
            return self.country_state_id.name
        raise UserError('Debe establecer un Estado/Departamento destino.')
    
    
    country_state_id = fields.Many2one(
        string='Estado (BO)',
        comodel_name='res.country.state',
        ondelete='restrict',
        help='Deptartamento/Estado/Puerto al que se exporta.'        
    )

    def validate_CostExpenseNational(self):
        pass

    def getCostExpenseNational(self):
        self.validate_CostExpenseNational()
        expenses = {}
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and  line.product_id.national_cost:
                amount = expenses.get(line.name, 0)
                expenses[line.name] = (line.quantity * line.price_unit) + amount
                
        return expenses
    
    """
    cost_expense_national_ids = fields.One2many(
        string='Costo gastos nacionales (BO)',
        comodel_name='cost.expense.national',
        inverse_name='account_move_id',
    )
    """

    

    def getAmountDetailed(self):
        amount_total = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                amount_total += line.getSubTotal()
        return round(amount_total, 2)

    def getTotalNationalExpenseFob(self):
        return round(self.getAmountCostNationals() + self.getAmountDetailed(), 2)

    def getAmountCostNationals(self):
        cost_nationals = self.getCostExpenseNational()
        if cost_nationals:
            amount = 0
            for amount_cost_national in cost_nationals.values():
                amount += amount_cost_national
            return amount
        return 0

    
    def getCostExpenseInternational(self):
        expenses = {}
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and  line.product_id.international_cost:
                amount = expenses.get(line.name, 0)
                expenses[line.name] = (line.quantity * line.price_unit) + amount
                
        return expenses
    
    def getAmountCostInternationals(self):
        cost_internationals = self.getCostExpenseInternational()
        if cost_internationals:
            amount = 0
            for amount_cost_international in cost_internationals.values():
                amount += amount_cost_international
            return amount
        return 0

    """
    cost_expense_international_ids = fields.One2many(
        string='Costo gastos internacionales (BO)',
        comodel_name='cost.expense.international',
        inverse_name='account_move_id',
    )
    """
    aditional_description = fields.Text(
        string='Descripción adicional',
        copy=False
    )
    
    def set_country_id(self, country_id):
        self.write({'country_id' : country_id.id})
    
    @api.onchange('partner_id')
    def _onchange_exportation_partner_id(self):
        if self.partner_id and self.partner_id.country_id and self.partner_id.country_id.l10n_bo_country_id:
            self.set_country_id(self.partner_id.country_id)
            if self.partner_id.state_id:
                self.set_state_country_id(self.partner_id.state_id)
        
        if self.partner_id and self.partner_id.street:
            self.write({'destination_address' : self.partner_id.street})
        

    
    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            if not record.country_id:
                record._onchange_exportation_partner_id()
            
    
    def set_state_country_id(self, state_country_id):
        self.write({'country_state_id' : state_country_id.id})


    def getDescriptionPaquetesBulk(self):
        return self.aditional_description
