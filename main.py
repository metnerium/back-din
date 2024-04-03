from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt

# Подключение к базе данных
engine = create_engine("postgresql://app_user:Noneto57!@localhost/app_db")
Session = sessionmaker(bind=engine)

# Создание базовой модели
Base = declarative_base()

# Шифрование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секретный ключ для JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Модель пользователя SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

# Модель курса SQLAlchemy
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Модель записи на курс SQLAlchemy
class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    user = relationship("User", backref="enrollments")
    course = relationship("Course", backref="enrollments")

# Модели Pydantic
class UserModel(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

class CourseModel(BaseModel):
    id: int
    name: str
    description: str
    price: int
    created_at: datetime

    class Config:
        orm_mode = True

class EnrollmentModel(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrollment_date: datetime
    completion_date: Optional[datetime] = None

    class Config:
        orm_mode = True

# Создание таблиц в базе данных
Base.metadata.create_all(engine)

# Создание экземпляра FastAPI
app = FastAPI()

# Dependency для получения сессии
def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

# Функция для создания JWT токена
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency для получения пользователя по токену
def get_current_user(token: str = Depends(None), session=Depends(get_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

# Обработчики для пользователей
@app.post("/register", response_model=UserModel)
def register(username: str, email: str, password: str, session=Depends(get_session)):
    existing_user = session.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    hashed_password = pwd_context.hash(password)
    user = User(username=username, email=email, password=hashed_password)
    session.add(user)
    session.commit()
    return user

@app.post("/login")
def login(username: str, password: str, session=Depends(get_session)):
    user = session.query(User).filter(User.username == username).first()
    if not user or not user.verify_password(password):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token}

# Обработчики для курсов
@app.get("/courses", response_model=List[CourseModel])
def get_courses(session=Depends(get_session)):
    return session.query(Course).all()

# Обработчики для записей на курсы
@app.get("/my_courses", response_model=List[CourseModel])
def get_my_courses(user=Depends(get_current_user), session=Depends(get_session)):
    courses = [enrollment.course for enrollment in user.enrollments]
    return courses