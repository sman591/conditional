from flask import Blueprint, request, jsonify

from datetime import datetime

from conditional.db.models import FreshmanAccount, FreshmanEvalData, FreshmanCommitteeAttendance, \
    MemberCommitteeAttendance, FreshmanSeminarAttendance, MemberSeminarAttendance, FreshmanHouseMeetingAttendance, \
    MemberHouseMeetingAttendance, HouseMeeting, EvalSettings, OnFloorStatusAssigned, SpringEval, attendance_enum

from conditional.util.ldap import ldap_is_eval_director, ldap_is_financial_director, ldap_set_roomnumber, \
    ldap_set_active, ldap_set_housingpoints, ldap_get_room_number, ldap_get_housing_points, ldap_is_active, \
    ldap_is_onfloor

from conditional.util.flask import render_template

member_management_bp = Blueprint('member_management_bp', __name__)


@member_management_bp.route('/manage')
def display_member_management():
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and not ldap_is_financial_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    settings = EvalSettings.query.first()
    return render_template(request, "member_management.html",
                           username=user_name,
                           housing_form_active=settings.housing_form_active,
                           intro_form_active=settings.intro_form_active,
                           site_lockdown=settings.site_lockdown)


@member_management_bp.route('/manage/settings', methods=['POST'])
def member_management_eval():
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    if 'housing' in post_data:
        EvalSettings.query.update(
            {
                'housing_form_active': post_data['housing']
            })

    if 'intro' in post_data:
        EvalSettings.query.update(
            {
                'intro_form_active': post_data['intro']
            })

    if 'site_lockdown' in post_data:
        EvalSettings.query.update(
            {
                'site_lockdown': post_data['site_lockdown']
            })

    from conditional.db.database import db_session
    db_session.flush()
    db_session.commit()
    return jsonify({"success": True}), 200


@member_management_bp.route('/manage/adduser', methods=['POST'])
def member_management_adduser():
    from conditional.db.database import db_session

    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    name = post_data['name']
    onfloor_status = post_data['onfloor']

    db_session.add(FreshmanAccount(name, onfloor_status))
    db_session.flush()
    db_session.commit()
    return jsonify({"success": True}), 200


@member_management_bp.route('/manage/edituser', methods=['POST'])
def member_management_edituser():
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and not ldap_is_financial_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    uid = post_data['uid']
    active_member = post_data['active_member']

    if ldap_is_eval_director(user_name):
        room_number = post_data['room_number']
        housing_points = post_data['housing_points']

        ldap_set_roomnumber(uid, room_number)
        # TODO FIXME ADD USER TO ONFLOOR GROUP
        ldap_set_housingpoints(uid, housing_points)

    # Only update if there's a diff
    if ldap_is_active(uid) != active_member:
        ldap_set_active(uid, active_member)

        from conditional.db.database import db_session
        if active_member:
            db_session.add(SpringEval(uid))
        else:
            SpringEval.query.filter(
                SpringEval.uid == uid and
                SpringEval.active).update(
                {
                    'active': False
                })
        db_session.flush()
        db_session.commit()

    return jsonify({"success": True}), 200


@member_management_bp.route('/manage/getuserinfo', methods=['POST'])
def member_management_getuserinfo():
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and not ldap_is_financial_director(user_name) and user_name != 'loothelion':
        return "must be eval or financial director", 403

    post_data = request.get_json()

    uid = post_data['uid']

    if ldap_is_eval_director(user_name):

        # missed hm
        def get_hm_date(hm_id):
            return HouseMeeting.query.filter(
                HouseMeeting.id == hm_id). \
                first().date.strftime("%Y-%m-%d")

        missed_hm = [
            {
                'date': get_hm_date(hma.meeting_id),
                'id': hma.meeting_id,
                'excuse': hma.excuse,
                'status': hma.attendance_status
            } for hma in MemberHouseMeetingAttendance.query.filter(
                MemberHouseMeetingAttendance.uid == uid and
                (MemberHouseMeetingAttendance.attendance_status != attendance_enum.Attenaded))]

        hms_missed = []
        for hm in missed_hm:
            if hm['status'] != "Attended":
                hms_missed.append(hm)
        return jsonify(
            {
                'room_number': ldap_get_room_number(uid),
                'onfloor_status': ldap_is_onfloor(uid),
                'housing_points': ldap_get_housing_points(uid),
                'active_member': ldap_is_active(uid),
                'missed_hm': hms_missed,
                'user': 'eval'
            })
    else:
        return jsonify(
            {
                'active_member': ldap_is_active(uid),
                'user': 'financial'
            })


@member_management_bp.route('/manage/edit_hm_excuse', methods=['POST'])
def member_management_edit_hm_excuse():
    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    hm_id = post_data['id']
    hm_status = post_data['status']
    hm_excuse = post_data['excuse']

    MemberHouseMeetingAttendance.query.filter(
        MemberHouseMeetingAttendance.id == hm_id).update(
        {
            'excuse': hm_excuse,
            'attendance_status': hm_status
        })

    from conditional.db.database import db_session
    db_session.flush()
    db_session.commit()
    return jsonify({"success": True}), 200


# TODO FIXME XXX Maybe change this to an endpoint where it can be called by our
# user creation script. There's no reason that the evals director should ever
# manually need to do this
@member_management_bp.route('/manage/upgrade_user', methods=['POST'])
def member_management_upgrade_user():
    from conditional.db.database import db_session

    user_name = request.headers.get('x-webauth-user')

    if not ldap_is_eval_director(user_name) and user_name != 'loothelion':
        return "must be eval director", 403

    post_data = request.get_json()

    fid = post_data['fid']
    uid = post_data['uid']
    signatures_missed = post_data['sigsMissed']

    db_session.add(FreshmanEvalData(uid, signatures_missed))

    for fca in FreshmanCommitteeAttendance.query.filter(
                    FreshmanCommitteeAttendance.fid == fid):
        db_session.add(MemberCommitteeAttendance(uid, fca.meeting_id))
        # TODO FIXME Do we need to also remove FID stuff?

    for fts in FreshmanSeminarAttendance.query.filter(
                    FreshmanSeminarAttendance.fid == fid):
        db_session.add(MemberSeminarAttendance(uid, fts.seminar_id))

    for fhm in FreshmanHouseMeetingAttendance.query.filter(
                    FreshmanHouseMeetingAttendance.fid == fid):
        db_session.add(MemberHouseMeetingAttendance(
            uid, fhm.meeting_id, fhm.excuse, fhm.status))

    db_session.add(OnFloorStatusAssigned(uid, datetime.now()))
    db_session.flush()
    db_session.commit()
    return jsonify({"success": True}), 200
