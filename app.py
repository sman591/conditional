#!/usr/bin/env python

import os
import sys
from flask import Flask
from conditional import app
from conditional.util import ldap
from conditional.db import database, migrate

# Attempt to activate the virtualenv under OpenShift
try:
    virtualenv_path = os.path.join(os.environ.get('OPENSHIFT_PYTHON_DIR', '.'), 'virtenv')
    python_version = "python" + str(sys.version_info[0]) + "." + str(sys.version_info[1])
    os.environ['PYTHON_EGG_CACHE'] = os.path.join(virtualenv_path, 'lib', python_version, 'site-packages')
    virtualenv = os.path.join(virtualenv_path, 'bin', 'activate_this.py')
    exec(open(virtualenv).read(), dict(__file__=virtualenv))
except IOError:
    pass

#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

if __name__ == '__main__':
    app.config.from_pyfile('../config.py')
    port = app.config['PORT']
    ip = app.config['IP']
    app_name = app.config['APP_NAME']
    host_name = app.config['HOST_NAME']

    ldap.ldap_init(app.config['LDAP_RO'],
                   app.config['LDAP_URL'],
                   app.config['LDAP_BIND_DN'],
                   app.config['LDAP_BIND_PW'],
                   app.config['LDAP_USER_OU'],
                   app.config['LDAP_GROUP_OU'],
                   app.config['LDAP_COMMITTEE_OU'])

    database.init_db(app.config['DB_URL'])

    if len(sys.argv) > 1:
        if sys.argv[1] == "migrate":
            # Run database migration
            migrate_url = os.environ.get("MIGRATE_URL")
            if migrate_url:
                migrate.free_the_zoo(migrate_url, app.config['DB_URL'])
            else:
                print("You must set the MIGRATE_URL environment variable before attempting a migration.")
                print("Example: MIGRATE_URL='mysql:///user:pass@host/old_db' ./app.py migrate")
    else:
        # Start the server
        print('Starting WSGI server on {}:{}...'.format(ip, port))

        server = Flask(__name__)
        server.wsgi_app = app
        server.run(host=ip, port=port)
