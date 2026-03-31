from datetime import datetime
import email
import os
import random
from urllib import request
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.db import transaction
from .models import ContactMessage, Response, State, workers, users, ServiceCatogarys, Country, City, Feedback, ServiceRequests
from .forms import stateform
from django.shortcuts import render, redirect

from django.contrib import messages
from .models import City   
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from .models import Contact 

from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import PasswordChangeView



class Commenlib:
    def __init__(self):
        self.DEFAULT_REDIRECT_PATH={'ROOT':'/'}

common_lib = Commenlib()

# Create your views here.
class Login(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self,request):
        username = request.POST['uname']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            # ✅ Admin
            if user.is_superuser:
                return redirect('admmin_home')

            # ✅ Worker
            elif workers.objects.filter(admin=user).exists():
                return redirect('workers_home')

            # ✅ Client
            elif users.objects.filter(admin=user).exists():
                return redirect('index')

            else:
                return redirect('login')

        else:
            return render(request, 'login.html', {'error_msg': "Invalid credentials."})

def logout_view(request):
    logout(request)
    # return redirect('login')
    return redirect('login')



from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from .models import users  # your profile model

# views.py
class User_Register(View):

    def get(self, request):
        return render(request, 'user_register.html')

    def post(self, request):
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        contact_number = request.POST.get('contactnumber')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        profile_pic = request.FILES.get('profile_pic')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        # 🔐 Check password match
        if password != cpassword:
            return render(request, 'user_register.html', {'msg': "Passwords do not match!"})

        # ✅ Generate OTP
        otp = random.randint(100000, 999999)

        # ✅ Create Django User (inactive until OTP verified)
        new_user = User.objects.create(
            username=email,
            email=email,
            password=make_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=False,   # important! cannot login until verified
            is_staff=False,
        )

        # ✅ Create Profile (users model)
        user_obj = users.objects.create(
            admin=new_user,
            contact_number=contact_number,
            address=address,
            gender=gender,
            otp=otp,
            is_verified=False
        )

        if profile_pic:
            user_obj.profile_pic = profile_pic

        user_obj.save()


        otp_sent = False
        try:
            send_mail(
                'Fixora OTP Verification',
                f'Your OTP is {otp}',
                os.environ.get('EMAIL_USER'),  # must match EMAIL_HOST_USER
                [email],
                fail_silently=True,
            )
            otp_sent = True
        except Exception as e:
            print("Email failed:", e)

        if otp_sent:
            messages.success(request, "OTP sent to your email")
        else:
            messages.warning(request, f"Email failed. Your OTP is: {otp}")


        return redirect('verify_otp', user_id=user_obj.id)



class Worker_Register(View):
    def get(self, request):
        designations=ServiceCatogarys.objects.all()
        contaxt={
            'designations':designations,
        }
        return render(request, 'workers_registration.html',contaxt)

    def post(self, request):
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        contactnumber = request.POST.get('contactnumber')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        city = request.POST.get('city')
        address = request.POST.get('address')
        designation = request.POST.get('designation')
        profile_pic = request.FILES.get('profile_pic')
        aadhar_card = request.FILES.get('aadhar_card')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

    






        # user_type= 3
        # Check if passwords match
        if password == cpassword:
            new_user = User.objects.create(
                username=email,
                email=email,
                password=make_password(password),
                first_name=firstname,
                last_name=lastname,
                is_active=True,
                is_staff=False,
            )

            # For 'users'
            new_worker = workers(admin=new_user, contact_number=contactnumber, dob=dob, address=address, city=city,
                                 gender=gender, designation=designation, profile_pic=profile_pic,aadhar_card=aadhar_card,
                                 acc_activation=False, avalability_status=True)
            new_worker.save()

            return render(request, 'login.html', {'msg': "Addd succsfully!"})

            # return render(request, 'user_register.html', {'msg': "Passwords do not match!"})


        else:
            return render(request, 'workers_registration.html', {'msg': "Passwords do not match!"})

        return render(request, 'workers_registration.html', {'msg': "Something went wrong"})



