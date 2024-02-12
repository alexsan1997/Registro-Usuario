import aws_cdk as core
import aws_cdk.assertions as assertions

from registro_usuario.registro_usuario_stack import RegistroUsuarioStack

# example tests. To run these tests, uncomment this file along with the example
# resource in registro_usuario/registro_usuario_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = RegistroUsuarioStack(app, "registro-usuario")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
