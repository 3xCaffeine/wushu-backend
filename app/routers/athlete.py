from fastapi import APIRouter, HTTPException, Form
from app.core.utils import hash_password, verify_password
from app.core.models import (
    UserCreate,
    LoginRequest,
    athlete,
    endorsements,
    UpdateAthleteRequest,
    AthleteResponse,
    AthleteEndorsementRequest,
)
from sqlmodel import select
from sqlalchemy import func
from app.routers.deps import SessionDep
from uuid import uuid4, UUID

router = APIRouter(prefix="/athlete", tags=["Athlete"])


def get_user_by_email(email: str, session: SessionDep) -> athlete | None:
    try:
        statement = select(athlete).where(athlete.contact == email)
        session_user = session.exec(statement).first()
        return session_user
    except Exception as e:
        print(f"Error: {e}")
        raise


@router.post(
    "/register",
    summary="Register a new user",
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered successfully",
                        "user_id": "uuid",
                    }
                }
            },
        },
        400: {
            "description": "User already exists",
            "content": {
                "application/json": {"example": {"detail": "User already exists"}}
            },
        },
        500: {
            "description": "Server error during user registration",
            "content": {
                "application/json": {
                    "example": {"detail": "Error registering user: ERROR"}
                }
            },
        },
    },
)
def register_athlete(session: SessionDep, user: UserCreate = Form(...)):
    hashed_password = hash_password(user.password)
    uid = uuid4()
    try:
        existing_user = get_user_by_email(email=user.email, session=session)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

        new_user = athlete(
            athlete_id=uid,
            contact=user.email,
            name=user.name,
            password=hashed_password,
        )
        session.add(new_user)
        session.commit()
        return {
            "message": "User registered successfully",
            "user_id": uid,
            "username": user.name,
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error registering user: {e}")


@router.post(
    "/login",
    summary="Authenticate user and return user_id",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {"message": "Login successful", "user_id": "uuid"}
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials"}}
            },
        },
        500: {
            "description": "Server error during login",
            "content": {
                "application/json": {
                    "example": {"detail": "Error logging in: some error"}
                }
            },
        },
    },
)
def login_athlete(session: SessionDep, loginrequest: LoginRequest = Form(...)):
    try:
        credentials = get_user_by_email(email=loginrequest.email, session=session)
        if not credentials or not verify_password(
            loginrequest.password, credentials.password
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {
            "message": "Login successful",
            "user_id": credentials.athlete_id,
            "username": credentials.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging in: {e}")


@router.get(
    "/getDetails",
    summary="Fetch athlete details by athlete_id",
    response_model=AthleteResponse,
    responses={
        200: {
            "description": "Athlete details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "athlete_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "John Doe",
                        "age": 25,
                        "gender": "Male",
                        "division": "Senior",
                        "contact": "1234567890",
                        "matches_played": 10,
                    }
                }
            },
        },
        404: {
            "description": "Athlete not found",
            "content": {
                "application/json": {"example": {"detail": "Athlete not found"}}
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error fetching athlete: some error"}
                }
            },
        },
    },
)
def get_athlete_details(session: SessionDep, athlete_id: UUID):
    try:
        existing_athlete = session.exec(
            select(athlete).where(athlete.athlete_id == athlete_id)
        ).first()

        if not existing_athlete:
            raise HTTPException(status_code=404, detail="Athlete not found")

        endorsement_count = (
            session.exec(
                select(func.count()).where(
                    endorsements.athlete_id == athlete_id, endorsements.approve == True
                )
            ).first()
            or 0
        )

        return {
            "athlete_id": existing_athlete.athlete_id,
            "name": existing_athlete.name,
            "age": existing_athlete.age,
            "gender": existing_athlete.gender,
            "division": existing_athlete.division,
            "contact": existing_athlete.contact,
            "matches_played": endorsement_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching athlete: {e}")


# actually creation of athlete profile
@router.patch(
    "/updateDetails",
    summary="Update an athlete's details",
    responses={
        200: {
            "description": "Athlete updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Athlete updated successfully",
                        "athlete_id": "550e8400-e29b-41d4-a716-446655440000",
                    }
                }
            },
        },
        404: {
            "description": "Athlete not found",
            "content": {
                "application/json": {"example": {"detail": "Athlete not found"}}
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error updating athlete: some error"}
                }
            },
        },
    },
)
def update_athlete_details(session: SessionDep, request: UpdateAthleteRequest = Form(...)):
    try:
        updated_athlete = session.exec(
            select(athlete).where(athlete.athlete_id == request.athlete_id)
        ).first()

        if not updated_athlete:
            raise HTTPException(status_code=404, detail="Athlete not found")

        update_fields = request.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(updated_athlete, field, value)

        session.add(updated_athlete)
        session.commit()
        session.refresh(updated_athlete)

        return {
            "message": "Athlete updated successfully",
            "athlete_id": updated_athlete.athlete_id,
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating athlete: {e}")


## Endorsement Routes
@router.post(
    "/requestEndorsement",
    summary="Endorsement request made to an institute from an athlete",
    responses={
        201: {
            "description": "Endorsement request successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Endorsement request created successfully",
                    }
                }
            },
        },
        404: {
            "description": "Athlete or Institution not found",
            "content": {
                "application/json": {"example": {"detail": "Athlete not found"}}
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error creating endorsement request: some error"
                    }
                }
            },
        },
    },
)
def create_endorsement_request(
    session: SessionDep, request: AthleteEndorsementRequest = Form(...)
):
    try:
        new_endorse_request = endorsements(
            endorsement_id=uuid4(),
            tournament_id=request.tournament_id,
            endorser_id=request.institute_id,
            athlete_id=request.athlete_id,
            review=False,
            approve=False,
        )

        session.add(new_endorse_request)
        session.commit()

        return {"message": "Endorsement request created successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating endorsement request: {e}")
