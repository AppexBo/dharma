/** @odoo-module */

import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.identification_types = loadedData['l10n.bo.type.document.identity'];    
        this.pos_config = loadedData['pos.config'];    
        this.pos_payment_ref = loadedData['pos.payment'];
         
        //this.ui_res_partner = loadedData['res.partner'];    
        
        
    },
});