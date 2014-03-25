from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import timedelta


from django import forms
from django.db.models import Q
from django.db.models.sql.constants import QUERY_TERMS
from django.utils import six
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from .fields import RangeField, LookupTypeField, Lookup, BooleanField, DateOffsetField
import django_filters.widgets as widgets


__all__ = [
    'Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter',
    'MultipleChoiceFilter', 'DateFilter', 'DateTimeFilter', 'TimeFilter',
    'ModelChoiceFilter', 'ModelMultipleChoiceFilter', 'NumberFilter',
    'RangeFilter', 'DateRangeFilter', 'AllValuesFilter',
]


LOOKUP_TYPES = sorted(QUERY_TERMS)
VERBOSE_LOOKUP_TYPES = {
        'contains':_('contains'),
        'day':_('day'),
        'endswith':_('ends with'),
        'exact':_('is'),
        'gt':_('grater than'),
        'gte':_('grater or equal than'),
        'icontains':_('contains (ci)'),
        'iendswith':_('ends with (ci)'),
        'iexact':_('is (ci)'),
        'in':_('in'),
        'iregex':_('regex (ci)'),
        'isnull':_('is null'),
        'istartswith':_('starts with (ci)'),
        'lt':_('less than'),
        'lte':_('less or equal than'),
        'month':_('month'),
        'range':_('range'),
        'regex':_('regex'),
        'search':_('search'),
        'startswith':_('starts with'),
        'week_day':_('week day'),
        'year':_('year'),
        }

class Filter(object):
    creation_counter = 0
    field_class = forms.Field
    
    DEFAULT_LOOKUP_TYPES = LOOKUP_TYPES
    DEFAULT_VERBOSE_LOOKUP_TYPES = VERBOSE_LOOKUP_TYPES

    def __init__(self, name=None, label=None, widget=None, action=None,
        lookup_type='exact', required=False, distinct=False, **kwargs):
        self.name = name
        self.label = label
        if action:
            self.filter = action
        self.lookup_type = lookup_type
        self.widget = widget
        self.required = required
        self.extra = kwargs
        self.distinct = distinct
        self._is_used = False

        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1

    def _set_is_used(self, val):self._is_used = self.field.is_used = val
    is_used = property(lambda self: self._is_used, _set_is_used)
    
    @property
    def field(self):
        if not hasattr(self, '_field'):
            if (self.lookup_type is None or
                    isinstance(self.lookup_type, (list, tuple))):
                if self.lookup_type is None:
                    lookup = [(x, self.DEFAULT_VERBOSE_LOOKUP_TYPES.get(x, x)) for x in self.DEFAULT_LOOKUP_TYPES]
                else:
                    lookup = [(x, self.DEFAULT_VERBOSE_LOOKUP_TYPES.get(x, x)) for x in self.DEFAULT_LOOKUP_TYPES if x in self.lookup_type]
                self._field = LookupTypeField(self.field_class(
                    required=self.required, widget=self.widget, **self.extra),
                    lookup, required=self.required, label=self.label)
            else:
                self._field = self.field_class(required=self.required,
                    label=self.label, widget=self.widget, **self.extra)
        return self._field

    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_type
        if value in ([], (), {}, None, ''):
            return qs
        qs = qs.filter(**{'%s__%s' % (self.name, lookup): value})
        if self.distinct:
            qs = qs.distinct()
        self.is_used = True
        return qs


class CharFilter(Filter):
    field_class = forms.CharField


class BooleanFilter(Filter):
    field_class = BooleanField

    def filter(self, qs, value):
        if value is not None:
            self.is_used = True
            return qs.filter(**{self.name: value})
        return qs

class NullBooleanFilter(Filter):
    field_class = forms.NullBooleanField

    def filter(self, qs, value):
        if value is not None:
            self.is_used = True
            return qs.filter(**{self.name: value})
        return qs

class ChoiceFilter(Filter):
    field_class = forms.ChoiceField


class MultipleChoiceFilter(Filter):
    """
    This filter preforms an OR query on the selected options.
    """
    field_class = forms.MultipleChoiceField

    def filter(self, qs, value):
        value = value or ()
        if len(value) == len(self.field.choices):
            return qs
        q = Q()
        for v in value:
            q |= Q(**{self.name: v})
        self.is_used = True
        return qs.filter(q).distinct()


class DateFilter(Filter):
    field_class = forms.DateField


class DateTimeFilter(Filter):
    field_class = forms.DateTimeField


class TimeFilter(Filter):
    field_class = forms.TimeField


class ModelChoiceFilter(Filter):
    field_class = forms.ModelChoiceField


class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = forms.ModelMultipleChoiceField


class NumberFilter(Filter):
    field_class = forms.DecimalField


class RangeFilter(Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            lookup = '%s__range' % self.name
            self.is_used = True
            return qs.filter(**{lookup: (value.start, value.stop)})
        return qs


_truncate = lambda dt: dt.replace(hour=0, minute=0, second=0)


class DateRangeFilter(ChoiceFilter):
    options = {
        '': (_('Any date'), lambda qs, name: qs.all()),
        1: (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: now().day
        })),
        2: (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: _truncate(now() - timedelta(days=7)),
            '%s__lt' % name: _truncate(now() + timedelta(days=1)),
        })),
        3: (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month
        })),
        4: (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
        })),
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [
            (key, value[0]) for key, value in six.iteritems(self.options)]
        super(DateRangeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        try:
            value = int(value)
            self.is_used = True
        except (ValueError, TypeError):
            value = ''
        return self.options[value][1](qs, self.name)

class DateOffsetFilter(Filter):
    field_class = DateOffsetField
    
    def __init__(self, direction='past', *args, **kwargs):
        self.direction = direction
        kwargs['widget'] = widgets.DateOffsetWidget(direction=direction)
        super().__init__(*args, **kwargs)
    
    def filter(self, qs, value):
        directions = {'past':{'%s__gte' % self.name: _truncate(now() - timedelta(days=value[0]*value[1]))},
                      'future':{'%s__lt' % self.name: _truncate(now() + timedelta(days=value[0]*value[1]))}}
        return qs.filter(**directions[self.direction])

class AllValuesFilter(ChoiceFilter):
    @property
    def field(self):
        qs = self.model._default_manager.distinct()
        qs = qs.order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = [(o, o) for o in qs]
        return super(AllValuesFilter, self).field
