# Copyright 2020 Sergio Corato <https://github.com/sergiocorato>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HyddemoWhsPacking(models.Model):
    _name = "hyddemo.whs.packing"
    _description = "Packing received from WMS"
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Packing ID",
        required=True,
        index=True,
        help="Packing identifier as written by WMS.",
    )
    dbsource_id = fields.Many2one(
        comodel_name="base.external.dbsource",
        string="External DB Source",
        required=True,
        ondelete="cascade",
        readonly=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="dbsource_id.company_id",
        store=True,
        index=True,
    )
    read_date = fields.Datetime(
        string="Read on",
        readonly=True,
        default=fields.Datetime.now,
    )
    raw_json = fields.Text(
        string="WMS JSON payload",
        readonly=True,
        help="Payload received from WMS, kept for traceability.",
    )
    package_ids = fields.One2many(
        comodel_name="hyddemo.whs.package",
        inverse_name="packing_id",
        string="Packages",
        readonly=True,
    )
    package_count = fields.Integer(compute="_compute_count")
    content_count = fields.Integer(compute="_compute_count")

    _sql_constraints = [
        (
            "dbsource_name_uniq",
            "unique(dbsource_id, name)",
            "A packing with the same ID has already been read from this database.",
        ),
    ]

    @api.depends("package_ids", "package_ids.content_ids")
    def _compute_count(self):
        for packing in self:
            packing.package_count = len(packing.package_ids)
            packing.content_count = len(packing.package_ids.content_ids)

    @api.model
    def _get_text(self, value):
        if value is None or value is False or value == "":
            return False
        return str(value).strip()

    @api.model
    def _get_float(self, value):
        if value is None or value is False or value == "":
            return 0.0
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return 0.0

    @api.model
    def _get_products_by_code(self, packages, company):
        codes = {
            self._get_text(content.get("ItemId"))
            for package in packages or []
            if isinstance(package, dict)
            for content in (package.get("Contents") or [])
            if isinstance(content, dict) and content.get("ItemId")
        }
        if not codes:
            return {}
        products = self.env["product.product"].search(
            [
                ("default_code", "in", list(codes)),
                ("company_id", "in", [company.id, False]),
            ]
        )
        return {product.default_code: product for product in products}

    @api.model
    def _prepare_content_commands(self, contents, product_by_code):
        commands = []
        for content in contents or []:
            if not isinstance(content, dict):
                continue
            item_code = self._get_text(content.get("ItemId"))
            product = product_by_code.get(item_code)
            commands.append(
                (
                    0,
                    0,
                    {
                        "logistic_sn": self._get_text(content.get("LogisticSN")),
                        "item_code": item_code,
                        "product_id": product.id if product else False,
                        "lot": self._get_text(content.get("Lot")),
                        "lot2": self._get_text(content.get("Lot2")),
                        "lot3": self._get_text(content.get("Lot3")),
                        "qty": self._get_float(content.get("Qty")),
                        "order_number": self._get_text(content.get("OrderNumber")),
                        "row_number": self._get_text(content.get("RowNumber")),
                    },
                )
            )
        return commands

    @api.model
    def _prepare_package_commands(self, packages, product_by_code):
        commands = []
        for package in packages or []:
            if not isinstance(package, dict):
                continue
            serial_code = self._get_text(package.get("SerialCode"))
            if not serial_code:
                _logger.warning(
                    "WMS LOG: package without SerialCode received, skipped: %s",
                    package,
                )
                continue
            dimension = package.get("Dimension")
            if not isinstance(dimension, dict):
                dimension = {}
            commands.append(
                (
                    0,
                    0,
                    {
                        "serial_code": serial_code,
                        "package_type": self._get_text(package.get("PackageType")),
                        "weight_kg": self._get_float(dimension.get("WeightKg")),
                        "width_cm": self._get_float(dimension.get("WidthCm")),
                        "height_cm": self._get_float(dimension.get("HeightCm")),
                        "depth_cm": self._get_float(dimension.get("DepthCm")),
                        "content_ids": self._prepare_content_commands(
                            package.get("Contents"), product_by_code
                        ),
                    },
                )
            )
        return commands

    @api.model
    def _create_from_wms_payload(self, dbsource, packing_id, payload, raw_json=False):
        """Create or refresh a packing from a WMS JSON payload.

        ``payload`` is the object written in the WMS table. The full payload
        (``PackingId`` + ``Packages``) is accepted as well as a plain list of
        packages or a single package, so the reader keeps working if WMS
        changes the granularity of the rows.
        """
        if isinstance(payload, dict):
            packages = payload.get("Packages")
            if packages is None and payload.get("SerialCode"):
                packages = [payload]
            if packing_id in (None, ""):
                packing_id = payload.get("PackingId")
        elif isinstance(payload, list):
            packages = payload
        else:
            return self.browse()
        name = self._get_text(packing_id)
        if not name:
            _logger.warning("WMS LOG: packing without PackingId received, skipped")
            return self.browse()
        product_by_code = self._get_products_by_code(packages, dbsource.company_id)
        values = {
            "name": name,
            "dbsource_id": dbsource.id,
            "read_date": fields.Datetime.now(),
            "raw_json": raw_json or False,
            "package_ids": [
                (5, 0, 0),
                *self._prepare_package_commands(packages, product_by_code),
            ],
        }
        packing = self.search(
            [("dbsource_id", "=", dbsource.id), ("name", "=", name)], limit=1
        )
        if packing:
            packing.write(values)
        else:
            packing = self.create(values)
        return packing


