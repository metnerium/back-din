from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Course, Enrollment

# Создание соединения с базой данных
engine = create_engine('postgresql://app_user:Noneto57!@localhost/app_db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Регистрация пользователя
@app.post('/register')
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    # Проверка уникальности username и email
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return {'error': 'Username or email already taken'}

    # Создание нового пользователя
    user = User(username=username, email=email, password=password)
    db.add(user)
    db.commit()
    return {'message': 'User registered successfully'}


# Авторизация пользователя
@app.post('/login')
def login(username: str, password: str, db: Session = Depends(get_db)):
    # Поиск пользователя по username
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        return {'error': 'Invalid username or password'}

    # Возвращение информации о пользователе
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }


# Запись на курс
@app.post('/enroll')
def enroll(user_id: int, course_id: int, db: Session = Depends(get_db)):
    # Проверка существования пользователя и курса
    user = db.query(User).get(user_id)
    course = db.query(Course).get(course_id)
    if not user or not course:
        return {'error': 'User or course not found'}

    # Создание записи на курс
    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    return {'message': 'Enrollment successful'}


# Получение информации о записях на курсы
@app.get('/enrollments')
def get_enrollments(user_id: int, db: Session = Depends(get_db)):
    # Получение записей на курсы для пользователя
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    # Формирование ответа
    result = []
    for enrollment in enrollments:
        course = enrollment.course
        result.append({
            'course_id': course.id,
            'course_name': course.name,
            'course_description': course.description,
            'course_price': course.price,
            'enrollment_date': enrollment.enrollment_date
        })

    return result
