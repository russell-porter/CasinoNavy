frappe.ui.form.on("Data Import", {
    setup(frm){
        frm.trigger('setup_realtime_events');
        console.log('setup');
    },
    refresh (frm) {
        frm.trigger('add_custom_button');
        console.log('refresh');
    },
    add_custom_button (frm) {
        if (frm.is_new()) 
            return;

        frm.add_custom_button(__("Delete"), () => {
            // Let's prompt the user to confirm the deletion
            frappe.confirm(
                __('Are you sure you want to delete all imported records and this entry?'),
                () => {
                    frappe.call({
                        method: 'casino_navy.casino_navy.controllers.data_import.delete_all_data_imports',
                        freeze: true,
                        freeze_message: __('Deleting...'),
                        args: {
                            name: frm.docname
                        },
                        callback: (r) => {
                            if (r.message) {
                                frappe.msgprint(r.message);
                            }
                            // Let's return the user to the list view
                            frappe.set_route('List', 'Data Import');
                        }
                    });
                }
            );

        }).addClass('btn-danger');
    },
    set_realtime_events(frm) {
        frappe.realtime.on("delete_data_import", (data) => {
            if (data.mapping_name !== frm.doc.name) {
                return;
            }
            
            let percent = Math.floor((data.current * 100) / data.total);
            let message = `Deleting ${data.current} of ${data.total} records`;

            frm.dashboard.show_progress(`Deleting ${frm.doc.reference_doctype}`, percent, message);
            frm.page.set_indicator("In Progress", "orange");
    
            if (data.current === data.total) {
                setTimeout(() => {
                    frm.dashboard.hide_progress();
                    frm.reload_doc();
                }, 2000);
            }
        });

        frappe.realtime.on("delete_data_import_refresh", ({ mapping }) => {
            if (mapping === frm.doc.name) {
                frm.refresh();
            }
        });

        frappe.realtime.on("delete_data_import_complete", ({ mapping }) => {
            if (mapping === frm.doc.name) {
                frm.dashboard.hide_progress();
            }
        });
    },
});