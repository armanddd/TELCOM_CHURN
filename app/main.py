import uuid
from fastapi import FastAPI, Request, HTTPException, status, Form
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
async def make_prediction(tenureForm: float = Form(...), genderSelect: str = Form(...),
                          seniorCitizenSelect: float = Form(...),
                          partnerSelect: str = Form(...), dependentsSelect: str = Form(...),
                          phoneServiceSelect: str = Form(...), multipleLinesSelect: str = Form(...),
                          internetServiceSelect: str = Form(...), onlineSecuritySelect: str = Form(...),
                          onlineBackupSelect: str = Form(...), deviceProtectionSelect: str = Form(...),
                          techSupportSelect: str = Form(...), streamingTVSelect: str = Form(...),
                          streamingMoviesSelect: str = Form(...),
                          contractTypeSelect: str = Form(...), paymentMethodSelect: str = Form(...),
                          paperlessBillingSelect: str = Form(...),
                          monthlyChargesForm: float = Form(...), totalChargesForm: float = Form(...)):
    import joblib
    import pandas as pd
    global session_id

    if session_id is None:
        return RedirectResponse(url="/", status_code=303)

    services_pca = joblib.load("static/models/services_pca.joblib")
    voting_clf = joblib.load("static/models/pca_voting_classifier.joblib")
    scaler = joblib.load("static/models/scaler.joblib")

    ############################# PCA Part #############################
    pca_data = {"PhoneService": phoneServiceSelect, "MultipleLines": multipleLinesSelect,
                "InternetService": internetServiceSelect, "OnlineSecurity": onlineSecuritySelect,
                "OnlineBackup": onlineBackupSelect, "DeviceProtection": deviceProtectionSelect,
                "TechSupport": techSupportSelect, "StreamingTV": streamingTVSelect,
                "StreamingMovies": streamingMoviesSelect}

    pca_df = pd.DataFrame(data=pca_data, columns=['PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                                                  'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
                                                  'StreamingMovies'], index=["1"])
    pca_df = pd.get_dummies(pca_df)

    pca_example = pd.DataFrame(columns=['PhoneService_No', 'PhoneService_Yes', 'MultipleLines_No',
                                        'MultipleLines_No phone service', 'MultipleLines_Yes',
                                        'InternetService_DSL', 'InternetService_Fiber optic',
                                        'InternetService_No', 'OnlineSecurity_No',
                                        'OnlineSecurity_No internet service', 'OnlineSecurity_Yes',
                                        'OnlineBackup_No', 'OnlineBackup_No internet service',
                                        'OnlineBackup_Yes', 'DeviceProtection_No',
                                        'DeviceProtection_No internet service', 'DeviceProtection_Yes',
                                        'TechSupport_No', 'TechSupport_No internet service', 'TechSupport_Yes',
                                        'StreamingTV_No', 'StreamingTV_No internet service', 'StreamingTV_Yes',
                                        'StreamingMovies_No', 'StreamingMovies_No internet service',
                                        'StreamingMovies_Yes'])

    # set a row with only values of 0
    pca_example.loc[1] = 0

    # merge the two dfs so we have a replica of the training df with all the possible values
    pca_df = pd.merge(pca_example, pca_df, how="right").fillna(0)

    # store value of the services pca for later concat
    X_pca = pd.DataFrame(services_pca.transform(pca_df), columns=['PC1'])
    ############################# PCA Part #############################

    ############################# Voting Part #############################
    voting_data = {'gender': genderSelect, 'SeniorCitizen': seniorCitizenSelect, 'Partner': partnerSelect,
                   'Dependents': dependentsSelect, 'tenure': tenureForm,
                   'Contract': contractTypeSelect, 'PaperlessBilling': paperlessBillingSelect,
                   'PaymentMethod': paymentMethodSelect, 'MonthlyCharges': monthlyChargesForm,
                   'TotalCharges': totalChargesForm}

    voting_df = pd.DataFrame(data=voting_data, columns=['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
                                                        'Contract', 'PaperlessBilling', 'PaymentMethod',
                                                        'MonthlyCharges',
                                                        'TotalCharges'], index=["1"])

    # change cast types so get dummies doesnt create additional columns
    voting_df = voting_df.astype(
        {'SeniorCitizen': 'float', 'tenure': 'float', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})
    voting_df = pd.get_dummies(voting_df)

    voting_example = pd.DataFrame(columns=['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges',
                                           'gender_Female', 'gender_Male', 'Partner_No', 'Partner_Yes',
                                           'Dependents_No', 'Dependents_Yes', 'Contract_Month-to-month',
                                           'Contract_One year', 'Contract_Two year', 'PaperlessBilling_No',
                                           'PaperlessBilling_Yes', 'PaymentMethod_Bank transfer (automatic)',
                                           'PaymentMethod_Credit card (automatic)',
                                           'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check'])
    # change cast types so get dummies doesnt create additional columns
    voting_example = voting_example.astype(
        {'SeniorCitizen': 'int', 'tenure': 'int', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})
    # set a row with only values of 0
    voting_example.loc[1] = 0

    # print("vdf", voting_df, "\n\n\nvex",voting_example)
    # merge the two dfs so we have a replica of the training df with all the possible values
    voting_df = pd.merge(voting_example, voting_df, how="right").fillna(0)

    print(voting_df)

    voting_df = pd.DataFrame(scaler.transform(voting_df), columns=voting_df.columns.values)
    voting_df["PC1"] = X_pca[["PC1"]]
    print(voting_df)
    print(voting_clf.predict(voting_df))
    ############################# Voting Part #############################
    return RedirectResponse(url="/?prediction=" + str(voting_clf.predict(voting_df)[0]), status_code=303)
