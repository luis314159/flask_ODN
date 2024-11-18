# app/utils.py
from ldap3 import Server, Connection, ALL
from flask import current_app as app

def allowed_file(filename):
    """Check if a file is allowed based on its extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_user_email(username):
    """Retrieve the email of a user from the LDAP server."""
    try:
        server = Server('ldap://your_ldap_server', get_info=ALL)
        conn = Connection(server, user='bind_user', password='bind_password', auto_bind=True)
        conn.search('dc=your_domain,dc=com', f'(sAMAccountName={username})', attributes=['mail'])
        if conn.entries:
            return conn.entries[0]['mail'].value
    except Exception as e:
        app.logger.error(f"Error retrieving email: {e}")
    return None