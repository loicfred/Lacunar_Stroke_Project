# Early detection of lacunar stroke for early diagnosis: An AI-Powered System for Continuous Bilateral Sensory Asymmetry Monitoring

This program is our solution for a group project of **Research & Innovation** at university.
The solution involves a web application made using Flask and a Random Forest AI Algorithm trained with a data which is used to predict and assess a risk level for lacunar stroke patients. The application and patient data is stored on a MariaDB database.

The application's actors involve Doctor and Patient, a user logged as a patient has access to their data and the prediction feature and a user logged as doctor has access to all their patients and statistical data.


## Login Page
This allow a user to log as either a doctor or a patient. (role is defined in the user)

<img width="1700" height="800" alt="image" src="https://github.com/user-attachments/assets/11f23045-b1db-4b0e-8e95-46bbb29694cb" />


## Patient Dashboard
This dashboard allow patients to view their own data. It is a dynamic page for each patient, a patient can't access the dashboard of another patient.

<img width="1700" height="800" alt="image" src="https://github.com/user-attachments/assets/fb1f93eb-e68f-4021-bbde-54f9a2a2898a" />

## Doctor Dashboard
This dashboard allow doctors to view statistics and their patients. A doctor can access the dashboard of all patients.

<img width="1700" height="800" alt="image" src="https://github.com/user-attachments/assets/c6f70a60-c825-4dd1-9b10-cba081b1f219" />

## Predicton
The prediction page is used to calculate the risk level by inputting the current data of the patient.
Initially the data should be collected using sensors, but since this solution was more focused on the algorithm, we choose manual data input.

<img width="1700" height="800" alt="image" src="https://github.com/user-attachments/assets/47656111-914a-4029-9161-f5e0504d183c" />

## Results
The results are then shown and adding to the database records of the patient with the current data and values input.

<img width="1700" height="800" alt="image" src="https://github.com/user-attachments/assets/095e528e-59a7-4e50-88a0-769b9be594d8" />
