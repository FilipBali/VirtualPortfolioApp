import smtplib
import ssl


def send_email(email_recipient, email_subject, email_message):

    smtp_server = 'smtp.gmail.com'
    sender_email = 'bp.filipbali@gmail.com'
    password = "yp1LFYRd3mBP00EnNV"

    receiver_email = email_recipient
    subject = email_subject
    body = email_message

    message = """Subject: {}\n\n{}""".format(subject, body)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

    return True


