import smtplib

from email.message import EmailMessage

msg = EmailMessage()
msg.set_content("Hello World")
msg["To"] = "volker.andreas.austrup@cern.ch"
msg["From"] = "exotics.diskspace.watcher@cern.ch"
msg["Subject"] = "Weekly Exotics Diskspace Report"

# this only works from within the CERN network
# see https://mailservices.docs.cern.ch/Miscellaneous/Anonymous_smtp/
s = smtplib.SMTP(host='cernmx.cern.ch', port=25)
s.send_message(msg)
s.quit()