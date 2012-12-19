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
media_type["boundary-h5"] = "boundary_h5"
media_type["segmentation-substack"] = "segmentation_substack"
media_type["groundtruth-substack"] = "groundtruth_substack"
media_type["synapse-json"] = "synapse_json"
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
def get_cv_term_id(property_name, connection, cv_name = None):
    where_str = ''

    if cv_name is not None:
        where_str = ' AND cv.name = "' + cv_name + '" '
    
    type_id_res = connection.execute('SELECT cv_term.id as id FROM cv_term JOIN cv ON ' +
            'cv.id = cv_term.cv_id WHERE cv_term.name="' + property_name + '" ' + where_str + ';')
    type_id = type_id_res.first()["id"]
    return type_id
    

# set media file
def set_media(name, mtype, connection):
    type_id = get_cv_term_id(mtype, connection)
    lab_id = get_cv_term_id("flyem", connection)
   

    connection.execute('insert into media(name, lab_id, type_id) values("' + name + '", ' +
                str(lab_id) + ', ' + str(type_id) + ');')

    media_id_res = connection.execute('select id, create_date from media where name="' + name + '"')
    media_entry = media_id_res.first()
    media_id = media_entry["id"]
    create_date = media_entry["create_date"]

    return media_id, str(create_date)

# set property for a given media id
def set_media_property(media_id, property_name, value, connection, cv_name = None):
    property_id = get_cv_term_id(property_name, connection, cv_name)
    connection.execute('insert into media_property(media_id, type_id, value) values(' +
                str(media_id) + ', ' + str(property_id) + ', "' + value + '");')


def where_builder(where_str, term_name, value, predicate="LIKE"):
    if value is not None:
        if where_str == '':
            where_str += " WHERE "
        else:
            where_str += " AND "
        value = str(value)
        if predicate == "LIKE":
            where_str = where_str + term_name + ' LIKE "%%' + value.lower() + '%%" '
        else:
            where_str = where_str + term_name + ' = "' + value + '" '
    return where_str

def limit_builder(pos1, pos2):
    limit_str = ''
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
        media_id, dummy = set_media(name, "workflow", connection)
        json_data["workflow-id"] = media_id
        
        set_media_property(media_id, "description", description, connection)
        set_media_property(media_id, "owner", owner, connection)
        set_media_property(media_id, "workflow_type", workflow_type, connection)
        set_media_property(media_id, "workflow_interface_version", workflow_interface, connection)
    else:
        raise Exception("Not all parameters were specified")

def workflow_get(json_data, connection, owner, workflow_type, pos1, pos2):
    where_str = ''
    order_by = 'ORDER BY media.create_date DESC'

    limit_str = limit_builder(pos1, pos2)
    
    workflow_id = request.args.get('workflow-id')
    where_str = where_builder(where_str, "media.id", workflow_id, '=')

    name = request.args.get('name')
    where_str = where_builder(where_str, 'media.name', name)
    
    where_str = where_builder(where_str, "cv_term.name", "workflow", '=')

    where_str = where_builder(where_str, 'cv_term2.name', "workflow_type")
    where_str = where_builder(where_str, 'media_property.value', workflow_type)
    temp_type = request.args.get('workflow-type')
    where_str = where_builder(where_str, 'media_property.value', temp_type)

    where_str = where_builder(where_str, 'cv_term3.name', "description")
    description = request.args.get('description')
    where_str = where_builder(where_str, 'mp2.value', description)
  
    where_str = where_builder(where_str, 'cv_term4.name', "owner")
    where_str = where_builder(where_str, 'mp3.value', owner, '=')

    where_str = where_builder(where_str, 'cv_term5.name', "workflow_interface_version")
    workflow_interface = request.args.get('interface-version')
    where_str = where_builder(where_str, 'mp4.value', workflow_interface, '=')

    results = connection.execute("SELECT SQL_CALC_FOUND_ROWS  mp4.value as interface_version, "
            "mp2.value as description, media_property.value " +
            "AS workflow_type, media.name AS name, media.id AS id, cv_term.name AS type, " + 
            "media.create_date AS date FROM media JOIN cv_term ON cv_term.id = media.type_id JOIN " + 
            "media_property ON media_property.media_id = media.id JOIN cv_term as cv_term2 " +
            "ON cv_term2.id = media_property.type_id JOIN media_property AS mp2 ON mp2.media_id = " +
            "media.id JOIN cv_term AS cv_term3 ON cv_term3.id = mp2.type_id " + 
            "JOIN media_property AS mp3 ON mp3.media_id = " +
            "media.id JOIN cv_term AS cv_term4 ON cv_term4.id = mp3.type_id " + 
            "JOIN media_property AS mp4 ON mp4.media_id = " +
            "media.id JOIN cv_term AS cv_term5 ON cv_term5.id = mp4.type_id " + 
            where_str + order_by + limit_str + ";")

    json_results = []

    num_matches = connection.execute("SELECT found_rows();")
    json_data["num-matches"] = num_matches.first()[0]

    for result in results:
        json_result = {}
        json_result["name"] = result["name"]
        json_result["id"] = result["id"]
        json_result["date"] = str(result["date"])
        json_result["description"] = result["description"]
        json_result["workflow-type"] = result["workflow_type"]
        json_result["owner"] = owner
        json_result["interface-version"] = result["interface_version"]
        json_results.append(json_result)

    json_data["results"] = json_results

