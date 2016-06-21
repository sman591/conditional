from flask import Blueprint, request, jsonify, redirect

from conditional.util.ldap import ldap_get_name
from conditional.util.ldap import ldap_is_eval_director
from conditional.util.flask import render_template

from datetime import datetime

from conditional.db.models import Conditional

conditionals_bp = Blueprint('conditionals_bp', __name__)


@conditionals_bp.route('/conditionals/')
def display_conditionals():
    # get user data
    user_name = request.headers.get('x-webauth-user')

    conditionals = [
        {
            'name': ldap_get_name(c.uid),
            'date_created': c.date_created,
            'date_due': c.date_due,
            'description': c.description,
            'id': c.id
        } for c in
        Conditional.query.filter(
            Conditional.status == "Pending")]
    # return names in 'first last (username)' format
    return render_template(request,
                           'conditional.html',
                           username=user_name,
                           conditionals=conditionals,
                           conditionals_len=len(conditionals))


@conditionals_bp.route('/conditionals/create', methods=['POST'])
def create_conditional():
    from conditional.db.database import db_session

    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    uid = post_data['uid']
    description = post_data['description']
    due_date = datetime.strptime(post_data['due_date'], "%Y-%m-%d")

    db_session.add(Conditional(uid, description, due_date))
    db_session.flush()
    db_session.commit()

    return 'ok', 200


@conditionals_bp.route('/conditionals/review', methods=['POST'])
def conditional_review():
    # get user data
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return redirect("/dashboard", code=302)

    post_data = request.get_json()
    cid = post_data['id']
    status = post_data['status']

    print(post_data)
    Conditional.query.filter(
        Conditional.id == cid). \
        update(
        {
            'status': status
        })

    from conditional.db.database import db_session
    db_session.flush()
    db_session.commit()
    return jsonify({"success": True}), 200
