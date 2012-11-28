from flyem_core import *

### json outputs for HTTP requests will return a message in 'error' if an error occurs
### must specify username/password or uid/uidpassword created by a session


### Media POST ###
# url input: /<media type> (groundtruth_substack, substack, tbar_detect_ilp, boundary_ilp
# json input: name, description, file-path
# json ouptut: media-id
### Media GET ###
# url input: media type=none, id=none
# url query string: name, description, file-path, media-type 
# json_output: results = {name/id, date, media_type_name, description, file-path, num-matches}
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


### Workflow POST ###
# url input: /<owner>/workflows/<workflow type> (tbar, gala-train, gala-segmentation-pipeline)
# json input: name, description, workflow-interface-version
# json output: workflow-id 
### Workflow GET ###
# url input: /<owner/workflows/<workflow_type=None>/<workflow_id=None>/<position1 - position2>
# url query string: name, workflow-type, description, interface-version
# json output: results = {name, id, date, description, workflow-type, owner, interface-version, num-matches} 
@app.route("/owners/<owner>/workflows", methods=['GET'])
@app.route("/owners/<owner>/workflows/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>/<int:workflow_id>", methods=['GET'])
@app.route("/owners/<owner>/workflows/<workflow_type>/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def workflow_type(username, owner, workflow_type=None, workflow_id=None, pos1=None, pos2=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_post, owner, workflow_type)
    else:
        return query_handler(workflow_get, owner, workflow_type, workflow_id, pos1, pos2)


### Workflow parameter POST ###
# url input: /<owner>/workflows/<workflow_id>
# json input: parameters = [ { "name" : <name>, "value" : <value> }, ... ]
### Workflow parameter PUT ###
# url input: /<owner>/workflows/<workflow_id>/<parameter name>
# json input: value 
### Workflow parameter GET ###
# url input: /<owner>/workflows/<workflow id>/parameters/<parameter = None>
# json output: results = [ {name, value}, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/parameters/<parameter>", methods=['PUT', 'GET'])
@verify_login
def workflow_params(username, owner, workflow_id, parameter=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_param_post, workflow_id)
    elif request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(workflow_param_put, workflow_id, parameter)
    else:
        return query_handler(workflow_param_get, workflow_id, parameter)     


### Workflow media inputs POST ###
# url input: <owner>/workflows/<workflow_id>
# json input: media-inputs [ id1, id2, ... ]
### Workflow media inputs PUT ###
# url input: <owner>/workflows/<workflow id>/media-inputs/<media id>
### Workflow media inputs GET ###
# url input: /<owner>/workflows/<workflow id>
# json output: media-inputs = [ id1, id2, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/media-inputs/<int:mid>", methods=['PUT'])
@verify_login
def workflow_media(username, owner, workflow_id, mid=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_media_post, workflow_id)
    elif request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(workflow_media_put, workflow_id, mid)
    else:
        return query_handler(workflow_media_get, workflow_id)     


### Workflow workflow inputs POST ###
# url input: <owner>/workflows/<workflow_id>
# json input: workflow-inputs [ id1, id2, ... ]
### Workflow workflow inputs PUT ###
# url input: <owner>/workflows/<workflow id>/workflow-inputs/<workflow id>
### Workflow workflow inputs GET ###
# url input: /<owner>/workflows/<workflow id>
# json output: workflow-inputs = [ id1, id2, ... ]
@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs", methods=['POST', 'GET'])
@app.route("/owners/<owner>/workflows/<int:workflow_id>/workflow-inputs/<int:wid>", methods=['PUT'])
@verify_login
def workflow_workflow(username, owner, workflow_id, wid=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_workflow_post, workflow_id)
    elif request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(workflow_workflow_put, workflow_id, wid)
    else:
        return query_handler(workflow_workflow_get, workflow_id)     


### Job GET ###
# url input: <owner>
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date, num-matches ]
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
# json output: results = [ workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date, num-matches ]
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
# json output: results = [ workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date, num-matches ]
@app.route("/owners/<owner>/jobs/notcompleted", methods=['GET'])
@app.route("/owners/<owner>/jobs/notcompleted/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def jobs_notcompleted(username, owner, pos1=None, pos2=None):
    return query_handler(job_query_get, owner, False, None, pos1, pos2)


# job number will be name of workflow with the number of jobs for that workflow
### Job POST ###
# url input: <owner>/workflows/<workflow id>
# json input: workflow-version, description
# json output: job-name, job-id, job-start-time, is-complete 
### Job GET ###
# url input: <owner>/workflows/<workflow id>
# url query string: name, workflow-version, description, workflow-name, comment, is-complete 
# json output: results = [ workflow-name, workflow-id, name, id, submit-date, owner, description, workflow-version,
# comment, complete-date, num-matches ]
@app.route("/owners/<owner>/workflows/<workflow_id>/jobs", methods=['POST', 'GET']) # show comments
@app.route("/owners/<owner>/workflows/<workflow_id>/jobs/<int:pos1>-<int:pos2>", methods=['GET']) # show comments
@verify_login
def workflow_jobs(username, owner, workflow_id, pos1=None, pos2=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(workflow_jobs_post, owner, workflow_id)
    else:
        return query_handler(job_query_get, None, workflow_id, pos1, pos2)


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


### Job inputs POST ###
# url input: <owner>/jobs/<job id>
# json input: job-inputs [ id1, id2, ... ]
### Job inputs PUT ###
# url input: <owner>/jobs/<job id>/job-inputs/<job input id>
### Job inputs GET ###
# url input: <owner>/jobs/<job id>
# json output: job-inputs = [ id1, id2, ... ]
@app.route("/owners/<owner>/jobs/<job_id>/job-inputs", methods=['POST', 'GET'])
@app.route("/owners/<owner>/jobs/<job_id>/job-inputs/<par_id>", methods=['PUT'])
@verify_login
def job_job(username, owner, job_id, par_id=None):
    if request.method == 'POST':
        if owner != username:
            abort(401)
        return query_handler(job_job_post, job_id)
    elif request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(job_job_put, job_id, par_id)
    else:
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



