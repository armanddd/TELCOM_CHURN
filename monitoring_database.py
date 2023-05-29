import numpy as np
from databases import Database
from scipy.stats import skew
import datetime
import joblib
import asyncio
import pandas as pd
import smtplib

# RETRIEVE ROWS FROM DB
db = Database("sqlite:///./app/test.db")
today = datetime.date.today()

query = f"""
            SELECT *
            FROM predictions
            WHERE requested_time >= '{today}'
        """

SKEW_THRESHOLD = 0.7


async def get_from_db(q):
    return await db.fetch_all(query=q)


rows = asyncio.run(get_from_db(q=query))

# IMPORT THE MODEL USED BY THE WEB APP
# rf_model = joblib.load("app/static/models/rf_best.joblib")
# scaler = joblib.load("app/static/models/min_max_scaler.joblib")
#
#
# def transform_db_to_df(my_rows):
#     df = pd.DataFrame(columns=['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges',
#                                'MultipleLines_No', 'MultipleLines_No phone service',
#                                'MultipleLines_Yes', 'InternetService_DSL',
#                                'InternetService_Fiber optic', 'InternetService_No',
#                                'OnlineSecurity_No', 'OnlineSecurity_No internet service',
#                                'OnlineSecurity_Yes', 'OnlineBackup_No',
#                                'OnlineBackup_No internet service', 'OnlineBackup_Yes',
#                                'DeviceProtection_No', 'DeviceProtection_No internet service',
#                                'DeviceProtection_Yes', 'TechSupport_No',
#                                'TechSupport_No internet service', 'TechSupport_Yes', 'StreamingTV_No',
#                                'StreamingTV_No internet service', 'StreamingTV_Yes',
#                                'StreamingMovies_No', 'StreamingMovies_No internet service',
#                                'StreamingMovies_Yes', 'Contract_Month-to-month', 'Contract_One year',
#                                'Contract_Two year', 'PaymentMethod_Bank transfer (automatic)',
#                                'PaymentMethod_Credit card (automatic)',
#                                'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check',
#                                'gender_Female', 'gender_Male', 'Partner_No', 'Partner_Yes',
#                                'Dependents_No', 'Dependents_Yes', 'PaperlessBilling_No',
#                                'PaperlessBilling_Yes', 'PhoneService_No', 'PhoneService_Yes'])
#
#     df = df.astype(
#         {'SeniorCitizen': 'int', 'tenure': 'float', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})
#
#     # Create an empty array to store the DataFrames
#     concatenated_data = []
#
#     for row in my_rows:
#         data = {'gender': row[3], 'SeniorCitizen': row[4],
#                 'Partner': row[5],
#                 'Dependents': row[6], 'tenure': row[7],
#                 'Contract': row[17], 'PaperlessBilling': row[18],
#                 'PaymentMethod': row[19], 'MonthlyCharges': row[20],
#                 'TotalCharges': row[21]}
#         data_df = pd.DataFrame(data=data, columns=['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
#                                                    'Contract', 'PaperlessBilling', 'PaymentMethod',
#                                                    'MonthlyCharges',
#                                                    'TotalCharges'], index=["1"])
#         concatenated_data.append(data_df)
#
#     data_df = pd.concat(concatenated_data)
#
#     data_df = data_df.astype(
#         {'SeniorCitizen': 'float', 'tenure': 'float', 'MonthlyCharges': 'float', 'TotalCharges': 'float'})
#
#     data_df = pd.get_dummies(data_df)
#     data_df = pd.merge(df, data_df, how="right").fillna(0)
#
#     return data_df[['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges',
#                     'MultipleLines_No', 'MultipleLines_No phone service',
#                     'MultipleLines_Yes', 'InternetService_DSL',
#                     'InternetService_Fiber optic', 'InternetService_No',
#                     'OnlineSecurity_No', 'OnlineSecurity_No internet service',
#                     'OnlineSecurity_Yes', 'OnlineBackup_No',
#                     'OnlineBackup_No internet service', 'OnlineBackup_Yes',
#                     'DeviceProtection_No', 'DeviceProtection_No internet service',
#                     'DeviceProtection_Yes', 'TechSupport_No',
#                     'TechSupport_No internet service', 'TechSupport_Yes',
#                     'StreamingTV_No', 'StreamingTV_No internet service',
#                     'StreamingTV_Yes', 'StreamingMovies_No',
#                     'StreamingMovies_No internet service', 'StreamingMovies_Yes',
#                     'Contract_Month-to-month', 'Contract_One year',
#                     'Contract_Two year', 'PaymentMethod_Bank transfer (automatic)',
#                     'PaymentMethod_Credit card (automatic)',
#                     'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check',
#                     'gender_Female', 'gender_Male', 'Partner_No', 'Partner_Yes',
#                     'Dependents_No', 'Dependents_Yes', 'PaperlessBilling_No',
#                     'PaperlessBilling_Yes', 'PhoneService_No', 'PhoneService_Yes']]
#
#
# def transform_data_to_df(data_path):
#     df = pd.read_csv(data_path)
#
#     # Converting my original dataset df Total Charges to a numerical data type.
#     df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors='coerce')
#
#     # Remove my original dataset df if total charges is 0 (new client with one year or two years contract only)
#     df = df[~df["TotalCharges"].isnull()]
#
#     # Remove my original dataset df Customer ID Column (first column)
#     df = df.iloc[:, 1:]
#
#     # Convertin my original dataset predictor variable in a binary numeric variable
#     df['Churn'].replace(to_replace='Yes', value=1, inplace=True)
#     df['Churn'].replace(to_replace='No', value=0, inplace=True)
#
#     one_hot_encoding_columns = ['MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
#                                 'DeviceProtection',
#                                 'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract', 'PaymentMethod', 'gender',
#                                 'Partner', 'Dependents', 'PaperlessBilling', 'PhoneService']
#
#     encoded_df = pd.get_dummies(df, columns=one_hot_encoding_columns).astype(float)
#
#     return encoded_df
#
#
# storing my df from db
# my_db_df = transform_db_to_df(rows)
#
# # storing my original dataset df
# my_og_df = transform_data_to_df('WA_Fn-UseC_-Telco-Customer-Churn.csv')
#
# my_db_X = my_db_df
# my_og_X = my_og_df.drop(columns="Churn", axis=1)
#


