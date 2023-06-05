from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fhir.resources.patient import Patient as FhirPatient
from fhir.resources.identifier import Identifier as FhirIdentifier
import databases
from typing import Any

app = FastAPI()

# Define a Pydantic model for the patient data
class PatientData(BaseModel):
    name: str
    age: int
    diagnosis: str

# Set up the database
DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"  # Replace with your PostgreSQL connection details
database: databases.Database = databases.Database(DATABASE_URL)
Base: Any = declarative_base()

class Patient(Base):
    __tablename__: str = "patients"

    id: Column = Column(Integer, primary_key=True, index=True)
    name: Column = Column(String, index=True)
    age: Column = Column(Integer)
    diagnosis: Column = Column(String)
    fhir_identifier: Column = Column(String)

@app.on_event("startup")
async def startup() -> None:
    await database.connect()
    engine: Any = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal: Any = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app.db: Any = SessionLocal()

@app.on_event("shutdown")
async def shutdown() -> None:
    await database.disconnect()
    app.db.close()

@app.post("/patients")
async def create_patient(patient_data: PatientData) -> dict[str, str]:
    # Create a new FHIR Patient resource
    fhir_patient: FhirPatient = FhirPatient(
        identifier=[
            FhirIdentifier(
                system="http://example.com/patient-ids",
                value=str(patient_data.age),
            )
        ],
        name=[{"text": patient_data.name}],
    )

    # Serialize the FHIR resource to JSON
    fhir_json: str = fhir_patient.json()

    # Store the FHIR JSON along with other patient data in the database
    patient: Patient = Patient(
        name=patient_data.name,
        age=patient_data.age,
        diagnosis=patient_data.diagnosis,
        fhir_identifier=fhir_json,
    )
    app.db.add(patient)
    app.db.commit()

    return {"message": "Patient created successfully"}

@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
