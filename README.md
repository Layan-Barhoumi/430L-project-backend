
# LBP Exchange Tracker

The goal of this project is to provide users with an all-inclusive money exchange platform. This platform allows users to keep up with daily exchange rates, gain insight on the rate development over time, and perform transactions among each other.  


## Technologies

The backend has been developed in python flask and uses SQLAlchemy to store and manipulate the app's data in the MySQL database.

## Installation

- Clone this repository in a new directory
- Create a new python virtual environment ```py -3 -m venv venv```(windows) ```python3 -m venv venv```(unix)
- Open the terminal from the new directory
- Run the virtual environment ```venv\Scripts\activate``` (windows) ```venv/bin/activate```(unix)
- Install Flask ```pip install Flask```
- Install the requirements ```pip install -r requirements.txt```
- Run the server ```python -m flask --app app.py run```


## API Documentation

The openAPI documentation of the backend API layer can be found in this repository (openapi.yaml).

## Architecture
The backend architecture diagram can be found in this repository, under Backend_architecture.png.