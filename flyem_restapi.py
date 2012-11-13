from flask import Flask, render_template, session, request, redirect, url_for, abort, json
from flask.ext.sqlalchemy import SQLAlchemy
import os
from config import *
import binascii

app = Flask(__name__)
app.secret_key = str(os.urandom(33))
app.config['SQLALCHEMY_DATABASE_URI'] = SQLDB 
db = SQLAlchemy(app)
from functools import wraps

""" session informtation """

# types of media supported (excluding workflow and workflow run)
# and the actual media name it points to
media_type = {}
media_type["substack"] = "substack"
media_type["tbar-ilp"] = "tbar_ilp"
media_type["boundary-ilp"] = "boundary_ilp"
media_type["segmentation-substack"] = "segmentation_substack"
media_type["groundtruth-substack"] = "groundtruth_substack"

# core media properties (not currently in media table)
media_property = {}
media_property["description"] = "description"
media_property["file-path"] = "file_system_path"
media_property["date"] = "create_date"

# core workflow properties (not currently in media table)
workflow_property = {}
media_property["description"] = "description"
workflow_property["owner"] = "owner"
workflow_property["description"] = "description"
workflow_property["date"] = "create_date"

# core workflow_job properties (not current in media table)
workflow_job_property = {}
workflow_job_property["workflow-version"] = "workflow_version"
workflow_job_property["start-time"] = "create_date"
workflow_job_property["description"] = "description"

# general globals
authorization_stored = {}
NORMAL_REQUEST = 200
BAD_REQUEST = 400

""" end session information """



# wrapper for verifying login
def verify_login(f):
    @wraps(f)
    def wrapper_func(*args, **kwargs):
        try:
            auth = request.authorization
            username = auth.username
            password = auth.password
            if username in authorization_stored:
                username_stored, password_stored = authorization_stored[username]
                if password_stored != password:
                    abort(401)
                username = username_stored
            else:
                ## !! UNCOMMENT IN PRODUCTION 
                #conn = ldap.initialize(SERVER)
                #dn_base = ',ou=People,dc=janelia,dc=org'
                #dn = 'cn='+request.form['username']+dn_base
                #pw = request.form['password']
                #r = conn.bind_s(dn, pw, ldap.AUTH_SIMPLE)
            
                # !! COMMENT OUT -- dummy check for now
                if username != "plazas" or password != "password":
                    abort(401)
        except: 
            abort(401)

        if request.method == 'POST' or request.method == 'DELETE' or request.method == 'PUT':
            try:
                print 'SELECT user_property.value as perm FROM user_property JOIN user ON user.id = user_property.user_id JOIN cv_term ON cv_term.id = user_property.type_id WHERE cv_term.name = "workflow_run" and user.name = "' + username + '";'
                results = db.engine.execute('SELECT user_property.value as perm FROM ' +
                        'user_property JOIN user ON user.id = user_property.user_id JOIN ' + 
                        'cv_term ON cv_term.id = user_property.type_id WHERE cv_term.name ' +
                        '= "workflow_run" and user.name = "' + username + '";')

                result =  results.first()
                if result is None or result["perm"] != '1':
                    abort(401)
            except Exception, e:
                abort(401) 

        return f(username, *args, **kwargs)
    return wrapper_func
    
"""
@app.route("/substacks")
@verify_login
def substacks(username):
    result = db.engine.execute('select substack, tbar_annot, psd_annot, focus_annot from fly_em_annotations_vw;')

    json_data = {}
    entries = []
    for ent in result:
        entry = {}
        entry["substack"] = ent[0]
        entry["tbar_annot"] = ent[1]
        entry["psd_annot"] = ent[2]
        entry["focus_annot"] = ent[3]
        entries.append(entry)

    json_data["annotations"] = entries

    return json.dumps(json_data)
"""

# generic wrapper for all queries, json_data should be written to as appropriate
# all queries should start with json_data and connection
def query_handler(fn, *args):
    json_data = request.json
    connection = db.engine.connect()
    trans = connection.begin()
    code = NORMAL_REQUEST

    if json_data is None:
        json_data = {}

    try:
        fn(json_data, connection, *args)
        trans.commit()     
    except Exception, e:
        trans.rollback()     
        json_data["error"] = str(e)
        code = BAD_REQUEST
    
    return json.dumps(json_data), code


# get the cv_term_id from a property_name
def get_cv_term_id(property_name, connection):
    type_id_res = connection.execute('select id from cv_term where name="' + 
            property_name + '";')
    type_id = type_id_res.first()["id"]
    return type_id
    

# set media file
def set_media(name, mtype, connection):
    type_id = get_cv_term_id(mtype, connection)
    lab_id = get_cv_term_id("flyem", connection)
    
    connection.execute('insert into media(name, lab_id, type_id) values("' + name + '", ' +
                str(lab_id) + ', ' + str(type_id) + ');')

    media_id_res = connection.execute('select id from media where name="' + name + '"')
    media_id = media_id_res.first()["id"]

    return media_id

# set property for a given media id
def set_media_property(media_id, property_name, value, connection):
    property_id = get_cv_term_id(property_name, connection)
    connection.execute('insert into media_property(media_id, type_id, value) values(' +
                str(media_id) + ', ' + str(property_id) + ', "' + value + '");')

def media_post(json_data, connection, username, mtype):
    if mtype not in media_type:
        raise Exception("Media type not found")
    mtype = media_type[mtype]
    
    name = json_data["name"]
    description = json_data["description"]
    filepath = json_data["file-path"]
    
    if name is not None and description is not None and mtype is not None and filepath is not None:
        media_id = set_media(name, mtype, connection)
        json_data["media-id"] = media_id
        
        set_media_property(media_id, "file_system_path", filepath, connection)
        set_media_property(media_id, "description", description, connection)
    else:
        raise Exception("Not all parameters were specified")


# url input: media type
# json input: name, description, file-path
@app.route("/media/<mtype>", methods=['POST'])
@verify_login
def add_media(username, mtype):
    return query_handler(media_post, username, mtype)
    

@app.route("/sessionusers", methods=['POST'])
@app.route("/sessionusers/<userid>", methods=['DELETE'])
@verify_login
def sessionusers(username, userid=None):
    if request.method == 'DELETE':
        if userid in authorization_stored:
            name, pw = authorization_stored[userid]
            if name == username:
                del authorization_stored[userid]
                return userid + " deleted"
            else:
                abort(401)
        else:
            abort(404)
    elif request.method == 'POST' and userid is None:
        uid = str(binascii.b2a_hex(os.urandom(8)))
        secretkey = str(binascii.b2a_hex(os.urandom(8)))
        authorization_stored[uid] = (username, secretkey)
        json_data = {}
        json_data['uid'] = uid
        json_data['secretkey'] = secretkey

        return json.dumps(json_data)
    
    abort(401)

if __name__ == "__main__":
    try:
        app.run()
    except Exception, e:
        print e



