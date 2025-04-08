from fastapi import APIRouter, HTTPException, Form
from sqlmodel import select
from app.core.models import (
    GetOngoingTournamentDetailsResponse,
    GetAllTournamentDetailsResponse,
    tournament,
    endorsements,
    TournamentResultsRequest,
    TournamentDetails,
)
from app.routers.deps import SessionDep
from typing import List
from uuid import uuid4, UUID


router = APIRouter(prefix="/tournament", tags=["Tournament"])


# Fetching all tournament info for spectator view
@router.get(
    "/getAllTournaments",
    summary="Fetch all tournaments",
    response_model=List[GetAllTournamentDetailsResponse],
    responses={
        200: {
            "description": "List of ongoing tournaments",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "tournament_id": "d1b2f8e4-23a6-4d1b-b3a6-7f1d3b2e4d9f",
                            "division": "Senior",
                            "stage": 3,
                            "name": "National Championship",
                            "winner": "John Doe",
                            "runnerup": "Jane Smith",
                            "winnerscore": 95,
                            "runnerscore": 90,
                            "start_date": "2025-03-01T10:00:00",
                            "end_date": "2025-03-10T18:00:00",
                            "location": "New Delhi",
                            "archived": True,
                        }
                    ]
                }
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error fetching all tournament records: error"
                    }
                }
            },
        },
    },
)
def get_all_tournaments(session: SessionDep):
    try:
        tournaments = session.exec(select(tournament)).all()

        if not tournaments:
            return []

        results = [
            GetAllTournamentDetailsResponse(
                division=tournament.division,
                stage=tournament.stage,
                name=tournament.name,
                winner=tournament.winner,
                runnerup=tournament.runnerup,
                winnerscore=tournament.winnerscore,
                runnerscore=tournament.runnerscore,
                start_date=tournament.start_date,
                end_date=tournament.end_date,
                location=tournament.location,
                archived=not tournament.ongoing,
            )
            for tournament in tournaments
        ]

        return results

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error fetching all tournament records: {e}"
        )


# Ongoing tournaments pulled for athlete view
@router.get(
    "/getOngoingTournaments",
    summary="Fetch ongoing tournaments with status based on athlete endorsements",
    response_model=List[GetOngoingTournamentDetailsResponse],
    responses={
        200: {
            "description": "List of ongoing tournaments",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "tournament_id": "550e8400-e29b-41d4-a716-446655440000",
                            "division": "Senior",
                            "stage": 2,
                            "start_date": "2025-03-10T10:00:00",
                            "end_date": "2025-03-20T18:00:00",
                            "location": "Sports Complex",
                            "status": True,
                        }
                    ]
                }
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error fetching tournaments: some error"}
                }
            },
        },
    },
)
def get_ongoing_tournaments(session: SessionDep, athlete_id: UUID):
    try:
        tournaments = session.exec(
            select(tournament).where(tournament.ongoing == True)
        ).all()

        if not tournaments:
            return []

        response = []
        for existing_tournament in tournaments:
            endorsement = session.exec(
                select(endorsements)
                .where(endorsements.tournament_id == existing_tournament.tournament_id)
                .where(endorsements.athlete_id == athlete_id)
            ).first()

            if not endorsement or (endorsement.review and not endorsement.approve):
                status = False
            else:
                status = True

            response.append(
                {
                    "tournament_id": existing_tournament.tournament_id,
                    "name": existing_tournament.name,
                    "division": existing_tournament.division,
                    "stage": existing_tournament.stage,
                    "start_date": existing_tournament.start_date.isoformat(),
                    "end_date": existing_tournament.end_date.isoformat(),
                    "location": existing_tournament.location,
                    "status": status,
                }
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tournaments: {e}")


@router.post(
    "/createTournament",
    summary="Create a new tournament",
    responses={
        201: {"description": "Tournament created successfully"},
        500: {"description": "Error creating tournament"},
    },
)
def create_tournament(session: SessionDep, request: TournamentDetails = Form(...)):
    try:
        new_tournament = tournament(
            tournament_id=uuid4(),
            name=request.name,
            division=request.division,
            stage=request.stage,
            start_date=request.start_date,
            end_date=request.end_date,
            location=request.location,
            ongoing=True,
        )

        session.add(new_tournament)
        session.commit()
        session.refresh(new_tournament)

        return {"message": "Tournament created successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating tournament: {e}")


@router.patch(
    "/updateTournamentResults",
    summary="Update a tournament's results",
    responses={
        200: {"description": "Tournament updated successfully"},
        404: {"description": "Tournament not found"},
        500: {"description": "Error updating tournament"},
    },
)
def update_tournament_results(
    session: SessionDep, request: TournamentResultsRequest = Form(...)
):
    try:
        existing_tournament = session.exec(
            select(tournament).where(tournament.tournament_id == request.tournament_id)
        ).first()

        if not existing_tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        existing_tournament.winner = request.winner
        existing_tournament.runnerup = request.runnerup
        existing_tournament.winnerscore = request.winnerscore
        existing_tournament.runnerscore = request.runnerscore
        existing_tournament.ongoing = False

        session.add(existing_tournament)
        session.commit()
        session.refresh(existing_tournament)

        return {"message": "Tournament updated successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating tournament: {e}")
