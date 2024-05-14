import datetime
import smtplib
import subprocess

from email.message import EmailMessage

from helpers.logger import log

TODAY = datetime.datetime.now()
command_today = f'git show $(git rev-list -1 HEAD):reports/{"lpx"}.csv'
result_today = subprocess.run(command_today, shell=True, capture_output=True, text=True)
analyses_today = [x for x in result_today.stdout.split("\n") if x!='']
ONE_WEEK_AGO = (TODAY - datetime.timedelta(7)).strftime("%Y-%m-%d")
command_one_week_ago = f'git show $(git rev-list -1 --before="{ONE_WEEK_AGO}" HEAD):reports/{"lpx"}.csv'
result_one_week_ago = subprocess.run(command_one_week_ago, shell=True, capture_output=True, text=True)
analyses_one_week_ago = [x for x in result_one_week_ago.stdout.split("\n") if x!='']


msg = EmailMessage()
msg.set_content("Hello World")
msg["To"] = "volker.andreas.austrup@cern.ch"
msg["From"] = "exotics.diskspace.watcher@cern.ch"
msg["Subject"] = "Weekly Exotics Diskspace Report"

log.info(f"Sending weekly report to {msg['To']}.")

# this only works from within the CERN network
# see https://mailservices.docs.cern.ch/Miscellaneous/Anonymous_smtp/
s = smtplib.SMTP(host='cernmx.cern.ch', port=25)
s.send_message(msg)
s.quit()