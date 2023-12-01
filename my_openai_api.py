from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import requests
import json
import time
import uuid
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 添加 CORS 头
api = Api(app, version='1.0', title='OpenAI API', description='A simple OpenAI API')
ns = api.namespace('openai', description='OpenAI operations')

ns = api.namespace('', description='LLM operations')

message = api.model('Message', {
    'role': fields.String(required=True, description='The role of the message'),
    'content': fields.String(required=True, description='The content of the message')
})

llm = api.model('LLM', {
    'model': fields.String(required=True, description='The model to use'),
    'messages': fields.List(fields.Nested(message), description='The messages to process'),
    'temperature': fields.Float(description='The temperature to use'),
    'stream': fields.Boolean(description='Whether to stream the response')
})

def call_baichuan_api(data):
    url = "https://api.baichuan-ai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 47826f7b337b631af50a2b615fdb3436"  # 请替换为您的 Baichuan API 密钥
    }
    original_model = data["model"]  # 保存请求的 "model" 值
    data["model"] = "Baichuan2"  # 将 "model" 的值设置为 "Baichuan2"
    if "stream" in data and str(data["stream"]).lower() == "true":
        data["stream"] = True  # 如果请求中的 "stream" 参数为 "true"，则将其值改为布尔值 True
    else:
        data["stream"] = False  # 否则，将其值改为布尔值 False
    if "temperature" not in data or not isinstance(data["temperature"], float) or not 0.0 <= data["temperature"] <= 1.0:
        data["temperature"] = 0.3  # 如果 "temperature" 参数不存在，或者其值不是一个在 [0.0, 1.0] 范围内的浮点数，就设置默认值为 0.3
    if "messages" in data:
        for message in data["messages"]:
            if "role" in message and message["role"].lower() == "system":
                message["role"] = "user"  # 如果 "message" 中的 "role" 值为 "system"，则将其值改为 "user" 
    print("Request data: %s", data)  # 打印请求数据
    response = requests.post(url, headers=headers, data=json.dumps(data))
    logging.info("Response status code: %s", response.status_code)  # 打印响应状态码
    try:
        if data["stream"]:
            # 如果 "stream" 为 True，处理流式数据
            response_data = []
            for line in response.text.splitlines():
                if line.strip() == 'data: [DONE]':
                    break
                if line.startswith('data: '):
                    json_line = json.loads(line[6:])
                    json_line["model"] = original_model  # 将 "model" 的值改回请求的 "model" 值
                    response_data.append(json_line)
        else:
            # 否则，处理非流式数据
            response_data = response.json()
            response_data["model"] = original_model  # 将 "model" 的值改回请求的 "model" 值
        logging.info("Baichuan API response: %s", response_data)  # 打印响应内容
        return response_data
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON from response: %s", response.text)  # 打印原始响应内容
        return {}

def convert_to_openai_format(response, request_data):
    # 如果 "stream" 为 True，处理流式数据
    if request_data.get('stream', False):
        # 使用列表推导式来简化代码
        result = [
            'data: ' + json.dumps({
                "id": message["id"],
                "object": "chat.completion.chunk",
                "created": message["created"],
                "model": message["model"],
                "system_fingerprint": None,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": message["choices"][0]["delta"]["content"] if "content" in message["choices"][0]["delta"] else ""
                    },
                    "finish_reason": message["choices"][0].get("finish_reason")  # 使用 dict.get 方法获取 "finish_reason" 字段的值
                }]
            }, ensure_ascii=False) + '\n\n' for message in response if message != 'data:[DONE]'  # 如果消息为 "data:[DONE]"，则停止处理
        ]
        result.append('data: [DONE]\n')  # 添加结束标记
        return ''.join(result)  # 将所有响应对象的字符串连接起来
    # 否则，处理非流式数据
    else:
    # 检查响应中是否包含 "id" 键
     if "id" not in response:
        print("Error: Response does not contain 'id' key")
        return {"error": "Invalid response from Baichuan API"}

    # 将 Baichuan API 的响应转换为 OpenAI 格式
    if "choices" in response and response["choices"]:
        choices = [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"]
            },
            "finish_reason": "stop"
        }]
    else:
        choices = []
    result = {
        "id": response["id"],
        "object": "chat.completion",
        "created": int(time.time()),  # 使用当前时间的时间戳
        "model": response["model"],  # 使用响应数据中的 "model" 值
        "choices": choices,
        "usage": response.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),  # 如果响应中没有 "usage" 键，使用默认值
        "system_fingerprint": None  # 添加 "system_fingerprint" 键，其值为 None
    }
    print("Converted data:", result)  # 打印转换后的数据
    return result

@ns.route('/v1/chat/completions')
class LlmApi(Resource):
    @ns.expect(llm)
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