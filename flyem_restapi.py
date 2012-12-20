from restful_core import *

### json outputs for HTTP requests will return a message in 'error' if an error occurs
### must specify username/password or uid/uidpassword created by a session



## ?! protect alter comment command



## ?! REMOVE WORKFOW TYPE FROM MEDIA PROPERTY
## ?! create workflow types dynamically and fold into media table


## ?! test both job submissions


## ?! copy documentation of current system over along with dynamic cv-term strategy, state Tom's plan (need owner and non-unique), put on wiki
## ?! highlight weak parts of code/unfinished parts of code in a wiki





## ?! copy git repo to flyem
## ?! present stuff sometime on Thursday



## ?? how to do regular expressions on routes
## ?? occassional crashes -- why??
## ?! make an admin mode for submitting job completion status



### Media POST ###
# url input: /<media type> (groundtruth_substack, substack, tbar_detect_ilp, boundary_ilp
# json input: name, description, file-path
# json ouptut: media-id
### Media GET ###
# url input: media type=none, id=none
# url query string: name, description, file-path, media-type 
# json_output: results = [ {name/id, date, media_type_name, description, file-path}, ... ], num-matches
@app.route("/media", methods=['GET'])
@app.route("/media/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/media/<mtype>", methods=['POST', 'GET'])
@app.route("/media/<mtype>/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def media_route(username, mtype=None, pos1=None, pos2=None):
    if request.method == 'POST':
        return query_handler(media_post, mtype)
    else: 
        return query_handler(media_get, mtype, pos1, pos2)


### Workflow POST ###
# url input: /<owner>/workflows/<workflow type> (tbar, gala-train, gala-segmentation-pipeline)
# json input: name, description, workflow-interface-version,
# parameters = [ { "name" : <name>, "value" : <value> }, ... ]
# workflow-inputs [ {"name" : <name>, "id" : <id> }, ... ]
# media-inputs [ { "name" : <name>, "id" : <id> }, ... ]
# json output: workflow-id 
### Workflow GET ###
# url input: /<owner/workflows/<workflow_type=None>/<position1 - position2>
# url query string: name, workflow-type, workflow-id, description, interface-version
# json output: results = [ {name, id, date, description, workflow-type, owner, interface-version}, ... ], num-matches 
@app.route("/owners/<owner>/workflows", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def workflow_type(username, owner, workflow_type=None, pos1=None, pos2=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_post, owner, workflow_type)
    else:
        return query_handler(workflow_get, owner, workflow_type, pos1, pos2)


### Workflow parameter GET ###
# url input: /<owner>/workflows/<workflow id>/parameters/<parameter = None>
# json output: results = [ {name, value}, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters/<parameter>", methods=['GET'])
@verify_login
def workflow_params(username, owner, workflow_id, parameter=None):
    return query_handler(workflow_param_get, workflow_id, parameter)     


### Workflow media inputs GET ###
# url input: /<owner>/workflows/<workflow id>
# json output: media-inputs [ { "name" : <name>, "id" : <id> }, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs", methods=['GET'])
@verify_login
def workflow_media(username, owner, workflow_id, input_name=None, mid=None):
    return query_handler(workflow_media_get, workflow_id)     


### Workflow workflow inputs GET ###
# url input: /<owner>/workflows/<workflow id>
# json output: workflow-inputs [ { "name" : <name>, "id" : <id> }, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs", methods=['GET'])
@verify_login
def workflow_workflow(username, owner, workflow_id, wid=None):
    return query_handler(workflow_workflow_get, workflow_id)     


### Job GET ###
# url input: <owner>
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ {workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date}, ... ], num-matches
@app.route("/owners/<owner>/jobs", methods=['GET'])
@app.route("/owners/<owner>/jobs/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/jobs/<int:job_id>", methods=['GET'])
@verify_login
def jobs_basic(username, owner, pos1=None, pos2=None, job_id=None):
    return query_handler(job_query_get, owner, None, None, pos1, pos2, job_id)


### Job Put ###
# url input: <owner>/jobs/completed/<job id>
### Job GET ###
# url input: <owner>/jobs/completed
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ {workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date}, ...], num-matches
@app.route("/owners/<owner>/jobs/completed", methods=['GET'])
@app.route("/owners/<owner>/jobs/completed/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/jobs/completed/<int:job_id>", methods=['PUT'])
@verify_login
def jobs_completed(username, owner, pos1=None, pos2=None, job_id = None):
    if request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(job_complete_put, owner, job_id)
    else:
        return query_handler(job_query_get, owner, True, None, pos1, pos2)


### Job GET ###
# url input: <owner>/jobs/notcompleted
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ {workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date}, ...], num-matches
@app.route("/owners/<owner>/jobs/notcompleted", methods=['GET'])
@app.route("/owners/<owner>/jobs/notcompleted/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def jobs_notcompleted(username, owner, pos1=None, pos2=None):
    return query_handler(job_query_get, owner, False, None, pos1, pos2)


# job number will be name of workflow with the number of jobs for that workflow
### Job POST ###
# url input: <owner>/workflows/<workflow id>
# json input: workflow-version, description, job-inputs [ id1, id2, ... ]
# json output: job-name, job-id, job-start-time, is-complete 
### Job GET ###
# url input: <owner>/workflows/<workflow id>
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ {workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date}, ...], num-matches
@app.route("/owners/<owner>/workflows/<workflow_id>/jobs", methods=['POST', 'GET']) # show comments
@app.route("/owners/<owner>/workflows/<workflow_id>/jobs/<int:pos1>-<int:pos2>", methods=['GET']) # show comments
@verify_login
def workflow_jobs(username, owner, workflow_id, pos1=None, pos2=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_jobs_post, owner, workflow_id)
    else:
        return query_handler(job_query_get, owner, None, workflow_id, pos1, pos2)


### Job Put (will overwrite comment from before if it already exists) ###
# url input: <owner>/jobs/<job id>
# json input: value
### Job Get ###
# url input: <owner>/jobs/<job id>
# json output: value 
@app.route("/owners/<owner>/jobs/<job_id>/comment", methods=['PUT', 'GET'])
@verify_login
def workflow_job_comment(username, owner, job_id):
    if request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(workflow_job_comment_put, owner, job_id)
    else:
        return query_handler(workflow_job_comment_get, job_id)


### Job inputs GET ###
# url input: <owner>/jobs/<job id>
# json output: job-inputs = [ id1, id2, ... ]
@app.route("/owners/<owner>/jobs/<job_id>/job-inputs", methods=['GET'])
@verify_login
def job_job(username, owner, job_id, par_id=None):
    return query_handler(job_job_get, job_id)     


### session user POST ###
# create a new session
# json output: uid, secretkey
### session user DELETE ###
# delete user id supplied
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



