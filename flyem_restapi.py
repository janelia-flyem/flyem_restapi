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
rmedia_type = dict((reversed(item) for item in media_type.items()))


"""
# core media properties (not currently in media table)
media_property = {}
media_property["description"] = "description"
media_property["file-path"] = "file_system_path"
media_property["date"] = "create_date"
media_property["name"] = "name"

rmedia_property = dict((reversed(item) for item in media_property.items()))

# core workflow properties (not currently in media table)
workflow_property = {}
workflow_property["description"] = "description"
workflow_property["owner"] = "owner"
workflow_property["date"] = "create_date"
workflow_property["name"] = "name"

# core workflow_job properties (not current in media table)
workflow_job_property = {}
workflow_job_property["workflow-version"] = "workflow_version"
workflow_job_property["start-time"] = "create_date"
workflow_job_property["description"] = "description"

"""

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
    except:
        trans.rollback()     
        json_data["error"] = "Unknown error"
        code = 500

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


def where_builder(where_str, term_name, value, predicate="LIKE"):
    if value is not None:
        if where_str == '':
            where_str += " WHERE "
        else:
            where_str += " AND "
        if predicate == "LIKE":
            where_str = where_str + term_name + ' LIKE "%%' + value.lower() + '%%" '
        else:
            where_str = where_str + term_name + ' = "' + value + '" '
    return where_str

def limit_builder(pos1, pos2):
    if pos1 is not None and pos2 is not None:
        if pos2 < pos1:
            raise Exception("Incorrect data range specified")
        limit_str = ' LIMIT ' + str(pos1) + ', ' + str(pos2 - pos1 + 1) + ' '
    return limit_str


""" media handlers """

def workflow_post(json_data, connection, owner, workflow_type):
    name = json_data["name"]
    description = json_data["description"]
    workflow_interface = json_data["workflow-interface-version"]

    if name is not None and description is not None and workflow_interface is not None:
        media_id = set_media(name, "workflow", connection)
        json_data["workflow-id"] = media_id
        
        set_media_property(media_id, "description", description, connection)
        set_media_property(media_id, "owner", owner, connection)
        set_media_property(media_id, "workflow_type", workflow_type, connection)
        set_media_property(media_id, "workflow_interface_version", workflow_interface, connection)
    else:
        raise Exception("Not all parameters were specified")

def workflow_get():
    pass




def media_post(json_data, connection, mtype):
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


# only grab media with a file path (description is still optional)
def media_get(json_data, connection, mtype, mid, pos1, pos2):
    where_str = ''
    limit_str = ''
    order_by = 'ORDER BY media.create_date DESC'

    limit_str = limit_builder(pos1, pos2)
    if mtype is not None:
        mtype = media_type[mtype]
        where_str = where_builder(where_str, "cv_term.name", mtype, '=')
        where_str = where_builder(where_str, "media.id", mid, '=')

    name = request.args.get('name')
    where_str = where_builder(where_str, 'media.name', name)
    
    description = request.args.get('description')
    where_str = where_builder(where_str, 'mp2.value', description)
    
    file_path = request.args.get('file-path')
    where_str = where_builder(where_str, 'media_property.value', file_path)
    
    media_type_t = request.args.get('media-type')
    if media_type_t in media_type:
        media_type_t = media_type[media_type_t]
    where_str = where_builder(where_str, 'cv_term.name', media_type_t)

    where_str = where_builder(where_str, 'cv_term2.name', "file_system_path")
    where_str = where_builder(where_str, 'cv_term3.name', "description")
    
    results = connection.execute("SELECT mp2.value as description, media_property.value " +
            "AS file_system_path, media.name AS name, media.id AS mid, cv_term.name AS type, " + 
            "media.create_date AS date FROM media JOIN cv_term ON cv_term.id = media.type_id JOIN " + 
            "media_property ON media_property.media_id = media.id JOIN cv_term as cv_term2 " +
            "ON cv_term2.id = media_property.type_id JOIN media_property AS mp2 ON mp2.media_id = " +
            "media.id JOIN cv_term AS cv_term3 ON cv_term3.id = mp2.type_id " + where_str +
            order_by + limit_str + ";")

    json_results = []

    for result in results:
        json_result = {}
        json_result["name"] = result["name"]
        json_result["id"] = result["mid"]
        if result["type"] in rmedia_type:
            json_result["type"] = rmedia_type[(result["type"])]
        json_result["date"] = str(result["date"])
        json_result["description"] = result["description"]
        json_result["file-path"] = result["file_system_path"]
        json_results.append(json_result)

    json_data["results"] = json_results

""" end media handlers """


### POST ###
# url input: media type
# json input: name, description, file-path
### GET ###
# url input: media type=none, id=none
# json_output: name/id, date, media_type_name, description, original_file_path
@app.route("/media", methods=['GET'])
@app.route("/media/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/media/<mtype>", methods=['POST'])
@app.route("/media/<mtype>", methods=['GET'])
@app.route("/media/<mtype>/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/media/<mtype>/<int:mid>", methods=['GET'])
@verify_login
def media_route(username, mtype=None, mid=None, pos1=None, pos2=None):
    if request.method == 'POST':
        return query_handler(media_post, mtype)
    elif request.method == 'GET':
        return query_handler(media_get, mtype, mid, pos1, pos2)





@app.route("/owners/<owner>/workflows/<workflow_type>", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>/<workflow_id>", methods=['GET'])
@verify_login
def workflow_type(username, owner, workflow_type, workflow_id=None, pos1=None, pos2=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_post, owner, workflow_type)
    else:
        return query_handler(workflow_get, owner, workflow_type, workflow_id, pos1, pos2)
        





"""

# support general queries to workflows -- default date sort
@app.route("/owners/<owner>/workflows", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:pos1>-<int:pos2>", methods=['GET'])



# no support for general queries for more specific workflow calls
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters/<parameter>", methods=['PUT', 'GET'])

@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs/<int:mid>", methods=['PUT'])

@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs/<int:mid>", methods=['PUT'])


# support general queries (such as workflow type) to workflow jobs -- default date sort
@app.route("/owners/<owner>/jobs", methods=['GET'])
@app.route("/owners/<owner>/jobs/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/jobs/<not>completed", methods=['GET'])
@app.route("/owners/<owner>/jobs/<not>completed/<int:pos1>-<int:pos2>", methods=['GET'])

@app.route("/owners/<owner>/workflows/<workflow_id>/jobs", methods=['POST', 'GET']) # show comments
@app.route("/owners/<owner>/workflows/<workflow_id>/jobs/<int:pos1>-<int:pos2>", methods=['GET']) # show comments


# no support for general queries for more specific workflow job calls
@app.route("/owners/<owner>/jobs/<int:job_id>", methods=['GET'])

@app.route("/owners/<owner>/jobs/completed/<int:job_id>", methods=['PUT'])

@app.route("/owners/<owner>/jobs/<job_id>/job-parents", methods=['GET'])
@app.route("/owners/<owner>/jobs/<job_id>/job-parents/<par_id>", methods=['PUT'])

@app.route("/owners/<owner>/jobs/<job_id>/comments", methods=['POST', 'GET'])



"""









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



