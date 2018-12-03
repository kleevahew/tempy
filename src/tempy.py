from jira import JIRA
import jiraConfig
from datetime import datetime, timedelta
from tzlocal import get_localzone

# ---------------------------
#    INITIALIZE
# ---------------------------
_SCRUM_MASTER = True
_ISSUE_LIST = []
_WORKLOG = []
_SPRINT = ''
_TEST_MODE = False
_BOT_NAME = 'Tempy'
if _TEST_MODE:
    print('------------------------------------------')
    print('  WORKING IN TEST MODE  \(-.-)/ ')
    print('------------------------------------------')
# Login into Jira API
_JIRA = JIRA(jiraConfig.jira_url, basic_auth=(jiraConfig.jira_user, jiraConfig.jira_password))

# ---------------------------
#    Week values
# 0 - monday, 1 - tuesday ...
# ---------------------------
daily_hours = 7.4
monday = {'day': 'monday', 'day_num': 0, 'available': daily_hours, 'total': daily_hours}
tuesday = {'day': 'tuesday', 'day_num': 1, 'available': daily_hours, 'total': daily_hours}
wednesday = {'day': 'wednesday', 'day_num': 2, 'available': daily_hours, 'total': daily_hours}
thursday = {'day': 'thursday', 'day_num': 3, 'available': daily_hours, 'total': daily_hours}
friday = {'day': 'friday', 'day_num': 4, 'available': daily_hours, 'total': daily_hours}
week_days = ['monday','tuesday','wednesday','thursday','friday']
_WEEK_AVAILABILITY = [monday, tuesday, wednesday, thursday, friday]
print('')
print('=======================================================')
print('')
# inputs
print(_BOT_NAME + ' : Hello')
print(_BOT_NAME + ' : My name is ' + _BOT_NAME + ' and I will help you setup your hours')
print(_BOT_NAME + " : What can I call you ? ")
_NAME = str(input('> '))
print(_BOT_NAME + " : OK " + _NAME + " let's start")
print(_BOT_NAME + ' : What week of the year are you trying to log ?')
_WEEK = int(input(_NAME + ' : '))
_YEAR = int(datetime.now().strftime('%Y'))

if _WEEK % 2 == 0:
    _SPRINT = jiraConfig.main_project + ' ' + str(_YEAR) + '-W' + str(_WEEK) + '/' + str(_WEEK + 1)
else:
    _SPRINT = jiraConfig.main_project + ' ' + str(_YEAR) + '-W' + str(_WEEK - 1) + '/' + str(_WEEK)


def getWeekDays(year, week):
    d = datetime(year, 1, 1, 9)
    dlt = timedelta(days=(week - 1) * 7)
    return [d + dlt, d + dlt + timedelta(days=1), d + dlt + timedelta(days=2), d + dlt + timedelta(days=3),
            d + dlt + timedelta(days=4)]


def getRemainingTime():
    remaining = 0
    for day in _WEEK_AVAILABILITY:
        remaining = remaining + day['available']

    return remaining


def allocateTime(issue_key, hours):
    hours_to_log = round(hours, 1)

    for day in _WEEK_AVAILABILITY:
        available = round(day['available'], 1)
        if available > 0:

            if hours_to_log > available:
                log_time = available
            else:
                log_time = hours_to_log

            if hours_to_log > 0:
                hours_to_log = round(hours_to_log - log_time, 1)
                logWork(issue_key, log_time, day['day'], 'Development')


def logWork(log_key, log_time, log_day, comment):
    for day in _WEEK_AVAILABILITY:
        if day['day'] == log_day:
            available = day['available']
            if log_time > available:
                pass
            else:
                day['available'] = round(available - log_time, 1)
                log = {'day': day['day_num'], 'time': log_time, 'key': log_key, 'comment': comment}
                _WORKLOG.append(log)


def getTotalSP(issue_list):
    total_sp = 0
    for issue in issue_list:
        if _WEEK in issue['weeks']:
            total_sp = total_sp + float(issue['story_points'])

    return total_sp


