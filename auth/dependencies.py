from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import verify_token
from database.mysql import get_user_by_uuid

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    
    user_uuid = verify_token(credentials.credentials)
    if not user_uuid:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    
    user = get_user_by_uuid(user_uuid)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    
    user_uuid = verify_token(credentials.credentials)
    if not user_uuid:
        return None
    
    return get_user_by_uuid(user_uuid)
