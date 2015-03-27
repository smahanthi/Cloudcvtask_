__author__ = 'sunny.venki@gmail.com (Sandeep Manthi)'
from app import app

import json
import random
import string
from apiclient.discovery import build

from flask import Flask
from flask import make_response
from flask import render_template
from flask import request
from flask import session
from flask import send_from_directory

import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from simplekv.memory import DictStore
from flaskext.kvsession import KVSessionExtension
# --------------

import os
bsdir = os.path.abspath(os.path.dirname(__file__))

from otherfuncs import *
from app import app

APPLICATION_NAME = 'CloudCV_Task'

app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(32))

# See the simplekv documentation for details
store = DictStore()


# This will replace the app's session handling
KVSessionExtension(store, app)


# Update client_secrets.json with your Google API project information.
# Do not change this assignment.
clientsecretloc = str(bsdir)+'/'+'client_secrets.json'
CLIENT_ID = json.loads(
    open(clientsecretloc, 'r').read())['web']['client_id']
SERVICE = build('plus', 'v1')
imservice = build('customsearch' , 'v1', developerKey="AIzaSyAQjt2chYPf6Z7cWawlvLaq4H905QCwNP0")

myjobid=''

@app.route('/', methods=['GET'])
def index():
  """Initialize a session for the current user, and render index.html."""
  # Create a state token to prevent request forgery.
  # Store it in the session for later validation.
  state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                  for x in xrange(32))
  session['state'] = state
  # Set the Client ID, Token State, and Application Name in the HTML while
  # serving it.
  response = make_response(
      render_template('index.html',
                      CLIENT_ID=CLIENT_ID,
                      STATE=state,
                      APPLICATION_NAME=APPLICATION_NAME))
  response.headers['Content-Type'] = 'text/html'
  return response


@app.route('/connect', methods=['POST'])
def connect():
  global curruserid
  """Exchange the one-time authorization code for a token and
  store the token in the session."""
  # Ensure that the request is not a forgery and that the user sending
  # this connect request is the expected user.
  if request.args.get('state', '') != session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Normally, the state is a one-time token; however, in this example,
  # we want the user to be able to connect and disconnect
  # without reloading the page.  Thus, for demonstration, we don't
  # implement this best practice.
  # del session['state']

  code = request.data

  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets(clientsecretloc, scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
        json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # An ID Token is a cryptographically-signed JSON object encoded in base 64.
  # Normally, it is critical that you validate an ID Token before you use it,
  # but since you are communicating directly with Google over an
  # intermediary-free HTTPS channel and using your Client Secret to
  # authenticate yourself to Google, you can be confident that the token you
  # receive really comes from Google and is valid. If your server passes the
  # ID Token to other components of your app, it is extremely important that
  # the other components validate the token before using it.
  gplus_id = credentials.id_token['sub']
  #Store the id to the database
  curruserid = storetodb(gplus_id)
  stored_credentials = session.get('credentials')
  stored_gplus_id = session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Store the access token in the session for later use.
  session['credentials'] = credentials
  session['gplus_id'] = gplus_id
  response = make_response(json.dumps('Successfully connected user.', 200))
  response.headers['Content-Type'] = 'application/json'
  return response


@app.route('/disconnect', methods=['POST'])
def disconnect():
  """Revoke current user's token and reset their session."""

  # Only disconnect a connected user.
  credentials = session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Execute HTTP GET request to revoke current token.
  access_token = credentials.access_token
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]

  if result['status'] == '200':
    # Reset the user's session.
    del session['credentials']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
  else:
    # For whatever reason, the given token was invalid.
    response = make_response(
        json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    return response
    

@app.route('/fetchfromdropbox', methods=['POST'])
def fetchfromdropbox():
    global myjobid
    dburl = request.get_json()
    dburl = dburl['input']
    credentials = session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    try:
        imlist = dropboxfunc(dburl, myjobid)
        response = make_response(json.dumps(imlist), 200)
        return response
    except AccessTokenRefreshError:
        response = make_response(json.dumps('Failed to refresh access token.'), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    
@app.route('/testimages/<path:path>')
def sendtestimages(path):
    return send_from_directory(basedirec+"/testfolder/", path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory(basedirec+"/static/js/", path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory(basedirec+"/static/css/", path)

@app.route('/fonts/<path:path>')
def send_fonts(path):
    return send_from_directory(basedirec+"/static/fonts/", path)
    
@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory(basedirec+"/static/images/", path)

@app.route('/searchterm', methods=['POST'])
def searchterm():
  global myjobid
  myjobid = setjobid()
  sterm = request.get_json()
  sterm = sterm['input']
  credentials = session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  try:
#    # Create a new authorized API client.
#    http = httplib2.Http()
#    http = credentials.authorize(http)
#    # Get a list of people that this user has shared with this app.
#    # response = googleimsearch(sterm, 55)
#    imglist = getPic(sterm)
#    saveallPics(imglist, myjobid, sterm)
#    response = make_response(json.dumps(imglist),200)
#    response.headers['Content-Type'] = 'application/json'
    imglist = flickrsearch(sterm,  20)
    saveallPics(imglist, myjobid, sterm)
    response = make_response(json.dumps(imglist), 200)
    return response
  except AccessTokenRefreshError:
    response = make_response(json.dumps('Failed to refresh access token.'), 500)
    response.headers['Content-Type'] = 'application/json'
    return response
