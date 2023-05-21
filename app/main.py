import uuid
from io import BytesIO

from fastapi import FastAPI, Request, HTTPException, status, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from databases import Database
from argon2 import PasswordHasher, exceptions
from io import BytesIO
import pandas as pd
import secrets
import uvicorn
import os

from starlette.responses import JSONResponse

app = FastAPI()
database = Database("sqlite:///./test.db")
session = {}
session_id = None
ph = PasswordHasher()
fileDf = pd.DataFrame()


@app.on_event("startup")
async def create_tables():
    await database.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            api_key TEXT NOT NULL,
            first_login INTEGER DEFAULT 1
        )
    """)
    await database.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requested_user TEXT NOT NULL,
                requested_time DATETIME NOT NULL,
                gender TEXT NOT NULL,
                SeniorCitizen TEXT NOT NULL,
                Partner TEXT NOT NULL,
                Dependents TEXT NOT NULL,
                tenure TEXT NOT NULL,
                PhoneService TEXT NOT NULL,
                MultipleLines TEXT NOT NULL,
                InternetService TEXT NOT NULL,
                OnlineSecurity TEXT NOT NULL,
                OnlineBackup TEXT NOT NULL,
                DeviceProtection TEXT NOT NULL,
                TechSupport TEXT NOT NULL,
                StreamingTV TEXT NOT NULL,
                StreamingMovies TEXT NOT NULL,
                Contract TEXT NOT NULL,
                PaperlessBilling TEXT NOT NULL,
                PaymentMethod TEXT NOT NULL,
                MonthlyCharges TEXT NOT NULL,
                TotalCharges TEXT NOT NULL,
                predictions TEXT NOT NULL
            )
        """)
    await database.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requested_user TEXT NOT NULL,
                    requested_time DATETIME NOT NULL,
                    requested_origin TEXT NOT NULL,
                    requested_details TEXT NOT NULL,
                    requested_prediction TEXT NULL,
                    requested_prediction_file_path TEXT NULL
                )
            """)
    

# Get the directory path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the static files directory
static_dir = os.path.join(current_dir, "static")
# Mount static files directory for CSS, JS, and images
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2Templates for rendering templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request, "session": session, "session_id": session_id})


@app.get("/history", response_class=HTMLResponse)
async def read_home(request: Request):
    global session, session_id
    query = """
                SELECT *
                FROM requests
                WHERE requested_user = :requested_user
            """
    values = {
        "requested_user": session[session_id]['username']
    }
    rows = await database.fetch_all(query=query, values=values)
    if session_id not in session:
        return RedirectResponse(url="/", status_code=302)
    else:
        return templates.TemplateResponse("history.html", {"request": request, "session": session, "session_id": session_id, "history_rows": rows})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    if session_id not in session:
        return templates.TemplateResponse("login.html", {"request": request})
    else:
        return RedirectResponse(url="/", status_code=302)


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
            INSERT INTO users (username, password, email, api_key)
            VALUES (:username, :password, :email, :api_key)
        """
    values = {
        "username": username,
        "email": email,
        "password": ph.hash(password),
        "api_key": secrets.token_hex(16)
    }
    await database.execute(query=query, values=values)

    return RedirectResponse(url="/", status_code=303)


