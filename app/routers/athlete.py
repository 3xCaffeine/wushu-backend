from fastapi import APIRouter, HTTPException, Form
from app.core.utils import hash_password, verify_password
from app.db.models import UserCreate, LoginRequest, athlete, endorsements, UpdateAthleteRequest, AthleteEndorsementRequest
from sqlmodel import select
from typing import List
from app.routers.deps import SessionDep
from uuid import uuid4, UUID

router = APIRouter(prefix="/athlete", tags=["Athlete"])


def get_user_by_email(email: str, session: SessionDep) -> athlete | None:
    statement = select(athlete).where(athlete.email == email)
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

        new_user = athlete(
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

@router.post(
    "/updateDetails",
    summary="Update an athlete's details",
    responses={
        200: {
            "description": "Athlete updated successfully",
            "content": {"application/json": {"example": {
                "message": "Athlete updated successfully",
                "athlete_id": "550e8400-e29b-41d4-a716-446655440000",
            }}}
        },
        404: {
            "description": "Athlete not found",
            "content": {"application/json": {"example": {"detail": "Athlete not found"}}},
        },
        500: {
            "description": "Server error",
            "content": {"application/json": {"example": {"detail": "Error updating athlete: some error"}}},
        },
    },
)
def update_athlete_details(
    session: SessionDep,
    request: UpdateAthleteRequest = Form(...),
):
    try:
        athlete = session.exec(select(athlete).where(athlete.athlete_id == request.athlete_id)).first()

        if not athlete:
            raise HTTPException(status_code=404, detail="Athlete not found")

        update_fields = request.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(athlete, field, value)

        session.add(athlete)
        session.commit()
        session.refresh(athlete)

        return {
            "message": "Athlete updated successfully",
            "athlete_id": athlete.athlete_id,
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating athlete: {e}")

@router.post(
    "/requestEndorsement",
    summary="Endorsement request made to an institute from an athlete",
    responses={
        201: {
            "description": "Endorsement request successfully created",
            "content": {"application/json": {"example": {
                "message": "Endorsement request created successfully",
            }}}
        },
        404: {
            "description": "Athlete or Institution not found",
            "content": {"application/json": {"example": {"detail": "Athlete not found"}}},
        },
        500: {
            "description": "Server error",
            "content": {"application/json": {"example": {"detail": "Error creating endorsement request: some error"}}},
        },
    },
)
def create_endorsement_request(session: SessionDep, request: AthleteEndorsementRequest = Form(...)):
    try:
        new_endorse_request = endorsements(
            endorsement_id=uuid4(),
            tournament_id=request.tournament_id,
            endorser_id=request.institution_id,
            athlete_id=request.athlete_id,
            review=False,
            approve=False
        )

        session.add(new_endorse_request)
        session.commit()

        return {"message": "Endorsement request created successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating endorsement request: {e}")