
"""
MIT License

Copyright (c) [2017] [Zwodahs]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from ..dict_model import *
import arrow

class JsonStorageMixin(Mixin):
    """
    Json storage mixin deals with converting an dictionary with weird objects into
    a dictionary with only valid json types.

    It also deals with store_field, where if you want to store as _id, but return as id for example.

    When you have choices that is dictionary, it will also convert it to the actual values
    Essentially this do what MongoMixin do in the past, but more generic
    """
    DATETIME_STORE_PRECISION_V1 = 1e6

    @classmethod
    def dumps_json(cls, document):
        if document is None:
            return
        for key, definition in cls._fields.items():
            value = document.get(key)
            if value is not None:
                if isinstance(definition, DefinedDictField) and issubclass(definition.model, MongoMixin):
                    definition.model.dumps_json(value)
                elif isinstance(definition, ListField) and isinstance(definition.inner_type, DefinedDictField):
                    for v in value:
                        definition.inner_type.model.dumps_json(v)
                else:
                    if hasattr(definition, "reversed_choices") and definition.reversed_choices is not None:
                        if isinstance(definition, ListField):
                            document[key] = [ definition.choices.get(v) for v in value ]
                        else:
                            document[key] = definition.choices.get(value)
                    if isinstance(definition, DateTimeField):
                        document[key] = int(arrow.get(value).float_timestamp * cls.DATETIME_STORE_PRECISION_V1) # store all datetime microseconds
                    if hasattr(definition, "store_field"):
                        document[definition.store_field] = document[key]
                        document.pop(key)

    @classmethod
    def loads_json(cls, document):
        if document is None:
            return
        for key, definition in cls._fields.items():
            if hasattr(definition, "store_field") and definition.store_field in document:
                document[key] = document.pop(definition.store_field)
            value = document.get(key)
            if value is not None:
                if isinstance(definition, DefinedDictField) and issubclass(definition.model, MongoMixin):
                    definition.model.loads_json(value)
                elif isinstance(definition, ListField) and isinstance(definition.inner_type, DefinedDictField):
                    for v in value:
                        definition.inner_type.model.loads_json(v)
                else:
                    if hasattr(definition, "reversed_choices") and definition.reversed_choices is not None:
                        if isinstance(definition, ListField):
                            document[key] = [ definition.reversed_choices.get(v) for v in value ]
                        else:
                            document[key] = definition.reversed_choices.get(value)
                    if isinstance(definition, DateTimeField):
                        document[key] = int_to_datetime(document[key], cls.DATETIME_STORE_PRECISION_V1)
