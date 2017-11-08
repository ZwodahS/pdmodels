
import json
import logging

class DictMixin(object):

    def assertDictMustHave(self, data, must_haves):
        for k, v in must_haves.items():
            self.assertIn(k, data, msg="key {0} not in data".format(k))
            self.assertEqual(type(data.get(k)), type(v), msg=
                    "type of value of {0} is not same as what is expected".format(k))
            if isinstance(v, dict):
                self.assertDictMustHave(data.get(k), v)
            elif isinstance(v, (tuple, list)):
                self.assertListMustHave(data.get(k), v)
            else:
                self.assertEqual(data.get(k), v, msg=
                        "value of {0} is not same as what is expected".format(k))

    def assertListMustHave(self, data, must_haves):
        self.assertEqual(len(data), len(must_haves), msg=
                "length of data is not the same as what is expected")
        for v1, v2 in zip(data, must_haves):
            self.assertEqual(type(v1), type(v2))
            if isinstance(v2, dict):
                self.assertDictMustHave(v1, v2)
            elif isinstance(v2, list):
                self.assertListMustHave(v1, v2)
            else:
                self.assertEqual(v1, v2, msg="value in list is not what we expected")

    def assertDictHasField(self, document, field):
        """Assert that this document has this field
        """
        field_split = field.split(".")
        curr = document
        for ind, f in enumerate(field_split):
            if curr is None:
                self.fail(msg="fail to retrieve field {0} from None document".format(
                    ".".join(field_split[ind:])))
            if isinstance(curr, dict):
                if f not in curr:
                    self.fail(msg="key {0} not found in document".format(
                        ".".join(field_split[ind:])))
                curr = curr.get(f)
            else:
                self.fail(msg="fail to retrieve field {0} from non-dict".format(
                    ".".join(field_split[ind:])))

    def assertDictDoNotHaveField(self, document, field):
        """Assert that this document do not have this field
        """
        field_split = field.split(".")
        curr = document
        for ind, f in enumerate(field_split):
            if curr is None:
                self.fail(msg="fail to retrieve field {0} from None document".format(
                    ".".join(field_split[ind:])))
            if isinstance(curr, dict):
                if f not in curr:
                    return
                curr = curr.get(f)
            else:
                self.fail(msg="fail to retrieve field {0} from non-dict".format(
                    ".".join(field_split[ind:])))

        self.fail(msg="field {0} found, value {1}".format(field, curr))

    def assertListSimilarIgnoreOrder(self, list1, list2):
        """Assert 2 list is similar
        assumption : items in both list are unique and not duplicated within themself.
        """
        self.assertEqualLen(list1, list2, msg="list1 and list2 are of different length")
        set1 = set(list1)
        set2 = set(list2)

        self.assertLen(set1 - set2, 0, msg="list1 contains item not in list2")
        self.assertLen(set2 - set1, 0, msg="list2 contains item not in list1")


class MoreAssertMixin(object):

    def __init__(self, *args, **kwargs):
        pass

    def assertLen(self, value, expected_length, msg=None):
        self.assertEqual(len(value), expected_length, msg=msg)

    def assertEqualLen(self, value1, value2, msg=None):
        self.assertEqual(len(value1), len(value2), msg=None)

