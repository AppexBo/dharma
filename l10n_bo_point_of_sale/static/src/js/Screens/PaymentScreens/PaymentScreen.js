/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";

class CustomPaymentScreen extends PaymentScreen {
    setup() {
        super.setup();
    }

    async IsPaymentReferenceButton() {
        let startingValue = '';
        if (this.pos.pos_payment_ref.length > 0 && this.pos.pos_payment_ref[this.pos.pos_payment_ref.length-1].order == this.pos.get_order().name) {
            startingValue = this.pos.pos_payment_ref[this.pos.pos_payment_ref.length - 1].card;
        }
        
        let { confirmed, payload: code } = await this.env.services.popup.add(TextInputPopup, {
            title: 'Tarjeta',
            startingValue: startingValue,
            placeholder: 'eg:1234567890123456',
        });
        if (confirmed) {
            code = code.trim();
                        if (code !== '') {
                            if (code.length === 16) {
                                if (this.pos.pos_payment_ref.length > 0) {
                                    this.pos.pos_payment_ref[this.pos.pos_payment_ref.length - 1].card = code;
                                    this.pos.pos_payment_ref[this.pos.pos_payment_ref.length - 1].order = this.pos.get_order().name;
                                    
                                    await jsonrpc( '/create_card', {name: this.pos.get_order().name, card: code })

                                } else if (this.pos.pos_payment_ref.length === 0) {
                                    this.pos.pos_payment_ref.card = code;
                                    this.pos.pos_payment_ref.order = this.pos.get_order().name;
                                    await jsonrpc( '/create_card', {name: this.pos.get_order().name, card: code })
                                }
                            } else {
                                alert("Ta tarjeta debe tener exactamente 16 caracteres.");
                            }
                        }
                        else {
                            if (this.pos.pos_payment_ref.length > 0) {
                                this.pos.pos_payment_ref[this.pos.pos_payment_ref.length - 1].card = false;
                                
                            } else if (this.pos.pos_payment_ref.length === 0) {
                                this.pos.pos_payment_ref.card = false;
                            }
                        }
        }
    }
}

registry.category("actions").add("custom_payment_screen", CustomPaymentScreen);

patch(PaymentScreen.prototype, {
    async IsPaymentReferenceButton() {
        await CustomPaymentScreen.prototype.IsPaymentReferenceButton.call(this);
    }
});
