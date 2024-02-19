import json
import os
import boto3
from botocore.exceptions import ClientError

# Inicializa el recurso DynamoDB y obtiene el nombre de la tabla de entorno
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['USER_TABLE_NAME']
table = dynamodb.Table(table_name)

# Variable global para almacenar la caché de contraseñas
password_cache = {}

def handler(event, context):
    """
    Función principal que maneja la solicitud de validación de usuario.

    Args:
        event: El evento de la solicitud.
        context: El contexto de la ejecución de la función Lambda.

    Returns:
        Un diccionario que contiene la respuesta HTTP.
    """
    try:
        # Verifica si el cuerpo de la solicitud está presente y es un JSON válido
        if 'body' not in event or not event['body']:
            raise ValueError("El cuerpo de la solicitud está vacío")

        request_body = json.loads(event['body'])

        # Obtiene datos del evento
        user_email = request_body.get('email')
        user_password = request_body.get('password')

        # Valida si se proporcionó un correo electrónico y una contraseña
        if not user_email or not user_password:
            raise ValueError("Se requiere tanto el correo electrónico como la contraseña")

        # Obtiene la contraseña almacenada de la caché, si está disponible
        stored_password = password_cache.get(user_email)

        # Si la contraseña no está en la caché, obtenerla de DynamoDB
        if stored_password is None:
            response = table.get_item(Key={'email': user_email})
            stored_password = response.get('Item', {}).get('password')
            if not stored_password:
                raise ValueError("Usuario no encontrado")
            # Almacena la contraseña en la caché
            password_cache[user_email] = stored_password

        # Valida la contraseña
        is_valid = user_password == stored_password

        # Responde con el resultado de la validación
        response_data = {'valid': is_valid}
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }

    except ClientError as e:
        # Maneja errores de DynamoDB y responde con un estado de error
        return {
            'statusCode': 500,
            'body': json.dumps({'error': "Error de servidor al procesar la solicitud"})
        }
    except ValueError as e:
        # Maneja errores de validación y responde con un estado de error
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