def create_param_type_id(name, connection):
    cv_id_res = connection.execute('SELECT id FROM cv WHERE name = "workflow_parameters"')
    cv_id = cv_id_res.first()["id"]
    connection.execute('INSERT IGNORE INTO cv_term(cv_id, name, definition, is_current, display_name, data_type) ' +
            'VALUES(' + str(cv_id) + ', "' + name + '", "Parameter used in one of the workflows", 1, ' +
            '"' + name + '", "text");')

def create_media_input_type_id(name, connection):
    cv_id_res = connection.execute('SELECT id FROM cv WHERE name = "media_workflow_relationships"')
    cv_id = cv_id_res.first()["id"]
    connection.execute('INSERT IGNORE INTO cv_term(cv_id, name, definition, is_current, display_name, data_type) ' +
            'VALUES(' + str(cv_id) + ', "' + name + '", "Media input type to workflow", 1, ' +
            '"' + name + '", "text");')



def workflow_param_post(json_data, connection, workflow_id):
    for param in json_data["parameters"]:
        create_param_type_id(param["name"], connection)
        set_media_property(workflow_id, str(param["name"]), str(param["value"]), connection, 'workflow_parameters')


    
   
def workflow_param_put(json_data, connection, workflow_id, parameter):
    create_param_type_id(parameter, connection)
    set_media_property(workflow_id, parameter, str(json_data["value"]), connection)


def workflow_param_get(json_data, connection, workflow_id, parameter):
    where_str = ''
    where_str = where_builder(where_str, "media_property.media_id", str(workflow_id), '=')
    where_str = where_builder(where_str, "cv.name", "workflow_parameters", '=')
    
    results = connection.execute("SELECT media_property.value AS value, cv_term.name AS name FROM "
            + "media_property JOIN cv_term ON cv_term.id = media_property.type_id JOIN cv ON "
            + "cv.id = cv_term.cv_id " + where_str)

    parameters = []
    for result in results:
        if parameter is None or parameter == result["name"]:
            param = {}
            param["name"] = result["name"]
            param["value"] = result["value"]
            parameters.append(param)

    json_data["results"] = parameters

def insert_relationship(parent, child, type_name, connection):
    type_id = get_cv_term_id(type_name, connection)
    connection.execute("INSERT INTO media_relationship(type_id, subject_id, object_id, is_current) " +
            "VALUES(" + str(type_id) + ", " + str(parent) + ", " + str(child) + ", 1)")

    
def create_workflow_input_type_id(name, connection):
    cv_id_res = connection.execute('SELECT id FROM cv WHERE name = "workflow_workflow_relationships"')
    cv_id = cv_id_res.first()["id"]
    connection.execute('INSERT IGNORE INTO cv_term(cv_id, name, definition, is_current, display_name, data_type) ' +
            'VALUES(' + str(cv_id) + ', "' + name + '", "Workflow input type to workflow", 1, ' +
            '"' + name + '", "text");')

