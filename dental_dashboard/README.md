# Sam's Family Dental - Appointments Dashboard (Django)

A simple dashboard + API webhook to manage dental appointments, designed to work
with a Vapi voice assistant for booking, checking, cancelling and rescheduling
appointments.

## 1. Setup

```bash
pip install django
cd dental_dashboard
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Visit:
- Dashboard: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- Vapi webhook endpoint: http://127.0.0.1:8000/webhook/vapi/

## 2. Dashboard Features

- View all appointments (Name, Phone, Location, Service, Date, Time, Status)
- Add new appointment manually
- Edit / Reschedule appointment
- Cancel appointment (soft - status changes to "cancelled")
- Delete appointment (permanent removal)

## 3. Vapi Webhook

Single endpoint `/webhook/vapi/` handles 4 functions based on `function.name`:

- `book_appointment`
- `check_appointment`
- `cancel_appointment`
- `reschedule_appointment`

### Tool Definitions for Vapi (add in Tools tab)

#### 1. book_appointment
```json
{
  "type": "function",
  "function": {
    "name": "book_appointment",
    "description": "Book a new dental appointment for a patient",
    "parameters": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "description": "Patient full name" },
        "phone": { "type": "string", "description": "Patient phone number" },
        "location": { "type": "string", "enum": ["Jackson Heights", "Woodside"] },
        "service": { "type": "string", "description": "Type of treatment requested" },
        "date": { "type": "string", "description": "Appointment date (YYYY-MM-DD)" },
        "time": { "type": "string", "description": "Appointment time (HH:MM, 24-hour)" }
      },
      "required": ["name", "phone", "location", "service", "date", "time"]
    }
  },
  "server": { "url": "https://YOUR_DOMAIN/webhook/vapi/" }
}
```

#### 2. check_appointment
```json
{
  "type": "function",
  "function": {
    "name": "check_appointment",
    "description": "Check existing appointment details using phone number",
    "parameters": {
      "type": "object",
      "properties": {
        "phone": { "type": "string", "description": "Patient phone number" }
      },
      "required": ["phone"]
    }
  },
  "server": { "url": "https://YOUR_DOMAIN/webhook/vapi/" }
}
```

#### 3. cancel_appointment
```json
{
  "type": "function",
  "function": {
    "name": "cancel_appointment",
    "description": "Cancel an existing appointment using phone number",
    "parameters": {
      "type": "object",
      "properties": {
        "phone": { "type": "string", "description": "Patient phone number" },
        "appointment_id": { "type": "integer", "description": "Optional appointment ID" }
      },
      "required": ["phone"]
    }
  },
  "server": { "url": "https://YOUR_DOMAIN/webhook/vapi/" }
}
```

#### 4. reschedule_appointment
```json
{
  "type": "function",
  "function": {
    "name": "reschedule_appointment",
    "description": "Reschedule an existing appointment to a new date/time",
    "parameters": {
      "type": "object",
      "properties": {
        "phone": { "type": "string", "description": "Patient phone number" },
        "appointment_id": { "type": "integer", "description": "Optional appointment ID" },
        "new_date": { "type": "string", "description": "New date (YYYY-MM-DD)" },
        "new_time": { "type": "string", "description": "New time (HH:MM, 24-hour)" }
      },
      "required": ["phone", "new_date", "new_time"]
    }
  },
  "server": { "url": "https://YOUR_DOMAIN/webhook/vapi/" }
}
```

## 4. Deploying / Exposing Locally

For testing with Vapi, expose your local server using ngrok:

```bash
ngrok http 8000
```

Then use the ngrok URL (e.g. `https://abcd1234.ngrok.io/webhook/vapi/`) as the
`server.url` in each Vapi tool definition above.

## 5. Notes

- `cancel_appointment` does a soft cancel (status = "cancelled"); the dashboard
  "Delete" button performs permanent deletion.
- `reschedule_appointment` finds the most recent "booked" appointment for that
  phone number and updates date/time, setting status to "rescheduled".
- For multiple appointments per phone number, pass `appointment_id` for precision.
