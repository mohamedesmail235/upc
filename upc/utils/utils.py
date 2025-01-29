import frappe


def create_offline_qr_code():
    from electronic_invoice.events.accounts.sales_invoice import create_qr_code
    invoices = frappe.db.get_all("Sales Invoice",filters={"docstatus":1,"name":"UPFPP-SINV-2025-00171"},fields=["*"])
    if invoices:
        print("===============Staring===============")
        for invoice in invoices:
            doc = frappe.get_doc("Sales Invoice",invoice.name)
            try:
                create_qr_code(doc,None)
                print("invoice=============="+str(invoice.name))
            except Exception as e:
                frappe.error_log(e)
        print("===============Finished===============")