#
# If the skewness value is close to 0, it indicates that the distribution is approximately symmetric.
# If the skewness value is negative, it indicates that the distribution is skewed to the left (left-tailed), with a longer or fatter tail on the left side.
# If the skewness value is positive, it indicates that the distribution is skewed to the right (right-tailed), with a longer or fatter tail on the right side.
my_og_df = pd.read_csv('WA_Fn-UseC_-Telco-Customer-Churn.csv')

# monthly charges must be negative as skewed on the left
# Converting Total Charges to a numerical data type.
my_og_df["TotalCharges"] = pd.to_numeric(my_og_df["TotalCharges"], errors='coerce')

# Remove if total charges is 0 (new client with one year or two years contract only)
my_og_df = my_og_df[~my_og_df["TotalCharges"].isnull()]

# Remove Customer ID Column (first column)
my_og_df = my_og_df.iloc[:, 1:]

one_hot_encoding_columns = ['MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                            'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract', 'PaymentMethod', 'gender',
                            'Partner', 'Dependents', 'PaperlessBilling', 'PhoneService']

my_og_df = pd.get_dummies(my_og_df, columns=one_hot_encoding_columns, dtype=float)

# Convertin the predictor variable in a binary numeric variable
my_og_df['Churn'].replace(to_replace='Yes', value=1, inplace=True)
my_og_df['Churn'].replace(to_replace='No', value=0, inplace=True)

# TODO for all predictions of churned clients in database check if tenure skew is the same as here
my_og_df_skew = skew(my_og_df[my_og_df['Churn'] == 1]['tenure'])  # 1.148357706697273

# TODO for all predictions of not churned clients in database check if tenure skew is the same as here
# print(my_og_df[my_og_df['Churn'] == 0]['tenure'].skew())

# X_train values of model before train


tenure_skew_check = []

for row in rows:
    if row[-1] == "1.0":
        tenure_skew_check.append(float(row[7]))


if skew(np.array(tenure_skew_check)) < my_og_df_skew * SKEW_THRESHOLD:
    email_string = '\n'.join([''.join(str(t)) for t in rows])
    # EMAIL SENDING REGARDING THE SKEW DATA DRIFT
    sender = "Telco Churn Monitoring <monitoring@telcochurn.com>"
    receiver = "Admin <admin@telcochurn.com>"

    message = f"""\
    Subject: Potential Data Drift
    To: {receiver}
    From: {sender}
    
    Potential data drift has been detected on the following values:\n {email_string} """

    with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
        server.login("651db0e982bf5e", "a8b9bdaa41493a")
        server.sendmail(sender, receiver, message)

##############################SKEW TEST##################################
# import numpy as np
# # Generate skewed data
# data_right_skew = np.random.exponential(scale=2, size=1000)
#
# # Plot histogram
# plt.hist(data_right_skew, bins=30, edgecolor='black')
# plt.xlabel('Values')
# plt.ylabel('Frequency')
# plt.title('Data Skewed to the Right (Positive Skewness)')
# print("data_right", pd.DataFrame(data_right_skew).skew())
# plt.show()
#
#
# # Generate skewed data
# data_left_skew = np.random.beta(a=5, b=2, size=1000)
#
# # Plot histogram
# plt.hist(data_left_skew, bins=30, edgecolor='black')
# plt.xlabel('Values')
# plt.ylabel('Frequency')
# plt.title('Data Skewed to the Left (Negative Skewness)')
# print("data_left", pd.DataFrame(data_left_skew).skew())
# plt.show()
##############################
