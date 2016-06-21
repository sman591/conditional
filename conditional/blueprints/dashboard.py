from flask import Blueprint, request

from conditional.util.ldap import ldap_get_room_number, ldap_is_active, ldap_is_onfloor, ldap_get_housing_points, \
    ldap_is_intromember, ldap_get_name

from conditional.db.models import FreshmanEvalData, MemberCommitteeAttendance, MemberSeminarAttendance, \
    TechnicalSeminar, MemberHouseMeetingAttendance, MajorProject, Conditional, HouseMeeting, CommitteeMeeting

from conditional.util.housing import get_queue_length, get_queue_position
from conditional.util.flask import render_template

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/dashboard/')
def display_dashboard():
    # get user data

    user_name = request.headers.get('x-webauth-user')

    data = {
        'username': user_name,
        'name': ldap_get_name(user_name),
        'active': ldap_is_active(user_name),
        'onfloor': ldap_is_onfloor(user_name),
        'voting': True
    }

    # Member Status
    # On-Floor Status
    # Voting Status

    # freshman shit
    if ldap_is_intromember(user_name) or user_name == 'loothelion':
        freshman = {}
        freshman_data = FreshmanEvalData.query.filter(FreshmanEvalData.uid == user_name).first()

        freshman['status'] = freshman_data.freshman_eval_result
        # number of committee meetings attended
        c_meetings = [m.meeting_id for m in
                      MemberCommitteeAttendance.query.filter(
                          MemberCommitteeAttendance.uid == user_name
                      )]
        freshman['committee_meetings'] = len(c_meetings)
        # technical seminar total
        t_seminars = [s.seminar_id for s in
                      MemberSeminarAttendance.query.filter(
                          MemberSeminarAttendance.uid == user_name
                      )]
        freshman['ts_total'] = len(t_seminars)
        attendance = [m.name for m in TechnicalSeminar.query.filter(
            TechnicalSeminar.id.in_(t_seminars)
        )]

        freshman['ts_list'] = attendance

        h_meetings = [(m.meeting_id, m.attendance_status) for m in
                      MemberHouseMeetingAttendance.query.filter(
                          MemberHouseMeetingAttendance.uid == user_name
                      )]
        freshman['hm_missed'] = len([h for h in h_meetings if h[1] == "Absent"])
        freshman['social_events'] = freshman_data.social_events
        freshman['general_comments'] = freshman_data.other_notes
        freshman['fresh_proj'] = freshman_data.freshman_project
        freshman['sig_missed'] = freshman_data.signatures_missed
        freshman['eval_date'] = freshman_data.eval_date

        data['freshman'] = freshman
    else:
        data['freshman'] = False

    spring = {}
    c_meetings = [m.meeting_id for m in
                  MemberCommitteeAttendance.query.filter(
                      MemberCommitteeAttendance.uid == user_name
                  )]
    spring['committee_meetings'] = len(c_meetings)
    h_meetings = [(m.meeting_id, m.attendance_status) for m in
                  MemberHouseMeetingAttendance.query.filter(
                      MemberHouseMeetingAttendance.uid == user_name
                  )]
    spring['hm_missed'] = len([h for h in h_meetings if h[1] == "Absent"])

    data['spring'] = spring

    housing = False

    # only show housing if member has onfloor status
    if ldap_is_onfloor(user_name):
        housing = {
            'points': ldap_get_housing_points(user_name),
            'room': ldap_get_room_number(user_name),
            'queue_len': get_queue_length()
        }

        if housing['room'] == "N/A":
            housing['queue_pos'] = get_queue_position(user_name)
        else:
            housing['queue_pos'] = "On Floor"

    data['housing'] = housing

    data['major_projects'] = [
        {
            'name': p.name,
            'status': p.status,
            'description': p.description
        } for p in
        MajorProject.query.filter(MajorProject.uid == user_name)]

    data['major_projects_count'] = len(data['major_projects'])

    spring['mp_status'] = "Failed"
    for mp in data['major_projects']:
        if mp['status'] == "Pending":
            spring['mp_status'] = 'Pending'
            continue
        if mp['status'] == "Passed":
            spring['mp_status'] = 'Passed'
            break

    conditionals = [
        {
            'date_created': c.date_created,
            'date_due': c.date_due,
            'description': c.description,
            'status': c.status
        } for c in
        Conditional.query.filter(Conditional.uid == user_name)]
    data['conditionals'] = conditionals
    data['conditionals_len'] = len(conditionals)

    cm_attendance = [
        {
            'type': m.committee,
            'datetime': m.timestamp
        } for m in CommitteeMeeting.query.filter(
            CommitteeMeeting.id.in_(c_meetings)
        )]

    hm_attendance = [
        {
            'reason': m.excuse,
            'datetime': HouseMeeting.query.filter(
                HouseMeeting.id == m.meeting_id).first().date
        } for m in
        MemberHouseMeetingAttendance.query.filter(
            MemberHouseMeetingAttendance.uid == user_name
        ).filter(MemberHouseMeetingAttendance.attendance_status == "Absent")]

    data['cm_attendance'] = cm_attendance
    data['cm_attendance_len'] = len(cm_attendance)
    data['hm_attendance'] = hm_attendance
    data['hm_attendance_len'] = len(hm_attendance)

    return render_template(request, 'dashboard.html', **data)
