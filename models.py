from flask_restx import fields, Model

message = Model('Message', {
    'role': fields.String(required=True, description='The role of the message'),
    'content': fields.String(required=True, description='The content of the message')
})

llm = Model('LLM', {
    'model': fields.String(required=True, description='The model to use'),
    'messages': fields.List(fields.Nested(message), description='The messages to process'),
    'temperature': fields.Float(description='The temperature to use'),
    'stream': fields.Boolean(description='Whether to stream the response')
})