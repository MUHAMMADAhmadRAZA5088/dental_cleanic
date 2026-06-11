import json

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

from .models import Appointment


def normalize_phone(phone):
    """Keep only digits, so '+1 (234) 567-8900' and '12345678900' match."""
    if not phone:
        return ""
    return "".join(ch for ch in str(phone) if ch.isdigit())


# ---------------------------------------------------------------------
# DASHBOARD VIEWS (for staff to view/manage appointments in browser)
# ---------------------------------------------------------------------

def dashboard(request):
    appointments = Appointment.objects.all().order_by("date", "time")
    today = timezone.localdate()
    return render(request, "appointments/dashboard.html", {
        "appointments": appointments,
        "today": today,
    })


def add_appointment(request):
    if request.method == "POST":
        Appointment.objects.create(
            name=request.POST.get("name"),
            phone=normalize_phone(request.POST.get("phone")),
            location=request.POST.get("location"),
            service=request.POST.get("service"),
            date=request.POST.get("date"),
            time=request.POST.get("time"),
            notes=request.POST.get("notes", ""),
            status="booked",
        )
        messages.success(request, "Appointment created successfully.")
        return redirect("dashboard")
    return render(request, "appointments/add_appointment.html")


def edit_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        appointment.name = request.POST.get("name")
        appointment.phone = request.POST.get("phone")
        appointment.location = request.POST.get("location")
        appointment.service = request.POST.get("service")
        appointment.date = request.POST.get("date")
        appointment.time = request.POST.get("time")
        appointment.notes = request.POST.get("notes", "")
        appointment.status = request.POST.get("status")
        appointment.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect("dashboard")
    return render(request, "appointments/edit_appointment.html", {"appointment": appointment})


def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "cancelled"
    appointment.save()
    messages.success(request, f"Appointment for {appointment.name} cancelled.")
    return redirect("dashboard")


def delete_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.delete()
    messages.success(request, "Appointment deleted permanently.")
    return redirect("dashboard")


# ---------------------------------------------------------------------
# VAPI WEBHOOK (single endpoint that handles all 4 functions)
# ---------------------------------------------------------------------

@csrf_exempt
def vapi_webhook(request):
    """
    Handles tool calls coming from Vapi assistant:
      - book_appointment
      - check_appointment
      - cancel_appointment
      - reschedule_appointment
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = data.get("message", {})
    tool_calls = message.get("toolCalls") or message.get("tool_calls") or []

    results = []

    for call in tool_calls:
        function = call.get("function", {})
        function_name = function.get("name")
        params = function.get("arguments", {})

        # arguments may arrive as a JSON string
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                params = {}

        tool_call_id = call.get("id")

        if function_name == "book_appointment":
            result_text = handle_book_appointment(params)

        elif function_name == "check_appointment":
            result_text = handle_check_appointment(params)

        elif function_name == "cancel_appointment":
            result_text = handle_cancel_appointment(params)

        elif function_name == "reschedule_appointment":
            result_text = handle_reschedule_appointment(params)

        else:
            result_text = f"Unknown function: {function_name}"

        results.append({
            "toolCallId": tool_call_id,
            "result": result_text,
        })

    return JsonResponse({"results": results})


# ---------------------------------------------------------------------
# Function handlers
# ---------------------------------------------------------------------

def handle_book_appointment(params):
    required = ["name", "phone", "date", "time", "service"]
    missing = [f for f in required if not params.get(f)]
    if missing:
        return f"Missing required information: {', '.join(missing)}"

    phone = normalize_phone(params.get("phone"))
    date = params.get("date")
    time = params.get("time")
    location = params.get("location", "Jackson Heights")

    # Prevent double-booking the same slot at the same location
    slot_taken = Appointment.objects.filter(
        date=date,
        time=time,
        location=location,
        status__in=["booked", "rescheduled"],
    ).exists()
    if slot_taken:
        return (
            f"Sorry, the slot on {date} at {time} at {location} is already booked. "
            f"Please choose a different date or time."
        )

    # Prevent the same patient from having two active appointments at once
    existing = Appointment.objects.filter(
        phone=phone,
        status__in=["booked", "rescheduled"],
    ).first()
    if existing:
        return (
            f"This phone number already has an active appointment on "
            f"{existing.date} at {existing.time} for {existing.service}. "
            f"Please cancel or reschedule it before booking a new one."
        )

    appointment = Appointment.objects.create(
        name=params.get("name"),
        phone=phone,
        location=location,
        service=params.get("service"),
        date=date,
        time=time,
        status="booked",
    )

    return (
        f"Appointment booked successfully for {appointment.name} "
        f"on {appointment.date} at {appointment.time} "
        f"at {appointment.location} for {appointment.service}. "
        f"Appointment ID is {appointment.id}."
    )


def handle_check_appointment(params):
    phone = normalize_phone(params.get("phone"))
    if not phone:
        return "Please provide a phone number to check the appointment."

    appointments = Appointment.objects.filter(
        phone=phone, status__in=["booked", "rescheduled"]
    )

    if not appointments.exists():
        return "No active appointment found for this phone number."

    if appointments.count() == 1:
        a = appointments.first()
        return (
            f"You have an appointment on {a.date} at {a.time} "
            f"at {a.location} for {a.service}. Status: {a.status}."
        )

    lines = []
    for a in appointments:
        lines.append(f"- {a.date} at {a.time}, {a.service}, {a.location} (ID {a.id})")
    return "You have multiple appointments:\n" + "\n".join(lines)


def handle_cancel_appointment(params):
    phone = normalize_phone(params.get("phone"))
    appointment_id = params.get("appointment_id")

    appointment = None
    if appointment_id:
        appointment = Appointment.objects.filter(
            id=appointment_id, status__in=["booked", "rescheduled"]
        ).first()
    elif phone:
        appointment = Appointment.objects.filter(
            phone=phone, status__in=["booked", "rescheduled"]
        ).first()

    if not appointment:
        return "No active appointment found to cancel."

    appointment.status = "cancelled"
    appointment.save()

    return (
        f"Appointment for {appointment.name} on {appointment.date} "
        f"at {appointment.time} has been cancelled."
    )


def handle_reschedule_appointment(params):
    phone = normalize_phone(params.get("phone"))
    appointment_id = params.get("appointment_id")
    new_date = params.get("new_date")
    new_time = params.get("new_time")

    if not new_date or not new_time:
        return "Please provide both new date and new time to reschedule."

    appointment = None
    if appointment_id:
        appointment = Appointment.objects.filter(
            id=appointment_id, status__in=["booked", "rescheduled"]
        ).first()
    elif phone:
        appointment = Appointment.objects.filter(
            phone=phone, status__in=["booked", "rescheduled"]
        ).first()

    if not appointment:
        return "No active appointment found to reschedule."

    # Prevent moving into a slot that's already taken by someone else
    slot_taken = Appointment.objects.filter(
        date=new_date,
        time=new_time,
        location=appointment.location,
        status__in=["booked", "rescheduled"],
    ).exclude(id=appointment.id).exists()
    if slot_taken:
        return (
            f"Sorry, the slot on {new_date} at {new_time} at {appointment.location} "
            f"is already booked. Please choose a different date or time."
        )

    old_date, old_time = appointment.date, appointment.time
    appointment.date = new_date
    appointment.time = new_time
    appointment.status = "rescheduled"
    appointment.save()

    return (
        f"Appointment for {appointment.name} has been rescheduled "
        f"from {old_date} {old_time} to {new_date} {new_time}."
    )
