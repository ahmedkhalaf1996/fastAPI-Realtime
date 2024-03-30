import logging
from typing import List

from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

from grserver import friends

app = FastAPI()

class Message(BaseModel):
    sender: str
    recever: str
    content: str

class ConnectionManager:
    def __init__(self):
        self.connections = {}
        self.online_friends = {}

    async def add_connection(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        self.online_friends[user_id] = []

        # Notify existing users about the new online friend
        for friend_id in self.online_friends:
            if friend_id != user_id and await self.is_friend(user_id, friend_id):
                self.online_friends[friend_id].append(user_id)
                try:
                    await self.connections[friend_id].send_json({"onlineFriends": self.online_friends[friend_id]})
                except Exception as e:
                    logging.error(f"Error notifying {friend_id} about {user_id}: {e}")
                    return

        # Update the online friends list for the new user
        for friend_id in await friends.get_user_friends(user_id):
            if self.connections.get(friend_id):
                self.online_friends[user_id].append(friend_id)
                try:
                    await websocket.send_json({"onlineFriends": self.online_friends[user_id]})
                except Exception as e:
                    logging.error(f"Error notifying {user_id} about {friend_id}: {e}")
                    return

    async def remove_connection(self, user_id: str):
        del self.connections[user_id]
        del self.online_friends[user_id]
        for friend_id in self.online_friends:
            if user_id in self.online_friends[friend_id]:
                self.online_friends[friend_id].remove(user_id)
                try:
                    await self.connections[friend_id].send_json({"onlineFriends": self.online_friends[friend_id]})
                except Exception as e:
                    logging.error(f"Error notifying {friend_id} about {user_id}: {e}")

    async def send_to_recever(self, msg: Message):
        try:
            recever = msg.recever
            if recever in self.connections:
                conn = self.connections[recever]
                try:
                    await conn.send_json(msg.model_dump())
                except Exception as e:
                    logging.error(f"Error sending message to {recever}: {e}")
            else:
                logging.error(f"recever {recever} not found")
        except Exception as e:
            print("send message ", e)

    async def is_friend(self, user_id: str, friend_id: str) -> bool:
        return friend_id in await friends.get_user_friends(user_id)

manager = ConnectionManager()

@app.websocket("/ws/{id}")
async def websocket_endpoint(websocket: WebSocket, id: str):
    await manager.add_connection(id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = Message(**data)
            await manager.send_to_recever(msg)
    except Exception as e:
        logging.error(f"WebSocket error for user {id}: {e}")
    finally:
        await manager.remove_connection(id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
