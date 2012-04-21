import os
import os.path
from django.conf import settings
import shutil
import hashlib
from datetime import datetime

class FileStoreLocations(object):
    FILE_SYSTEM         = 0
    APP_INBOX           = 10
    OBJECT_FOLDER       = 20
    CLOUD_STORAGE_S3    = 30
    TEMP                = 999

    CHOICES = (
          (FILE_SYSTEM, "File System"),
          (APP_INBOX, "Application Inbox"),
          (OBJECT_FOLDER, "Object's Folder"),
          (CLOUD_STORAGE_S3, "S3 Cloud Storage"),
          (TEMP, "Temp File"),
    )
    #
    # Signifiers can be used in a path name
    # Example  file:/dkwjdwkd/dwdwd/  means its on the file system
    #          inbox:foo.txt is a file foo.txt in an app specific inbox
    #
    SIGNIFIERS = {
        FILE_SYSTEM: "file",
        APP_INBOX  :  "inbox",
        OBJECT_FOLDER :  "object",
        CLOUD_STORAGE_S3 :  "s3",
        TEMP   : "tmp"
    }

    @classmethod
    def add_signifier_prefix_to_path(self, path, signifier_id):
        return "%s:%s" % (self.SIGNIFIERS[signifier_id], path)

    @classmethod
    def split_path_and_signifier(self, path):
        sig = self.FILE_SYSTEM
        rpath = path
        if ":" in path:
            sig, rpath = path.split(':')
            for x in self.SIGNIFIERS:
                if self.SIGNIFIERS[x] == sig:
                    sig = x
                    break

        return rpath, sig




def get_path_with_folders(path, group, object_kind = None, folder = None):
    if group:
        path = os.path.join(path,group)

    if object_kind:
        path = os.path.join(path, object_kind)

    if folder:
        path = os.path.join(path, folder)


    insure_folder(path)
    return path


def get_object_folder_file_path(filename, object_group, object_kind, object_folder):
    """
    Return a file path for filename and the given path folder.
    """
    path = get_path_with_folders(settings.FILE_PERMANENT_DATA_ROOT, object_group, object_kind, object_folder)
    jp= os.path.join(path, filename)
    return jp

def get_date_filename(prefix):
    n = datetime.now()
    return prefix + "_" + n.strftime("%y_%m_%d_%H_%M_%S")

def path_exists(path, group, kind=None, folder=None):
    path, sig = FileStoreLocations.split_path_and_signifier(path)
    if sig == FileStoreLocations.APP_INBOX:
        path = get_inbox_file_path(path, group)
    if sig == FileStoreLocations.FILE_SYSTEM:
        path = path
    if sig == FileStoreLocations.OBJECT_FOLDER:
        path = get_object_folder_file_path(path, group, kind, folder)

    return os.path.exists(path)
    
    
def insure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, 0744)
    return path


def check_extensions(x, elist):
    """
    Does the file x have any of the extensions in the list elist
    """
    if not elist:  # if no qualifier then we are good
        return True

    extension = os.path.splitext(x)[1].lower()

    for y in elist: # for each extension we just have to match one
        if '.'+ y == extension:
            return True
    return False

def switch_extension(filename, new_extension):
    file, old_extension = os.path.splitext(filename)
    return file+new_extension

def strip_extension(filename):
    return os.path.splitext(filename)[0]

def get_inbox_file_list(group = None, extensions = None):
    """
    Abstracts looking for incoming files. for now just looks in a dir. Someday might look
    at S3/Cloudfiles etc.
    """
    path = get_path_with_folders(settings.FILE_INBOX_DATA_ROOT, group)
    files  =  sorted([(os.path.getmtime(os.path.join(path, x)), x) for x in os.listdir(path) if check_extensions(x, extensions)], reverse=True)

    return [x[1] for x in files]


def get_inbox_file_path(filename, group):
    """
    Return a file path for filename and the given path folder.
    """
    path = get_path_with_folders(settings.FILE_INBOX_DATA_ROOT, group)
    return os.path.join(path, filename)

def get_file_size_for_path(pathname):
    return os.path.getsize(pathname)

def humanize_file_size(size):
    if size < 1024:
        return "%d Bytes" % size
    elif size < 1024*1024:
        return "%4.2f kB" % (size/1024.0)
    elif size < 1024*1024*1024:
        return "%4.2f MB" % (size/(1024.0*1024.0))
    elif size < 1024*1024*1024*1024:
        return "%4.2f GB" % (size/(1024.9*1024.0*1024.0))

def get_sha256_digest_for_path(pathname):
    f = open(pathname, 'rb')
    digest = hashlib.sha256()
    endOfFile = False
    while not endOfFile:
        bytes = f.read(8192)
        digest.update(bytes)
        endOfFile = len(bytes) != 8192

    return digest.hexdigest()


def remove_file_from_inbox(filename, group):
    os.remove(get_inbox_file_path(filename, group))


def insure_file_in_object_folder(filename, signifier, group, kind, folder):
    """
    Copy a file from the  to the permanent storage location
    """
    if signifier == FileStoreLocations.OBJECT_FOLDER:
        return
    src = filename
    if signifier == FileStoreLocations.FILE_SYSTEM:
        src = filename
        filename = os.path.basename(filename)

    elif signifier == FileStoreLocations.APP_INBOX:
        src =  get_inbox_file_path(filename, group)
    else:
        assert 0, "File store location (%s) not supported" % (FileStoreLocations.SIGNIFIERS.get(signifier,"Unknown"))

    dest = get_object_folder_file_path(filename, group, kind, folder)
    shutil.copy(src, dest)


def handle_django_file_upload(f, group):
    """
    Handles the uploading of a file from a django form fileField
    """
    f_obj = open(get_inbox_file_path(f.name, group), "wb")
    for chunk in f.chunks():
        f_obj.write(chunk)
    f_obj.close()
    return f.name