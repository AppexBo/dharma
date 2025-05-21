# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountMove8(models.Model):
    _inherit = ['account.move']

    

    def zero_rate_format(self):
        if self.pos_id.zero_rate_type:
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
            cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""
            cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
            cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
            cabecera += f"""<montoTotal>{self.getAmountTotal()}</montoTotal>"""
            cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva()}</montoTotalSujetoIva>"""
            cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
            cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
            cabecera += f"""<montoTotalMoneda>{self.amountCurrency()}</montoTotalMoneda>"""
            cabecera += f"""<montoGiftCard>{self.getAmountGiftCard()}</montoGiftCard>""" if self.is_gift_card and self.amount_giftcard > 0 else """<montoGiftCard xsi:nil="true"/>"""
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
                    detalle += f"""<descripcion>{line.name}</descripcion>"""
                    detalle += f"""<cantidad>{line.getQuantity(self.document_type_code)}</cantidad>"""
                    detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                    detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                    detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                    detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
                    detalle += """</detalle>"""
                
            return cabecera + detalle
        raise UserError(f"{self.pos_id.name}, no tiene seleccionado un regimen para el tipo Documento: TASA CERO")
    
    def zero_rate_format_computerized(self):

        _format = f"""<facturaComputarizadaTasaCero xsi:noNamespaceSchemaLocation="facturaComputarizadaTasaCero.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        _format += self.zero_rate_format()
        _format += f"""</facturaComputarizadaTasaCero>"""
        return _format
    

    def zero_rate_format_electronic(self):

        _format = f"""<facturaElectronicaTasaCero xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="facturaElectronicaTasaCero.xsd">"""
        _format += self.zero_rate_format()
        _format += f"""</facturaElectronicaTasaCero>"""
        return _format