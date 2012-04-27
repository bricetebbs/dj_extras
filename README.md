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

