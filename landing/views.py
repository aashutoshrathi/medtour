from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from social_django.models import UserSocialAuth
from hospital.models import Doctor, Appointment, Hospital
from hospital.views import HospitalsAll
from hospital.forms import InviteDocForm
from landing.models import Region, City, Profile
from landing.tokens import account_activation_token
from .forms import ProfileForm, UsernameForm, SignUpForm, HospitalForm
from medtour import settings
from landing.utils import sg_mail


def land(request):
    return render(request, 'landing/base.html')


class CompleteHospitalProfile(View):
    def get(self, request):
        form = HospitalForm(instance=request.user.hospital)
        return render(request, 'landing/hospital_profile_complete.html', {'form': form})

    def post(self, request):
        form = HospitalForm(request.POST, instance=request.user.hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('home')
        else:
            messages.error(
                request, 'Slug is already taken, please try another one.')
            return render(request, 'landing/hospital_profile_complete.html', {'form': form})


class ChangeUsername(View):
    def get(self, request):
        form = UsernameForm(instance=request.user)
        return render(request, 'landing/username.html', {'form': form})

    def post(self, request):
        form = UsernameForm(request.POST, request.user)
        if form.is_valid():
            form = UsernameForm(request.POST, instance=request.user)
            form.save()
            messages.success(
                request, 'Your username was successfully updated!')
            update_session_auth_hash(request, request.user)
            return redirect('username')
        else:
            messages.error(
                request, 'Username is already taken, please try another one.')
        return render(request, 'landing/username.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        hospital = Hospital(user=user, email=user.email,
                            name=user.first_name, slug=user.username).save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('complete_hospital_profile')
    else:
        return HospitalsAll.as_view()(request, message=settings.INVALID_ACTIVATION_STRING)


def account_activation_sent(request):
    return render(request, 'registration/account_activation_sent.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your MedTour Account'
            from_email = settings.EMAIL_HOST_USER
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': force_text(urlsafe_base64_encode(force_bytes(user.pk))),
                'token': account_activation_token.make_token(user),
            })
            plain_msg = strip_tags(message)
            send_mail(subject, plain_msg, from_email, [
                      user.email], html_message=message, fail_silently=True)
            response = HospitalsAll.as_view()(request, good_message=settings.EMAIL_SENT_STRING)
            return response
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


class HomeView(View):
    def get(self, request, message=None, good_message=None):
        doctors = None
        hospital_appointments = None
        try:
            if request.user.hospital:
                if not request.user.hospital.user.profile.city:
                    message = "Please add city to your profile, for better visibility on platform."
                hospital = request.user.hospital
                doctors = Doctor.objects.filter(hospital=hospital)
                hospital_appointments = Appointment.objects.filter(
                    doctor__in=doctors)
                form = InviteDocForm(request.POST or None)
                return render(request, 'landing/home.html', {'doctors': doctors,
                                                             'happs': hospital_appointments,
                                                             'form': form,
                                                             'message': message,
                                                             'good_message': good_message
                                                             })
        except Hospital.DoesNotExist:
            pass
        try:
            if request.user.doctor:
                slug = request.user.doctor.slug
                doctor = Doctor.objects.get(slug=slug)
                doc_appointments = Appointment.objects.filter(
                    doctor=doctor)
                return render(request, 'landing/doc_home.html', {'happs': doc_appointments, 'message': message,
                                                                 'good_message': good_message})
        except Doctor.DoesNotExist:
            pass
        patient_appointments = Appointment.objects.filter(
            patient__user=request.user) or None
        return render(request, 'landing/patient_home.html', {'doctors': doctors,
                                                             'happs': hospital_appointments,
                                                             'papps': patient_appointments,
                                                             'message': message,
                                                             'good_message': good_message
                                                             })

    def post(self, request, message=None, good_message=None):
        form = InviteDocForm(request.POST or None)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.hospital = Hospital.objects.get(
                slug=request.user.hospital.slug)
            doctor.slug = doctor.user.username
            form.save()
            return redirect('home')
        return render(request, 'landing/home.html', {'form': form, 'message': message,
                                                     'good_message': good_message})


# only4 testing
def test_func():
    return True


class AccountOverview(View):
    def get(self, request):
        user = request.user

        try:
            google_login = user.social_auth.get(provider='google-oauth2')
        except UserSocialAuth.DoesNotExist:
            google_login = None

        try:
            twitter_login = user.social_auth.get(provider='twitter')
        except UserSocialAuth.DoesNotExist:
            twitter_login = None

        try:
            facebook_login = user.social_auth.get(provider='facebook')
        except UserSocialAuth.DoesNotExist:
            facebook_login = None

        can_disconnect = (user.social_auth.count() >
                          1 or user.has_usable_password())
        form = ProfileForm(instance=request.user.profile)
        return render(request, 'landing/profile.html', {
            'twitter_login': twitter_login,
            'facebook_login': facebook_login,
            'google_login': google_login,
            'user': user,
            'form': form,
            'can_disconnect': can_disconnect
        })

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('overview')
        else:
            messages.error(request, 'Please correct the error below.')


class PasswordChangeView(View):
    def get(self, request):
        if request.user.has_usable_password():
            password_form = PasswordChangeForm
        else:
            password_form = AdminPasswordChangeForm
        form = password_form(request.user)
        return render(request, 'landing/password.html', {'form': form})

    def post(self, request):
        if request.user.has_usable_password():
            password_form = PasswordChangeForm
        else:
            password_form = AdminPasswordChangeForm

        if request.method == 'POST':
            form = password_form(request.user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                messages.success(
                    request, 'Your password was successfully updated!')
                return redirect('password')
            else:
                messages.error(request, 'Please correct the error below.')
        else:
            form = password_form(request.user)
        return render(request, 'landing/password.html', {'form': form})


def load_state(request):
    regions = Region.objects.all().order_by('name')
    return render(request, 'hr/region_list.html', {'regions': regions})


def load_city(request):
    region = request.GET.get('state')
    cities = City.objects.filter(region__id=region).order_by('name')
    return render(request, 'hr/city_list.html', {'cities': cities})


def autocomplete(request):
    if request.is_ajax():
        query = request.GET.get('search')
        queryset = City.objects.filter(name__istartswith=query)
        suggestions = []
        for i in queryset:
            if len(suggestions) < 10:
                suggestions.append(i.display_name)
        data = {
            'list': suggestions,
        }
        return JsonResponse(data)