class HyddemoWhsPackage(models.Model):
    _name = "hyddemo.whs.package"
    _description = "Package (collo) received from WMS"
    _order = "serial_code"
    _check_company_auto = True

    packing_id = fields.Many2one(
        comodel_name="hyddemo.whs.packing",
        string="Packing",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="packing_id.company_id",
        store=True,
        index=True,
    )
    serial_code = fields.Char(
        required=True,
        index=True,
        help="Package barcode (SerialCode in the WMS payload).",
    )
    package_type = fields.Char(
        help="Free text package type chosen by the WMS operator (e.g. pallet, box).",
    )
    weight_kg = fields.Float(string="Weight (kg)", digits=(16, 3))
    width_cm = fields.Float(string="Width (cm)", digits=(16, 2))
    height_cm = fields.Float(string="Height (cm)", digits=(16, 2))
    depth_cm = fields.Float(string="Depth (cm)", digits=(16, 2))
    content_ids = fields.One2many(
        comodel_name="hyddemo.whs.package.content",
        inverse_name="package_id",
        string="Contents",
        readonly=True,
    )
    content_count = fields.Integer(compute="_compute_content_count")

    @api.depends("content_ids")
    def _compute_content_count(self):
        for package in self:
            package.content_count = len(package.content_ids)


class HyddemoWhsPackageContent(models.Model):
    _name = "hyddemo.whs.package.content"
    _description = "Package content received from WMS"
    _order = "id"
    _check_company_auto = True

    package_id = fields.Many2one(
        comodel_name="hyddemo.whs.package",
        string="Package",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="package_id.company_id",
        store=True,
        index=True,
    )
    logistic_sn = fields.Char(
        string="Package Barcode",
        help="LogisticSN in the WMS payload: barcode of the package containing "
        "the material.",
    )
    item_code = fields.Char(index=True)
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        check_company=True,
    )
    lot = fields.Char()
    lot2 = fields.Char()
    lot3 = fields.Char()
    qty = fields.Float(string="Quantity", digits=(16, 3))
    order_number = fields.Char(
        help="Order for which the material has been picked, as sent by WMS.",
    )
    row_number = fields.Char(
        help="Order row for which the material has been picked, as sent by WMS.",
    )
