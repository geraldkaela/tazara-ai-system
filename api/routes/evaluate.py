from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def evaluate_schedule():
    return {
        "message": "Evaluation endpoint ready (RL inference coming next)"
    }