# views.py
class VerifyOTP(View):

    def get(self, request, user_id):
        return render(request, 'userpages/verify_otp.html', {'user_id': user_id})

    def post(self, request, user_id):
        entered_otp = request.POST.get('otp')
        user_obj = users.objects.get(id=user_id)

        # ✅ Compare OTP
        if str(user_obj.otp) == str(entered_otp):
            user_obj.is_verified = True
            user_obj.otp = None
            user_obj.save()

            # Activate Django user so they can login
            user_obj.admin.is_active = True
            user_obj.admin.save()

            messages.success(request, "OTP verified successfully! You can now login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'userpages/verify_otp.html', {
                'user_id': user_id
            })






class home(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request):
        # Fetch all services and feedbacks
        services = ServiceCatogarys.objects.all()
        feedbacks = Feedback.objects.select_related('User').all()

        # Convert queryset to list for random sampling
        all_services = list(services)

        # Safely select up to 3 random services
        num_to_sample = 3
        if all_services:
            selected_services = random.sample(all_services, min(len(all_services), num_to_sample))
        else:
            selected_services = []  # fallback if no services exist

        context = {
            'services': services,
            'feedbacks': feedbacks,
            'selected_services': selected_services,
        }

        return render(request, 'userpages/index.html', context)







class about(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        return render(request, 'userpages/about.html')
    
class services(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        services = ServiceCatogarys.objects.all()
        feedbacks = Feedback.objects.select_related('User').all()
        all_services = list(ServiceCatogarys.objects.all())  # Convert QuerySet to a list
         # Select 6 random services
        print('services:', services)
        context = {
            'services': services,
            'feedbacks': feedbacks,
        }
        return render(request,'userpages/service.html',context)


class bookservice(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        services = ServiceCatogarys.objects.get(id=id)
        cities=City.objects.all()
        print(services.Name)
        context = {
            'services': services,
            'cities': cities,
        }

        return render(request,'userpages/servicebook.html',context)
    def post(self,request,id):
        user_id = request.user.id
        user=users.objects.get(admin=user_id)
        print(user)
        problem_description = request.POST.get('Problem_Description')
        service_id = ServiceCatogarys.objects.get(id=id)
        # service_id = request.POST.get('service')
        address = request.POST.get('Address')
        city_id = request.POST.get('city')
        pin = request.POST.get('Pincode')
        house_no = request.POST.get('House_No')
        landmark = request.POST.get('landmark')
        contact = request.POST.get('contact')

        # Create a new ServiceRequests instance and save it
        service_request = ServiceRequests(
            user=user,
            Problem_Description=problem_description,
            service=service_id,
            Address=address,
            city_id=city_id,
            pin=pin,
            House_No=house_no,
            landmark=landmark,
            contact=contact,
        )
        service_request.save()


        messages.success(request, "Service booked successfully!")
        return redirect('index')

class admmin_home(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self,request):
        if not request.user.is_superuser:
            return HttpResponse("Unauthorized", status=403)

        total_requests = ServiceRequests.objects.count()
        completed_requests = Response.objects.filter(status=True).count()
        pending_requests = Response.objects.filter(status=False).count()
        total_users = users.objects.count()

        context = {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
            'total_users': total_users,
        }
        return render(request, 'adminpages/adminhompage.html',context)

        

class workers_home(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request):
        if not workers.objects.filter(admin=request.user).exists():
            return HttpResponse("Unauthorized", status=403)

        worker = workers.objects.get(admin=request.user)

        assigned_responses = Response.objects.filter(assigned_worker=worker)

        total_requests = assigned_responses.count()
        completed_requests = assigned_responses.filter(status=True).count()
        pending_requests = assigned_responses.filter(status=False).count()

        context = {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
        }

        return render(request, 'workerpages/Workerhompage.html', context)





class manageworker(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        workers_records=workers.objects.all()
        context={'workers_records':workers_records}
        return render(request,'adminpages/Manage_Workers.html',context)

class verify_worker(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request, action, id):
        worker = workers.objects.get(id=id)

        if action == 'verify':
           if worker.aadhar_card:
                worker.acc_activation = True
                worker.save()
                messages.success(request, "Worker verified successfully ✅")
           else:
                messages.error(request, "Cannot verify: Aadhaar not uploaded ❌")

        elif action == 'activate':
            worker.avalability_status = True
            worker.save()

        elif action == 'deactivate':
            worker.avalability_status = False
            worker.save()

        elif action == 'delete':
            worker.delete()
            return redirect('manageworker')

        return redirect('manageworker')
    


class manageusers(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request):
        user_data = users.objects.filter(admin__is_staff=False)

        return render(request, 'adminpages/View_Users.html', {
            'users': user_data
        })


class verify_user(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request, id):
        user_obj = users.objects.get(id=id)
        user_obj.is_verified = True
        user_obj.save()
        return HttpResponseRedirect('/manageusers')


class toggle_user_status(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request, id):
        user_obj = users.objects.get(id=id)

        if user_obj.admin.is_active:
            user_obj.admin.is_active = False
        else:
            user_obj.admin.is_active = True

        user_obj.admin.save()
        return HttpResponseRedirect('/manageusers')


class delete_user(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request, id):
        user_obj = users.objects.get(id=id)
        user_obj.admin.delete()
        return HttpResponseRedirect('/manageusers')
    



class AddCountry(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request):
        return render(request, 'country.html')

    def post(self, request):
        country_name = request.POST.get('name')
        Country.objects.create(name=country_name)
        return HttpResponseRedirect('/ManageCountry')

class ManageCountry(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        Country_record=Country.objects.all()
        context={
            'Country_record':Country_record
        }
        return render(request,'adminpages/Manage_Country.html',context)
class DeleteCountry(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        data=Country.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect('/ManageCountry')



class ManageState(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        State_record=State.objects.all()
        context={
            'State_record':State_record
        }
        return render(request,'adminpages/ManageState.html',context)

class AddState(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request):
        country_recorsd = Country.objects.all()
        return render(request, 'state.html', {'country_recorsd': country_recorsd})

    def post(self, request):
        form = stateform(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/ManageState')
        else:
            # Handle the case where the form data is not valid
            country_records = State.objects.all()
            return render(request, 'state.html', {'form': form, 'country_records': country_records})

class DeleteState(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        data=State.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect('/ManageState')

class managecity(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        city_records=City.objects.all()
        context={
            'city_records':city_records
        }
        return render(request,'adminpages/ManageCity.html',context)
    
class AddCity(LoginRequiredMixin, View):

    def get(self, request):
        states = State.objects.all()
        return render(request, 'city.html', {'state_recorsd': states})

    def post(self, request):
        city_name = request.POST.get('name')
        state_id = request.POST.get('state')

        if not state_id:
            return render(request, 'city.html', {
                'state_recorsd': State.objects.all(),
                'error': 'Please select a state'
            })

        state_obj = State.objects.get(id=int(state_id))

        City.objects.create(name=city_name, state=state_obj)

        return redirect('managecity')
    
    
    
class DeleteCity(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        data=City.objects.get(id=id)
        data.delete()
        return HttpResponseRedirect('/managecity')



class AddServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request):
        return render(request, 'adminpages/ServiceCatogry.html')

    def post(self, request):
        Name = request.POST.get('Name')
        Description = request.POST.get('Description')
        img = request.FILES.get('img')
        price = request.POST.get('price')

        ServiceCatogarys.objects.create(
            Name=Name,
            Description=Description,
            img=img,
            price=price
        )

        return HttpResponseRedirect("/ManageServices")



class ManageServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        service_records=ServiceCatogarys.objects.all()
        context= {
            'services':service_records,
        }
        return render(request,'adminpages/Manage_Services.html',context)
    

        # form = ServiceCatogoryForm(request.POST,request.FILES)
        # if form.is_valid():
        #     form.save()
        #     return HttpResponse("Ok")
        # else:
        #     return HttpResponse('wrong')

class DeleteServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        data = ServiceCatogarys.objects.get(id=id)
        data.delete()

        service_records=ServiceCatogarys.objects.all()
        context= {
            'services':service_records,
        }
        return render(request,'adminpages/Manage_Services.html',context)
    
class EditServices(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        return render(request,'adminpages/ServiceCatogry.html',{'record':service})
    
    def post(self, request, id):
        service = get_object_or_404(ServiceCatogarys, id=id)
        Name = request.POST.get('Name')
        Description = request.POST.get('Description')
        img = request.FILES.get('img')

        # Update the service category fields
        service.Name = Name
        service.Description = Description
        if img:
            service.img = img
        service.save()
        return HttpResponse("Update Successful")
    
class feedback_form(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self,request):
        worker = workers.objects.all()
        return render(request, 'userpages/feedback_form.html', {'workers': worker})

    def post(self,request):
        rating = int(request.POST['rating'])
        description = request.POST['description']
        user = request.user
        employ_id = request.POST['employ']
        employ = workers.objects.get(id=employ_id)
        date = datetime.now()

        Feedback.objects.create(
            Rating=rating,
            Description=description,
            User=user,
            Employ=employ,
            Date=date
        )

        
        messages.success(request, "Thanks for your feedback!")

        
        return redirect('index')   
    

class viewfeedbacks(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        feedback_records=Feedback.objects.all()
        context= {
            'feedback_records':feedback_records,
        }
        return render(request,'adminpages/View_feedbacks.html',context)

class ViewRequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        request_records=ServiceRequests.objects.all()
        context={
            'request_records':request_records,
        }
        return render(request, 'adminpages/View_request.html', context)



class ViewColleagues(LoginRequiredMixin, View):
    def get(self,request):

        # 🔒 Only allow workers
        if not workers.objects.filter(admin=request.user).exists():
            return HttpResponse("Unauthorized", status=403)

        workers_records = workers.objects.all().values(
            'admin__first_name',
            'admin__last_name',
            'city',
            'designation',
            'avalability_status'
        )

        context = {'workers_records': workers_records}
        return render(request, 'workerpages/View_colleagues.html', context)



class WorkerViewRequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request):
        worker_id = request.user.id
        print("worker_id", worker_id)
        assigned_responses = Response.objects.filter(assigned_worker__admin__id=worker_id)
        service_ids = [response.requests.service.id for response in assigned_responses]
        request_records = ServiceRequests.objects.filter(service__id__in=service_ids)

        context = {
            'request_records': request_records,
            'assigned_responses': assigned_responses,
        }
        return render(request, 'workerpages/View_request.html', context)


class viewworkerfeedbacks(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        feedback_records=Feedback.objects.all()
        context= {
            'feedback_records':feedback_records,
        }
        return render(request,'workerpages/View_feedbacks.html',context)


class viewrequests(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        worker=request.user
        print("worker_id",worker)
        request_records=ServiceRequests.objects.all()
        context= {
            'request_records':request_records,
        }
        return render(request,'adminpages/View_request.html',context)
    
class acceptrequest(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,action,id):
        request_records=ServiceRequests.objects.get(id=id)
        
        if action == 'accept' and request_records.status == False:
            ServiceRequests.objects.filter(id=id).update(status=True)
            assigned_worker=request.user
            # worker_id=User.objects.get(username=assigned_worker)
            userid = request.user.id
            worker_id=workers.objects.get(admin=userid) 
            response=Response.objects.create(requests=request_records,assigned_worker=worker_id,status=False)
            return HttpResponseRedirect('/WorkerViewRequests')
        
        elif action == 'reject' and request_records.status == True:
            ServiceRequests.objects.filter(id=id).update(status=False)
            response=Response.objects.get(requests=request_records)
            response.delete()


            return HttpResponseRedirect('/WorkerViewRequests')
        
class viewresponse(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):
        Response_records=Response.objects.all()
        context= {
            'Response_records':Response_records,
        }
        return render(request,'adminpages/view_response.html',context)
    
class workerviewresponse(LoginRequiredMixin, View):
    def get(self,request):
        worker_id = request.user.id

        assigned_responses = Response.objects.filter(
            assigned_worker__admin__id=worker_id,
            status=False   # ✅ ONLY PENDING
        )

        return render(request,'workerpages/viewpending_task.html',{
            'Response_records':assigned_responses
        })



class WorkerCompletedTasks(LoginRequiredMixin, View):
    def get(self, request):
        worker_id = request.user.id

        completed_tasks = Response.objects.filter(
            assigned_worker__admin__id=worker_id,
            status=True
        )

        return render(request, 'workerpages/viewpending_task.html', {
            'Response_records': completed_tasks
        })


class Viewappointment_history(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request):
            # Get the logged-in user's ID
            user_id = request.user.id

            # Query request data for the logged-in user
            requests_data = ServiceRequests.objects.filter(user__admin_id=user_id)

            # Initialize lists to store request and response data
            request_list = []
            response_list = []

            for request_data in requests_data:
                # Check if a response exists for the request
                response = Response.objects.filter(requests=request_data).first()

                if response:
                    # If a response exists, add it to the response list
                    response_list.append(response)
                else:
                    # If no response exists, add the request to the request list
                    request_list.append(request_data)

            context = {
                'requests': request_list,
                'responses': response_list,
            }

            return render(request, 'userpages/appointment_history.html', context)
    


class CancelRequest(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,id):
        if request.user.is_superuser:
            r_id=ServiceRequests.objects.get(id=id)
            r_id.delete()
            return HttpResponseRedirect('/ViewRequests')
        
        else:
            uid=request.user.id
            # admin=User.object.get(admin=uid)
            user=users.objects.get(admin=uid)
            user_id=user.id
            r_id=ServiceRequests.objects.get(Q(id=id) & Q(user=user_id))
            r_id.delete()
            return HttpResponseRedirect('/index')


class AssignWorker(LoginRequiredMixin, View):
    def get(self, request, id):
        # Fetch the specific service request
        req = get_object_or_404(ServiceRequests, id=id)
        
        # Fetch all workers to display in dropdown
        workers_records = workers.objects.all()
        
        context = {
            'req': req,
            'workers_records': workers_records,
        }
        return render(request, 'adminpages/assign_worker.html', context)

    def post(self, request, id):
        # Get the selected worker id from POST data
        worker_id = request.POST.get('assigned_worker')
        req = get_object_or_404(ServiceRequests, id=id)
        assigned_worker = get_object_or_404(workers, id=worker_id)

        # Update the ServiceRequest to mark it as assigned
        req.worker = assigned_worker 
        req.status = True
        req.save()

        # Create a Response entry
        Response.objects.create(
            requests=req,
            assigned_worker=assigned_worker,
            status=False
        )

        # Redirect to the view responses page
        return redirect('/viewresponse')
        
class userprofile(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']

    def get(self, request):
        user = request.user

        data, created = users.objects.get_or_create(
            admin= request.user,
            defaults={
                'contact_number': '',
                'address': '',
                'gender': '',
                'profile_pic': ''
            }
        )

        context = {
            'data': data,
        }

        return render(request, 'userpages/user_profile.html', context)
    

class admin_profile(LoginRequiredMixin, View):
    def get(self, request):
        data, created = users.objects.get_or_create(
            admin=request.user,
            defaults={
                'contact_number': '',
                'address': '',
                'gender': 'Not Set'
            }
        )

        return render(request, 'adminpages/admin_profile.html', {'data': data})


    
class workerprofile(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request):

        user=request.user.id

        data = workers.objects.filter(admin=user).first()
        context={
            'data':data,
        }
        return render(request,'workerpages/worker_profile.html',context)

class markcompleted(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self, request, action, id):
        try:
            if action == 'completed':
                Response.objects.filter(id=id, status=False).update(status=True)
                print("Response status updated successfully.")
            else:
                print("Action not 'completed' or status is already True.")

            return HttpResponseRedirect('/WorkerpendingTask')
        except Response.DoesNotExist:
            print(f"Response with id {id} does not exist.")
            return HttpResponse(status=404)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return HttpResponse(status=500)

class reject(LoginRequiredMixin, View):
    login_url = common_lib.DEFAULT_REDIRECT_PATH['ROOT']
    def get(self,request,action,id):
        response_record = Response.objects.get(id=id)
        request_record = response_record.requests
        r_id=request_record.id
        ServiceRequests.objects.filter(id=r_id).update(status=False)
    
        response_record.delete()
        return HttpResponseRedirect('/WorkerpendingTask')



def edit_profile(request):
    user = request.user

    try:
        data = users.objects.get(admin=user)
    except users.DoesNotExist:
        data = users.objects.create(admin=user)

    if request.method == "POST":
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        print("POST DATA:", request.POST)  # DEBUG

        data.contact_number = request.POST.get('contact_number') or ""
        data.address = request.POST.get('address') or ""
        data.gender = request.POST.get('gender') or ""

        if request.FILES.get('profile_pic'):
            data.profile_pic = request.FILES.get('profile_pic')

        data.save()

        print("SAVED:", data.contact_number, data.gender, data.address)  # DEBUG

        messages.success(request, "Profile updated successfully!")
        return redirect('userprofile')

    return render(request, 'userpages/edit_profile.html', {'data': data})




class ContactView(View):
    def get(self, request):
        return render(request, 'userpages/contact.html')

    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        return render(request, 'userpages/contact.html', {
            'msg': 'Message sent successfully'
        })


class ViewContacts(View):
    def get(self, request):
        contacts = Contact.objects.all().order_by('-id')
        return render(request, 'adminpages/view_contacts.html', {'contacts': contacts})

    


class AdminPendingRequests(LoginRequiredMixin, View):
    def get(self, request):
        pending = Response.objects.filter(status=False)
        return render(request, 'adminpages/view_response.html', {
            'Response_records': pending
        })
    


class AdminCompletedRequests(LoginRequiredMixin, View):
    def get(self, request):
        completed = Response.objects.filter(status=True)
        return render(request, 'adminpages/view_response.html', {
            'Response_records': completed
        })




from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import users
from .forms import UserProfileForm

class edit_admin_profile(LoginRequiredMixin, View):

    def get(self, request):
        profile, _ = users.objects.get_or_create(admin=request.user)
        return render(request, 'adminpages/edit_profile.html', {'data': profile})

    def post(self, request):
        profile, _ = users.objects.get_or_create(admin=request.user)

        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        profile.contact_number = request.POST.get('contact_number')
        profile.gender = request.POST.get('gender')
        profile.address = request.POST.get('address')

        if request.FILES.get('profile_pic'):
            profile.profile_pic = request.FILES.get('profile_pic')

        profile.save()

        return redirect('admin_user_profile')






@login_required
def change_password(request):
    if request.method == "POST":
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        user = request.user

        # 🔐 Check current password
        if not user.check_password(current):
            messages.error(request, "Current password is incorrect!")
            return redirect('change_password')

        # 🔐 Check new password match
        if new != confirm:
            messages.error(request, "New passwords do not match!")
            return redirect('change_password')

        # 🔐 Set new password
        user.set_password(new)
        user.save()

        # ✅ Keep user logged in
        update_session_auth_hash(request, user)

        messages.success(request, "Password updated successfully!")
        return redirect('userprofile')

    return render(request, 'userpages/change_password.html')







class WorkerProfileView(LoginRequiredMixin, View):
    login_url = '/'

    def get(self, request):
        worker = request.user.workers  # your worker instance
        return render(request, 'workerpages/worker_profile.html', {'data': worker})

    def post(self, request):
        worker = request.user.workers

        # ✅ ONLY update allowed fields
        worker.contact_number = request.POST.get('contact_number', worker.contact_number)
        worker.address = request.POST.get('address', worker.address)

        # profile_pic editable
        if 'profile_pic' in request.FILES:
            worker.profile_pic = request.FILES['profile_pic']

        # 🔒 Fields you want read-only will NOT be updated here
        # e.g., worker.gender, worker.dob, worker.designation remain unchanged

        worker.save()
        messages.success(request, "Profile updated successfully!")
        return render(request, 'workerpages/worker_profile.html', {'data': worker})