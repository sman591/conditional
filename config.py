import os

# Flask config
DEBUG = True if os.environ.get('DEBUG', 'false') == "true" else False
HOST_NAME = os.environ.get('OPENSHIFT_APP_DNS', 'localhost')
APP_NAME = os.environ.get('OPENSHIFT_APP_NAME', 'conditional')
IP = os.environ.get('OPENSHIFT_PYTHON_IP', '0.0.0.0')
PORT = int(os.environ.get('OPENSHIFT_PYTHON_PORT', 8080))

# LDAP config
LDAP_RO = True if os.environ.get('LDAP_RO', 'false') == "true" else False
LDAP_URL = os.environ.get('LDAP_URL', 'ldaps://ldap.csh.rit.edu:636/')
LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', 'uid=conditional,ou=Apps,dc=csh,dc=rit,dc=edu')
LDAP_BIND_PW = os.environ.get('LDAP_BIND_PW', '')
LDAP_USER_OU = os.environ.get('LDAP_USER_OU', 'ou=Users,dc=csh,dc=rit,dc=edu')
LDAP_GROUP_OU = os.environ.get('LDAP_GROUP_OU', 'ou=Groups,dc=csh,dc=rit,dc=edu')
LDAP_COMMITTEE_OU = os.environ.get('LDAP_COMMITTEE_OU', 'ou=Committees,dc=csh,dc=rit,dc=edu')

# Database config
DB_URL = os.environ.get('DB_URL', 'sqlite:///conditional.db')
