from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from medtour import settings


def sg_mail(to_emails, subject, content):
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to_emails,
        subject=subject,
        html_content=content)

    try:
        sg = SendGridAPIClient(settings.EMAIL_HOST_USER)
        response = sg.send(message)
    except Exception as e:
        print(e.message)
