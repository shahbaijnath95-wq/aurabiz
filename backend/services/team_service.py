from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Team, TeamMember, User
from datetime import datetime, timezone


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(self, business_id: str, name: str, description: str = None, owner_user_id: str = None) -> Team:
        team = Team(business_id=business_id, name=name, description=description)
        self.db.add(team)
        await self.db.flush()
        if owner_user_id:
            member = TeamMember(
                team_id=team.id,
                user_id=owner_user_id,
                role="owner",
                permissions=["*"],
            )
            self.db.add(member)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def list_teams(self, business_id: str) -> list[Team]:
        result = await self.db.execute(select(Team).where(Team.business_id == business_id, Team.is_active == True))
        return result.scalars().all()

    async def get_team(self, team_id: str) -> Team | None:
        result = await self.db.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def update_team(self, team_id: str, **kwargs) -> Team | None:
        team = await self.get_team(team_id)
        if not team:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(team, k):
                setattr(team, k, v)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def delete_team(self, team_id: str) -> bool:
        team = await self.get_team(team_id)
        if not team:
            return False
        team.is_active = False
        await self.db.commit()
        return True

    async def add_member(self, team_id: str, user_id: str, role: str = "staff", permissions: list = None) -> TeamMember | None:
        existing = await self.db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return None
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            permissions=permissions or [],
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def update_member(self, team_id: str, user_id: str, **kwargs) -> TeamMember | None:
        result = await self.db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(member, k):
                setattr(member, k, v)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, team_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await self.db.delete(member)
        await self.db.commit()
        return True

    async def get_members(self, team_id: str) -> list[TeamMember]:
        result = await self.db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.is_active == True)
        )
        return result.scalars().all()

    async def get_user_teams(self, user_id: str, business_id: str) -> list[Team]:
        result = await self.db.execute(
            select(Team).join(TeamMember).where(
                TeamMember.user_id == user_id,
                Team.business_id == business_id,
                TeamMember.is_active == True,
            )
        )
        return result.scalars().all()

    async def check_permission(self, user_id: str, business_id: str, permission: str) -> bool:
        result = await self.db.execute(
            select(TeamMember)
            .join(Team)
            .where(
                TeamMember.user_id == user_id,
                Team.business_id == business_id,
                TeamMember.is_active == True,
            )
        )
        members = result.scalars().all()
        for m in members:
            if "*" in (m.permissions or []):
                return True
            if permission in (m.permissions or []):
                return True
            if m.role == "owner":
                return True
        return False

    async def get_team_count(self, business_id: str) -> int:
        result = await self.db.execute(
            select(func.count(Team.id)).where(Team.business_id == business_id, Team.is_active == True)
        )
        return result.scalar() or 0
