from flask import Blueprint
from flask import request

from conditional.util.ldap import ldap_get_intro_members, ldap_get_name

from conditional.db.models import MemberCommitteeAttendance, FreshmanEvalData, MemberHouseMeetingAttendance, \
    MemberSeminarAttendance, HouseMeeting, TechnicalSeminar

from conditional.util.flask import render_template

intro_evals_bp = Blueprint('intro_evals_bp', __name__)


@intro_evals_bp.route('/intro_evals/')
def display_intro_evals(internal=False):
    # get user data
    def get_cm_count(user_uid):
        return len([a for a in MemberCommitteeAttendance.query.filter(
            MemberCommitteeAttendance.uid == user_uid)])

    user_name = None
    if not internal:
        user_name = request.headers.get('x-webauth-user')

    members = [m['uid'] for m in ldap_get_intro_members()]

    ie_members = []
    for member_uid in members:
        uid = member_uid[0].decode('utf-8')
        freshman_data = FreshmanEvalData.query.filter(
            FreshmanEvalData.uid == uid).first()
        h_meetings = [m.meeting_id for m in
                      MemberHouseMeetingAttendance.query.filter(
                          MemberHouseMeetingAttendance.uid == uid
                      ).filter(
                          MemberHouseMeetingAttendance.attendance_status == "Absent"
                      )]
        member = {
            'name': ldap_get_name(uid),
            'uid': uid,
            'eval_date': freshman_data.eval_date.strftime("%Y-%m-%d"),
            'signatures_missed': freshman_data.signatures_missed,
            'committee_meetings': get_cm_count(uid),
            'committee_meetings_passed': get_cm_count(uid) >= 10,
            'house_meetings_missed': [
                {
                    "date": m.date.strftime("%Y-%m-%d"),
                    "reason":
                        MemberHouseMeetingAttendance.query.filter(
                            MemberHouseMeetingAttendance.uid == uid).filter(
                            MemberHouseMeetingAttendance.meeting_id == m.id).first().excuse
                } for m in HouseMeeting.query.filter(HouseMeeting.id.in_(h_meetings))
                ],
            'technical_seminars':
                [s.name for s in TechnicalSeminar.query.filter(
                    TechnicalSeminar.id.in_(
                        [a.seminar_id for a in MemberSeminarAttendance.query.filter(
                            MemberSeminarAttendance.uid == uid)]
                    ))
                 ],
            'social_events': freshman_data.social_events,
            'freshman_project': freshman_data.freshman_project,
            'comments': freshman_data.other_notes,
            'status': freshman_data.freshman_eval_result
        }
        ie_members.append(member)

    ie_members.sort(key=lambda x: x['freshman_project'] == "Passed")
    ie_members.sort(key=lambda x: len(x['house_meetings_missed']))
    ie_members.sort(key=lambda x: x['committee_meetings'], reverse=True)
    ie_members.sort(key=lambda x: x['signatures_missed'])

    if internal:
        return ie_members
    else:
        # return names in 'first last (username)' format
        return render_template(request,
                               'intro_evals.html',
                               username=user_name,
                               members=ie_members)
