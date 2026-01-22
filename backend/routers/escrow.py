"""Escrow Router"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def get_escrow_info():
    return {"message": "Escrow endpoint"}
