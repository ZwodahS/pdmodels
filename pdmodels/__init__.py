
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
import re
import datetime
import logging

def int_to_datetime(microsecond, precision):
    """convert microsecond to datetime properly.
    datetime.datetime.fromtimestamp(1432550134353845/1e6)
    datetime.datetime(2015, 5, 25, 10, 35, 34, 353844)
    need to deal with cases like this

    TODO: need to test if this is still a problem in later python version
    """
    seconds_part = int(microsecond//precision)
    microseconds_part = int(microsecond%precision)
    return datetime.datetime.fromtimestamp(seconds_part).replace(microsecond=microseconds_part)

"""
Note:

    1.  Most of the code treat missing key and None value as the same thing.
        For example : is_required field.

    TODO: fix this, as it can be done
"""
#################################### Exceptions ####################################
class DictFieldError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class DictValueError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


#################################### Fields ####################################
class Field(object):

    """The parent class of all fields
    It allow for any value to be stored.

    Basic fields values

    is_required                 if true, None value or missing key is not allowed.
    choices                     defines the valid fields for this field.
                                if choices is a dict, a reversed_choices is will also be created.
    default                     default value for this field, either a callable or a value.
                                for callable, a single parameter containing the instance of the field will be provided.
    """

    ERROR_IS_REQUIRED = "required"
    ERROR_TYPE = "type"
    ERROR_VALUE = "value"

    def __init__(self, is_required=False, choices=None, default=None, dict_key=None, fixed_value=None, **kwargs):
        """
        is_required                 specify if this field is required
        choices                     specify in a list, set or dictionary what are the allowed values
                                    if choices is provided as a dictionary, a reversed_choices is created
                                    this will then requires both side to be unique or an Exception will be raised.
        default                     default value for this field
                                    default can be a value or a callable,
                                    the callable will take in a single value containing the field
        dict_key                    overwrite where this field is stored in the dictionary.
                                    if not provided will default to the key in the model definition.
        fixed_value                 force the value of this field to be always of this value.

        **kwargs                    any other kwargs can also be set.
                                    this is to mainly support extensions that requires more configuration.
        """
        self.is_required = is_required
        self.choices = choices
        self.default = default
        self.dict_key = dict_key
        self.fixed_value = fixed_value

        if isinstance(choices, dict):
            self.reversed_choices = { v : k for k, v in choices.items() }
            if len(self.reversed_choices != self.choices):
                raise DictFieldError("choices is not unique")

        for k, v in kwargs.items():
            setattr(self, k, v)

    def errors(self, value, with_key=None):
        """ a generator that returns errors

        if with_key is not None
            returns (with_key, error_type, value)

        if with_key is None
            returns error_type

        """
        if value is None:
            if self.is_required:
                if with_key is not None:
                    yield (with_key, Field.ERROR_IS_REQUIRED, None)
                else:
                    yield Field.ERROR_IS_REQUIRED
        else:
            if self.choices is not None and value not in self.choices:
                if with_key is not None:
                    yield (with_key, Field.ERROR_VALUE, value)
                else:
                    yield Field.ERROR_VALUE

    def get_errors(self, value):
        """returns a list of errors instead of generator
        """
        return list(self.errors(value))

    def is_valid_value(self, value):
        """return True if this is a valid value, False otherwise
        """
        try:
            next(self.errors(value))
            return False
        except StopIteration:
            return True

    def make_default(self):
        """return a default value for this field
        """
        if self.default is None:
            return None
        if callable(self.default):
            return self.default(self)
        else:
            return self.default

    def clean(self, document, key, set_default=True, **kwargs):
        """clean the field

        document                the dictionary containing this field
        key                     the key that the value is contained in
        set_default             True will set the default if value is not present, else False
        """
        if self.fixed_value is not None:
            document[key] = self.fixed_value
        if key not in document:
            if set_default:
                document[key] = self.make_default()

    def update(self, document, key, value):
        """update the key in this document with the value

        document                the dictionary to update
        key                     the key of the field
        value                   the value to update it to
        """
        document[key] = value


class TypedField(Field):

    """A Field that enforces type
    """

    def __init__(self, allowed_type, **kwargs):
        """
        allowed_type                a single type or a list/tuple of types
        """
        super().__init__(**kwargs)
        if allowed_type is None:
            raise DictFieldError(message="Invalid valid for allowed_type : None")
        self.allowed_type = allowed_type

    def errors(self, value, with_key=None):
        """override the original errors with type checking
        """
        yield from super().errors(value, with_key)
        if value is not None and not isinstance(value, self.allowed_type):
            if with_key is not None:
                yield (with_key, Field.ERROR_TYPE, value)
            else:
                yield Field.ERROR_TYPE


class StringField(TypedField):

    """Typed Field for str

    Additional functionality for string field

    regex               define a regex for this StringField
    """

    def __init__(self, regex=None, **kwargs):
        """
        regex                   a string or a compiled regex
        """
        super().__init__(allowed_type=(str, ), **kwargs)
        if isinstance(regex, str):
            regex = re.compile(regex)
        self.regex = regex

    def errors(self, value, with_key=None):
        """override the original errors for regex checking
        """
        yield from super().errors(value, with_key)
        if self.regex is not None and value is not None and not self.regex.match(value):
            yield (with_key, Field.ERROR_VALUE, value)


class NumberField(TypedField):
    """Abstract TypedField for number

    Additional value to number field

    min                 define the min value of this number field (inclusive)
    max                 define the max value of this number field (exclusive)

    if choices is defined, min, max will have no effect
    """

    def __init__(self, allowed_type=None, min=None, max=None, **kwargs):
        """
        allowed_type        define the allowed_type
        min                 define the min value of this number field (inclusive)
        max                 define the max value of this number field (exclusive)

        if choices is defined, min, max will have no effect, since choices is stricter
        """
        super().__init__(allowed_type=allowed_type, **kwargs)
        if self.choices is None:
            self.min = min
            self.max = max
        else:
            self.min = None
            self.max = None

    def errors(self, value, with_key=None):
        """override the original errors with min/max checking
        """
        yield from super().errors(value, with_key)
        if value is not None:
            if (self.min is not None and value < self.min) or (self.max is not None and value > self.max):
                if with_key:
                    yield (with_key, Field.ERROR_VALUE, value)
                else:
                    yield Field.ERROR_VALUE


class IntField(NumberField):
    """TypedField for int
    """

    def __init__(self, **kwargs):
        super().__init__(allowed_type=(int, ), **kwargs)


class FloatField(NumberField):
    """TypedField for float
    """

    def __init__(self, **kwargs):
        super().__init__(allowed_type=(float, int), **kwargs)

    def update(self, document, key, value):
        """override the original update to cast int to float
        """
        if isinstance(value, int):
            try:
                # if fail to convert, chances are it is not inta
                # we fail silently here since it is the default behavior
                # we will let "errors()" catch the type error
                value = float(value)
            except Exception as e:
                pass
        super().update(document, key, value)


class BoolField(TypedField):
    """TypedField for boolean
    """

    def __init__(self, **kwargs):
        super().__init__(allowed_type=(bool, ), **kwargs)


class ListField(TypedField):
    """TypedField for list
    """

    def __init__(self, inner_type=None, ensure_list=True, remove_none_value=True, **kwargs):
        """Constructor

        inner_type              The type of field for the values in the list.
                                if None, then it will not enforced (default : None)
        ensure_list             Ensure that this field is always a list and never a None.
                                All None value will be converted to list upon cleaning.
        remove_none_value       If True, then any None value will be removed from list
                                when clean is called
        """
        super().__init__(allowed_type=(list, ), **kwargs)
        if inner_type is not None and not isinstance(inner_type, Field):
            raise DictFieldError(message="Innertype for ListField needs to be a Field")
        self.inner_type = inner_type
        self.ensure_list = ensure_list
        self.remove_none_value = remove_none_value

    def errors(self, value, with_key=None):
        """override the original errors with additional checks
        """
        yield from super().errors(value, with_key)
        if self.inner_type is not None and isinstance(value, list):
            if with_key is not None:
                for ind, inner in enumerate(value):
                    yield from self.inner_type.errors(inner, ".".join([with_key, str(ind)]))
            else:
                for inner in value:
                    yield from self.inner_type.errors(inner, None)

    def clean(self, document, key, **kwargs):
        """override the original clean with additional cleaning
        """
        super().clean(document, key, **kwargs)
        # if is not a list, and we want to ensure is a list, we force it to be a list
        # this will only force None value to list
        if self.ensure_list and document.get(key) is None:
            document[key] = []
        # find and remove None if enabled
        if (self.remove_none_value and document.get(key) is not None and
                isinstance(document.get(key), list)):
            document[key] = [ item for item in document.get(key) if item is not None ]
        # if list is a dictionary, inform the inner definition to also clean
        if self.inner_type is not None and document.get(key):
            # TODO: there is a reason why I didn't clean other types, but I can't remember why.
            if isinstance(self.inner_type, DefinedDictField):
                for item in document[key]:
                    self.inner_type.model.clean_document(item, **kwargs)


class DateTimeField(Field):
    """Field used to store datetime object.
    """

    def __init__(self, precision=1e6, **kwargs):
        """
        precision               the precision to use in storing/converting the value
        """
        super().__init__(**kwargs)
        self.precision = precision

    def errors(self, value, with_key=None):
        """override the original errors with various checks
        """
        yield from super().errors(value, with_key)
        if value is not None and not isinstance(value, (datetime.datetime, )):
            if with_key is not None:
                yield (with_key, Field.ERROR_TYPE, value)
            else:
                yield Field.ERROR_TYPE

    def clean(self, document, key, **kwargs):
        """override the original errors with various checks
        will convert int to datetime
        """
        super().clean(document, key, **kwargs)
        if isinstance(document[key], int):
            document[key] = int_to_datetime(document[key], self.precision)


class DictField(TypedField):
    """Abstract class for Dict
    """

    def __init__(self, **kwargs):
        if "choices" in kwargs:
            raise DictFieldError(message="choices is not allow for DictField or subclass of DictField")
        super().__init__(allowed_type=(dict, ), **kwargs)


    def update(self, document, key, value):
        """override update to do update all keys
        does not recursively update.
        """
        if isinstance(value, dict):
            if document.get(key) is None:
                document[key] = value
            elif isinstance(document.get(key), dict):
                document[key].update(value)


class MapField(DictField):
    """A specialized dict field such that all the value is of one type
    """

    def __init__(self, inner_type=None, ensure_dict=True, remove_none_value=True, **kwargs):
        super().__init__(**kwargs)
        if inner_type is None or not isinstance(inner_type, Field):
            raise DictFieldError(message="Innertype for MapField needs to be a Field")
        self.inner_type = inner_type
        self.ensure_dict = ensure_dict
        self.remove_none_value = remove_none_value

    def errors(self, value, with_key=None):
        """override the original errors with various checks
        """
        yield from super().errors(value, with_key)
        if isinstance(value, dict):
            if with_key is not None:
                for k, v in value.items():
                    yield from self.inner_type.errors(v, ".".join([with_key, k]))
            else:
                for k, v in value:
                    yield from self.inner_type.errors(v, None)

    def update(self, document, key, value):
        """override the original update to recursively update
        """
        if isinstance(value, dict):
            if document.get(key) is None:
                document[key] = {}
        if isinstance(value, dict):
            if isinstance(self.inner_type, DefinedDictField):
                for k, v in value.items():
                    if document[key].get(k) is None or v is None:
                        document[key][k] = v
                    else:
                        self.inner_type.model.update(document[key][k], v)
            else:
                for k, v in value.items():
                    if document[key].get(k) is None:
                        document[key][k] = v
                    else:
                        self.inner_type.update(document[key], k, v)

    def clean(self, document, key, **kwargs):
        """override the original clean to recursively clean
        """
        super().clean(document, key, **kwargs)
        if self.ensure_dict and document.get(key) is None:
            document[key] = {}
        if document.get(key) is not None:
            if self.remove_none_value:
                none_keys = []
                for k, v in document[key].items():
                    if v is None:
                        none_keys.append(k)
                for n in none_keys:
                    document[key].pop(n)
            for k, v in document.get(key).items():
                self.inner_type.clean(document.get(key), k, **kwargs)


class DefinedDictField(DictField):
    """A specialized dict field that the inner dictionary is also well-defined.
    """

    def __init__(self, model, **kwargs):
        if not issubclass(model, DefinedDict):
            raise DictFieldError(message="Model value for DefinedDictField needs to be a DefinedDict")
        super().__init__(**kwargs)
        self.model = model

    def errors(self, value, with_key=None):
        """override the original errors to perform checks from models
        """
        yield from super().errors(value, with_key)
        if isinstance(value, dict):
            yield from self.model._yield_errors(value, parent=with_key)

    def make_default(self):
        """override the original make_default to create default using models create default
        """
        if self.default is None:
            return self.model.make_default()
        else:
            return super().make_default()

    def update(self, document, key, value):
        """override the original update to use the models' update
        """
        if isinstance(value, dict):
            if document.get(key) is None:
                document[key] = value
            else:
                self.model.update(document[key], value)

    def clean(self, document, key, set_default=True, **kwargs):
        """override the original clean to use the models' clean
        """
        if key not in document:
            if set_default:
                document[key] = self.make_default()
        if document.get(key) is not None:
            self.model.clean_document(document[key], set_default=set_default, **kwargs)


class VariableDefinedDictField(DictField):
    """A specialized dict field that the inner dictionary is also well-defined.

    This is slightly different from DefinedDictField as the inner model can be different based on
    a value of a key, i.e. "type"

    See test cases for example
    """

    def __init__(self, check_field, models, **kwargs):
        """
        check_field                 the field to check to decide which model to use
        models                      a dictionary with key value.
                                    this enforced that the "check_field" is not None and
                                    must be present in the model.
        """
        for key, model in models.items():
            if not issubclass(model, DefinedDict):
                raise DictFieldError(message="Model value for VariableDefinedDictField needs to be a DefinedDict")

            if not hasattr(model, check_field):
                raise DictFieldError(message="Model value for VariableDefinedDictField does not contain the required check_field '{0}'".format(check_field))

        super().__init__(**kwargs)
        self.check_field = check_field
        self.models = { k: v for k, v in models.items() } # make a copy

    def _get_model(self, value):
        if value is None:
            return None

        _type = value.get(self.check_field)
        if _type is None:
            return None

        return self.models.get(_type)

    def make_default(self):
        """override make_default to always return None
        """
        return None

    def update(self, document, key, value):
        """override update to use the correct model to update

        document            the parent dict containing this key
        key                 the key that we are writing to
        value               the value we are updating, a dict
        """
        if isinstance(value, dict):
            # keep the original dictionary value
            doc = document.get(key)
            # if either is None, then there is no merging, we just set it and we are done
            if value is None or doc is None:
                document[key] = value
                return

            # original type
            doc_type = doc.get(self.check_field) if doc is not None else None
            # the new type
            value_type = value.get(self.check_field) if value is not None else None

            # if either one of the value is None or they are the same
            if doc_type is None or value_type is None or doc_type == value_type:
                # get the model
                model = self.models.get(doc_type or value_type)
                if model is None: # if we are not able to find the model, means something is wrong
                    raise ValueError("Invalid {0}: {1}".format(self.check_field, doc_type or value_type))

                # tell the model to update the value
                model.update(doc, value)

            # this only happens if doc_type and value_type is not None, and they are not the same value
            # thus we just overwrite it
            elif value_type is not None:
                # if above doesn't work, the other case that we need to care is
                # we overwrite the original doc with value
                # TODO: do we need to deepcopy?
                document[key] = value

    def errors(self, value, with_key=None):
        """override the original errors to call the correct model's errors
        """
        yield from super().errors(value, with_key)
        if isinstance(value, dict):
            # decide which is the model we are using
            _type = value.get(self.check_field)
            if _type is None:
                if with_key is None:
                    yield Field.ERROR_IS_REQUIRED
                else:
                    yield ("{0}.{1}".format(with_key, self.check_field), Field.ERROR_IS_REQUIRED, None)
                return

            model = self.models.get(_type)
            if model is None:
                if with_key is None:
                    yield Field.ERROR_VALUE
                else:
                    yield ("{0}.{1}".format(with_key, self.check_field), Field.ERROR_VALUE, _type)
                return

            yield from model._yield_errors(value, parent=with_key)

    def clean(self, document, key, set_default=True, **kwargs):
        """override the original clean to call the correct model's clean
        """
        if key not in document:
            if set_default:
                document[key] = self.make_default()
        if document.get(key) is not None:
            value = document.get(key)
            model = self._get_model(value)
            model.clean_document(value, set_default=set_default, **kwargs)

#################################### Mixin ####################################
class Mixin(object):
    """Parent class for mixins

    _apply_mixin will be run for each class created with this mixin and
    each class that inherits a class with this mixin.
    """

    @classmethod
    def _apply_mixin(cls, new_cls, name, bases, cdict):
        """
        cls             The mixin
        new_cls         The new class that is being created
        name            The name of the class
        bases           The bases of the new class (including this mixin)
        cdict           The attributes of the new classes.

        This method is called after all fields are added to new_cls._fields. See DefinedDictMetaClass

        Note, DO NOT modify _fields and _mixins of the new_cls, as they will produce side effects.
        """
        pass

#################################### Documents ####################################
class DefinedDictMetaClass(type):
    """Meta class
    """

    def __init__(cls, name, bases, cdict):
        super().__init__(name, bases, cdict)
        cls._fields = {}
        cls._mixins = []
        # stores all fields in _fields
        for base in bases:
            if hasattr(base, "_fields"):
                cls._fields.update(base._fields)
        for k, v in cdict.items():
            if isinstance(v, Field) and v.dict_key is None:
                v.dict_key = k

        cls._fields.update({ (v.dict_key or k) : v for k, v in cdict.items() if isinstance(v, Field) })
        # stores all mixin in _mixins, and also retrieve all mixin from parent.
        for base in bases:
            if issubclass(base, Mixin):
                base._apply_mixin(cls, name, bases, cdict)
                cls._mixins.append(base)
            if hasattr(base, "_mixins"):
                for m in base._mixins:
                    m._apply_mixin(cls, name, bases, cdict)
                    cls._mixins.append(m)


class DefinedDict(object, metaclass=DefinedDictMetaClass):
    """The main definition object
    """

    @classmethod
    def _yield_errors(cls, document, parent=None):
        """generator to retrieve error from document, internal used

        See get_document_errors
        """
        for key, definition in cls._fields.items():
            key = definition.dict_key or key # use dict_key if present
            key_string = key if parent is None else ".".join([parent, key])
            value = document.get(key)
            yield from definition.errors(value, with_key=key_string)

    @classmethod
    def get_document_errors(cls, document):
        """returns all the document errors
        """
        return list(cls._yield_errors(document))

    @classmethod
    def is_document_valid(cls, document):
        """return True if there is no errors, False otherwise
        """
        try:
            next(cls._yield_errors(document))
            return False
        except StopIteration:
            return True

    @classmethod
    def make_default(cls):
        """return a default value for this model
        """
        return { (definition.dict_key or key) : definition.make_default() for key, definition in cls._fields.items() }

    @classmethod
    def clean_document(cls, document, set_default=True, remove_undefined=True):
        """clean the dictionary using the model definition

        document                the dictionary to clean
        set_default             True to set all keys to default value. (default: True)
        remove_undefined        True to remove all keys that are not defined in the model (default: True)
        """
        if document is None:
            return document

        # iterate all keys and recursively clean
        for key, definition in cls._fields.items():
            key = definition.dict_key or key
            definition.clean(document, key, set_default=set_default, remove_undefined=remove_undefined)

        # pop keys if remove_undefined is True
        if remove_undefined:
            for key in set(document.keys()) - set(cls._fields.keys()) : # remove all the undefined keys
                document.pop(key)

        return document

    @classmethod
    def update(cls, document, new_value):
        """Recursively update the dictionary
        """
        for key, value in new_value.items():
            if key in cls._fields:
                definition = cls._fields.get(key)
                definition.update(document, key, value)

    @classmethod
    def from_dict(cls, name, fields):
        """returns a definition from a dictionary instead of defining it.
        Useful if you are defining nested models

        name                the name of the class
        fields              a dictionary containinig the key: Field mappings
        """
        return type(name, (cls, ), fields)
