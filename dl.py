from flask import Flask, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
import json, os, jwt, redis, hashlib


app = Flask(__name__)

app.config.from_pyfile('NoSecretThere.cfg')  # for SECRET_KEY
secret_jwt = open('NoSecretThere.cfg', 'rb').read().decode('utf-8')

red = redis.Redis()

@app.route('/zychp/dl/download/<path:filename>', methods=['POST'])
def download(filename):
    username = getUserAndCheckAuth()
    if (username):
        userpath = getUserDirPath(username)
        if (filename!="Brak pliku"):
            print("File downloaded")
            return send_from_directory(directory=userpath, filename=filename, as_attachment=True)
        else: 
            print("No file")
            return redirect("/zychp/webapp/fileslist")
    else:
        return redirect("/zychp/webapp/fileslist")
   

@app.route('/zychp/dl/upload', methods=['POST'])
def upload():
    username = getUserAndCheckAuth()
    if (username):
        crateUploadDirectoryIfNotExist(username)
        n_to_upload = 5-countUserFiles(username)
        userpath = getUserDirPath(username)
        n_uploaded = 0
        for filee in request.files:
            if(n_uploaded < n_to_upload):
                f = request.files[filee]
                f.save(userpath + secure_filename(f.filename))
                n_uploaded += 1
            else:
                print("File upload aborted")
        print("Files uploaded")
        return redirect("/zychp/webapp/fileslist")
    else:
        return redirect("/zychp/webapp/fileslist")


@app.route('/zychp/dl/getfilesnames', methods=['POST'])
def getFilesNames():
    username = getUserAndCheckAuth()
    if (username):
        crateUploadDirectoryIfNotExist(username)
        listed_files = listUserFiles(username)
        red.hset('zychp:webapp:userfiles'+ getHash(username), 'fileslist', json.dumps(listed_files))
        red.hset('zychp:webapp:userfiles'+ getHash(username), 'nfiles', countUserFiles(username))
        print("Fileslist read")
        return redirect("/zychp/webapp/fileslist")
    else:
        return redirect("/zychp/webapp/fileslist")



def listUserFiles(username):
    userpath = getUserDirPath(username)
    listed_files = os.listdir(userpath)
    for i in range(len(listed_files), 5):
        listed_files.append("Brak pliku")
    return listed_files

def countUserFiles(username):
    return len(os.listdir(getUserDirPath(username)))

def crateUploadDirectoryIfNotExist(username):
    userpath = getUserDirPath(username)
    if not os.path.exists(userpath):
        os.makedirs(userpath)
    return

def getHash(string):
    string += secret_jwt
    return hashlib.sha256(string.encode()).hexdigest() 

def getUserDirPath(username):
    return 'userfiles/' + secure_filename(getHash(username)) + '/'

def getUserAndCheckAuth():
    encoded = request.form['jwt']
    try:
        decoded = jwt.decode(encoded, secret_jwt, algorithms='HS256')
        return decoded['username']
    except jwt.ExpiredSignatureError:
        print("JWT expired")
    except jwt.exceptions.DecodeError:
        print("JWT wrong signature")
    return False