from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User, Permission
from catalog.models import Author, Book, BookInstance, Genre, Language
import datetime

# Create your tests here.

from django.test import TestCase
from django.urls import reverse

from catalog.models import Author

class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 13 authors for pagination tests
        number_of_authors = 13

        for author_id in range(number_of_authors):
            Author.objects.create(
                first_name=f'Christian {author_id}',
                last_name=f'Surname {author_id}',
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/catalog/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        
    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/author_list.html')
        
    def test_pagination_is_ten(self):
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertTrue(len(response.context['author_list']) == 10)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        response = self.client.get(reverse('authors')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] == True)
        self.assertTrue(len(response.context['author_list']) == 3)

class LoanedBookInstanceByUserListViewTest(TestCase):
    def setUp(self):

        test_user1 = User.objects.create_user(username = 'test_user1', password = '123')
        test_user2 = User.objects.create_user(username = 'test_user2', password = '123')

        test_user1.save()
        test_user2.save()

        test_author = Author.objects.create(first_name = 'Bob', last_name = 'Smith')
        test_genre = Genre.objects.create(name = 'Random')
        test_language = Language.objects.create(name = 'Randomish')
        test_book = Book.objects.create(
            title = 'Test Book',
            author = test_author,
            language = test_language,
            isbn = '123456789abc'
        )
        # ManyToMany field can not be assigned directly
        test_genre_all = Genre.objects.all()
        test_book.genre.set(test_genre_all)

        test_author.save()
        test_genre.save()
        test_language.save()
        test_book.save()

        for instance in range(30):
            due_back = timezone.localdate() + datetime.timedelta(days = instance % 5)
            borrower = test_user1 if instance % 2 else test_user2
            status = 'm'
            BookInstance.objects.create(
                book = test_book,
                due_back = due_back,
                imprint = 'test imprint',
                status = status,
                borrower = borrower
            ).save()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(response, '/accounts/login/?next=/catalog/myBooks/')

    def test_logged_in_user_correct_template(self):
        self.client.login(username = 'test_user1', password = '123')
        response = self.client.get(reverse('my-borrowed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].username, 'test_user1')
        self.assertTemplateUsed(response, 'catalog/bookinstance_list_borrowed_user.html')

    def test_borrowed_book_in_list(self):
        self.client.login(username = 'test_user1', password = '123')
        response = self.client.get(reverse('my-borrowed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].username, 'test_user1')

        # check no book in the list
        self.assertTrue('bookinstance_list', response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 0)

        # set some bookinstances on loan
        some_bookinstances = BookInstance.objects.all()[:20]
        for instance in some_bookinstances:
            instance.status = 'o'
            instance.save()

        # check borrowed books in the list
        response = self.client.get(reverse('my-borrowed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].username, 'test_user1')
        self.assertTrue('bookinstance_list', response.context)
        self.assertEqual(len(response.context['bookinstance_list']), 10)
        for instance in response.context['bookinstance_list']:
            self.assertEqual(instance.status, 'o')
            self.assertEqual(instance.borrower, response.context['user'])

    def test_list_ordered_by_due_back(self):
        self.client.login(username = 'test_user1', password = '123')
        response = self.client.get(reverse('my-borrowed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].username, 'test_user1')

        for i, instance in enumerate(response.context['bookinstance_list']):
            if i != len(response.context['bookinstance_list']) - 1:
                next_instance = response.context['bookinstance_list'][i + 1]
                self.assertTrue(instance.due_back <= next_instance.due_back)


class RenewBookInstanceViewTest(TestCase):
    def setUp(self):

        test_user1 = User.objects.create_user(username = 'test_user1', password = '123')
        test_user2 = User.objects.create_user(username = 'test_user2', password = '123')

        test_user1.save()
        test_user2.save()

        permission = Permission.objects.get(name = 'Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Create a book
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(
            title='Book Title',
            isbn='ABCDEFG',
            author=test_author,
            language=test_language,
        )
        
        # Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book) # Direct assignment of many-to-many types not allowed.
        test_book.save()

        # Create a BookInstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user1,
            status='o',
        )

        # Create a BookInstance object for test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user2,
            status='o',
        )

    def test_cannot_access_renew_page_without_permission(self):
        self.client.login(username = 'test_user1', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}))
        self.assertEqual(response.status_code, 302)

    def test_can_access_own_renew_page_with_permission(self):
        self.client.login(username = 'test_user2', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance2.id}))
        self.assertEqual(response.status_code, 200)

    def test_can_access_else_renew_page_with_permission(self):
        self.client.login(username = 'test_user2', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}))
        self.assertEqual(response.status_code, 200)

    def test_correct_renew_view_template(self):
        self.client.login(username = 'test_user2', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}))
        self.assertTemplateUsed(response, 'catalog/book_renew_librarian.html')

    def test_renew_date_initial_3_weeks_in_the_future(self):
        self.client.login(username = 'test_user2', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}))
        expected_initial_date = datetime.date.today() + datetime.timedelta(weeks = 3)
        self.assertEqual(response.context['form'].initial['renewal_date'], expected_initial_date)

    def test_redirect_after_renew(self):
        self.client.login(username = 'test_user2', password = '123')
        response = self.client.get(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}))
        response = self.client.post(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.pk}), {'renewal_date': response.context['form'].initial['renewal_date']})
        self.assertRedirects(response, reverse('all-borrowed'))

    def test_renew_error_message_past(self):
        self.client.login(username = 'test_user2', password = '123')
        invalid_date = datetime.date.today() - datetime.timedelta(weeks = 2)
        response = self.client.post(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}), {'renewal_date': invalid_date})
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_renew_error_message_future(self):
        self.client.login(username = 'test_user2', password = '123')
        invalid_date = datetime.date.today() + datetime.timedelta(weeks = 5)
        response = self.client.post(reverse('renew-book-librarian', kwargs = {'pk': self.test_bookinstance1.id}), {'renewal_date': invalid_date})
        self.assertFormError(response, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')