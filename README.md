# FMAX Backend API README

This is the backend api for the FMAX frontend client


## Setup

To install the necessary dependencies for the FastAPI application, follow these steps:

- Make sure you have Python 3.7+ installed on your system.

- Clone this repository to your local machine:
```bash
git clone git@ssh.dev.azure.com:v3/flapmax/Measure/measure-backend-updated
cd measure-backend-updated
```

- Create and setup a virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate
```

- Install the required dependencies:
```bash
pip install --upgrade pip wheel
pip install -r requirements.txt
```

## Configuration

Ensure that all the environment variables specified in the `example.env` file are set as environment variables, or in the `.env` file

## Running the App

To start the FastAPI application, run the following command:

```bash
uvicorn app:app --port 8000 --reload
```

* app.main:app refers to the FastAPI app instance in the main.py file.
* --port 8000 sets the port number for the application (you can change it to any available port).
* --reload enables auto-reloading of the app when code changes are made (for development).

The FastAPI application will start, and you can access it by navigating to (http://localhost:8000)[http://localhost:8000] in your web browser.

## Contributing

We welcome contributions to improve the application. To contribute, follow these steps:

- Fork the repository and create your branch:
```bash
git checkout -b feature/your-feature-name
```

-Make your changes and commit them:
```bash
git commit -m "Add your message here"
```

-Push to your branch:
```bash
git push origin feature/your-feature-name
```

-Finally, create a pull request on Azure Devops.

## Issues and Bug Reports

If you encounter any issues or bugs with the application, please open a new issue via the azure devops board.


## Deployment

This codebase is to be deployed to the Azure app service under the `MARKETPLACE` resource group. 

Here is the current [live url](https://measure-backend.azurewebsites.net/docs)