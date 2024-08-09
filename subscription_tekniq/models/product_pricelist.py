from odoo import fields, models

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    product_subscription_pricing_ids = fields.One2many(
        'sale.subscription.pricing',
        'pricelist_id',
        string="Recurring Pricing",
        domain=[
            '|', ('product_template_id', '=', None), ('product_template_id.active', '=', True),
        ],
    )

    def _compute_price_rule(
        self, products, quantity, currency=None, date=False, subscription_template=None,
        **kwargs
    ):
        """ Override to handle the subscription product price

        """
        self and self.ensure_one()  # self is at most one record

        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()

        if not products:
            return {}

        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()

        results = {}
        subscription_products = products.filtered('subscribable')
        Pricing = self.env['sale.subscription.pricing']
        for product in subscription_products:
            pricing = Pricing._get_first_suitable_recurring_pricing(product, pricelist=self)
            if pricing:
                price = pricing.price
            elif product._name == 'product.product':
                price = product.lst_price
            else:
                price = product.list_price
            results[product.id] = pricing.currency_id._convert(
                price, currency, self.env.company, date
            ), False

        price_computed_products = self.env[products._name].browse(results.keys())
        return {
            **results,
            **super()._compute_price_rule(
                products - price_computed_products, quantity, currency=currency, date=date, **kwargs
            ),
        }

