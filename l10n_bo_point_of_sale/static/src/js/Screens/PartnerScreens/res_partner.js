/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";

patch(PartnerDetailsEdit.prototype, {
    setup() {
        super.setup(...arguments);
        this.intFields.push("identification_type_id", "complement", "nit_state");
        this.changes.identification_type_id = this.props.partner.identification_type_id && this.props.partner.identification_type_id[0];
        this.changes.complement = this.props.partner.complement;
        this.changes.nit_state = this.props.partner.nit_state;
        this.changes.exception = this.props.partner.exception;
    },
    saveChanges() {
        return super.saveChanges(...arguments);
    },
});