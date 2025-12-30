# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teachers can register/unregister students for activities
- Announcements banner driven from the database
- Authenticated teachers can manage announcements (add/edit/delete)

## Getting Started

### Prerequisites

- MongoDB running locally on `mongodb://localhost:27017/`

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=...&teacher_username=...` | Register a student (teacher authentication required)               |
| POST   | `/activities/{activity_name}/unregister?email=...&teacher_username=...` | Unregister a student (teacher authentication required)         |
| POST   | `/auth/login?username=...&password=...`                           | Login as a teacher                                                  |
| GET    | `/auth/check-session?username=...`                                | Validate a saved user session (by username)                         |
| GET    | `/announcements/active`                                           | Get active announcements (public)                                   |
| GET    | `/announcements?teacher_username=...`                             | List all announcements (teacher required)                            |
| POST   | `/announcements?teacher_username=...`                             | Create announcement (teacher required, JSON body)                    |
| PUT    | `/announcements/{id}?teacher_username=...`                        | Update announcement (teacher required, JSON body)                    |
| DELETE | `/announcements/{id}?teacher_username=...`                        | Delete announcement (teacher required)                               |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB (database name: `mergington_high`). Sample data is seeded from `src/backend/database.py` when collections are empty.

### Announcements

- `message` (string, required)
- `start_date` (date, optional)
- `expiration_date` (date, required)
