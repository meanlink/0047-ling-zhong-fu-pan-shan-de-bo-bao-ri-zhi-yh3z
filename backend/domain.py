from fastapi import APIRouter
from beacon import decision_routes,observation_routes,tour_routes
from beacon.demo import seed
from beacon.receipt import correction

router=APIRouter()
for section in (tour_routes,observation_routes,decision_routes):
    router.include_router(section.router)

def run_job(cx,kind,payload):
    if kind=="clock-correction":return correction(cx,payload)
    raise ValueError(f"Unknown clock task {kind}")
