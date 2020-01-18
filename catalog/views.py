import datetime
from django.urls import reverse
from django.views import generic
from catalog.models import Author
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from catalog.forms import RenewBookForm, NewUserForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import Book, Author, Genre, BookInstance, Language
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Create your views here.

def index(request):
	"""View function for home page of site."""

	# Generate counts of some of the main objects
	num_books = Book.objects.all().count()
	num_instances = BookInstance.objects.all().count()

	# Available books (status = 'a')
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()

	# The 'all()' is implied by default.    
	num_authors = Author.objects.count()
	num_languages = Language.objects.count()

	# Number of visits to this view, as counted in the session variable.
	num_visits = request.session.get('num_visits', 0)
	request.session['num_visits'] = num_visits + 1

	context = {
		'num_books': num_books,
		'num_instances': num_instances,
		'num_instances_available': num_instances_available,
		'num_authors': num_authors,
		'num_visits': num_visits,
	}

	# Render the HTML template index.html with the data in the context variable
	return render(request, 'index.html', context=context)

def register(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect("index")
		else:
			for msg in form.error_messages:
				print(msg)

	form = NewUserForm
	return render(request,"catalog/register.html",context={"form":form})

class UserUpdate(UpdateView):
	model = User
	fields = ['first_name', 'last_name']
	template_name = 'catalog/update_user.html'
	success_url = reverse_lazy('index')

class UserDetailView(generic.DetailView):
	model = User
	template_name = 'catalog/user_detail.html'

class BookListView(generic.ListView):
	model = Book
	paginate_by = 10

class BookDetailView(generic.DetailView):
	model = Book

class AuthorListView(generic.ListView):
	model = Author

class AuthorDetailView(generic.DetailView):
	model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to current user."""
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 10

	def get_queryset(self):
		return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LentBooksListView(LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to users."""
	model = BookInstance
	template_name = 'catalog/lentbooks.html'
	paginate_by = 10

	def get_queryset(self):
		return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
	"""View function for renewing a specific BookInstance by librarian."""
	book_instance = get_object_or_404(BookInstance, pk=pk)

	# If this is a POST request then process the Form data
	if request.method == 'POST':

		# Create a form instance and populate it with data from the request (binding):
		form = RenewBookForm(request.POST)

		# Check if the form is valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required (here we just write it to the model due_back field)
			book_instance.due_back = form.cleaned_data['renewal_date']
			book_instance.save()

			# redirect to a new URL:
			return HttpResponseRedirect(reverse('borrowed') )

	# If this is a GET (or any other method) create the default form.
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

	context = {
		'form': form,
		'book_instance': book_instance,
	}

	return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(CreateView):
	model = Author
	fields = '__all__'
	# initial = {'date_of_death': '05/01/2018'}

class AuthorUpdate(UpdateView):
	model = Author
	fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

class AuthorDelete(DeleteView):
	model = Author
	success_url = reverse_lazy('authors')

class BookCreate(PermissionRequiredMixin, CreateView):
	model = Book
	fields = '__all__'
	permission_required = 'catalog.can_mark_returned'

class BookUpdate(PermissionRequiredMixin, UpdateView):
	model = Book
	fields = '__all__'
	permission_required = 'catalog.can_mark_returned'

class BookDelete(PermissionRequiredMixin, DeleteView):
	model = Book
	success_url = reverse_lazy('books')
	permission_required = 'catalog.can_mark_returned'