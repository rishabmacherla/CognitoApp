import datetime
import os
import streamlit as st
from dotenv import load_dotenv
import requests
import base64
import json
import uuid

import threading
import boto3
# ------------------------------------
# Read constants from environment file
# ------------------------------------

# def get_reqs():
load_dotenv()
#     c = []
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
APP_URI = os.environ.get("APP_URI")
info = {}
auth_codes = {}
authentication_codes_list = []
user_all_details = {}

# logged_in_user = {}
# time = datetime.datetime.now()
# formatted_login_time = datetime.strptime(time)
print("initial info is", info)
print("initial auth_codes", auth_codes)
    # return COGNITO_DOMAIN,CLIENT_ID,CLIENT_SECRET,APP_URI
# ------------------------------------
# Initialise Streamlit state variables
# ------------------------------------

def initialise_st_state_vars():
    """
    Initialise Streamlit state variables.
    Returns:
        Nothing.
    """

    if "auth_code" not in st.session_state:
        st.session_state["auth_code"] = ""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_cognito_groups" not in st.session_state:
        st.session_state["user_cognito_groups"] = []
    print(st.session_state)
# ----------------------------------
# Get authorization code after login
# ----------------------------------
def get_auth_code(cur_sys_id):
    """
    Gets auth_code state variable.
    Returns:
        Nothing.
    """

    auth_query_params = st.query_params
    # st.write(auth_query_params)
    try:
        auth_code = dict(auth_query_params)["code"]
        if auth_code != '':
            auth_codes[cur_sys_id] = auth_code
        print("Heellloooooooooooooooo", auth_codes)
        #

    except (KeyError, TypeError):
        auth_code = ""
    print("auth code is ",auth_code)
    return auth_codes
# ----------------------------------
# Set authorization code after login
# ----------------------------------
def set_auth_code():
    """
    Sets auth_code state variable.
    Returns:
        Nothing.
    """
    initialise_st_state_vars()
    auth_code = get_auth_code()
    st.session_state["auth_code"] = auth_code
# -------------------------------------------------------
# Use authorization code to get user access and id tokens
# -------------------------------------------------------
def get_user_tokens(auth_code):
    """
    Gets user tokens by making a post request call.
    Args:
        auth_code: Authorization code from cognito server.
    Returns:
        {
        'access_token': access token from cognito server if user is successfully authenticated.
        'id_token': access token from cognito server if user is successfully authenticated.
        }
    """
    # resp = get_reqs()
    # Variables to make a post request
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    print("token url", token_url)
    client_secret_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    print("clinet secret string", client_secret_string)
    client_secret_encoded = str(
        base64.b64encode(client_secret_string.encode("utf-8")), "utf-8"
    )
    print("client secret encoded", client_secret_encoded)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {client_secret_encoded}",
    }
    body = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "redirect_uri": APP_URI,
    }
    token_response = requests.post(token_url, headers=headers, data=body)
    print('token response',token_response.json())
    try:
        access_token = token_response.json()["access_token"]
        id_token = token_response.json()["id_token"]
    except (KeyError, TypeError):
        access_token = ""
        id_token = ""
    print("access token is ", access_token)
    print("id token is ", id_token)
    return access_token, id_token
# ---------------------------------------------
# Use access token to retrieve user information
# ---------------------------------------------
def get_user_info(access_token):
    """
    Gets user info from aws cognito server.
    Args:
        access_token: string access token from the aws cognito user pool
        retrieved using the access code.
    Returns:
        userinfo_response: json object.
    """
    userinfo_url = f"{COGNITO_DOMAIN}/oauth2/userInfo"

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {access_token}",
    }
    userinfo_response = requests.get(userinfo_url, headers=headers)
    print(userinfo_response.json())
    return userinfo_response.json()
