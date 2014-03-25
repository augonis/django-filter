from __future__ import absolute_import
from __future__ import unicode_literals

from collections import namedtuple

from django import forms

from .widgets import RangeWidget, LookupTypeWidget, BooleanSelect, DateOffsetWidget


class RangeField(forms.MultiValueField):
    widget = RangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DecimalField(),
            forms.DecimalField(),
        )
        super(RangeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None

Lookup = namedtuple('Lookup', ('value', 'lookup_type'))
class LookupTypeField(forms.MultiValueField):
    def __init__(self, field, lookup_choices, *args, **kwargs):
        fields = (
            
            forms.ChoiceField(choices=lookup_choices), field
        )
        defaults = {
            'widgets': [f.widget for f in fields],
        }
        widget = LookupTypeWidget(**defaults)
        kwargs['widget'] = widget
        super(LookupTypeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if len(data_list)==2:
            return Lookup(value=data_list[1], lookup_type=data_list[0] or 'exact')
        return Lookup(value=None, lookup_type='exact')


class BooleanField(forms.NullBooleanField):
    widget = BooleanSelect

class DateOffsetField(forms.Field):
    widget = DateOffsetWidget
    def to_python(self, value):
        if value:
            return int(value[0]), int(value[1])
    
    def validate(self, value):
        pass
    
