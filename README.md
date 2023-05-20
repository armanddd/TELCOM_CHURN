# TELCOM_CHURN

Api Prediction:
Single prediction
```
tenureForm=5
genderSelect=Male
seniorCitizenSelect=1
partnerSelect=Yes
dependentsSelect=No
phoneServiceSelect=No
multipleLinesSelect=No
internetServiceSelect=Yes
onlineSecuritySelect=Yes
onlineBackupSelect=Yes
deviceProtectionSelect=No
techSupportSelect=No
streamingTVSelect=No
streamingMoviesSelect=No
contractTypeSelect=One year
paymentMethodSelect=Credit card (automatic)
paperlessBillingSelect=Yes
monthlyChargesForm=25
totalChargesForm=125
api_key=xxxxxxxxxxx
```

Multiple prediction using the template:
```
curl -X POST -F "templateFile=@test.xlsx" -F "api_key=xxxxxxxxxxx" http://localhost:8000/make_prediction
```