def workflow_workflow_post(json_data, connection, workflow_id):
    for entry in json_data["workflow-inputs"]:
        create_workflow_input_type_id(entry["name"], connection)
        insert_relationship(entry["id"], workflow_id, entry["name"], connection)    
 
def workflow_workflow_put(json_data, connection, workflow_id, input_name, wid):
    create_workflow_input_type_id(input_name, connection)
    insert_relationship(wid, workflow_id, input_name, connection)    

def workflow_workflow_get(json_data, connection, workflow_id):
    where_str = ''
    where_str = where_builder(where_str, "media_relationship.object_id", workflow_id, '=')
    where_str = where_builder(where_str, "cv.name", "workflow_workflow_relationships", '=')
    
    results = connection.execute("SELECT media_relationship.subject_id AS parent, cv_term.name AS type FROM "
            + "media_relationship JOIN cv_term ON cv_term.id = media_relationship.type_id JOIN cv ON cv.id = "
            + "cv_term.cv_id " + where_str)

    workflow_inputs = []
    for result in results:
        workflow_inputs.append({ "name" : result["type"], "id" : result["parent"] })

    json_data["workflow-inputs"] = workflow_inputs 

def workflow_media_post(json_data, connection, workflow_id):
    for entry in json_data["media-inputs"]:
        create_media_input_type_id(entry["name"], connection)
        insert_relationship(entry["id"], workflow_id, entry["name"], connection)    
    
def workflow_media_put(json_data, connection, workflow_id, input_name, mid):
    create_media_input_type_id(input_name, connection)
    insert_relationship(mid, workflow_id, input_name, connection)    

def workflow_media_get(json_data, connection, workflow_id):
    where_str = ''
    where_str = where_builder(where_str, "media_relationship.object_id", workflow_id, '=')
    where_str = where_builder(where_str, "cv.name", "media_workflow_relationships", '=')
    
    results = connection.execute("SELECT media_relationship.subject_id AS parent, cv_term.name AS type FROM "
            + "media_relationship JOIN cv_term ON cv_term.id = media_relationship.type_id JOIN cv ON cv.id = "
            + "cv_term.cv_id " + where_str)

    media_inputs = []
    for result in results:
        media_inputs.append({ "name" : result["type"], "id" : result["parent"] })

    json_data["media-inputs"] = media_inputs 


def media_post(json_data, connection, mtype):
    if mtype not in media_type:
        raise Exception("Media type not found")
    mtype = media_type[mtype]
    
    name = json_data["name"]
    description = json_data["description"]
    filepath = json_data["file-path"]
    
    if name is not None and description is not None and mtype is not None and filepath is not None:
        media_id, dummy = set_media(name, mtype, connection)
        json_data["media-id"] = media_id
        
        set_media_property(media_id, "file_system_path", filepath, connection)
        set_media_property(media_id, "description", description, connection)
    else:
        raise Exception("Not all parameters were specified")


# only grab media with a file path (description is still optional)
def media_get(json_data, connection, mtype, pos1, pos2):
    where_str = ''
    limit_str = ''
    order_by = 'ORDER BY media.create_date DESC'

    limit_str = limit_builder(pos1, pos2)
    if mtype is not None:
        mtype = media_type[mtype]
        where_str = where_builder(where_str, "cv_term.name", mtype, '=')
    
    mid = request.args.get('media-id')
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

    where_str = where_builder(where_str, 'cv_term2.name', "file_system_path", '=')
    where_str = where_builder(where_str, 'cv_term3.name', "description", '=')
   
    results = connection.execute("SELECT SQL_CALC_FOUND_ROWS mp2.value as description, media_property.value " +
            "AS file_system_path, media.name AS name, media.id AS mid, cv_term.name AS type, " + 
            "media.create_date AS date FROM media JOIN cv_term ON cv_term.id = media.type_id JOIN " + 
            "media_property ON media_property.media_id = media.id JOIN cv_term as cv_term2 " +
            "ON cv_term2.id = media_property.type_id JOIN media_property AS mp2 ON mp2.media_id = " +
            "media.id JOIN cv_term AS cv_term3 ON cv_term3.id = mp2.type_id " + where_str +
            order_by + limit_str + ";")
    
    num_matches = connection.execute("SELECT found_rows();")
    json_data["num-matches"] = num_matches.first()[0]
    
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

