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

authorization_stored = {}


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
                if username != "steve" or password != "blah":
                    abort(401)
        except: 
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


@app.route("/media/{type}", methods=['POST'])
@verify_login
def add_media(username, mtype):
    




@app.route("/sessionusers", methods=['POST', 'DELETE'])
@app.route("/sessionusers/<userid>", methods=['POST', 'DELETE'])
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
    elif userid is None:
        uid = str(binascii.b2a_hex(os.urandom(8)))
        secretkey = str(binascii.b2a_hex(os.urandom(8)))
        authorization_stored[uid] = (username, secretkey)
        json_data = {}
        json_data['uid'] = uid
        json_data['secretkey'] = secretkey

        return json.dumps(json_data)
    else:
        if userid not in authorization_stored:
            abort(404)
        else:
            name, pw = authorization_stored[userid]
            if name == username:
                json_data = {}
                json_data['uid'] = userid
                json_data['secretkey'] = pw
                return json.dumps(json_data) 
            else:
                abort(401)

if __name__ == "__main__":
    try:
        app.run()
    except Exception, e:
        print e



