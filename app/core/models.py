from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from datetime import datetime

# Application Data Models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AthleteEndorsementRequest(BaseModel):
    athlete_id: UUID
    institute_id: UUID 
    tournament_id: UUID

class AthleteResponse(BaseModel):
    name: str
    age: int
    gender: str
    division: str
    contact: str
    matches_played: int

class TournamentDetails(BaseModel):
    division: str
    stage: int
    name: str
    start_date: datetime
    end_date: datetime
    location: str

class GetEndorsementResponse(BaseModel):
    athlete: AthleteResponse
    tournament: TournamentDetails

class EndorsementReviewRequest(BaseModel):
    endorsement_id: UUID
    approve: bool

class UpdateAthleteRequest(BaseModel):
    athlete_id: UUID
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    division: Optional[str] = None
    contact: Optional[str] = None
    password: Optional[str] = None

class InstitutionUpdateRequest(BaseModel):
    institute_id: UUID
    contact: str
    name: str

class GetTournamentDetailsResponse(BaseModel):
    tournament_id: UUID
    division: str
    stage: int
    name: str
    start_date: datetime
    end_date: datetime
    location: str
    status: bool

class TournamentResultsRequest(BaseModel):
    tournament_id: UUID
    winner: str
    runnerup: str
    winnerscore: int
    runnerscore: int


# Database Table Models
class endorsements(SQLModel, table=True):
    endorsement_id: UUID = Field(primary_key=True)
    tournament_id: UUID = Field(foreign_key="tournament.tournament_id")
    endorser_id: UUID = Field(foreign_key="institution.institute_id")
    athlete_id: UUID = Field(foreign_key="athlete.athlete_id")
    review: bool = Field(default=False)
    approve: bool = Field(default=False)

class athlete(SQLModel, table=True):
    athlete_id: UUID = Field(primary_key=True)
    name: str
    age: int
    gender: str
    division: str
    contact: str
    password: str
    matches_played: int = Field(default=0)

class tournament(SQLModel, table=True):
    tournament_id: UUID = Field(primary_key=True)
    division: str
    stage: int
    name: str
    winnerscore: Optional[int] = Field(default=0)
    runnerscore: Optional[int] = Field(default=0)
    start_date: datetime
    end_date: datetime
    location: str
    winner: Optional[str] = None
    runnerup: Optional[str] = None
    ongoing: bool = Field(default=True)

class institution(SQLModel, table=True):
    institute_id: UUID = Field(primary_key=True)
    name: str
    contact: str
    password: str
