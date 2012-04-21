
from django.forms.widgets import TextInput
from django.db.models import PositiveIntegerField
from django.core.validators import MaxValueValidator, MinValueValidator
from django import forms

import models


class ParameterTypes(object):
    NONE = 0
    FILE = 10
    STRING = 20
    INTEGER = 30
    FLOAT = 40
    BOOLEAN = 50
    ENUM = 60
    LABEL = 100
    URL = 110
    UUID = 120

    CHOICES = (
            (NONE, "None"),
            (FILE, "FILE"),
            (STRING, "String"),
            (INTEGER, "Integer"),
            (FLOAT, "Float"),
            (BOOLEAN, "Bool"),
            (ENUM, "Enum"),
            (LABEL, "Label"),
            (URL, "URL"),
            (UUID, "UUID")
    )


class PositiveNumberWidget(TextInput):
    """
        A widget for entering positive numbers. Using html5 'number'
    """
    input_type = 'number'
    def __init__(self, *args, **kwargs):
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0)
        else:
            kwargs['attrs'].setdefault('min', 0)

        super(PositiveNumberWidget, self).__init__(*args, **kwargs)


class PercentageWidget(TextInput):
    """
    A widget for entering percentages. Using html5 'number'
    """
    input_type = 'number'
    def __init__(self, *args, **kwargs):
        #
        # Set defaults to 0 and 100 if not overriden
        #
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0, max=100)
        else:
            for x in (('min', 0), ('max', 100)):
                kwargs['attrs'].setdefault(x[0], x[1])


        super(PercentageWidget, self).__init__(*args, **kwargs)

class PercentageField(forms.FloatField):
    def __init__(self, *args, **kwargs):

        if not 'widget' in kwargs:
            kwargs['widget'] = PercentageWidget()

        super(PercentageField, self).__init__(*args, **kwargs)


class RatingSliderWidget(TextInput):
    """
     A widget for entering ratings using the html5 range
    """
    input_type = 'range'
    def __init__(self, *args, **kwargs):
        #
        # Set defaults to 0 and 100 if not overriden
        #
        if not 'attrs' in kwargs:
            kwargs['attrs'] = dict(min=0, max=100)
        else:
            for x in (('min', 0), ('max', 100)):
                kwargs['attrs'].setdefault(x[0], x[1])
        super(RatingSliderWidget, self).__init__(*args, **kwargs)


class SliderField(forms.FloatField):
    def __init__(self, *args, **kwargs):
        if not 'widget' in kwargs:
            kwargs['widget'] = RatingSliderWidget()

        super(SliderField, self).__init__(*args, **kwargs)




def custom_formfield_callback(f, **kwargs):
    """
    Applies our own assignment of widgets etc when using model forms
    """

    #
    # Percentage fields have their own widget
    #
    if isinstance(f, models.PercentageField):
        return f.formfield(widget = PercentageWidget(), **kwargs)
    elif isinstance(f, PositiveIntegerField):
        #
        # Check in the validators for a Positive integer field
        # If it has a MaxValue Validator then it gets a special widget
        #
        attrs = {}
        for v in f.validators:
            if isinstance(v, MaxValueValidator):
                attrs['max'] = v.limit_value
            elif isinstance(v, MinValueValidator):
                attrs['min'] = v.limit_value
        if 'max' in attrs:
            return f.formfield(widget=PositiveNumberWidget(attrs=attrs), **kwargs)
        

    #
    # Fallthrough and just do the default
    #
    return f.formfield(**kwargs)

def get_form_class_for_class(klass):
    meta_dict = dict(model=klass)
    if hasattr(klass, 'get_editable_fields'):
        meta_dict['fields'] = klass.get_editable_fields()

    meta = type('Meta', (),meta_dict)
    modelform_class = type('modelform', (forms.ModelForm,), {"Meta": meta})
    return modelform_class

def create_form_field_with_parameter(parameter):
    field = None
    label = parameter.get('display', parameter['name'])
    kind = parameter['kind']

    if parameter['kind'] == ParameterTypes.BOOLEAN:
        field =  forms.BooleanField(label=label)
    elif kind == ParameterTypes.NONE:
        field =  forms.BooleanField(label=label)
    elif kind == ParameterTypes.INTEGER:
        field = SliderField(label=label)
    elif kind == ParameterTypes.FLOAT:
        field = forms.FloatField(label=label)
    elif kind == ParameterTypes.STRING:
        field = forms.CharField(label=label)
    elif kind == ParameterTypes.FILE:
        field = forms.FileField(label=label)
    elif kind == ParameterTypes.ENUM:
        field = forms.ChoiceField(choices=parameter['choices'], label=label)

    return field


def create_form_class_with_parameter_list(param_list, name='dynform'):

    field_dict = {}

    for x in param_list:
        field = create_form_field_with_parameter(x)
        if field:
            field_dict[x['name']] = field

    return type(name, (forms.BaseForm,), dict(base_fields=field_dict, formfield_callback = custom_formfield_callback ))

def create_form_with_parameter_list(param_list, name='dynform', initial_dict={}):

    form_class = create_form_class_with_parameter_list(param_list, name)

    form = form_class(initial=initial_dict)

    return form
