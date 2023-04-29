import uuid
from fastapi import FastAPI, Request, HTTPException, status, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from databases import Database
from argon2 import PasswordHasher, exceptions

app = FastAPI()
database = Database("sqlite:///./test.db")
session = {}
session_id = None
ph = PasswordHasher()


@app.on_event("startup")
async def create_tables():
    await database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)


# Mount static files directory for CSS, JS, and images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2Templates for rendering templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    print(request, session)
    return templates.TemplateResponse("base.html", {"request": request, "session": session, "session_id": session_id})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    if session_id not in session:
        return templates.TemplateResponse("login.html", {"request": request})
    else:
        return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    global session
    global session_id

    session = {}
    session_id = None

    return RedirectResponse("/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    if session_id not in session:
        return templates.TemplateResponse("register.html", {"request": request})
    else:
        return RedirectResponse(url="/", status_code=303)


@app.post('/register_user', status_code=201)
async def register_user(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    query = """
            INSERT INTO users (username, password, email)
            VALUES (:username, :password, :email)
        """
    values = {
        "username": username,
        "email": email,
        "password": ph.hash(password)
    }
    user_id = await database.execute(query=query, values=values)
    response = RedirectResponse(url="/", status_code=303)
    # response.set_cookie("user_id", user_id)
    return response


@app.post('/login_user')
async def login_user(email: str = Form(...), password: str = Form(...)):
    global session, session_id
    query = """
            SELECT id, username, password, email
            FROM users
            WHERE email = :email
        """
    values = {
        "email": email
    }
    row = await database.fetch_one(query=query, values=values)
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    else:
        try:
            ph.verify(row[2], password)
        except exceptions.VerifyMismatchError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    session_id = str(uuid.uuid4())
    session[session_id] = {'username': row[1], 'email': row[3], 'logged_in': True}

    return RedirectResponse(url="/", status_code=303)


@app.post('/make_prediction')
async def make_prediction(tenureForm: str = Form(...), genderSelect: str = Form(...), seniorCitizenSelect: str = Form(...),
                          partnerSelect: str = Form(...), dependentsSelect: str = Form(...), additionalServicesSelect: str = Form(...),
                          contractTypeSelect: str = Form(...), paymentMethodSelect: str = Form(...), paperlessBillingSelect: str = Form(...),
                          monthlyChargesForm: str = Form(...), totalChargesForm: str = Form(...)):
    import joblib
    global session_id

    services_pca = joblib.load("static/models/services_pca.joblib")
    voting_clf = joblib.load("static/models/pca_voting_classifier.joblib")


    if session_id is None:
        return RedirectResponse(url="/", status_code=303)

    return RedirectResponse(url="/", status_code=303)
