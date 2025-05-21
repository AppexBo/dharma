# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountMoveParams(models.Model):
    _inherit = ['account.move']


    #####  < PARAMETROS DE EMISION > ####

    def getReceptionARGS(self, METHOD = False):
        if METHOD:
            return {
                METHOD : {
                    'codigoAmbiente'    : self.company_id.getL10nBoCodeEnvironment(),
                    'codigoPuntoVenta'  : self.getPosCode(),
                    'codigoSistema'     : self.company_id.getL10nBoCodeSystem(),
                    'codigoSucursal'    : self.getBranchCode(),
                    'nit'               : self.company_id.getNit(),
                    'codigoDocumentoSector' : self.sector_document_id.getCode(),
                    'codigoEmision'     : self.pos_id.getEmisionCode(),
                    'codigoModalidad'   : self.company_id.getL10nBoCodeModality(),
                    'cufd'              : self.pos_id.getCufd(),
                    'cuis'              : self.pos_id.getCuis(),
                    'tipoFacturaDocumento'  : self.document_type_id.name.invoice_type_id.getCode(),
                    'archivo'           : self.zip_edi_str,
                    'fechaEnvio'        :  self.pos_id.getFechaHora().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
                    'hashArchivo'       : self.hash
                }
            } 
        raise UserError('NO se encontro un metodo para la operacion')
    
    def recepcionFactura(self, WSDL_SERVICE):
        OBJECT = self.getReceptionARGS(METHOD = 'SolicitudServicioRecepcionFactura')
        WSDL = WSDL_SERVICE.getWsdl()
        #raise UserError(f"{OBJECT}")
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'recepcionFactura')
        return WSDL_RESPONSE


    def recepcionDocumentoAjuste(self, WSDL_SERVICE):
        OBJECT = self.getReceptionARGS(METHOD = 'SolicitudServicioRecepcionDocumentoAjuste')
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'recepcionDocumentoAjuste')
        return WSDL_RESPONSE
