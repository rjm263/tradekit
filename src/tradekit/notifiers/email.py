"""This module provides the EmailNotifier class.

It is a subclass of :class:`~tradekit.notifiers.base.Notifier` and notifies the client by email about trading events.
"""

from tradekit.notifiers.events import Event
import smtplib, ssl, os
from email.message import EmailMessage
from pathlib import Path
import mimetypes

class EmailNotifier:
    """The class providing email notifications via SMTP about trading events.
    """    
    def __init__(self, smtp_host: str, smtp_port: str, user: str, smtp_password: str, sender: str, recipients: str | list[str]) -> None:
        """Initialises the EmailNotifier class.

        Parameters
        ----------
        smtp_host : str
            The smtp host of the email client
        smtp_port : str
            The smtp port of the email client (usually 465)
        user : str
            The username of the sender email account
        smtp_password : str
            The *environment variable* pointing to the email account password; no plain password is permitted here, it must be stored as an environment variable, e.g., by including a .env file in the project folder
        sender : str
            The sender's email address
        recipients : str | list[str]
            The recipients' email addresses
        """        
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_password = smtp_password
        self.user = user
        self.sender = sender
        self.recipients = recipients if isinstance(recipients, list) else [recipients]

    def notify(self, event: Event) -> None:
        """Sends an email notification.

        This is the main method of the class. Provided all init parameters, it sends an email to all recipients listed.

        Parameters
        ----------
        event : Event
            The event to be notified about, see :class:`~tradekit.notifiers.events.Event`
        """        
        subject, body = self._format(event)
        
        msg = EmailMessage()
        msg['from'] = self.sender
        msg['to'] = ', '.join(self.recipients)
        msg['subject'] = subject
        msg.set_content(body)

        # If the event contains a file path, attach the file to the email
        if event.path_to_file is not None:
            file_path = Path(event.path_to_file)

            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = file_path.name

            mime_type, _ = mimetypes.guess_type(file_path)
            maintype, subtype = mime_type.split("/")

            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=file_name
            )

        context = ssl.create_default_context()
        password = self._get_smtp_password(self.smtp_password)

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as s:
            s.login(self.user, password)
            s.send_message(msg)

    def _format(self, event):
        if event.type == 'trade_exit':
            subject = f'[TRADE EXIT] {event.source}'
        elif event.type == 'all_engines_finished':
            subject = f"[SUPERVISOR] {event.source}: {event.type.replace('_', ' ').upper()}"
        else:
            subject = f"[ENGINE] {event.source}: {event.type.replace('_', ' ').upper()}"

        body = '\n'.join(f"{k}: {v}" for k, v in event.payload.items())

        return subject, body
    

    def _get_smtp_password(self, var: str):
        try:
            return os.environ.get(var)
        except KeyError:
            raise MissingSecretError(
                f"{self.smtp_password} environment variable is not set"
            )
    
class MissingSecretError:
    pass