@app.post('/login_user')
async def login_user(email: str = Form(...), password: str = Form(...)):
    global session, session_id
    query = """
            SELECT id, username, password, email, first_login, api_key
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
    session[session_id] = {'username': row[1], 'email': row[3], 'logged_in': True, 'first_login': row[4],
                           'api_key': row[5]}

    return RedirectResponse(url="/", status_code=303)


@app.post('/remove_first_login')
async def remove_first_login():
    global session_id
    query = "UPDATE users SET first_login = 0 WHERE username = :username"
    values = {'username': session[session_id]['username']}
    await database.execute(query, values)
    session[session_id]['first_login'] = 0


@app.post('/make_prediction')
async def make_prediction(tenureForm: float = Form(None), genderSelect: str = Form(None),
                          seniorCitizenSelect: float = Form(None),
                          partnerSelect: str = Form(None), dependentsSelect: str = Form(None),
                          phoneServiceSelect: str = Form(None), multipleLinesSelect: str = Form(None),
                          internetServiceSelect: str = Form(None), onlineSecuritySelect: str = Form(None),
                          onlineBackupSelect: str = Form(None), deviceProtectionSelect: str = Form(None),
                          techSupportSelect: str = Form(None), streamingTVSelect: str = Form(None),
                          streamingMoviesSelect: str = Form(None),
                          contractTypeSelect: str = Form(None), paymentMethodSelect: str = Form(None),
                          paperlessBillingSelect: str = Form(None),
                          monthlyChargesForm: float = Form(None), totalChargesForm: float = Form(None),
                          api_key: str = Form(None), templateFile: UploadFile = File(None)):
    import joblib
    global session_id, fileDf
    # if user not logged in then check for api key
    if session_id not in session:
        query = """
                    SELECT id, username, password, email, first_login
                    FROM users
                    WHERE api_key = :api_key
                """
        values = {
            "api_key": api_key
        }
        row = await database.fetch_one(query=query, values=values)
        if row is None:
            return RedirectResponse(url="/", status_code=401)

    rf_model = joblib.load("static/models/rf_best.joblib")
    scaler = joblib.load("static/models/min_max_scaler.joblib")

    # store for later use
    # file_df = pd.read_excel(BytesIO(await templateFile.read()), engine='openpyxl')

    data_df = await transformDfForPrediction(locals())

    ############################# SCALER TRANSFORMATION #############################
    # select independent variables
    features = data_df.columns.values
    data_df = pd.DataFrame(scaler.transform(data_df))
    data_df.columns = features
    ############################# SCALER TRANSFORMATION #############################

    # define api values
    try:
        username = session[session_id]["username"]
    except KeyError:
        username = row[1]

    ############################# Database Part ###########################
    predictions_query = """INSERT INTO predictions ("requested_user", "requested_time", "gender", "SeniorCitizen", "Partner", 
    "Dependents", "tenure", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup", 
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling", 
    "PaymentMethod", "MonthlyCharges", "TotalCharges", "predictions") VALUES (:username, DATE('now'), :gender, 
    :senior_citizen, :partner, :dependents, :tenure, :phone_service, :multiple_lines, :internet_service, 
    :online_security, :online_backup, :device_protection, :tech_support, :streaming_tv, :streaming_movies, :contract, 
    :paperless_billing, :payment_method, :monthly_charges, :total_charges, :prediction)"""

    requests_query = """INSERT INTO requests ("requested_user", "requested_time", "requested_origin", 
    "requested_details", "requested_prediction", "requested_prediction_file_path") VALUES (:requested_user, 
    DATE('now'), :requested_origin, :requested_details, :requested_prediction, :requested_prediction_file_path)
    """

    if templateFile is not None and templateFile.filename:
        import glob
        fileDf['Churn'] = rf_model.predict(data_df)
        data_df['Churn'] = rf_model.predict(data_df)
        path = f"static/files/{username}_{len(glob.glob(f'static/files/{username}*'))}_ChurnPrediction.xlsx"
        fileDf.to_excel(path)

        for index, row in fileDf.iterrows():
            predictions_values = {
                "username": username,
                "gender": row["gender"],
                "senior_citizen": row["SeniorCitizen"],
                "partner": row["Partner"],
                "dependents": row["Dependents"],
                "tenure": row["tenure"],
                "phone_service": row["PhoneService"],
                "multiple_lines": row["MultipleLines"],
                "internet_service": row["InternetService"],
                "online_security": row["OnlineSecurity"],
                "online_backup": row["OnlineBackup"],
                "device_protection": row["DeviceProtection"],
                "tech_support": row["TechSupport"],
                "streaming_tv": row["StreamingTV"],
                "streaming_movies": row["StreamingMovies"],
                "contract": row["Contract"],
                "paperless_billing": row["PaperlessBilling"],
                "payment_method": row["PaymentMethod"],
                "monthly_charges": row["MonthlyCharges"],
                "total_charges": row["TotalCharges"],
                "prediction": str(data_df['Churn'].iloc[index])
            }

        requests_values = {
            "requested_user": username,
            "requested_origin": "API" if api_key else "FORM",
            "requested_details": "Template Prediction" if templateFile else "Single Prediction",
            "requested_prediction": None,
            "requested_prediction_file_path": path
        }

        await database.execute(predictions_query, predictions_values)
        await database.execute(requests_query, requests_values)
    else:
        predictions_values = {
            "username": username,
            "gender": genderSelect,
            "senior_citizen": seniorCitizenSelect,
            "partner": partnerSelect,
            "dependents": dependentsSelect,
            "tenure": tenureForm,
            "phone_service": phoneServiceSelect,
            "multiple_lines": multipleLinesSelect,
            "internet_service": internetServiceSelect,
            "online_security": onlineSecuritySelect,
            "online_backup": onlineBackupSelect,
            "device_protection": deviceProtectionSelect,
            "tech_support": techSupportSelect,
            "streaming_tv": streamingTVSelect,
            "streaming_movies": streamingMoviesSelect,
            "contract": contractTypeSelect,
            "paperless_billing": paperlessBillingSelect,
            "payment_method": paymentMethodSelect,
            "monthly_charges": monthlyChargesForm,
            "total_charges": totalChargesForm,
            "prediction": str(rf_model.predict(data_df)[0])
        }

        requests_values = {
            "requested_user": username,
            "requested_origin": "API" if api_key else "FORM",
            "requested_details": "Template Prediction" if templateFile is not None and templateFile.filename else "Single Prediction",
            "requested_prediction": str(rf_model.predict(data_df)[0]),
            "requested_prediction_file_path": None
        }

        await database.execute(predictions_query, predictions_values)
        await database.execute(requests_query, requests_values)

    ############################# Database Part ###########################
    if api_key:
        if templateFile:
            return JSONResponse(f"Your template with the predictions can be found at {path}")
        else:
            return JSONResponse(content={"churn_prediction": str(rf_model.predict(data_df)[0])})
    else:
        if templateFile.filename:
            return JSONResponse(f"Your template with the predictions can be found at {path}")
        else:
            return RedirectResponse(url="/?prediction=" + str(rf_model.predict(data_df)[0]), status_code=303)


async def transformDfForPrediction(args):
    global fileDf

    df = pd.DataFrame(columns=['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges',
                               'MultipleLines_No', 'MultipleLines_No phone service',
                               'MultipleLines_Yes', 'InternetService_DSL',
                               'InternetService_Fiber optic', 'InternetService_No',
                               'OnlineSecurity_No', 'OnlineSecurity_No internet service',
                               'OnlineSecurity_Yes', 'OnlineBackup_No',
                               'OnlineBackup_No internet service', 'OnlineBackup_Yes',
                               'DeviceProtection_No', 'DeviceProtection_No internet service',
                               'DeviceProtection_Yes', 'TechSupport_No',
                               'TechSupport_No internet service', 'TechSupport_Yes', 'StreamingTV_No',
                               'StreamingTV_No internet service', 'StreamingTV_Yes',
                               'StreamingMovies_No', 'StreamingMovies_No internet service',
                               'StreamingMovies_Yes', 'Contract_Month-to-month', 'Contract_One year',
                               'Contract_Two year', 'PaymentMethod_Bank transfer (automatic)',
                               'PaymentMethod_Credit card (automatic)',
                               'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check',
                               'gender_Female', 'gender_Male', 'Partner_No', 'Partner_Yes',
                               'Dependents_No', 'Dependents_Yes', 'PaperlessBilling_No',
                               'PaperlessBilling_Yes', 'PhoneService_No', 'PhoneService_Yes'])

    df = df.astype(
        {'SeniorCitizen': 'int', 'tenure': 'float', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})

    # transform if we use form data
    if args['templateFile'] is None or not args['templateFile'].filename:
        data = {'gender': args['genderSelect'], 'SeniorCitizen': args['seniorCitizenSelect'],
                'Partner': args['partnerSelect'],
                'Dependents': args['dependentsSelect'], 'tenure': args['tenureForm'],
                'Contract': args['contractTypeSelect'], 'PaperlessBilling': args['paperlessBillingSelect'],
                'PaymentMethod': args['paymentMethodSelect'], 'MonthlyCharges': args['monthlyChargesForm'],
                'TotalCharges': args['totalChargesForm']}
        data_df = pd.DataFrame(data=data, columns=['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
                                                   'Contract', 'PaperlessBilling', 'PaymentMethod',
                                                   'MonthlyCharges',
                                                   'TotalCharges'], index=["1"])
        data_df = data_df.astype(
            {'SeniorCitizen': 'float', 'tenure': 'float', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})
    # transform if we use FILE data
    else:
        templateFileExtension = args['templateFile'].filename.split(".")[-1]

        if templateFileExtension != "xlsx" and templateFileExtension != "csv" and templateFileExtension != "xls":
            return JSONResponse("Your file needs to be of the type xlsx, csv or xls.")

        data_df = pd.read_excel(BytesIO(await args['templateFile'].read()), engine='openpyxl')
        fileDf = data_df

    data_df = pd.get_dummies(data_df)
    data_df = pd.merge(df, data_df, how="right").fillna(0)

    return data_df[['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges',
                    'MultipleLines_No', 'MultipleLines_No phone service',
                    'MultipleLines_Yes', 'InternetService_DSL',
                    'InternetService_Fiber optic', 'InternetService_No',
                    'OnlineSecurity_No', 'OnlineSecurity_No internet service',
                    'OnlineSecurity_Yes', 'OnlineBackup_No',
                    'OnlineBackup_No internet service', 'OnlineBackup_Yes',
                    'DeviceProtection_No', 'DeviceProtection_No internet service',
                    'DeviceProtection_Yes', 'TechSupport_No',
                    'TechSupport_No internet service', 'TechSupport_Yes',
                    'StreamingTV_No', 'StreamingTV_No internet service',
                    'StreamingTV_Yes', 'StreamingMovies_No',
                    'StreamingMovies_No internet service', 'StreamingMovies_Yes',
                    'Contract_Month-to-month', 'Contract_One year',
                    'Contract_Two year', 'PaymentMethod_Bank transfer (automatic)',
                    'PaymentMethod_Credit card (automatic)',
                    'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check',
                    'gender_Female', 'gender_Male', 'Partner_No', 'Partner_Yes',
                    'Dependents_No', 'Dependents_Yes', 'PaperlessBilling_No',
                    'PaperlessBilling_Yes', 'PhoneService_No', 'PhoneService_Yes']]

if __name__ == "__main__":
    uvicorn.run(app)
