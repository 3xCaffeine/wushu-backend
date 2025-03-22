from fastapi import APIRouter, HTTPException, Form
from sqlmodel import select
from app.core.models import (
    GetTournamentDetailsResponse, 
    tournament,
    TournamentResultsRequest,
    TournamentDetails
)
from app.routers.deps import SessionDep
from typing import List
from uuid import uuid4, UUID


router = APIRouter(prefix="/tournament", tags=["Tournament"])


@router.get(
    "/getOngoingTournaments",
    summary="Fetch ongoing tournaments with status based on athlete endorsements",
    response_model=List[GetTournamentDetailsResponse],
    responses={
        200: {
            "description": "List of ongoing tournaments",
            "content": {"application/json": {"example": [{
                "tournament_id": "550e8400-e29b-41d4-a716-446655440000",
                "division": "Senior",
                "stage": 2,
                "start_date": "2025-03-10T10:00:00",
                "end_date": "2025-03-20T18:00:00",
                "location": "Sports Complex",
                "status": True
            }]}},
        },
        500: {
            "description": "Server error",
            "content": {"application/json": {"example": {"detail": "Error fetching tournaments: some error"}}},
        },
    },
)
def get_ongoing_tournaments(
    session: SessionDep,
    athlete_id: UUID = Form(...),
):
    try:
        tournaments = session.exec(select(tournament).where(tournament.ongoing == True)).all()

        if not tournaments:
            return []

        response = []
        for tournament in tournaments:
            
            endorsement = session.exec(
                select(endorsement)
                .where(endorsement.tournament_id == tournament.tournament_id)
                .where(endorsement.athlete_id == athlete_id)
            ).first()

            if not endorsement or (endorsement.review and not endorsement.approve):
                status = False
            else:
                status = True

            response.append({
                "tournament_id": tournament.tournament_id,
                "name": tournament.name,
                "division": tournament.division,
                "stage": tournament.stage,
                "start_date": tournament.start_date.isoformat(),
                "end_date": tournament.end_date.isoformat(),
                "location": tournament.location,
                "status": status
            })

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tournaments: {e}")


@router.post(
    "/createTournament",
    summary="Create a new tournament",
    responses={
        201: {"description": "Tournament created successfully"},
        500: {"description": "Error creating tournament"},
    }
)
def create_tournament(
    session: SessionDep,
    request: TournamentDetails = Form(...),
):
    try:
        new_tournament = tournament(
            tournament_id=uuid4(),
            name=request.name,
            division=request.division,
            stage=request.stage,
            start_date=request.start_date,
            end_date=request.end_date,
            location=request.location,
            ongoing=True
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
    }
)
def update_tournament_results(
    session: SessionDep,
    request: TournamentResultsRequest = Form(...),
):
    try:
        tournament = session.exec(select(tournament).where(tournament.tournament_id == request.tournament_id)).first()

        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        tournament.winner = request.winner
        tournament.runnerup = request.runnerup
        tournament.winnerscore = request.winnerscore
        tournament.runnerscore = request.runnerscore
        tournament.ongoing = False

        session.add(tournament)
        session.commit()
        session.refresh(tournament)

        return {"message": "Tournament updated successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating tournament: {e}")