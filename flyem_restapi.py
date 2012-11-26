from flyem_core import *


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

##############################################################################

# workflow checks: workflow queries, workflow_version, workflow job complete, comment, description
# return all workflow properties when returning job info (also workflow version, start time, description, comment )

@app.route("/owners/<owner>/jobs", methods=['GET'])
@app.route("/owners/<owner>/jobs/<int:pos1>-<int:pos2>", methods=['GET'])
@app.route("/owners/<owner>/jobs/<int:job_id>", methods=['GET'])
@verify_login
def jobs_basic(username, owner, pos1=None, pos2=None, job_id=None):
    return query_handler(job_query_get, owner, None, None, pos1, pos2, job_id)

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


@app.route("/owners/<owner>/jobs/notcompleted", methods=['GET'])
@app.route("/owners/<owner>/jobs/notcompleted/<int:pos1>-<int:pos2>", methods=['GET'])
@verify_login
def jobs_notcompleted(username, owner, pos1=None, pos2=None):
    return query_handler(job_query_get, owner, False, None, pos1, pos2)


# job number will be name of workflow with the number of jobs for that workflow
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


@app.route("/owners/<owner>/jobs/<job_id>/comment", methods=['PUT', 'GET'])
@verify_login
def workflow_job_comment(username, owner, job_id):
    if request.method == 'PUT':
        if owner != username:
            abort(401)
        return query_handler(workflow_job_comment_put, owner, job_id)
    else:
        return query_handler(workflow_job_comment_get, job_id)


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



