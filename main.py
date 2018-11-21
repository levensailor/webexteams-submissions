import urllib.request
import requests
import shutil
import json
import datetime
import os
import time
import sys
import dropbox
from webexteamssdk import WebexTeamsAPI, ApiError
from tqdm import tqdm

'''
Some global variables
cwd: current working directory to prepend for absolute paths
state: used to compare message timestamp against last ran timetamp
run_every: 60s by default, can be increased to fine tune performance
'''

cwd  = os.path.abspath(os.path.dirname('.'))
state = cwd+'/state.txt'
run_every = 60

'''
Set your webex api token and roomId if send_link_to_space = True
'''
token = 'webex token goes here'
api = WebexTeamsAPI(access_token=token)
headers = {'Authorization': 'Bearer '+token}

send_link_to_space = False #Specify submissions space by roomId below
roomId = 'webex roomid goes here'

'''
Setup your Dropbox account with api key and directory for submissions
'''
dbx_token = 'dropbox token goes here'
dbx = dropbox.Dropbox(dbx_token)
dbx_dir = 'team' #Specify the subdirectory on Dropbox to store files

'''
Some utility functions
'''

def round(float_num):
    return eval("'{:." + str(int(0)) + "f}'.format(" + str(float_num) + ")")

def update_last_runtime():
    global state
    f = open(state, 'w+')
    f.write(round(datetime.datetime.now(datetime.timezone.utc).timestamp()))
    f.close()

def find_last_runtime():
    global state
    try:
        f = open(state, 'r')
        return f.read()
    except:
        f = open(state, 'w+')
        f.write('0')
        return f.read()

def is_new_message(created):
    global last_ran
    if created > last_ran:
        return True
    else:
        return False #change to false for prod

def find_roomId():
    spaces = api.rooms.list()
    for space in spaces:
        print(space)

def find_direct():
    spaces = []
    response = requests.request("GET", "https://api.ciscospark.com/v1/rooms?type=direct", headers=headers)
    data = json.loads(response.text)['items']
    for directs in data:
        try:
            spaces.append(directs)
        except KeyError:
            pass
    return spaces

def find_group():
    spaces = []
    response = requests.request("GET", "https://api.ciscospark.com/v1/rooms?type=group", headers=headers)
    data = json.loads(response.text)['items']
    for directs in data:
        try:
            spaces.append(directs)
        except KeyError:
            pass
    return spaces

def upload_to_dropbox(filename):
    print('Initiating Upload of: '+filename)
    global cwd
    global dbx_dir
    CHUNK_SIZE = 4 * 1024 * 1024
    file = '/'+cwd+'/'+filename
    target = '/'+dbx_dir+'/'+filename
    f = open(file, 'rb')
    file_size = os.path.getsize(file)
    if file_size <= CHUNK_SIZE:
        dbx.files_upload(f.read(), target)
    else:
        upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                offset=f.tell())
        commit = dropbox.files.CommitInfo(path=target)
        while f.tell() < file_size:
            pbar = tqdm(bar_format='{l_bar}{bar}', 
                        desc=">Uploading To Dropbox", 
                        total=file_size, 
                        unit='', 
                        unit_scale=1, 
                        unit_divisor=CHUNK_SIZE)
            for i in range(0, (file_size-CHUNK_SIZE), CHUNK_SIZE):
                if ((file_size - f.tell()) <= CHUNK_SIZE):
                    pbar.update(CHUNK_SIZE)
                    dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                    pbar.close()
                else:
                    pbar.update(CHUNK_SIZE)
                    dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = f.tell()

def create_dropbox_link(file):
    print('Creating Dropbox Link')
    global dbx_dir
    try:
        res = dbx.sharing_create_shared_link('/'+dbx_dir+'/'+file)
        return res.url
    except:
        pass

def send_link_to_webex(roomid, title, url):
    print('Sending Link to Webex Teams Space')
    link = '[Click Here To View]('+url+')'
    msg = '> New Submission from: '+title+', '+link
    api.messages.create(roomId=roomId, markdown=msg)

def save(file, title):
    print("\nNew submission from: "+title)
    global cwd
    req = urllib.request.Request(file, headers=headers)
    with urllib.request.urlopen(req) as response, open(title.replace(" ", "")+'-'+response.info()['Content-Disposition'][21:].replace('"', "").replace(" ", ""), 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
        filename = title+'-'+response.info()['Content-Disposition'][21:].replace('"', "")
        res = filename.replace(" ", "")
        return res

def main():
    spaces = find_direct()
    for space in spaces:
        messages = api.messages.list(space['id'])
        for message in messages:
            if message.files is not None:
                if is_new_message(round(message.created.timestamp())):
                    try:
                        each = api.messages.get(message.id)
                        for data in each.files:
                            file = save(data, space['title'])
                            upload_to_dropbox(file)
                            if send_link_to_space:
                                url = create_dropbox_link(file)
                                send_link_to_webex(roomId, space['title'], url)
                    except ApiError as e:
                        pass

while True:
    for index, char in enumerate("." * run_every):
        sys.stdout.write(char)
        last_ran = find_last_runtime()
        main()
        update_last_runtime()
        sys.stdout.flush()
        time.sleep(run_every)
    index+=1
    sys.stdout.write("\b" * index + " " * index + "\b" * index)
    sys.stdout.flush()