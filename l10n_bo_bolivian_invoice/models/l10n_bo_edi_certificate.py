# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
import logging

from copy import deepcopy
from lxml import etree
from pytz import timezone
from datetime import datetime
from odoo.exceptions import ValidationError
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from signxml import XMLSigner
from base64 import b64decode, b64encode


_logger = logging.getLogger(__name__)


class Certificate(models.Model):
    _name = 'l10n.bo.edi.certificate'
    _description = 'SIAT Digital Certificate'
    _order = 'date_start desc, id desc'
    _rec_name = 'serial_number'

    content = fields.Binary(string="Certificado", required=True, help="PFX Certificate")
    password = fields.Char( string="Contraseña", help="Passphrase for the PFX certificate")
    serial_number = fields.Char(readonly=True, index=True, help="The serial number to add to electronic documents")
    date_start = fields.Datetime(string="Fecha de inicio",  readonly=True, help="The date on which the certificate starts to be valid")
    date_end = fields.Datetime(string="Fecha de expiracion", readonly=True, help="The date on which the certificate expires")
    company_id = fields.Many2one( string="Compañia", comodel_name='res.company', required=True, default=lambda self: self.env.company)

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    @api.model
    def _get_pe_current_datetime(self):
        bolivian_tz = timezone('America/Lima')
        return datetime.now(bolivian_tz)

    @tools.ormcache('self.content', 'self.password')
    def _decode_certificate(self):
        "Return: _private_key, _cert"
        self.ensure_one()
        cert = pkcs12.load_key_and_certificates(b64decode(self.content), self.password.encode(), default_backend())
        return cert[0], cert[1]

    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        record = super(Certificate, self).create(vals)
        self.env.company.partner_id.write({'tz': 'America/La_Paz'})
        if not self.env.company.partner_id.tz:
            raise ValidationError(_('Time Zone no configured in company'))
        bolivian_tz = timezone(self.env.company.partner_id.tz)
        bolivian_dt = self._get_pe_current_datetime()
        try:
            dummy, certificate = record._decode_certificate()
            serial_number = certificate.serial_number
            cert_date_start = bolivian_tz.localize(certificate.not_valid_before)
            cert_date_end = bolivian_tz.localize(certificate.not_valid_after)
        except:
            raise ValidationError(_('There has been a problem with the certificate, some usual problems can be:\n'
                                    '- The password given or the certificate are not valid.\n'
                                    '- The certificate content is invalid.'))
        # Assign extracted values from the certificate
        record.write({
            'serial_number': ('%x' % serial_number)[1::2],
            'date_start': fields.Datetime.to_string(cert_date_start),
            'date_end': fields.Datetime.to_string(cert_date_end),
        })
        if bolivian_dt > cert_date_end:
            raise ValidationError(_('The certificate is expired since %s') % record.date_end)
        return record

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _sign(self, edi_tree):
        self.ensure_one()
        _private_key, _cert = self._decode_certificate()
        edi_tree_copy = deepcopy(edi_tree)
        etree.SubElement(edi_tree_copy, '{http://www.w3.org/2000/09/xmldsig#}Signature', Id='placeholder',
                         nsmap={None: 'http://www.w3.org/2000/09/xmldsig#'})
        signed_edi_tree = XMLSigner(c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
                                    signature_algorithm=u'rsa-sha256',
                                    digest_algorithm=u'sha256').sign(edi_tree_copy, key=_private_key, cert=[_cert])
        signed_edi_tree = etree.tostring(signed_edi_tree).replace(b'\n', b'')
        return signed_edi_tree
    