def workflow_jobs_post(json_data, connection, owner, workflow_id):
    workflow_version = json_data["workflow-version"]
    description = json_data["description"]
    json_data["workflow-id"] = workflow_id
    json_data["is-complete"] = "false"

    if description is not None and workflow_version is not None:
        num_jobs_res = connection.execute('SELECT cv_term.id from media_relationship JOIN cv_term ON ' +
               'cv_term.id = media_relationship.type_id WHERE cv_term.name = "workflow_to_workflow_job" AND ' +
               'media_relationship.subject_id = ' + str(workflow_id) + ';') 

        max_index = 1
        for job in num_jobs_res:
            max_index += 1 

        name =  str(workflow_id) + "-job-" + str(max_index)

        media_id, create_date = set_media(name, "workflow_job", connection)
       
        insert_relationship(workflow_id, media_id, "workflow_to_workflow_job", connection) 

        set_media_property(media_id, "description", description, connection)
        set_media_property(media_id, "owner", owner, connection)
        #set_media_property(media_id, "workflow_job_complete", "0", connection)
        set_media_property(media_id, "workflow_version", workflow_version, connection)
        
        json_data["job-name"] = name 
        json_data["job-id"] = media_id
        json_data["job-start-time"] = create_date
    else:
        raise Exception("Not all parameters were specified")

def job_query_get(json_data, connection, owner, complete_status, workflow_id, pos1, pos2, job_id=None):
    where_str = ''
    order_by = 'ORDER BY media.create_date DESC'
    limit_str = limit_builder(pos1, pos2)

    comment_id = get_cv_term_id("comment", connection)
    completion_id = get_cv_term_id("workflow_job_complete", connection)

    where_str = where_builder(where_str, "media.id", job_id, '=')
    
    name = request.args.get('name') 
    where_str = where_builder(where_str, "media.name", name)
    
    where_str = where_builder(where_str, "cv_term.name", "workflow_job", '=')

    where_str = where_builder(where_str, 'cv_term2.name', "workflow_version")
    workflow_version = request.args.get('workflow-version') 
    where_str = where_builder(where_str, 'media_property.value', workflow_version)
    
    where_str = where_builder(where_str, 'cv_term3.name', "description")
    description = request.args.get('description')
    where_str = where_builder(where_str, 'mp2.value', description)
  
    where_str = where_builder(where_str, 'cv_term4.name', "owner")
    where_str = where_builder(where_str, 'mp3.value', owner, '=')

    # JOIN MEDIA_RELATIONSHIP
    where_str = where_builder(where_str, "cv_term5.name", "workflow_to_workflow_job", '=')
    workflow_name = request.args.get('workflow-name')
    where_str = where_builder(where_str, "media_wf.name", workflow_name)

    if workflow_id is None:
        workflow_id = request.args.get('workflow-id')
        
    where_str = where_builder(where_str, "media_wf.id", workflow_id)
    

    # LEFT JOIN special for comment and complete date
    comment = request.args.get('comment')
    where_str = where_builder(where_str, 'm_comment.value', comment)

    if complete_status is not None:
        if where_str == '':
            where_str += " WHERE "
        else:
            where_str += " AND "    
        if complete_status:
            where_str = where_str + "m_status.value IS NOT NULL "
        else:
            where_str = where_str + "m_status.value IS NULL "

    status = request.args.get('is-complete')
    if status is not None:
        if where_str == '':
            where_str += " WHERE "
        else:
            where_str += " AND "    
        status = status.lower()
        if status == "true":
            where_str = where_str + "m_status.value IS NOT NULL "
        else:
            where_str = where_str + "m_status.value IS NULL "    

    results = connection.execute("SELECT SQL_CALC_FOUND_ROWS  m_status.create_date AS complete_date, " +
            "m_comment.value AS comment, media_wf.name AS workflow_name, " +
            "media_wf.id AS workflow_id, "
            "mp2.value as description, media_property.value " +
            "AS workflow_version, media.name AS name, media.id AS id, cv_term.name AS type, " + 
            "media.create_date AS submit_date FROM media JOIN cv_term ON cv_term.id = media.type_id JOIN " + 
            "media_property ON media_property.media_id = media.id JOIN cv_term as cv_term2 " +
            "ON cv_term2.id = media_property.type_id JOIN media_property AS mp2 ON mp2.media_id = " +
            "media.id JOIN cv_term AS cv_term3 ON cv_term3.id = mp2.type_id " + 
            "JOIN media_property AS mp3 ON mp3.media_id = " +
            "media.id JOIN cv_term AS cv_term4 ON cv_term4.id = mp3.type_id " + 
            "JOIN media_relationship AS mr ON mr.object_id = media.id " +
            "JOIN media AS media_wf ON media_wf.id = mr.subject_id " +
            "JOIN cv_term AS cv_term5 ON cv_term5.id = mr.type_id " +
            "LEFT JOIN media_property AS m_comment ON media.id = m_comment.media_id " +
            "AND m_comment.type_id = " + str(comment_id) + " " + 
            "LEFT JOIN media_property AS m_status ON media.id = m_status.media_id " +
            "AND m_status.type_id = " + str(completion_id) + " " + 
            where_str + order_by + limit_str + ";")

    num_matches = connection.execute("SELECT found_rows();")
    json_data["num-matches"] = num_matches.first()[0]

    json_results = []
    for result in results:
        json_result = {}
        json_result["workflow-name"] = result["workflow_name"]
        json_result["workflow-id"] = result["workflow_id"]
        json_result["name"] = result["name"]
        json_result["id"] = result["id"]
        json_result["submit-date"] = str(result["submit_date"])
        json_result["owner"] = owner
        json_result["description"] = result["description"]
        json_result["workflow-version"] = result["workflow_version"]
        
        
        json_result["comment"] = result["comment"]
        json_result["complete-date"] = str(result["complete_date"])
        json_results.append(json_result)

    json_data["results"] = json_results




