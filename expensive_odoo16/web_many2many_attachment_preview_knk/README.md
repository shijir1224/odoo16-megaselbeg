Odoo Many2many Attachment Preview
------------------------------------

This module can be used as a extension of Many2many field attachment preview in back-end.

This code is a simple example. So, that the user can change the model name according to their requirements.
------------------------------------

## In .py file
```
from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    attachments = fields.Many2many("ir.attachment", string="Attachments")
```

## In .xml file
```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_order_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.form</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='order_line']//tree//field[@name='product_uom_qty']" position="after">
                <field name="attachments" widget="many2many_binary"/>
            </xpath>
        </field>
    </record>
</odoo>
```