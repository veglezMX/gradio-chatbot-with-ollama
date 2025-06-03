from fastapi import APIRouter, Response, Request

router = APIRouter(prefix="/api", tags=["cookies"])

@router.get("/set-cookie")
def set_cookie(response: Response):
    response.set_cookie(key="username", value="valen", httponly=True)
    return {"message": "Cookie set"}

@router.get("/get-cookie")
def get_cookie(request: Request):
    username = request.cookies.get("username")
    return {"username": username}