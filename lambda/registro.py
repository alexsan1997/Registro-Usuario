import json
import os
import boto3
import random
import string

# Inicializa los clientes de AWS
dynamodb = boto3.client('dynamodb')
ses = boto3.client('ses')
table_name = os.environ['USER_TABLE_NAME']

# Variable global para almacenar la caché
cache = {}


def handler(event, context):
    """
    Función principal que maneja la solicitud de registro de usuarios.

    Args:
        event: El evento de la solicitud.
        context: El contexto de la ejecución de la función Lambda.

    Returns:
        Un diccionario que contiene la respuesta HTTP.
    """
    try:
        print(event)

        # Verifica si se proporciona un cuerpo en la solicitud
        if 'body' not in event or not event['body']:
            raise ValueError("El cuerpo de la solicitud está vacío")

        request_body = json.loads(event['body'])

        # Verifica si se proporciona un correo electrónico en el cuerpo de la solicitud
        if 'email' not in request_body or not request_body['email']:
            raise ValueError("El correo electrónico no fue proporcionado en la solicitud")

        user_email = request_body['email']

        # Comprueba si el correo electrónico ya está en caché
        generated_password = cache.get(user_email)

        if not generated_password:
            generated_password = generate_password()

            # Agrega el correo electrónico y la contraseña a la caché
            cache[user_email] = generated_password

            send_email(user_email, generated_password)

            dynamodb.put_item(
                TableName=table_name,
                Item={'email': {'S': user_email}, 'password': {'S': generated_password}}
            )

        response = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Registro exitoso'}),
        }

    except ValueError as ve:
        response = {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)}),
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }

    return response


def generate_password():
    """
    Genera una contraseña aleatoria.

    Returns:
        Una cadena que representa la contraseña generada.
    """
    characters = string.ascii_letters + string.digits + '!$%^'
    password = ''.join(random.choices(characters, k=12))
    return password


def send_email(to_address, generated_password):
    """
    Envía un correo electrónico de notificación sobre el registro exitoso.

    Args:
        to_address: La dirección de correo electrónico del destinatario.
        generated_password: La contraseña generada para el usuario.
    """
    subject = 'Registro Exitoso'
    body_text = f'Tu contraseña generada automáticamente: {generated_password}'
    body_html = f'<p>Tu contraseña generada automáticamente: {generated_password}</p>'

    try:
        ses.send_email(
            Destination={'ToAddresses': [to_address]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                    'Html': {'Data': body_html}
                }
            },
            Source='angel_may_s@hotmail.com' # El correo tiene que estar verificado en tu cuenta de aws
        )
    except Exception as e:
        raise Exception("No se pudo enviar el correo electrónico. Por favor, inténtalo de nuevo más tarde.")