def getSprintIssues():
    # ----------------------
    #    JIRA VARIABLES
    # -----------------------

    start_at = 0
    jira_field_list = 'customfield_11836,created,customfield_15820,issuetype'
    jira_query = 'project = ' + jiraConfig.main_project + '  and sprint = "' + _SPRINT + '"'

    # Search issues
    issues = _JIRA.search_issues(jira_query, start_at, jiraConfig.jira_max_results, True, jira_field_list, 'changelog')

    # Maximum number of issues
    total_issues = int(issues.total)

    sprint_issues = []
    while total_issues >= start_at:
        for issue in issues:

            development_date_list = []
            po_review_date_list = []
            issue_key = ''
            story_points = 0

            for hist in issue.changelog.histories:
                for item in hist.items:
                    if item.field == 'status':
                        if item.toString in jiraConfig.development_status and item.fromString in jiraConfig.start_status:

                            year = int(str(hist.created)[0:4])
                            month = int(str(hist.created)[5:7])
                            day = int(str(hist.created)[8:10])
                            development_date_list.append(datetime(year, month, day))

                            if hist.author.emailAddress == jiraConfig.jira_user:
                                issue_key = issue.key

                        if item.toString in jiraConfig.po_status and item.fromString in jiraConfig.team_status:
                            year = int(str(hist.created)[0:4])
                            month = int(str(hist.created)[5:7])
                            day = int(str(hist.created)[8:10])
                            po_review_date_list.append(datetime(year, month, day))

            if str(issue.fields.customfield_11836) != 'None':
                story_points = str(issue.fields.customfield_11836)

            if len(issue_key) > 0:
                start_date = min(development_date_list)

                if len(po_review_date_list) > 0:
                    end_date = max(po_review_date_list)
                else:
                    end_date = datetime.now()

                weeks = list(range(start_date.isocalendar()[1], end_date.isocalendar()[1] + 1))

                issue_info = {'key': issue.key, 'weeks': weeks, 'story_points': story_points}
                sprint_issues.append(issue_info)

        # Increment startAt point
        start_at = start_at + jiraConfig.jira_max_results

        # Search issues
        issues = _JIRA.search_issues(jira_query, start_at, jiraConfig.jira_max_results, True, jira_field_list,
                                     'changelog')

    return sprint_issues

def askHours():
    print(_BOT_NAME + ' : How many hours did you work for that ?')
    print(_BOT_NAME + ' : The maximum available is 7.4 ?')
    hours = float(input(_NAME + ' : '))
    return hours


def askComment():
    print(_BOT_NAME + ' : What did you do that day ?')
    comment = str(input(_NAME + ' : '))
    return comment


def askDays(key,comment='',ask_hours=False,ask_comment=False):

    print(_BOT_NAME + ' : When ?')
    rerun = True
    while rerun:
        print(_BOT_NAME + ' : (Separate days of the week with comma. i.e : monday,wednesday)')
        days = str(input(_NAME + ' : '))
        rerun = False
        incorrect_days = []
        for day in days.split(','):
            if day.strip() not in week_days:
                incorrect_days.append(day.strip())
                rerun = True
            else:
                print(_BOT_NAME + ' : I will insert a log on ' + day.strip() + ' for you.')

                log_comment = comment
                if ask_comment:
                    log_comment = askComment()

                hours = 7.4

                if ask_hours:
                    hours = askHours()

                logWork(key, hours, day.strip(), log_comment)



        if rerun:
            print(_BOT_NAME + " : (O.o) I don't know these days " + str(incorrect_days) + " " + _NAME + "??")
            print(_BOT_NAME + ' : Do you want to correct or add other days ? [y/n]')
            correct = str(input(_NAME + ' : '))
            if correct == 'n':
                print(_BOT_NAME + ' : OK ')
                rerun = False


def addInternalToWorklog():
    print(_BOT_NAME + ' : Hey ' + _NAME + ' do you want to add the standard Internal Work ? [y/n]')
    internal = str(input(_NAME + ' : '))
    if internal == 'y':
        #    RETROSPECTIVE
        logWork('INT-6', 1, 'monday', '.')
        #    REFINEMENT
        logWork('INT-9', 1.5, 'thursday', '.')
        #    PLANNING
        logWork('INT-8', 1, 'monday', '.')
        #    DAILY STAND-UP
        if _WEEK % 2 != 0:
            logWork('INT-7', 0.25, 'monday', '.')

        logWork('INT-7', 0.25, 'tuesday', '.')
        logWork('INT-7', 0.25, 'wednesday', '.')
        logWork('INT-7', 0.25, 'thursday', '.')
        logWork('INT-7', 0.25, 'friday', '.')
        #    TECH SESSION
        if _WEEK % 2 == 0:
            logWork('INT-4', 0.75, 'monday', 'Tech Session')
    else:
        print(_BOT_NAME + ' : OK ')


