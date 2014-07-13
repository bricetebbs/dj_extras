import models

from forms import create_form_field_with_parameter
from forms import PercentageWidget, PositiveIntegerField, MaxValueValidator, MinValueValidator, PositiveIntegerWidget


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
            return f.formfield(widget=PositiveIntegerWidget(attrs=attrs), **kwargs)
    #
    # Fall through and just do the default
    #
    return f.formfield(**kwargs)


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
