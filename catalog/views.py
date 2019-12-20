from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from catalog.models import Book, BookInstance, Author, Genre
from catalog.forms import RenewBookForm
import datetime

# Create your views here.

def index(request):

    num_books = Book.objects.all().count()
    num_book_instances = BookInstance.objects.all().count()

    num_book_instances_available = BookInstance.objects.filter(status__exact='a').count()

    num_authors = Author.objects.count()

    num_books_literature = Book.objects.filter(genre__name__icontains = '文學').count()
    num_genres = Genre.objects.count()
    num_books_cat = Book.objects.filter(title__icontains = '貓').count()

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_book_instances': num_book_instances,
        'num_book_instances_available': num_book_instances_available,
        'num_authors': num_authors,
        'num_books_literature': num_books_literature,
        'num_genres': num_genres,
        'num_books_cat': num_books_cat,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context = context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_modify_book'
    model = Book
    fields = '__all__'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_modify_book'
    model = Book
    fields = '__all__'

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_modify_book'
    model = Book
    success_url = reverse_lazy('books')


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_modify_author'
    model = Author
    fields = '__all__'

class AuthorUpdate(UpdateView):
    permission_required = 'catalog.can_modify_author'
    model = Author
    fields = '__all__'
    exclude = ['id']

class AuthorDelete(DeleteView):
    permission_required = 'catalog.can_modify_author'
    model = Author
    success_url = reverse_lazy('authors')

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower = self.request.user).filter(status__exact = 'o').order_by('due_back')

class LoanedBooksLibrarianListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_librarian.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact = 'o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk = pk)

    if request.method == 'POST':
        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        default_renewal_date = datetime.date.today() + datetime.timedelta(weeks = 3)
        form = RenewBookForm(initial = {'renewal_date': default_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)