import requests
import json

def test_streaming():
    try:
        # Test the streaming endpoint
        response = requests.post(
            'http://localhost:8000/query/stream',
            data={
                'question': 'Hello, how are you?',
                'n_results': 3,
                'expand': 2,
                'conversation_history': '[]',
                'online_model': 'openai'
            },
            stream=True
        )
        
        print(f'Response status: {response.status_code}')
        
        if response.status_code == 200:
            print('Streaming response received:')
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f'Raw line: {decoded_line}')
                    try:
                        data = json.loads(decoded_line)
                        print(f'Parsed data: {data}')
                    except json.JSONDecodeError as e:
                        print(f'JSON decode error: {e}')
        else:
            print(f'Error: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

if __name__ == '__main__':
    test_streaming()
