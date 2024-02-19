from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
)
from constructs import Construct


class RegistroUsuarioStack(Stack):
    """
    Stack para manejar el registro y la autenticación de usuarios.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Constructor de la clase.

        Args:
            scope: El scope de la construcción.
            construct_id: El ID de la construcción.
            kwargs: Argumentos adicionales para el stack.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Se Crea la tabla DynamoDB para almacenar información de usuario
        table = dynamodb.Table(
            self, "UserTable",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            ),
            read_capacity=5,
            write_capacity=5
        )

        # Función Lambda para manejar el registro de usuarios
        lambda_function_signup = _lambda.Function(
            self, "sign-up",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="registro.handler",
            code=_lambda.Code.from_asset("./lambda"),
            environment={
                "USER_TABLE_NAME": table.table_name,
            }
        )

        # Función Lambda para manejar la autenticación de usuarios
        lambda_function_signin = _lambda.Function(
            self, "sign-in",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="validacion.handler",
            code=_lambda.Code.from_asset("./lambda"),
            environment={
                "USER_TABLE_NAME": table.table_name,
            }
        )

        # Permisos a las funciones Lambda para acceder a la tabla DynamoDB
        table.grant_read_write_data(lambda_function_signup)
        table.grant_read_write_data(lambda_function_signin)

        # Configurar API Gateway
        api = apigateway.RestApi(self, "EmailServiceApi")

        # Endpoint de registro de usuario
        resource_users = api.root.add_resource("users")
        resource_registro = resource_users.add_resource("signup")
        integration = apigateway.LambdaIntegration(lambda_function_signup)
        resource_registro.add_method("POST", integration)

        # Endpoint de autenticación de usuario restringido por API Key
        resource_validacion = resource_users.add_resource("signin")
        integration = apigateway.LambdaIntegration(lambda_function_signin)
        method = resource_validacion.add_method(
            "POST", integration, api_key_required=True
        )

        # Plan de uso asociado con la API Gateway
        api_key = api.add_api_key("ApiKey")
        usage_plan = api.add_usage_plan(
            "UsagePlan",
            name="UsagePlan",
            description="Plan de uso para la API Gateway",
            api_stages=[{"api": api, "stage": api.deployment_stage}],
            quota={"limit": 10000, "period": apigateway.Period.MONTH},
            throttle={"rate_limit": 500, "burst_limit": 100}
        )
        usage_plan.add_api_key(api_key)

        # Permisos de envío de correos electrónicos
        ses_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ses:SendEmail", "ses:SendRawEmail", "ses:SendTemplatedEmail"],
            resources=["*"]
        )
        lambda_function_signup.add_to_role_policy(ses_policy_statement)
