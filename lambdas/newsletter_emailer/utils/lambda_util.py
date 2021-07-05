import json
import typing

import boto3


def invoke_lambda(*, func_name: str = None, payload: typing.Mapping[str, str] = None):
    if func_name is None:
        raise Exception('ERROR: functionName parameter cannot be NULL')
    payload_str = json.dumps(payload)
    payload_bytes_arr = bytes(payload_str, encoding='utf8')
    client = boto3.client('lambda')
    resp = client.invoke(
        FunctionName=func_name,
        InvocationType="RequestResponse",
        Payload=payload_bytes_arr
    )
    return resp


if __name__ == '__main__':
    payload = {
        {"to_emails": ["xxx@gmail.com"], "newsletter_date": "20210102"}
    }
    response = invoke_lambda(func_name='EmailNewsletterStack-EmailNewsletterAPI9C71001D-cSxvNXkaTTT6',
                             payload=payload)
    print(f'response:{response}')
