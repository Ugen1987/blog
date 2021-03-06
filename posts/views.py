from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Min, Max, Avg, Count
from itertools import chain
from collections import Counter
import datetime
from .models import Post, Comment, Country, City
from .forms import PostForm, CommentForm
from .decorators import superuser_only, user_is_post_author
from django.contrib.contenttypes.models import ContentType
import csv
import os
from django.conf import settings
from matplotlib import pyplot as plt
import six
from django.forms.models import model_to_dict



def post_list(request, date=None):
    if date:
        if 'q' in request.GET:
            query = request.GET.get('q')
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            posts_list = Post.objects.filter(Q(timestamp__month=date.month), Q(timestamp__year=date.year),
                                             Q(title__icontains=query) | Q(content__contains=query)).order_by('-timestamp')
            '''Look for q in comments'''
            posts_with_comments = Post.objects.filter(Q(timestamp__month=date.month), Q(timestamp__year=date.year),
                                                        comment__content__icontains=query).order_by('-timestamp')
            '''Exclude multiple posts'''
            posts_list = set(list(chain(posts_list, posts_with_comments)))
            posts_list = sorted(posts_list, key=lambda x: x.timestamp, reverse=True)
        else:
            date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            posts_list = Post.objects.filter(timestamp__month=date.month,
                                             timestamp__year=date.year).order_by("-timestamp")
    else:
        if 'q' in request.GET:
            query = request.GET.get('q')
            posts_list = Post.objects.filter(Q(title__icontains=query) | Q(content__contains=query)).order_by('-timestamp')
            '''Look for q in comments'''
            posts_with_comments = Post.objects.filter(comment__content__icontains=query).order_by('-timestamp')
            '''Exclude multiple posts'''
            posts_list = set(list(chain(posts_list, posts_with_comments)))
            posts_list = sorted(posts_list, key=lambda x: x.timestamp, reverse=True)
        else:
            posts_list = Post.objects.all().order_by("-timestamp")
    paginator = Paginator(posts_list, 5)
    '''
     Convert datetime object to str '2018-06-01'
     then convert this str to  datetime object '2018-06-01'
    '''
    year_month = []
    posts_timestamps = Post.objects.values_list('timestamp', flat=True).order_by('-timestamp')
    for date in posts_timestamps:
        new_date = date.strftime('%Y-%m')
        new_date_object = datetime.datetime.strptime(new_date, "%Y-%m").date()
        year_month.append(new_date_object)
    """
    Counter - counts number of post occurrences in year_month list
    then make list with tuples [(date(year, month, 1), number of posts)]
    which is number of posts for specific year-month
    """
    unique_year_month = reversed(sorted(list(Counter(year_month).items())))

    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:

        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "post_list.html", locals())


# @login_required(login_url='/login/')
@superuser_only
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        messages.success(request, "The post was successfully created")
        return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, "post_form.html", locals())


def post_detail(request, id=None):
    instance = get_object_or_404(Post, id=id)
    comments = instance.comments

    initial_data = {
        "content_type": instance.get_content_type,
        "object_id": instance.id
    }
    form = CommentForm(request.POST or None, initial=initial_data)
    if form.is_valid():
        c_type = form.cleaned_data.get('content_type')
        content_type = ContentType.objects.get(model=c_type)
        obj_id = form.cleaned_data.get('object_id')
        content_data = form.cleaned_data.get('content')
        new_comment, created = Comment.objects.get_or_create(
                                    user=request.user,
                                    content_type=content_type,
                                    object_id=obj_id,
                                    content=content_data
                                   )
        return redirect("posts:detail", id=instance.id)
    return render(request, "post_detail.html", locals())


# @login_required(login_url='/login/')
@user_is_post_author
def post_update(request, id=None):
    instance = get_object_or_404(Post, id=id)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request, "The post was successfully updated")
        return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, "post_form.html", locals())


@user_is_post_author
def post_delete(request, id=None):
    instance = get_object_or_404(Post, id=id)
    instance.delete()
    messages.success(request, "The post was deleted")
    return redirect("posts:list")


def get_weather(request):
    filename = os.path.join(settings.MEDIA_ROOT, 'weather.csv')
    with open(filename) as f:
        reader = csv.reader(f)
        header_row = next(reader)
        highs = []
        for row in reader:
            highs.append(row[1])
        # fig = plt.figure(dpi=128, figsize=(10, 6))
        plt.plot(highs, c='red')
        plt.title("Daily high temperatures, July 2014", fontsize=24)
        plt.xlabel('', fontsize=16)
        plt.ylabel("Temperature (F)", fontsize=16)
        plt.tick_params(axis='both', which='major', labelsize=16)
        # plt.show()
        plt.savefig(os.path.join(settings.MEDIA_ROOT, 'graphic.jpg'))
        image_path = os.path.join("/media/", "graphic.jpg")
        return render(request, 'graphic.html', {'image_path': image_path})


def read_xml(request):
    import xml.etree.ElementTree as et
    file = os.path.join(settings.MEDIA_ROOT, 'planes.xml')
    tree = et.ElementTree(file=file)
    root = tree.getroot()
    print(root.tag)
    planes = []
    for child in root:
        print('tag:', child.tag)
        plane = {}
        for grandchild in child:
            print('\ttag:', grandchild.tag, grandchild.text)
            plane.update({grandchild.tag: grandchild.text})
        planes.append(plane)
    return render(request, 'planes.html', locals())


def aggregate_countries(request):
    sum_min_population = Country.objects.aggregate(Sum('population'), Min('population'))
    result = Country.objects.aggregate(average_pop=Avg('population'))
    return render(request, 'aggregate_countries.html', locals())


def annotate(request):
    countries = Country.objects.annotate(num_cities=Count('city'))
    print(countries[1].num_cities)

    qss = City.objects.all().values('country__text')

    print(qss)

    # Number of cities with x country
    qs = City.objects.all().values('country__text').annotate(number_of_cities=Count('country__text'))

    print(qs)

    return render(request, 'annotate.html', locals())


def get_country(request, id):
    try:
        post = Country.objects.get(id=id)
    except Country.DoesNotExist:
        return JsonResponse('Nothing', safe=False)
    else:
        return JsonResponse(model_to_dict(post))




