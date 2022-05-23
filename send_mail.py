from datetime import datetime
import yagmail

def send_mail(reciever, sender_e, sender_pass):
    msg = 'Movement detected in the system on '+str(datetime.now())
    reciever = str(reciever)

    yag = yagmail.SMTP(sender_e, sender_pass)

    yag.send(
        to=reciever,
        subject="Motion notification",
        contents=msg
    )
