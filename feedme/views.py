from django.views.generic import ListView, FormView, CreateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render

from infuse.auth.permissions import LoginRequiredMixin

from .models import Feed, FeedItem, Category
from .forms import AddFeedForm, ImportFeedForm
from .google_takeout import GoogleReaderTakeout
from .mixins import AjaxableResponseMixin


class FeedList(LoginRequiredMixin, ListView):
    """
    Show the feed list for the logged in user.
    @todo - need to protect ti with logged in user
    """
    template_name = 'feedme/feed_list.html'
    context_object_name = 'feed_items'

    def update_feeds(self, user):
        for feed in Feed.objects.filter(user=user):
            # FIXME(halldor): this will fail if a feed has been created and is being processed by celery (has no last_upated)
            feed.update()
        return True

    def get_queryset(self):
        # Update the feed on page load..
        self.update_feeds(self.request.user)
        items = FeedItem.objects.my_feed_items(self.request.user).un_read()

        if self.kwargs.get('category', None):
            return items.category(self.kwargs.get('category'))

        if self.kwargs.get('feed_id', None):
            return items.filter(feed__id=self.kwargs.get('feed_id'))

        return items

    def get_context_data(self, **kwargs):
        context = super(FeedList, self).get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(user=self.request.user)
        context['add_form'] = AddFeedForm()

        return context


class AddView(LoginRequiredMixin, AjaxableResponseMixin, CreateView):
    form_class = AddFeedForm
    model = Feed


def import_from_takeout(request):
    form = ImportFeedForm(request.POST, request.FILES, user=request.user)
    logger.debug("Post data: %s" % request.POST)
    if request.method.lower() == "post" and form.is_valid():
        logger.debug("Import form valid.")
        takeout = GoogleReaderTakeout(request.FILES['archive'])
        for data in takeout.subscriptions():
            if not data['xmlUrl']:
                logger.info("Found feed without url. Dumping %s." % data['title'])
                continue
            if data['category']:
                category, created = Category.objects.get_or_create(name=data['category'], user=request.user)
                if created:
                    logger.info("Created new category for user '%s': '%s'" % (request.user, data['category']))
            else:
                category = form.cleaned_data['category']
            Feed.objects.get_or_create(
                url=data['xmlUrl'], title=data['title'],
                user=request.user, last_update=None,
                category=category
            )
        return HttpResponseRedirect(reverse('feedme-feed-list'))

    context = {
        'add_form': AddFeedForm(),
        'form': form,
    }

    return render(request, 'feedme/takeout_form.html', context)
