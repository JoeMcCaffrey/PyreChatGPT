from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fhir.resources.patient import Patient as FhirPatient
from fhir.resources.identifier import Identifier as FhirIdentifier
import databases

app = FastAPI()

# Define a Pydantic model for the patient data
class PatientData(BaseModel):
    name: str
    age: int
    diagnosis: str

# Set up the database
DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"  # Replace with your PostgreSQL connection details
database = databases.Database(DATABASE_URL)
Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    diagnosis = Column(String)
    fhir_identifier = Column(String)

@app.on_event("startup")
async def startup():
    await database.connect()
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app.db = SessionLocal()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    app.db.close()

@app.post("/patients")
async def create_patient(patient_data: PatientData):
    # Create a new FHIR Patient resource
    fhir_patient = FhirPatient(
        identifier=[
            FhirIdentifier(
                system="http://example.com/patient-ids",
                value=str(patient_data.age),
            )
        ],
        name=[{"text": patient_data.name}],
    )

    # Serialize the FHIR resource to JSON
    fhir_json = fhir_patient.json()

    # Store the FHIR JSON along with other patient data in the database
    patient = Patient(
        name=patient_data.name,
        age=patient_data.age,
        diagnosis=patient_data.diagnosis,
        fhir_identifier=fhir_json,
    )
    app.db.add(patient)
    app.db.commit()

    return {"message": "Patient created successfully"}

@app.get("/")
def read_root():
    return {"Hello": "World"}
