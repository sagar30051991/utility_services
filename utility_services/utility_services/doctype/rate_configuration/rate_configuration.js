// Copyright (c) 2025, sagar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rate Configuration', {
    refresh: function(frm) {
        frm.set_df_property('fixed_rate', 'reqd', frm.doc.is_fixed=== 1);
    },
    is_fixed: function(frm) {
        frm.set_df_property('fixed_rate', 'reqd', frm.doc.is_fixed === 1);
        frm.set_df_property('fixed_rate', 'hidden', frm.doc.is_fixed === 0);
    }
});