
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

class LabelMixin(Mixin):
    """
    Label mixin allows you to specify a label and allow you to run a "clean_label" method
    to remove fields with those labels.

    For this to work, all nested types needs to also include the LabelMixin
    """

    @classmethod
    def _apply_mixin(cls, new_cls, name, bases, cdict):
        for key, definition in new_cls._fields.items():
            if hasattr(definition, "labels"):
                if isinstance(definition.labels, str):
                    definition.labels = set([definition.labels])
                if not isinstance(definition.labels, set):
                    definition.labels = set(definition.labels)

    @classmethod
    def clean_labels(cls, document, labels, exclude=None):
        exclude = exclude or set()
        if exclude is not None and isinstance(exclude, str):
            exclude = (exclude, )
        if isinstance(labels, str):
            labels = (labels, )
        labels = set(labels)
        exclude = set(exclude)

        for key, definition in cls._fields.items():
            if key in document and hasattr(definition, "labels"):
                if (len(labels & definition.labels) > 0) and len(definition.labels & exclude) == 0:
                    document.pop(key)
            if isinstance(definition, DefinedDictField) and document.get(key) is not None and LabelMixin in definition.model._mixins:
                definition.model.clean_labels(document.get(key), labels, exclude=exclude)