def job_complete_put(json_data, connection, owner, job_id):
    set_media_property(job_id, "workflow_job_complete", "1", connection)

def workflow_job_comment_put(json_data, connection, owner, job_id):
    property_id = get_cv_term_id("comment", connection)

    connection.execute('INSERT INTO media_property(media_id, type_id, value) VALUES(' +
            str(job_id) + ', ' + str(property_id) + ', "' + str(json_data["value"]) + '") ' +
            'ON DUPLICATE KEY UPDATE value = "' + str(json_data["value"]) + '";')  

def workflow_job_comment_get(json_data, connection, job_id):
    where_str = ''
    where_str = where_builder(where_str, "media_property.media_id", job_id, '=')
    where_str = where_builder(where_str, "cv_term.name", "comment", '=')
   
    results = connection.execute("SELECT media_property.value AS value FROM "
            + "media_property JOIN cv_term ON cv_term.id = media_property.type_id " + where_str)

    json_data["value"] = results.first()["value"]


def job_job_post(json_data, connection, job_id):
    for parent_id in json_data["job-inputs"]:
        insert_relationship(parent_id, job_id, "workflow_job_to_workflow_job", connection)    
    
def job_job_put(json_data, connection, job_id, parent_id):
    insert_relationship(parent_id, job_id, "workflow_job_to_workflow_job", connection)    

def job_job_get(json_data, connection, job_id):
    where_str = ''
    where_str = where_builder(where_str, "media_relationship.object_id", job_id, '=')
    where_str = where_builder(where_str, "cv_term.name", "workflow_job_to_workflow_job", '=')
    
    results = connection.execute("SELECT media_relationship.subject_id AS parent FROM "
            + "media_relationship JOIN cv_term ON cv_term.id = media_relationship.type_id "
            + where_str)

    job_inputs = []
    for result in results:
        job_inputs.append(result["parent"])

    json_data["job-inputs"] = job_inputs 




""" end media handlers """


