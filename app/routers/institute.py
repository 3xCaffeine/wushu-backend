from fastapi import APIRouter, HTTPException, Form
from app.core.utils import hash_password, verify_password
from app.db.models import UserCreate, LoginRequest, AthleteResponse, TournamentResponse, GetEndorsementResponse, EndorsementReviewRequest, institution, tournament, endorsements, athlete
from sqlmodel import select
from typing import List
from app.routers.deps import SessionDep
from uuid import uuid4, UUID

router = APIRouter(prefix="/institute", tags=["Institution"])


def get_user_by_email(email: str, session: SessionDep) -> institution | None:
    statement = select(institution).where(institution.email == email)
    session_user = session.exec(statement).first()
    return session_user


@router.post(
    "/register",
    summary="Register a new user",
    responses={
        201: {
            "description": "User registered successfully",
            "content": {"application/json": {"example": {"message": "User registered successfully", "user_id": "uuid"}}},
        },
        400: {
            "description": "User already exists",
            "content": {"application/json": {"example": {"detail": "User already exists"}}},
        },
        500: {
            "description": "Server error during user registration",
            "content": {"application/json": {"example": {"detail": "Error registering user: ERROR"}}},
        },
    },
)
def register_user(session: SessionDep, user: UserCreate = Form(...)):
    hashed_password = hash_password(user.password)
    uid = str(uuid4())
    try:
        existing_user = get_user_by_email(email=user.email, session=session)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

        new_user = institution(
            user_id=uid,
            email=user.email,
            username=user.name,
            password=hashed_password,
        )
        session.add(new_user)
        session.commit()
        return {"message": "User registered successfully", "user_id": uid, "username": user.username}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering user: {e}")


@router.post(
    "/login",
    summary="Authenticate user and return user_id",
    responses={
        200: {
            "description": "Login successful",
            "content": {"application/json": {"example": {"message": "Login successful", "user_id": "uuid"}}},
        },
        401: {
            "description": "Invalid credentials",
            "content": {"application/json": {"example": {"detail": "Invalid credentials"}}},
        },
        500: {
            "description": "Server error during login",
            "content": {"application/json": {"example": {"detail": "Error logging in: some error"}}},
        },
    },
)
def login_user(session: SessionDep, loginrequest: LoginRequest = Form(...)):
    try:
        credentials = get_user_by_email(email=loginrequest.email, session=session)
        if not credentials or not verify_password(loginrequest.password, credentials.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": "Login successful", "user_id": credentials.user_id, "username": credentials.username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging in: {e}")


@router.get(
    "/searchInstitution",
    summary="Fetch institutes against a name",
    responses={
        200: {
            "description": "List of matching institutions",
            "content": {"application/json": {"example": [
                {
                    "institute_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Sports Academy",
                    "contact": "9876543210"
                }
            ]}}
        },
        404: {
            "description": "No matching institutions found",
            "content": {"application/json": {"example": {"detail": "No institutions found matching the given name"}}},
        },
        500: {
            "description": "Server error",
            "content": {"application/json": {"example": {"detail": "Error fetching institutions: some error"}}},
        },
    },
)
def search_institutions(session: SessionDep, name: str = ""):
    try:
        stmt = select(institution).where(institution.name.ilike(f"%{name}%"))
        institutions = session.exec(stmt).all()

        if not institutions:
            raise HTTPException(status_code=404, detail="No institutions found matching the given name")
        
        return [{"name": row.name, "contact": row.contact} for row in institutions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching institutions: {e}")


@router.get(
    "/getEndorsements",
    summary="Fetch pending endorsements with athlete and tournament details",
    response_model=List[GetEndorsementResponse],
)
def get_pending_endorsements(session: SessionDep, endorser_id: UUID = Form(...)):
    try:
        stmt = (
            select(
                endorsements.endorsements_id,
                endorsements.tournament_id,
                athlete.name.label("athlete_name"), athlete.age, athlete.gender, athlete.division,
                athlete.contact, athlete.matches_played, tournament.name.label("tournament_name"),
                tournament.division, tournament.stage, tournament.start_date,
                tournament.end_date, tournament.location,
            )
            .join(athlete, endorsements.athlete_id == athlete.athlete_id)
            .join(tournament, endorsements.tournament_id == tournament.tournament_id)
            .where(endorsements.endorser_id == endorser_id, endorsements.review == False)
        )

        results = session.exec(stmt).all()

        if not results:
            raise HTTPException(status_code=404, detail="No pending endorsementss found")

        endorsements = [
            GetEndorsementResponse(
                endorsements_id=row.endorsements_id,
                match_id=row.match_id,
                athlete=AthleteResponse(
                    name=row.athlete_name,
                    age=row.age,
                    gender=row.gender,
                    division=row.division,
                    contact=row.contact,
                    matches_played=row.matches_played,
                ),
                tournament=TournamentResponse(
                    division=row.division,
                    stage=row.stage,
                    name=row.tournament_name,
                    start_date=row.start_date.isoformat(),
                    end_date=row.end_date.isoformat(),
                    location=row.location,
                ),
            )
            for row in results
        ]

        return endorsements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching endorsements: {e}")


@router.post(
    "/reviewEndorsement",
    summary="Update a pending endorsement's review and approval status",
    responses={
        200: {
            "description": "Endorsement updated successfully",
            "content": {"application/json": {"example": {
                "message": "Endorsement updated successfully",
                "endorsement_id": "550e8400-e29b-41d4-a716-446655440000",
            }}}
        },
        404: {
            "description": "Endorsement not found",
            "content": {"application/json": {"example": {"detail": "Endorsement not found"}}},
        },
        500: {
            "description": "Server error",
            "content": {"application/json": {"example": {"detail": "Error updating endorsement: some error"}}},
        },
    },
)
def review_endorsement(
    session: SessionDep,
    request: GetEndorsementResponse = Form(...),
):
    try:
        endorsement = session.exec(select(endorsements).where(endorsements.endorsement_id == request.endorsement_id)).first()

        if not endorsement:
            raise HTTPException(status_code=404, detail="Endorsement not found")

        endorsement.review = True
        endorsement.approve = request.approve

        session.add(endorsement)
        session.commit()
        session.refresh(endorsement)

        return {
            "message": "Endorsement updated successfully",
            "endorsement_id": endorsement.endorsement_id,
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating endorsement: {e}")