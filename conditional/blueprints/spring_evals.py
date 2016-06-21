from flask import Blueprint
from flask import request

from conditional.util.ldap import ldap_get_active_members, ldap_get_name

from conditional.db.models import MemberCommitteeAttendance, MemberHouseMeetingAttendance, MajorProject, HouseMeeting, \
    SpringEval, HousingEvalsSubmission

from conditional.util.flask import render_template

spring_evals_bp = Blueprint('spring_evals_bp', __name__)


@spring_evals_bp.route('/spring_evals/')
def display_spring_evals(internal=False):
    def get_cm_count(user_uid):
        return len([a for a in MemberCommitteeAttendance.query.filter(
            MemberCommitteeAttendance.uid == user_uid)])

    user_name = None
    if not internal:
        user_name = request.headers.get('x-webauth-user')

    members = [m['uid'] for m in ldap_get_active_members()]

    sp_members = []
    for member_uid in members:
        uid = member_uid[0].decode('utf-8')
        print(uid)
        spring_entry = SpringEval.query.filter(
            SpringEval.uid == uid and
            SpringEval.active).first()

        if spring_entry is None:
            # This user isn't actually supposed to be here
            # something bad happened to get here
            print("CRITICAL ERROR!")
            continue

        eval_data = None
        if internal:
            eval_data = HousingEvalsSubmission.query.filter(
                HousingEvalsSubmission.uid == uid).first()

            if HousingEvalsSubmission.query.filter(
                            HousingEvalsSubmission.uid == uid).count() > 0:
                eval_data = {
                    'social_attended': eval_data.social_attended,
                    'social_hosted': eval_data.social_hosted,
                    'seminars_attended': eval_data.technical_attended,
                    'seminars_hosted': eval_data.technical_hosted,
                    'projects': eval_data.projects,
                    'comments': eval_data.comments
                }
        h_meetings = [m.meeting_id for m in
                      MemberHouseMeetingAttendance.query.filter(
                          MemberHouseMeetingAttendance.uid == uid
                      ).filter(
                          MemberHouseMeetingAttendance.attendance_status == "Absent"
                      )]
        member = {
            'name': ldap_get_name(uid),
            'uid': uid,
            'status': spring_entry.status,
            'committee_meetings': get_cm_count(uid),
            'house_meetings_missed': [
                {
                    "date": m.date.strftime("%Y-%m-%d"),
                    "reason":
                        MemberHouseMeetingAttendance.query.filter(
                            MemberHouseMeetingAttendance.uid == uid).filter(
                            MemberHouseMeetingAttendance.meeting_id == m.id).first().excuse
                } for m in HouseMeeting.query.filter(HouseMeeting.id.in_(h_meetings))
                ],
            'major_projects': [
                {
                    'name': p.name,
                    'status': p.status,
                    'description': p.description
                } for p in MajorProject.query.filter(MajorProject.uid == uid)
                ]
        }

        member['major_projects_len'] = len(member['major_projects'])
        member['major_project_passed'] = False
        for mp in member['major_projects']:
            if mp['status'] == "Passed":
                member['major_project_passed'] = True
                break

        if internal:
            member['housing_evals'] = eval_data
        sp_members.append(member)

    sp_members.sort(key=lambda x: x['committee_meetings'], reverse=True)
    sp_members.sort(key=lambda x: len(x['house_meetings_missed']))
    sp_members.sort(key=lambda x: len([p for p in x['major_projects'] if p['status'] == "Passed"]), reverse=True)
    # return names in 'first last (username)' format
    if internal:
        return sp_members
    else:
        return render_template(request,
                               'spring_evals.html',
                               username=user_name,
                               members=sp_members)
