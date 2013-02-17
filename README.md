dj_extras
=========

A collection of stuff that gets re-used in a few django projects. The features in the files are described below.


## utils.py

Some helper functions used to access models and responses

##### get_or_none
Gets the model you specify or returns none if it doesn't exist. Calls objects.get but returns None on model.DoesNotExist.

    def get_or_none(model, **kwargs):


##### get_or_create_or_update
  If a model matching key_dict for model_class exists then update it with values dict otherwise if it doesn't exist then create it used the defaults from values dict

     def get_or_create_or_update(model_class, key_dict,
                                              values_dict):

##### update_model_from_dict
Update a model instance's fieled from the specified dictionary. Note: This does not save the model.

     def update_model_from_dict(instance, d):

## forms.py
Some Fields and other helpers for making forms

### Widgets
A few widgets which work more directly with Html5 input types

##### PositiveNumberWidget
Uses Html5 type **number** and sets min to 0 if it is not already set.

##### PercentageWidget
Uses Html5 type **number** and sets min and max to 0 and 100.

###### RatingSliderWidget
Uses Html5 type **range** (usually a slider in the UI). If no min and max values are set they will also be 0 and 100.

### Fields
A few custom fields for HTML5 controls
##### PercentageField
Based on django's **FloatField** it sets min and max to 0 and 100 respectively. Also the default widget is set to **PercentageWidget**.

##### SliderField
Also based on **FloatField** but in this case defaults to **RatingSliderWidget**.

### Helpers

##### custom_formfield_callback
This can be used with a model form to control which form fields get used for each kind of model field.

     class MyClassModelForm(forms.ModelForm):
          formfield_callback = custom_formfield_callback
          class Meta:
              model = MyClass
              # etc
When this is used a models defined as percentage fields as in (dj_extras.models.PercentageField) will be assigned a field of dj_extras.forms.Percentage field. In addition ordinary **PositiveIntegerField** fields which have min and max will be assiged the PositiveNumberWidget.

##### get_form_class_for_class
A helper function for creating a model form class for a model on-the-fly. This is used with models (usually part of an inheritance hierarchy) which define a function **get_editable_fields** which returns an iterable of the field names which should be placed in the form.

### Parameter Lists
A few helper functions which allow the creation of on-the-fly forms and formfields based on a list of parameters. The parameter types are defined by the enum **ParameterTypes** so that **ParameterTypes.INTEGER** is an int **ParameterTypes.STRING** is a string etc.

#### create_form_field_with_parameter(pdict)
Essentially a case statment which returns a django form field based on the give parameter specified as a dict with keys:

*  display - the ui name for this field
*  name    - the actually field name
*  kind    - the parameter enum value Ex. ParameterTypes.BOOLEAN

A suitable django formfield object such as forms.BooleanField(label=pdict('display')) is returned.

#### create_form_class_with_parameter_list(plist, name)
Create a class for a form using the list of parameter descriptions given. You can optionally give it a name as well.

#### create_form_with_parameter_list(plist, name, initial_dict)
Like create_form_class_with_parameter_list but will create the actual form and assign values based on intial dict.

## mysql_utils.py

This file includes a couple functions which use the process module and mysql/mysqldump to create mysql backups of tables in the db. The filename will be `app_name.sql.gz`

##### Create a zipped dump file of the tables in an app.
    dump_mysql_db(app_name,
     				tables = None,
     				dump_path = None)



##### Load a zipped mysqldump file into the database
    load_mysql_db(app_name, dump_path = None):




## License

MIT , see the `LICENSE` file for details.
