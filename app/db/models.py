from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AthleteResponse(BaseModel):
    name: str
    age: int
    gender: str
    division: str
    contact: str
    matches_played: int

class TournamentResponse(BaseModel):
    division: str
    stage: int
    start_date: str
    end_date: str
    location: str

class EndorsementResponse(BaseModel):
    athlete: AthleteResponse
    tournament: TournamentResponse


class endorsements(SQLModel, table=True):
    endorsement_id: UUID = Field(default_factory=UUID, primary_key=True)
    tournament_id: UUID = Field(foreign_key="tournament.tournament_id")
    endorser_id: UUID = Field(foreign_key="institution.institute_id")
    athlete_id: UUID = Field(foreign_key="athlete.athlete_id")
    review: bool = Field(default=False)
    approve: bool = Field(default=False)

class athlete(SQLModel, table=True):
    athlete_id: UUID = Field(default_factory=UUID, primary_key=True)
    endorsed: Optional[bool] = None
    name: str
    age: int
    gender: str
    division: str
    contact: str
    password: str
    matches_played: int = Field(default=0)

class tournament(SQLModel, table=True):
    tournament_id: UUID = Field(default_factory=UUID, primary_key=True)
    division: str
    stage: int
    name: str
    winnerscore: int
    runnerscore: int
    start_date: datetime
    end_date: datetime
    location: str
    winner: Optional[str] = None
    runnerup: Optional[str] = None
    ongoing: bool = Field(default=True)

class institution(SQLModel, table=True):
    institute_id: UUID = Field(default_factory=UUID, primary_key=True)
    name: str
    contact: str
    password: str