# -------------------------------------------------------
# Decode access token to JWT to get user's cognito groups
# -------------------------------------------------------
# Ref - https://gist.github.com/GuillaumeDerval/b300af6d4f906f38a051351afab3b95c
def pad_base64(data):
    """
    Makes sure base64 data is padded.
    Args:
        data: base64 token string.
    Returns:
        data: padded token string.
    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += "=" * (4 - missing_padding)
    return data
def get_user_cognito_groups(id_token):
    """
    Decode id token to get user cognito groups.
    Args:
        id_token: id token of a successfully authenticated user.
    Returns:
        user_cognito_groups: a list of all the cognito groups the user belongs to.
    """

    if id_token != "":
        header, payload, signature = id_token.split(".")
        printable_payload = base64.urlsafe_b64decode(pad_base64(payload))
        payload_dict = json.loads(printable_payload)
        user_cognito_groups = list(dict(payload_dict)["cognito:groups"])
        user_name = dict(payload_dict)["cognito:username"]
        email = dict(payload_dict)["email"]
        # middle_name = dict(payload_dict)["middle_name"]
        cognito_user_id = dict(payload_dict)["sub"]
        user_attr = {
            'Cognito User Id': cognito_user_id,
            'Username': user_name,
            'Email' : email,
            'id_token': id_token
            # 'Middle Name' : middle_name
         }
        print(user_attr)
    else:
        user_cognito_groups = []
        user_attr = {}
    print("user group", user_cognito_groups)
    return user_cognito_groups, user_attr

# -----------------------------
# get token, groups info
# -----------------------------


def get_token_group_info(cur_sys_id):
    # current_time = datetime.datetime.now()
    # time_diff = current_time - time
    logged_in_user_det = {}
    authen_code = get_auth_code(cur_sys_id) # gets the auuth_code
    if authen_code:
        print("auttthhhheennnnnnn", list(auth_codes.values()))
        print("autthnnnn codeeee", authen_code[cur_sys_id])
        info['auth_code'] = authen_code[cur_sys_id]
        if info['auth_code'] not in authentication_codes_list and info['auth_code'] != '': # checks if the auth_code is already available,
            # which means if user is already logged in but trying to refresh or moving between pages
            # If not it means new user is logging in, so add that user and gets his info.
            print("heeerrrreeeeeee")
            authentication_codes_list.append((info['auth_code']))

            info['access_token'], info['id_token'] = get_user_tokens(info['auth_code'])
            info['user_cognito_groups'], user_attributes = get_user_cognito_groups(info['id_token'])
            # st.write("the user sttributes are", user_attributes)

            if len(user_attributes) > 0:
                logged_in_user_det['user_name'] = user_attributes['Username']
                logged_in_user_det['email'] = user_attributes['Email']
                logged_in_user_det['auth_code'] = info['auth_code']
                logged_in_user_det['access_token'] = info['access_token']
                logged_in_user_det['id_token'] = info['id_token']
                logged_in_user_det['user_groups'] = info['user_cognito_groups']
                logged_in_user_det['user_system_id'] = uuid.UUID(int=uuid.getnode())
                user_all_details[user_attributes['Cognito User Id']] = logged_in_user_det



        # print("auth codes are",auth_codes)
        # if the auth_code is available but expired, then, access token and other info will be null.
        # So, this condition checks, if auth_code is available but expired and other token and info is
        # null then asks to re-login
        if info['auth_code'] != '' and (info['access_token'] == '' or info['id_token'] == '' or
                                        info['user_cognito_groups'] == ''):
            # if we want to logout user after sometime (even they are using) then add this below code as
            # another or after and in above if
            # or (time_diff.total_seconds() >= time_we_want_in_secs
            button_login()
            st.error("Please login")
            st.stop()
            # This above code asks the user to re-login and then show the error message and
            # then stops the further execution of code.


    # print("info is ", info)
    print("user detailos are", user_all_details)
    return user_all_details, info
# -----------------------------
# Set Streamlit state variables
# -----------------------------
def set_st_state_vars(access_token, auth_code, user_cognito_groups):
    """
    Sets the streamlit state variables after user authentication.
    Returns:
        Nothing.
    """
    sim_sess_vars = {}
    if access_token != "":
        # if 'authenticated' not in st.session_state:
        sim_sess_vars["authenticated"] = True

        sim_sess_vars["auth_code"] = auth_code

        sim_sess_vars["user_cognito_groups"] = user_cognito_groups

        # sim_sess_vars["user_name"] = user_name

    print("sim_sess_vars", sim_sess_vars)
    print("==========")
    return sim_sess_vars


# -----------------------------
# Login/ Logout HTML components
# -----------------------------
login_link = f"{COGNITO_DOMAIN}/login?client_id={CLIENT_ID}&response_type=code&scope=email+openid&redirect_uri={APP_URI}"
logout_link = f"{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={'https://ganesh-pool-2.auth.us-east-2.amazoncognito.com/login?client_id=2s3v6i6v223nul1n0938447fsm&response_type=code&scope=email+openid+phone&redirect_uri=http%3A%2F%2Flocalhost%3A8501%2F'}"
html_css_login = """
<style>
.button-login {
  background-color: skyblue;
  color: white !important;
  padding: 1em 1.5em;
  text-decoration: none;
  text-transform: uppercase;
}
.button-login:hover {
  background-color: #555;
  text-decoration: none;
}
.button-login:active {
  background-color: black;
}
</style>
"""
html_button_login = (
    html_css_login
    + f"<a href='{login_link}' class='button-login' target='_self'>Log In</a>"
)
html_button_logout = (
    html_css_login
    + f"<a href='{logout_link}' class='button-login' target='_self'>Log Out</a>"
)
def button_login():
    """
    Returns:
        Html of the login button.
    """
    return st.sidebar.markdown(f"{html_button_login}", unsafe_allow_html=True)
def button_logout():
    """
    Returns:
        Html of the logout button.
    """
    return st.sidebar.markdown(f"{html_button_logout}", unsafe_allow_html=True)