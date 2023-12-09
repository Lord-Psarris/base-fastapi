from fastapi.exceptions import HTTPException
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from typing import Union

import requests
import configs


def send_email(subject: str, recipient_email: str, text_content: Union[str, None], html_content: Union[str, None]) -> None:
    
    post_data = {
        "recipients": [recipient_email],
        "text_message": text_content,
        "html_message": html_content,
        "subject": subject,
    }
    
    # send notification
    response = requests.post(f"{configs.NOTIFICATIONS_URL}/send-email", json=post_data, headers={"x-api-key": configs.API_KEY})
    response.raise_for_status()
    
    return response.json()
