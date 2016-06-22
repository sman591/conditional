#!/usr/bin/env python

import os
import getpass
import unittest.mock as mock
from conditional import app
from conditional.util import ldap
from conditional.db import database, migrate

# https://lists.openshift.redhat.com/openshift-archives/dev/2015-July/msg00043.html
with mock.patch.object(getpass, "getuser", return_value='default'):
    app.config.from_pyfile('../config.py')

    ldap.ldap_init(app.config['LDAP_RO'],
                   app.config['LDAP_URL'],
                   app.config['LDAP_BIND_DN'],
                   app.config['LDAP_BIND_PW'],
                   app.config['LDAP_USER_OU'],
                   app.config['LDAP_GROUP_OU'],
                   app.config['LDAP_COMMITTEE_OU'])

    database.init_db(app.config['DB_URL'])

    migrate_url = os.environ.get("MIGRATE_URL")
    if migrate_url:
        # Free the zoo! Run database migration.
        print("---> Migrating database...")
        migrate.free_the_zoo(migrate_url, app.config['DB_URL'])
        print("---> Migration complete!")

    if __name__ == '__main__':
        app.run(debug=app.config['DEBUG'], host=app.config['IP'], port=app.config['PORT'])
