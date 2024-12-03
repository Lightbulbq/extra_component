from streamlit_gsheets import GSheetsConnection
import streamlit as st
import streamlit_authenticator as stauth
import visualization.visualization as vis
import logging
import os
import config

# Configure logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

# load all required config variables early on to inform the user of any missing variables

try:
    require_auth = st.secrets.auth["require_auth"]
    auth_cookie_name = st.secrets.auth["cookie_name"]
    auth_cookie_key = st.secrets.auth["cookie_key"]
    auth_cookie_expiry = st.secrets.auth["cookie_expiry"]
    auth_cache_ttl = st.secrets.connections.authdb["ttl"]
    authdb_url = st.secrets.connections.authdb["spreadsheet"]
except Exception as e:
    require_auth = False
    auth_cookie_name = "qsviz-cookie"
    auth_cookie_key = "qsviz-cookie-key"
    auth_cookie_expiry = 1
    auth_cache_ttl = 3600
    authdb_url = ""
    st.info(repr(e))


@st.cache_data(ttl=auth_cache_ttl)
def get_authorized_users():
    # retrieve data from google sheet containing authorized users
    authorized_users = {'usernames': {}}

    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=authdb_url, ttl=auth_cache_ttl)
    for row in df.itertuples():
        username = row.username
        authorized_users["usernames"][username] = {
            'email': row.email,
            'failed_login_attempts': 0,  # Will be managed automatically
            'first_name': row.first_name,
            'last_name': row.last_name,
            'logged_in': False,  # Will be managed automatically
            'password': row.password
        }

    # Pre-hashing all plain text passwords once
    stauth.Hasher.hash_passwords(authorized_users)

    return authorized_users

# checking if the directory exist if it doesnt it will automatically create a unique folder base of unique email


def create_user_directory(email=None):
    if email is None:
        user_dir = os.path.join(config.ROOT_DIR, "user","single_user", "admin")
    else:
        user_dir = os.path.join(config.ROOT_DIR, "user","multi_user", f"datafiles_{email}")
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    st.session_state['user_directory'] = user_dir

    return user_dir


def updated_dataset(user_dir):
    if "newly_added_files" not in st.session_state:
        st.session_state["newly_added_files"] = []
    newly_added_files = []
    for dirpath, direname, filenames in os.walk(user_dir):
        for filename in filenames:
            if filename.endswith('.json'):
                relative_path = os.path.relpath(dirpath, start=config.ROOT_DIR)
                if os.path.join(relative_path, filename) not in config.FILES_IN_GENERATED_SIGNALS_DIR:
                    config.FILES_IN_GENERATED_SIGNALS_DIR.append(
                        os.path.join(relative_path, filename))
                    newly_added_files.append(
                        os.path.join(relative_path, filename))
    st.session_state["newly_added_files"].extend(newly_added_files)
    return newly_added_files


def resetting_data_signal():
    if "newly_added_files" in st.session_state:
        for file in st.session_state["newly_added_files"]:
            if file in config.FILES_IN_GENERATED_SIGNALS_DIR:
                config.FILES_IN_GENERATED_SIGNALS_DIR.remove(file)

        # Clear the list in session state after processing
        st.session_state["newly_added_files"].clear()


if __name__ == "__main__":
    # if authentication is not required, load the visualization app immediately
    if not require_auth:
        user_dataset = create_user_directory(None)
        newly_added_files = updated_dataset(user_dataset)
        vis.load_visualization()
        resetting_data_signal()
        st.stop()

    authorized_users = get_authorized_users()

    try:
        authenticator = stauth.Authenticate(
            authorized_users,
            auth_cookie_name,
            auth_cookie_key,
            auth_cookie_expiry
        )

        authenticator.login(location='unrendered')

        if st.session_state['authentication_status'] is True:
            user_email = st.session_state['email']
            sanitized_email = user_email.replace("@", "_at_").replace(".", "_")
            user_dataset = create_user_directory(sanitized_email)
            newly_added_files = updated_dataset(user_dataset)
            st.write(f'Welcome {user_email}')
            vis.load_visualization()
            resetting_data_signal()
            authenticator.logout('Logout', 'sidebar')
        else:
            authenticator.login(location="main")

            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')

    except stauth.LoginError as e:
        st.error(e)
