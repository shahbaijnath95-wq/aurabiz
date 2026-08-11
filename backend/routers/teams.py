"""
Teams Router — Multi-user/team access, RBAC, role-based permissions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.team_service import TeamService
from schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse,
)

router = APIRouter(prefix="/api/v1/teams", tags=["Teams"])


@router.get("/{business_id}")
async def list_teams(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = TeamService(db)
    teams = await svc.list_teams(business_id)
    count = await svc.get_team_count(business_id)
    return {"teams": [{"id": t.id, "business_id": t.business_id, "name": t.name,
                        "description": t.description, "is_active": t.is_active,
                        "created_at": str(t.created_at) if t.created_at else None} for t in teams],
            "count": count}


@router.post("")
async def create_team(data: TeamCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = TeamService(db)
    team = await svc.create_team(data.business_id, data.name, data.description)
    return {"id": team.id, "name": team.name, "message": "Team ban gaya!"}


@router.get("/detail/{team_id}")
async def get_team(team_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    members = await svc.get_members(team_id)
    return {
        "id": team.id, "name": team.name, "description": team.description,
        "is_active": team.is_active,
        "members": [{"id": m.id, "user_id": m.user_id, "role": m.role,
                      "permissions": m.permissions or [], "is_active": m.is_active} for m in members],
    }


@router.put("/{team_id}")
async def update_team(team_id: str, data: TeamUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    team = await svc.update_team(team_id, **data.model_dump(exclude_unset=True))
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    return {"message": "Team update ho gaya!", "name": team.name}


@router.delete("/{team_id}")
async def delete_team(team_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    ok = await svc.delete_team(team_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    return {"message": "Team delete ho gaya!"}


@router.post("/{team_id}/members")
async def add_member(team_id: str, data: TeamMemberAdd, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    member = await svc.add_member(team_id, data.user_id, data.role, data.permissions)
    if not member:
        raise HTTPException(status_code=400, detail="Member already exists ya error aaya")
    return {"message": "Member add ho gaya!", "id": member.id, "role": member.role}


@router.put("/{team_id}/members/{user_id}")
async def update_member(team_id: str, user_id: str, data: TeamMemberUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    member = await svc.update_member(team_id, user_id, **data.model_dump(exclude_unset=True))
    if not member:
        raise HTTPException(status_code=404, detail="Member nahi mila")
    return {"message": "Member update ho gaya!", "role": member.role}


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(team_id: str, user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    ok = await svc.remove_member(team_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Member nahi mila")
    return {"message": "Member remove ho gaya!"}


@router.get("/{team_id}/members")
async def list_members(team_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = TeamService(db)
    team = await svc.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team nahi mila")
    if not await verify_business_access(current_user, team.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    members = await svc.get_members(team_id)
    return {"members": [{"id": m.id, "user_id": m.user_id, "role": m.role,
                          "permissions": m.permissions or [], "is_active": m.is_active} for m in members]}


@router.get("/user/{user_id}/{business_id}")
async def get_user_teams(user_id: str, business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = TeamService(db)
    teams = await svc.get_user_teams(user_id, business_id)
    return {"teams": [{"id": t.id, "name": t.name} for t in teams]}
