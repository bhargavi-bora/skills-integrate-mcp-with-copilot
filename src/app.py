"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database setup
DATABASE_URL = "sqlite:///./activities.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for departments and teams
department_teams = Table('department_teams', Base.metadata,
    Column('department_id', Integer, ForeignKey('departments.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)

# Models
class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    schedule = Column(String)
    max_participants = Column(Integer)

    participants = relationship("ActivityParticipant", back_populates="activity")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)

    activities = relationship("ActivityParticipant", back_populates="user")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    coach = relationship("User")
    players = relationship("Player", back_populates="team")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    head_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    head = relationship("User")
    teams = relationship("Team", secondary="department_teams")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    user = relationship("User")
    team = relationship("Team", back_populates="players")

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    sport = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    status = Column(String, default="scheduled")  # scheduled, ongoing, completed

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    winner_team_id = Column(Integer, ForeignKey("teams.id"))
    loser_team_id = Column(Integer, ForeignKey("teams.id"))
    score = Column(String)

    tournament = relationship("Tournament")
    winner = relationship("Team", foreign_keys=[winner_team_id])
    loser = relationship("Team", foreign_keys=[loser_team_id])

class ActivityParticipant(Base):
    __tablename__ = "activity_participants"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    activity = relationship("Activity", back_populates="participants")
    user = relationship("User", back_populates="activities")

# Create tables
Base.metadata.create_all(bind=engine)

# Seed initial data
def seed_data():
    with SessionLocal() as session:
        # Check if data already exists
        if session.query(Activity).first():
            return

        # Initial activities
        activities_data = [
            {"name": "Chess Club", "description": "Learn strategies and compete in chess tournaments", "schedule": "Fridays, 3:30 PM - 5:00 PM", "max_participants": 12, "participants": ["michael@mergington.edu", "daniel@mergington.edu"]},
            {"name": "Programming Class", "description": "Learn programming fundamentals and build software projects", "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", "max_participants": 20, "participants": ["emma@mergington.edu", "sophia@mergington.edu"]},
            {"name": "Gym Class", "description": "Physical education and sports activities", "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", "max_participants": 30, "participants": ["john@mergington.edu", "olivia@mergington.edu"]},
            {"name": "Soccer Team", "description": "Join the school soccer team and compete in matches", "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", "max_participants": 22, "participants": ["liam@mergington.edu", "noah@mergington.edu"]},
            {"name": "Basketball Team", "description": "Practice and play basketball with the school team", "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["ava@mergington.edu", "mia@mergington.edu"]},
            {"name": "Art Club", "description": "Explore your creativity through painting and drawing", "schedule": "Thursdays, 3:30 PM - 5:00 PM", "max_participants": 15, "participants": ["amelia@mergington.edu", "harper@mergington.edu"]},
            {"name": "Drama Club", "description": "Act, direct, and produce plays and performances", "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 20, "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]},
            {"name": "Math Club", "description": "Solve challenging problems and participate in math competitions", "schedule": "Tuesdays, 3:30 PM - 4:30 PM", "max_participants": 10, "participants": ["james@mergington.edu", "benjamin@mergington.edu"]},
            {"name": "Debate Team", "description": "Develop public speaking and argumentation skills", "schedule": "Fridays, 4:00 PM - 5:30 PM", "max_participants": 12, "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]}
        ]

        for act_data in activities_data:
            participants = act_data.pop("participants")
            activity = Activity(**act_data)
            session.add(activity)
            session.flush()  # to get id
            for email in participants:
                user = session.query(User).filter(User.email == email).first()
                if not user:
                    user = User(email=email)
                    session.add(user)
                    session.flush()
                participant = ActivityParticipant(activity_id=activity.id, user_id=user.id)
                session.add(participant)
        session.commit()

seed_data()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with SessionLocal() as session:
        activities_db = session.query(Activity).all()
        result = {}
        for act in activities_db:
            participants = [p.user.email for p in act.participants]
            result[act.name] = {
                "description": act.description,
                "schedule": act.schedule,
                "max_participants": act.max_participants,
                "participants": participants
            }
        return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with SessionLocal() as session:
        # Get activity
        activity = session.query(Activity).filter(Activity.name == activity_name).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get or create user
        user = session.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            session.add(user)
            session.flush()

        # Check if already signed up
        existing = session.query(ActivityParticipant).filter(
            ActivityParticipant.activity_id == activity.id,
            ActivityParticipant.user_id == user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        # Check max participants
        current_count = session.query(ActivityParticipant).filter(ActivityParticipant.activity_id == activity.id).count()
        if current_count >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        # Add participant
        participant = ActivityParticipant(activity_id=activity.id, user_id=user.id)
        session.add(participant)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with SessionLocal() as session:
        # Get activity
        activity = session.query(Activity).filter(Activity.name == activity_name).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # Get user
        user = session.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="Student not found")

        # Get participant
        participant = session.query(ActivityParticipant).filter(
            ActivityParticipant.activity_id == activity.id,
            ActivityParticipant.user_id == user.id
        ).first()
        if not participant:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        # Remove participant
        session.delete(participant)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
