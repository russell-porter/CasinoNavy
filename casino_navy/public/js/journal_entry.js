frappe.ui.form.on("Journal Entry", {
    refresh(frm){
        frm.trigger("add_custom_buttons");
    },
    add_custom_buttons(frm){
        if (!frm.doc.reference_type || !frm.doc.reference_name) 
            return 
        
    
        frm.add_custom_button(__("View Transaction"), ()=> {
            frappe.set_route("Form", frm.doc.reference_type, frm.doc.reference_name);
        }, __("View"));
    },
});