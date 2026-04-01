# web search



import requests
url = "https://google.serper.dev/search"

payload = {
  "q": "what is surat weather"
}
headers = {
  'X-API-KEY': '5c95ba5909f99d6a5487d8588782f8eec9d00b04',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, json=payload)

print(response.text)