def addScrumMasterActivities():
    print(_BOT_NAME + ' : Are you a Scrum Master ' +_NAME+' ? [y/n]')
    sm = str(input(_NAME + ' : '))
    if sm == 'y':
        if _WEEK % 2 == 0:
            logWork('INT-14', 1, 'monday', 'Sprint start activities')
            logWork('INT-14', 1, 'tuesday', 'Agile Guild')

        logWork('INT-14', 0.25, 'tuesday', 'SoS')
    else:
        print(_BOT_NAME + ' : I prefer developers also')
        print(_BOT_NAME + ' : DEVELOPERS DEVELOPERS DEVELOPERS ...')


def addIssuesToWorklog():
    print(_BOT_NAME + ' : Hey ' + _NAME + ' I can get to JIRA and calculate pre calculate the hours of your tickets')
    print(_BOT_NAME + ' : I use a logic of Story points and remaining time to log')
    print(_BOT_NAME + ' : Do you want me to do that ? [y/n]')

    addjira = str(input(_NAME + ' : '))
    if addjira == 'y':
        print(_BOT_NAME + ' : Ok let me check JIRA ...')
        total = getRemainingTime()
        issue_list = getSprintIssues()
        total_sp = getTotalSP(issue_list)
        for issue in issue_list:
            if _WEEK in issue['weeks']:
                allocateTime(issue['key'], round(float(issue['story_points']) * (total / total_sp), 1))
    else:
        print(_BOT_NAME + ' : OK')


def sendWorklog(worklog, jira):
    total_logged = 0
    for day in getWeekDays(_YEAR, _WEEK):
        _LOG_DATE = get_localzone().localize(day)
        for log in worklog:
            if log['day'] == day.weekday():
                if not _TEST_MODE:
                    jira.add_worklog(log['key'], str(log['time']) + 'h', started=_LOG_DATE, comment=log['comment'])
                total_logged = total_logged + log['time']

    return total_logged


def addOthersToWorklog():
    print(_BOT_NAME + ' : ' + _NAME + ' do you have miscellaneous work to log ? [y/n]')
    miscellaneous = str(input(_NAME + ' : '))
    if miscellaneous == 'y':
        askDays('INT-4',ask_comment=True,ask_hours=True)

    else:
        print(_BOT_NAME + ' : OK ')

def addOutOfOfficeToWorklog():
    print(_BOT_NAME + ' : ' +_NAME  + ' were you on vacations this week ? [y/n]')
    vacations = str(input(_NAME + ' : '))
    if vacations == 'y':
        print(_BOT_NAME + ' : All week ? [y/n]')
        all_week = str(input(_NAME + ' : '))
        if all_week == 'y':
            logWork('INT-1', 7.4, 'monday', 'Vacations')
            logWork('INT-1', 7.4, 'tuesday', 'Vacations')
            logWork('INT-1', 7.4, 'wednesday', 'Vacations')
            logWork('INT-1', 7.4, 'thursday', 'Vacations')
            logWork('INT-1', 7.4, 'friday', 'Vacations')
        else:
            askDays('INT-1',comment='Vacations',ask_comment=False)

    else:
        print(_BOT_NAME + " : Yeah me neither, it's a bummer")

def main():
    addOutOfOfficeToWorklog()
    addOthersToWorklog()
    addInternalToWorklog()
    addScrumMasterActivities()
    addIssuesToWorklog()

    print(_BOT_NAME + ' : I got these worklog from you')
    for log in _WORKLOG:
        print(log)

    print(_BOT_NAME + ' : Is this correct ? [y/n]')
    validate_worklog = str(input(_NAME + ' : '))
    if validate_worklog == 'y':
        print(_BOT_NAME + ' : I am going to log your hours now ' + _NAME + ' ...')
        total_logged = sendWorklog(_WORKLOG, _JIRA)
        if total_logged > 0:
            print(_BOT_NAME + ' : I have Logged ' + str(total_logged) + ' hours for you')
        else:
            print(_BOT_NAME + ' : Nothing to log')
    else:
        print(_BOT_NAME + ' : We just wasted time, nice')
        print(_BOT_NAME + ' : .\.  `(-.-)´ ./. ')

    print(_BOT_NAME + ' : See you next time ' + _NAME)
    print(_BOT_NAME + ' : Bye')
    print(_BOT_NAME + ' : '+_BOT_NAME+' out')


# -------------------------------
# START EXECUTION SCRIPT HERE
# ------------------------------->
main()

