import openai
import json

openai.api_key = 'sk-fl2IJdcT92BYr4YG43B33557F550416e9cD72d4dDc4d1f7c'
openai.api_base = 'http://35.74.130.198:5000/llm/v1'

response_generator = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
        {
            "role": "user",
            "content": "你好",
        }
    ],
  stream=True
)

# 遍历生成器，打印每一条消息的响应体和响应头
for response in response_generator:
    print("Response body:")
    print(json.dumps(response, indent=4))

# 打印响应内容
for response in response_generator:
    print("Response body:", response)
# openai.api_key = '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'
# import requests
# import json

# url = "https://api.baichuan-ai.com/v1/chat/completions"
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": "Bearer 47826f7b337b631af50a2b615fdb3436",  # 请替换为你的 API 密钥
# }
# data = {
#     "model": "Baichuan2",
#     "messages": [
#         {
#             "role": "user",
#             "content": "世界第一高峰是?"
#         }
#     ],
#     "temperature": 0.3,
#     "stream": True
# }

# response = requests.post(url, headers=headers, data=json.dumps(data))

# if response.status_code == 200:
#     print('请求成功')
#     print('返回的内容是：', response.text)
# else:
#     print('请求失败，状态码：', response.status_code)