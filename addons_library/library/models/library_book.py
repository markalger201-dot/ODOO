# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Book"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    isbn_13 = fields.Char(string="ISBN 13", required=True)
    author_id = fields.Many2one("res.partner", string="Author", required=True)
    category_ids = fields.Many2many("library.book.category", string="Categories")

    category_count = fields.Integer(
        string="Number of Categories",
        compute="_compute_category_count"
    )

    @api.depends("category_ids")
    def _compute_category_count(self):
        for book in self:
            book.category_count = len(book.category_ids)

    @api.onchange("category_ids")
    def _onchange_categories(self):
        if len(self.category_ids) > 5:
            return {
                "warning": {
                    "title": "Too many categories",
                    "message": "A book can have at most 5 categories."
                }
            }

    @api.constrains("category_ids")
    def _check_category_limit_and_duplicates(self):
        """Enforce 5-category limit and prevent duplicate categories per book"""
        for book in self:
            if len(book.category_ids) > 5:
                raise ValidationError("A book can have at most 5 categories.")
            if len(book.category_ids.ids) != len(set(book.category_ids.ids)):
                raise ValidationError("A book cannot have the same category assigned more than once.")

    def action_print_book(self):
        return {
            "type": "ir.actions.report",
            "report_name": "library.book_report",
            "docids": self.ids,
        }

    def get_authors_books(self):
        self.ensure_one()
        return self.search([("author_id", "=", self.author_id.id)])


class LibraryBookCategory(models.Model):
    _name = "library.book.category"
    _description = "Book Category"

    name = fields.Char(string="Category Name", required=True)

    
    _sql_constraints = [
        ("name_unique", "unique(name)", "The category name must be unique.")
    ]

    @api.model
    def create_default_categories(self):
        """Automatically create default categories if they don't exist"""
        default_categories = ["Fiction", "Horror", "Mystery", "Science", "Biography"]
        for category_name in default_categories:
            if not self.search([("name", "=", category_name)]):
                self.create({"name": category_name})

    @api.model
    def _auto_init(self):
        res = super(LibraryBookCategory, self)._auto_init()
        self.create_default_categories()
        return res

    @api.constrains("name")
    def _check_unique_name(self):
        for record in self:
            existing = self.search([("name", "=", record.name), ("id", "!=", record.id)])
            if existing:
                raise ValidationError(
                    f"A category with the name '{record.name}' already exists. Please choose a different name."
                )
