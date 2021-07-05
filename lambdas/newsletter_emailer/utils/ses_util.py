from botocore.exceptions import ClientError


def send_raw_email(ses_client, msg, sender, recipients):
    print(sender, 'to', recipients)

    # Provide the contents of the email.
    response = ses_client.send_raw_email(
        Source=sender,
        Destinations=recipients,
        RawMessage={
            'Data': msg.as_string(),
        }
    )
    print("Email sent! Message ID:", response['MessageId'])
    return response


def send_email(ses_client, emails, subject, from_address, message_text, message_html=''):
    charset = 'utf8'
    try:
        resp = ses_client.send_email(
            Source=from_address,
            Destination={
                'ToAddresses': emails
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': charset
                },
                'Body': {
                    'Text': {
                        'Data': message_text,
                        'Charset': charset
                    },
                    'Html': {
                        'Charset': charset,
                        'Data': message_html,
                    },
                }
            },
            ReplyToAddresses=[from_address]
        )
        print(resp['MessageId'])
    except Exception as e:
        raise Exception('Error in sending email:', str(e))
    return True
