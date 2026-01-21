import websocket
import json

# Called when a message is received
def on_message(ws, message):
    print("Received:", message)

# Called when the connection is opened
def on_open(ws):
    print("Connected!")
    # Send a test message
    ws.send(json.dumps({
        "message": "Hello from Python!",
        "user_id": 2  # Replace with your Django user ID
    }))

# Called when the connection closes
def on_close(ws, close_status_code, close_msg):
    print("Disconnected!")

# Replace 1 with your ChatRoom ID
ws_url = "ws://127.0.0.1:8000/ws/chat/2/"

ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_open=on_open,
    on_close=on_close
)

# Start the WebSocket connection
ws.run_forever()
