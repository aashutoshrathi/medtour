from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from medtour import settings
from hospital.filters import DoctorSpecFilter
from hospital.forms import AppointmentForm
from landing.models import City, Profile
from .models import Hospital, Doctor, Appointment


class AppointmentApprove(View):
    def get(self, request, id):
        appointment = Appointment.objects.get(id=id)
        appointment.approved = True
        appointment.rejected = False
        appointment.save()
        send_approval_mail(appointment)
        return redirect(reverse('home', args=[]))


class AppointmentReject(View):
    def get(self, request, id):
        appointment = Appointment.objects.get(id=id)
        appointment.approved = False
        appointment.rejected = True
        appointment.save()
        return redirect(reverse('home', args=[]))


class HospitalHome(View):
    def get(self, request, slug):
        hospital = get_object_or_404(Hospital, slug=slug)
        specs = hospital.specialisation.all()
        doctors = Doctor.objects.filter(hospital=hospital)
        doctors_filter = DoctorSpecFilter(request.GET, queryset=doctors)
        return render(request, 'hospital/hospital-profile.html', {
            'doctors': doctors,
            'specs': specs,
            'hospital': hospital,
            'filter': doctors_filter
        })


class DoctorHome(View):
    def get(self, request, slug):
        doctor = get_object_or_404(Doctor, slug=slug)
        return render(request, 'hospital/doctor-profile.html', {
            'doctor': doctor,
        })


def send_appointment_mail(doctor, patient):
    patient_name = patient.user.first_name
    subject = '[New] Appointment with {}'.format(patient)
    from_email = settings.EMAIL_HOST_USER
    message = render_to_string('emails/new_appointment.html',)
    plain_msg = strip_tags(message)
    send_mail(subject, plain_msg, from_email, [
        doctor.user.email], html_message=message, fail_silently=True)
    return redirect('home')


def send_approval_mail(appointment):
    patient = appointment.patient.user.first_name
    doctor = appointment.doctor.user.first_name
    subject = '[CONFIRMED] Appointment with {}'.format(doctor)
    from_email = settings.EMAIL_HOST_USER
    message = render_to_string('emails/approved_appointment.html',
                               {'patient': patient, 'doctor': doctor, 'appointment': appointment})
    plain_msg = strip_tags(message)
    send_mail(subject, plain_msg, from_email, [
        appointment.patient.user.email], html_message=message, fail_silently=True)
    return redirect('home')


@login_required
def appoint_doctor(request, slug):
    form = AppointmentForm(request.POST or None)
    if form.is_valid():
        formwa = form.save(commit=False)
        formwa.doctor = Doctor.objects.get(slug=slug)
        formwa.patient = Profile.objects.get(user=request.user)
        form.save()
        send_appointment_mail(formwa.doctor, formwa.patient)
        return redirect('home')
    return render(request, 'hospital/appointment.html', {'form': form})


class HospitalsAll(View):
    def get(self, request, message=None, good_message=None):
        search_box_city_value = None
        if 'q' in request.GET:
            search_box_city_value = request.GET['q']
        hospitals = Hospital.objects.all()
        if search_box_city_value is not None:
            search_box_city_value_trimmed = "".join(
                search_box_city_value.split())
            city_name = search_box_city_value_trimmed.split(',')
            city = get_object_or_404(City, name=city_name[0])
            hospitals = Hospital.objects.filter(user__profile__city=city)
        if not request.user.is_anonymous and not message:
            if not request.user.profile.city:
                message = "Please add city to your profile, for better visibility on platform."
        return render(request, 'hospital/hospital-list.html', {
            'hospitals': hospitals,
            'search_box_city_value': search_box_city_value,
            'message': message,
            'good_message': good_message
        })

    def post(self, request, message=None, good_message=None):
        hospitals = Hospital.objects.all()
        if not request.user.is_anonymous:
            if not request.user.profile.city:
                message = "Please add city to your profile, for better visibility on platform."
        return render(request, 'hospital/hospital-list.html', {
            'hospitals': hospitals,
            'message': message,
            'good_message': good_message
        })
