from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource
from models import message, llm
from api import call_baichuan_api, convert_to_openai_format
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 添加 CORS 头
api = Api(app, version='1.0', title='OpenAI API', description='A simple OpenAI API')
ns = api.namespace('', description='OpenAI operations')

message_model = api.model('Message', message)
llm_model = api.model('LLM', llm)

@ns.route('/v1/chat/completions')
class LlmApi(Resource):
    @ns.expect(llm_model)
    def post(self):
        data = api.payload
        response_data = call_baichuan_api(data)
        response_data = convert_to_openai_format(response_data, data)  # 使用新的函数处理 response_data
        if data.get('stream', False):
            response = app.response_class(
                response=response_data,  # 对于流式数据，直接使用处理后的 response_data，无需再次转换为 JSON
                status=200,
                mimetype='application/json; charset=utf-8'  # 指定字符集
            )
        else:
            response = app.response_class(
                response=json.dumps(response_data, ensure_ascii=False),  # 对于非流式数据，使用 json.dumps 函数将数据转换为 JSON 字符串
                status=200,
                mimetype='application/json; charset=utf-8'  # 指定字符集
            )
        return response

@ns.route('/v1/models')
class ModelsApi(Resource):
    def get(self):
        model_names = ["dall-e-2","dall-e-3","whisper-1","tts-1","tts-1-1106","tts-1-hd","tts-1-hd-1106","gpt-3.5-turbo","gpt-3.5-turbo-0301","gpt-3.5-turbo-0613","gpt-3.5-turbo-16k","gpt-3.5-turbo-16k-0613","gpt-3.5-turbo-1106","gpt-3.5-turbo-instruct","gpt-4","gpt-4-0314","gpt-4-0613","gpt-4-32k","gpt-4-32k-0314","gpt-4-32k-0613","gpt-4-1106-preview","gpt-4-vision-preview","text-embedding-ada-002","text-davinci-003","text-davinci-002","text-curie-001","text-babbage-001","text-ada-001","text-moderation-latest","text-moderation-stable","text-davinci-edit-001","code-davinci-edit-001","claude-instant-1","claude-2","claude-2.1","claude-2.0","ERNIE-Bot","ERNIE-Bot-turbo","ERNIE-Bot-4","Embedding-V1","PaLM-2","chatglm_turbo","chatglm_pro","chatglm_std","chatglm_lite","qwen-turbo","qwen-plus","text-embedding-v1","SparkDesk","360GPT_S2_V9","embedding-bert-512-v1","embedding_s1_v1","semantic_similarity_s1_v1","hunyuan"]

        models = {
            "object": "list",
            "data": [
                {
                    "id": model_name,
                    "object": "model",
                    "created": 1686935002,
                    "owned_by": "organization-owner"
                } for model_name in model_names
            ]
        }
        return models
    
if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=5000)