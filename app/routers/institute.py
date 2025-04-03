from fastapi import APIRouter, HTTPException, Form
from app.core.utils import hash_password, verify_password
from app.core.models import (
    UserCreate,
    LoginRequest,
    AthleteResponse, 
    TournamentDetails, 
    GetEndorsementResponse, 
    EndorsementReviewRequest, 
    InstitutionUpdateRequest,
    institution, 
    tournament, 
    endorsements, 
    athlete
)
from sqlmodel import select
from typing import List
from app.routers.deps import SessionDep
from uuid import uuid4, UUID

router = APIRouter(prefix="/institute", tags=["Institution"])


def get_institute_by_email(email: str, session: SessionDep) -> institution | None:
    try:
        statement = select(institution).where(institution.contact == email)
        session_user = session.exec(statement).first()
        return session_user
    except Exception as e:
        print(f"Error: {e}")
        raise


# create institute
@router.post(
    "/register",
    summary="Register a new institute",
    responses={
        201: {
            "description": "Institute registered successfully",
            "content": {"application/json": {"example": {"message": "Institute registered successfully", "user_id": "uuid"}}},
        },
        400: {
            "description": "Institute already exists",
            "content": {"application/json": {"example": {"detail": "Institute already exists"}}},
        },
        500: {
            "description": "Server error during institute registration",
            "content": {"application/json": {"example": {"detail": "Error registering institute: ERROR"}}},
        },
    },
)
def register_institute(session: SessionDep, user: UserCreate = Form(...)):
    hashed_password = hash_password(user.password)
    uid = uuid4()
    try:
        existing_user = get_institute_by_email(email=user.email, session=session)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

        new_user = institution(
            institute_id=uid,
            contact=user.email,
            name=user.name,
            password=hashed_password,
        )
        session.add(new_user)
        session.commit()
        return {"message": "Institute registered successfully", "institute_id": uid, "username": user.name}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering institute: {e}")


@router.post(
    "/login",
    summary="Authenticate Institute and return user_id",
    responses={
        200: {
            "description": "Login successful",
            "content": {"application/json": {"example": {"message": "Login successful", "institute_id": "uuid"}}},
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
def login_institute(session: SessionDep, loginrequest: LoginRequest = Form(...)):
    try:
        credentials = get_institute_by_email(email=loginrequest.email, session=session)
        if not credentials or not verify_password(loginrequest.password, credentials.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {"message": "Login successful", "user_id": credentials.institute_id, "username": credentials.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging in: {e}")


@router.patch(
    "/updateDetails",
    summary="Update an institution's name and contact",
    responses={
        200: {"description": "Institution updated successfully"},
        404: {"description": "Institution not found"},
        500: {"description": "Error updating institution"},
    }
)
def update_institute(
    session: SessionDep,
    request: InstitutionUpdateRequest = Form(...)
):
    try:
        institutions = session.exec(
            select(institution).where(institution.institute_id == request.institute_id)
        ).first()

        if not institutions:
            raise HTTPException(status_code=404, detail="Institution not found")

        institutions.name = request.name
        institutions.contact = request.contact

        session.add(institutions)
        session.commit()
        session.refresh(institutions)

        return {"message": "Institution updated successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating institution: {e}")


@router.get(
    "/getDetails",
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
def search_institutes(session: SessionDep, name: str = Form(...)):
    try:
        stmt = select(institution).where(institution.name.ilike(f"%{name}%"))
        institutions = session.exec(stmt).all()

        if not institutions:
            raise HTTPException(status_code=404, detail="No institutions found matching the given name")
        
        return [{"name": row.name, "contact": row.contact} for row in institutions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching institutions: {e}")



## Endorsement Routes
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
                tournament=TournamentDetails(
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
    request: EndorsementReviewRequest = Form(...),
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
    

@router.get(
    "/getApprovedAthletes",
    summary="Fetch approved athletes and their ongoing tournaments for a given institution",
    response_model=List[AthleteResponse],
    responses={
        200: {"description": "Approved athletes retrieved successfully"},
        404: {"description": "No approved athletes or tournaments found"},
        500: {"description": "Error fetching data"},
    }
)
def get_approved_athletes(
    institute_id: UUID,
    session: SessionDep,
):
    try:
        # Query: Get all approved endorsements with matching athlete_id and ongoing tournaments
        subquery = (
            select(endorsements.athlete_id)
            .join(tournament, endorsements.tournament_id == tournament.tournament_id)
            .where(
                endorsements.institute_id == institute_id,
                endorsements.approve == True,
                tournament.ongoing == True
            )
            .distinct()
        )

        # Fetch unique athletes from the endorsement results
        athletes = session.exec(
            select(athlete)
            .where(athlete.athlete_id.in_(subquery))
        ).all()

        if not athletes:
            raise HTTPException(status_code=404, detail="No matching records found")

        return {"athletes": athletes}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")