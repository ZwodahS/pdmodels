
import copy
import unittest

import pdmodels
from . import test_base

class TestModelBaseTest(unittest.TestCase, test_base.DictMixin, test_base.MoreAssertMixin):
    pass


class BaseFieldTest(TestModelBaseTest):
    # although it is not recommended to create Field instead of the other type,
    # we can still create it for testing purpose

    def test_is_required(self):
        class Book(pdmodels.DefinedDict):
            name = pdmodels.StringField(is_required=True)

        book = {}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("name", "required", None))

        # ensure that None and missing key is the same
        book = {"name": None}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("name", "required", None))

        # test happy case
        book = { "name": "something" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

    def test_choices(self):
        """Test the choices field of any Field object
        """
        class Book(pdmodels.DefinedDict):
            category = pdmodels.StringField(choices={"fiction", "non-fiction"})

        # test that choices doesn't care if key is None
        book = {}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        # test that choices are enforced
        book = { "category": "Something" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("category", "value", "Something"))

        # test that valid choices are still valid
        book = { "category": "fiction" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "category": "non-fiction" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

    def test_default_value(self):
        class Book(pdmodels.DefinedDict):
            status = pdmodels.StringField(default="available")

        book = {}
        Book.clean_document(book)
        self.assertDictHasField(book, "status")
        self.assertEqual(book["status"], "available")


class StringFieldTest(TestModelBaseTest):

    def test_values_checks(self):
        class Book(pdmodels.DefinedDict):
            name = pdmodels.StringField()

        # ensures document errors
        book = { "name": 1000 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("name", "type", 1000))

        book = { "name": "abc" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

    def test_regex_string(self):
        class Book(pdmodels.DefinedDict):
            id = pdmodels.StringField(regex="\d{4}-\d{4}-[A-Z]")

        book = {"id": "qda1-123a-1"}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("id", "value", "qda1-123a-1"))

        book = {"id": "1231-1231-a"}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("id", "value", "1231-1231-a"))

        book = {"id": "1231-1231-A"}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)


class NumberFieldTest(TestModelBaseTest):

    def test_number_field_min_max(self):
        class Book(pdmodels.DefinedDict):
            price = pdmodels.NumberField(allowed_type=int, min=0)
            published_year = pdmodels.NumberField(allowed_type=int, max=2030)
            copies = pdmodels.NumberField(allowed_type=int, min=0, max=1000)

        # test min only
        book = { "price": 10000000}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "price": -1}
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("price", "value", -1))

        # test max only
        book = { "published_year": -1031 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "published_year": 2031 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("published_year", "value", 2031))

        # test min and max at the same time
        book = { "copies": 0 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "copies": 1000 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "copies": 1001 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("copies", "value", 1001))

        book = { "copies": -1 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("copies", "value", -1))


class IntFieldTest(TestModelBaseTest):

    def test_int_type(self):
        class Book(pdmodels.DefinedDict):
            copies = pdmodels.IntField()

        book = { "copies": 3 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "copies": 3.0 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("copies", "type", 3.0))

        book = { "copies": "strange_string" }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("copies", "type", "strange_string"))


class FloatFieldTest(TestModelBaseTest):

    def test_float_type(self):
        class Book(pdmodels.DefinedDict):
            price = pdmodels.FloatField()

        book = { "price": 35.5 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

        book = { "price": 35 }
        errors = Book.get_document_errors(book)
        self.assertLen(errors, 0)

# too lazy to write the rest, will write when i am free.
# let's just do a full example

class Book(pdmodels.DefinedDict):

    id = pdmodels.StringField(is_required=True, regex="\d{4}-[A-Z]+")
    author = pdmodels.StringField()
    type = pdmodels.StringField(fixed_value="book")

class Pen(pdmodels.DefinedDict):

    color = pdmodels.StringField(is_required=True, choices={"red", "blue", "green"})
    type = pdmodels.StringField(fixed_value="pen")

class Product(pdmodels.DefinedDict):

    name = pdmodels.StringField(is_required=True)
    price = pdmodels.FloatField(is_required=True)
    stock = pdmodels.IntField(default_value=0)

    product_info = pdmodels.VariableDefinedDictField("type", {
        "book": Book,
        "pen": Pen,
    })

class VariableDocTest(TestModelBaseTest):

    def test_variable_doc(self):

        product1 = {
            "name": "Introduction to Programming",
            "price": 1231.0,
            "stock": 3,
            "product_info": {
                "type": "book"
            }
        }

        errors = Product.get_document_errors(product1)
        self.assertLen(errors, 1)
        self.assertEqual(errors[0], ("product_info.id", "required", None))

        product1["product_info"]["id"] = "1231-A"
        product1["product_info"]["author"] = "Some Dude"

        errors = Product.get_document_errors(product1)
        self.assertLen(errors, 0)

        product1["product_info"]["color"] = "blue"
        Product.clean_document(product1)
        self.assertNotIn("color", product1["product_info"])

        product2 = {
            "name": "Red Pen",
            "price": 1.5,
            "stock": 1000,
            "product_info": {
                "type": "pen",
                "color": "blue",
            }
        }

        errors = Product.get_document_errors(product2)
        self.assertLen(errors, 0)

        product2["product_info"]["id"] = "1234-A"
        Product.clean_document(product2)
        self.assertNotIn("id", product2["product_info"])

    def test_variable_doc_update(self):
        product1 = {
            "name": "Introduction to Programming",
            "price": 1231.0,
            "stock": 3,
            "product_info": {
                "type": "book",
                "id": "1234-A",
            }
        }

        product2 = {
            "name": "Red Pen",
            "price": 1.5,
            "stock": 1000,
            "product_info": {
                "type": "pen",
                "color": "blue",
            }
        }

        Product.update(product1, {"product_info": {"author": "somedude"}})
        self.assertEqual(product1["product_info"]["author"], "somedude")

        Product.update(product1, {"product_info": {"color": "blue"}})
        self.assertNotIn("color", product1["product_info"])

        Product.update(product1, product2)

        self.assertEqual(product1["name"], "Red Pen")
        self.assertEqual(product1["price"], 1.5)
        self.assertEqual(product1["stock"], 1000)
        self.assertEqual(product1["product_info"]["type"], "pen")
        self.assertEqual(product1["product_info"]["color"], "blue")

        # ensure no additional key
        self.assertListSimilarIgnoreOrder(
            list(product1.keys()),
            ["name", "price", "stock", "product_info"]
        )
        self.assertListSimilarIgnoreOrder(
            list(product1["product_info"].keys()),
            ["type", "color"]
        )
