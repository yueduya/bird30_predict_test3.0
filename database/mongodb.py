from pymongo import MongoClient
from datetime import datetime
from config import settings

mongo_client = MongoClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB]
conv_col = mongo_db["conversations"]

def save_message(user_uuid: str, role: str, content: str, session_id: str = None):
    doc = {
        "user_uuid": user_uuid,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }
    if session_id:
        doc["session_id"] = session_id
    conv_col.insert_one(doc)

def get_recent_conversations(user_uuid: str, n_rounds: int = 10, session_id: str = None):
    query = {"user_uuid": user_uuid}
    if session_id:
        query["session_id"] = session_id
    
    cursor = conv_col.find(
        query, 
        {"_id": 0, "role": 1, "content": 1}
    ).sort("created_at", -1).limit(2 * n_rounds)
    
    history = []
    for doc in cursor:
        history.append({"role": doc["role"], "content": doc["content"]})
    history.reverse()
    return history

def get_user_sessions(user_uuid: str, limit: int = 20):
    pipeline = [
        {"$match": {"user_uuid": user_uuid}},
        {"$group": {
            "_id": "$session_id",
            "last_message": {"$last": "$content"},
            "last_time": {"$last": "$created_at"},
            "message_count": {"$sum": 1}
        }},
        {"$sort": {"last_time": -1}},
        {"$limit": limit}
    ]
    return list(conv_col.aggregate(pipeline))

def delete_session(user_uuid: str, session_id: str):
    conv_col.delete_many({"user_uuid": user_uuid, "session_id": session_id})
