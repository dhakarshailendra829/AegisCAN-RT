from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def external_test():
    return {"message": "External data router is active"}