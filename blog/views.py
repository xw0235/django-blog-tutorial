# -*- coding: utf-8 -*-
import markdown

from markdown.extensions.toc import TocExtension

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.text import slugify
from django.http import JsonResponse

from comments.forms import CommentForm
from .models import Post, Category, Tag, qkCookies, avatarImages, wallpaperImages

import json
import requests
from selenium import webdriver
import time,datetime
import oss2
import re
from requests.exceptions import RequestException

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging





"""
请使用下方的模板引擎方式。
def index(request):
    return HttpResponse("欢迎访问我的博客首页！")
"""

"""
请使用下方真正的首页视图函数
def index(request):
    return render(request, 'blog/index.html', context={
        'title': '我的博客首页',
        'welcome': '欢迎访问我的博客首页'
    })
"""


def index(request):
    post_list = Post.objects.all()
    return render(request, 'blog/index.html', context={'post_list': post_list})


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """
        在视图函数中将模板变量传递给模板是通过给 render 函数的 context 参数传递一个字典实现的，
        例如 render(request, 'blog/index.html', context={'post_list': post_list})，
        这里传递了一个 {'post_list': post_list} 字典给模板。
        在类视图中，这个需要传递的模板变量字典是通过 get_context_data 获得的，
        所以我们复写该方法，以便我们能够自己再插入一些我们自定义的模板变量进去。
        """

        # 首先获得父类生成的传递给模板的字典。
        context = super(IndexView, self).get_context_data(**kwargs)

        # 父类生成的字典中已有 paginator、page_obj、is_paginated 这三个模板变量，
        # paginator 是 Paginator 的一个实例，
        # page_obj 是 Page 的一个实例，
        # is_paginated 是一个布尔变量，用于指示是否已分页。
        # 例如如果规定每页 10 个数据，而本身只有 5 个数据，其实就用不着分页，此时 is_paginated=False。
        # 关于什么是 Paginator，Page 类在 Django Pagination 简单分页：http://zmrenwu.com/post/34/ 中已有详细说明。
        # 由于 context 是一个字典，所以调用 get 方法从中取出某个键对应的值。
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')

        # 调用自己写的 pagination_data 方法获得显示分页导航条需要的数据，见下方。
        pagination_data = self.pagination_data(paginator, page, is_paginated)

        # 将分页导航条的模板变量更新到 context 中，注意 pagination_data 方法返回的也是一个字典。
        context.update(pagination_data)

        # 将更新后的 context 返回，以便 ListView 使用这个字典中的模板变量去渲染模板。
        # 注意此时 context 字典中已有了显示分页导航条所需的数据。
        return context

    def pagination_data(self, paginator, page, is_paginated):
        if not is_paginated:
            # 如果没有分页，则无需显示分页导航条，不用任何分页导航条的数据，因此返回一个空的字典
            return {}

        # 当前页左边连续的页码号，初始值为空
        left = []

        # 当前页右边连续的页码号，初始值为空
        right = []

        # 标示第 1 页页码后是否需要显示省略号
        left_has_more = False

        # 标示最后一页页码前是否需要显示省略号
        right_has_more = False

        # 标示是否需要显示第 1 页的页码号。
        # 因为如果当前页左边的连续页码号中已经含有第 1 页的页码号，此时就无需再显示第 1 页的页码号，
        # 其它情况下第一页的页码是始终需要显示的。
        # 初始值为 False
        first = False

        # 标示是否需要显示最后一页的页码号。
        # 需要此指示变量的理由和上面相同。
        last = False

        # 获得用户当前请求的页码号
        page_number = page.number

        # 获得分页后的总页数
        total_pages = paginator.num_pages

        # 获得整个分页页码列表，比如分了四页，那么就是 [1, 2, 3, 4]
        page_range = paginator.page_range

        if page_number == 1:
            # 如果用户请求的是第一页的数据，那么当前页左边的不需要数据，因此 left=[]（已默认为空）。
            # 此时只要获取当前页右边的连续页码号，
            # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 right = [2, 3]。
            # 注意这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
            right = page_range[page_number:page_number + 2]

            # 如果最右边的页码号比最后一页的页码号减去 1 还要小，
            # 说明最右边的页码号和最后一页的页码号之间还有其它页码，因此需要显示省略号，通过 right_has_more 来指示。
            if right[-1] < total_pages - 1:
                right_has_more = True

            # 如果最右边的页码号比最后一页的页码号小，说明当前页右边的连续页码号中不包含最后一页的页码
            # 所以需要显示最后一页的页码号，通过 last 来指示
            if right[-1] < total_pages:
                last = True

        elif page_number == total_pages:
            # 如果用户请求的是最后一页的数据，那么当前页右边就不需要数据，因此 right=[]（已默认为空），
            # 此时只要获取当前页左边的连续页码号。
            # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 left = [2, 3]
            # 这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]

            # 如果最左边的页码号比第 2 页页码号还大，
            # 说明最左边的页码号和第 1 页的页码号之间还有其它页码，因此需要显示省略号，通过 left_has_more 来指示。
            if left[0] > 2:
                left_has_more = True

            # 如果最左边的页码号比第 1 页的页码号大，说明当前页左边的连续页码号中不包含第一页的页码，
            # 所以需要显示第一页的页码号，通过 first 来指示
            if left[0] > 1:
                first = True
        else:
            # 用户请求的既不是最后一页，也不是第 1 页，则需要获取当前页左右两边的连续页码号，
            # 这里只获取了当前页码前后连续两个页码，你可以更改这个数字以获取更多页码。
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            right = page_range[page_number:page_number + 2]

            # 是否需要显示最后一页和最后一页前的省略号
            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True

            # 是否需要显示第 1 页和第 1 页后的省略号
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True

        data = {
            'left': left,
            'right': right,
            'left_has_more': left_has_more,
            'right_has_more': right_has_more,
            'first': first,
            'last': last,
        }

        return data


"""
请使用下方包含评论列表和评论表单的详情页视图
def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])
    return render(request, 'blog/detail.html', context={'post': post})
"""


def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # 阅读量 +1
    post.increase_views()

    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])
    # 记得在顶部导入 CommentForm
    form = CommentForm()
    # 获取这篇 post 下的全部评论
    comment_list = post.comment_set.all()

    # 将文章、表单、以及文章下的评论列表作为模板变量传给 detail.html 模板，以便渲染相应数据。
    context = {'post': post,
               'form': form,
               'comment_list': comment_list
               }
    return render(request, 'blog/detail.html', context=context)


# 记得在顶部导入 DetailView
class PostDetailView(DetailView):
    # 这些属性的含义和 ListView 是一样的
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get(self, request, *args, **kwargs):
        # 覆写 get 方法的目的是因为每当文章被访问一次，就得将文章阅读量 +1
        # get 方法返回的是一个 HttpResponse 实例
        # 之所以需要先调用父类的 get 方法，是因为只有当 get 方法被调用后，
        # 才有 self.object 属性，其值为 Post 模型实例，即被访问的文章 post
        response = super(PostDetailView, self).get(request, *args, **kwargs)

        # 将文章阅读量 +1
        # 注意 self.object 的值就是被访问的文章 post
        self.object.increase_views()

        # 视图必须返回一个 HttpResponse 对象
        return response

    def get_object(self, queryset=None):
        # 覆写 get_object 方法的目的是因为需要对 post 的 body 值进行渲染
        post = super(PostDetailView, self).get_object(queryset=None)
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            TocExtension(slugify=slugify),
        ])
        post.body = md.convert(post.body)
        post.toc = md.toc
        return post

    def get_context_data(self, **kwargs):
        # 覆写 get_context_data 的目的是因为除了将 post 传递给模板外（DetailView 已经帮我们完成），
        # 还要把评论表单、post 下的评论列表传递给模板。
        context = super(PostDetailView, self).get_context_data(**kwargs)
        form = CommentForm()
        comment_list = self.object.comment_set.all()
        context.update({
            'form': form,
            'comment_list': comment_list
        })
        return context


def archives(request, year, month):
    post_list = Post.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    )
    return render(request, 'blog/index.html', context={'post_list': post_list})


class ArchivesView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        return super(ArchivesView, self).get_queryset().filter(created_time__year=year,
                                                               created_time__month=month
                                                               )


def category(request, pk):
    cate = get_object_or_404(Category, pk=pk)
    post_list = Post.objects.filter(category=cate)
    return render(request, 'blog/index.html', context={'post_list': post_list})


class CategoryView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))
        return super(CategoryView, self).get_queryset().filter(category=cate)


class TagView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super(TagView, self).get_queryset().filter(tags=tag)


"""
def search(request):
    q = request.GET.get('q')
    error_msg = ''

    if not q:
        error_msg = "请输入关键词"
        return render(request, 'blog/index.html', {'error_msg': error_msg})

    post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    return render(request, 'blog/index.html', {'error_msg': error_msg,
                                               'post_list': post_list})
"""

def getList(request):
    tempList = []
    for i in Post.objects.all():
        temp = {}
        temp['id'] = i.id
        temp['title'] = i.title
        temp['created_time'] = datetime.datetime.strftime(i.created_time, '%Y-%m-%d %H:%M:%S') 
        temp['excerpt'] = i.excerpt
        temp['views'] = i.views
        temp['category'] = i.category.name
        temp['author'] = i.author.username
        tempList.append(temp)
    return JsonResponse({'postList':tempList})

def getDetail(request,pk):
    i = Post.objects.get(id = pk)
    post = {}
    post['id'] = i.id
    post['title'] = i.title
    post['created_time'] = datetime.datetime.strftime(i.created_time, '%Y-%m-%d %H:%M:%S') 
    post['body'] = i.body
    post['views'] = i.views
    post['category'] = i.category.name
    post['author'] = i.author.username
    return JsonResponse({'post':post})


def qklogin():
    driver = webdriver.PhantomJS(executable_path='/root/phantomjs')
    driver.get('http://588ku.com/')
    time.sleep(1)

    driver.execute_script('qqLogin();')

    handles = driver.window_handles

    driver.switch_to_window(handles[1])
    time.sleep(3)

    driver.switch_to_frame('ptlogin_iframe')

    driver.find_element_by_id('switcher_plogin').click()
    time.sleep(1)
    driver.find_element_by_id('u').send_keys('zh***')
    driver.find_element_by_id('p').send_keys('mm*******')
    driver.find_element_by_id('login_button').click()

    driver.switch_to_window(handles[0])
    
    time.sleep(5)

    cookies = driver.get_cookies()
    
    qkCookies.objects.create(QQCookies=cookies)
    
    driver.quit()


def get_psd_url(id):
    url='http://588ku.com/index.php?m=element&a=downpsd&id='+id+'&tab='

    cookies = eval(qkCookies.objects.last().QQCookies)
    cookies = [(item["name"],item["value"]) for item in cookies]
    cookies = dict(cookies)

    r = requests.get(url,cookies=cookies)
    if '请先登录'.decode('utf-8') == r.text:
        return '失败了，晚点儿再来试试吧！'
    
    download_url = json.loads(r.text)['url']
    if ('.rar'in download_url) or ('.zip' in download_url) or ('.psd' in download_url):
        return download_url
    return '没有找到要下载的资源！'

def get_png_url(id):
    url='http://588ku.com/index.php?m=element&a=down&id='+id+'&tab='

    cookies = eval(qkCookies.objects.last().QQCookies)
    cookies = [(item["name"],item["value"]) for item in cookies]
    cookies = dict(cookies)

    r = requests.get(url,cookies=cookies)
    if '请先登录'.decode('utf-8') == r.text:
        # qklogin()
        return '失败了，晚点儿再来试试吧！'
    
    download_url = json.loads(r.text)['url']
    if ('.rar'in download_url) or ('.zip' in download_url) or ('.png' in download_url) or ('.gif' in download_url):
        return download_url
    return '没有找到要下载的资源！'

def qk(request):
    download_url = []
    if request.method == 'POST':
        url = request.POST['url']

        id = url.split('/')[-1].split('.')[0]

        download_url.append(get_psd_url(id))
        download_url.append(get_png_url(id))
        
        return render(request, 'blog/qk.html', context={'url': url,'psd_download_url' : download_url[0],'png_download_url': download_url[1]})
    else:
        return render(request, 'blog/qk.html')


def get_one_page(url):
    # oss   https://xhxz-img.oss-cn-shanghai.aliyuncs.com/
    auth = oss2.Auth('LTAIllkspFRf3e1a', '48FaHkoqhyIfo26H3iwTu6dXMgGVQV')
    bucket = oss2.Bucket(auth, 'http://oss-cn-shanghai.aliyuncs.com', 'xhxz-img')

    # # cos 	https://xhxz-1252795282.piccd.myqcloud.com/     https://xhxz-1252795282.image.myqcloud.com/

    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    # secret_id = 'AKIDkmgOtB1DvVu7gL7HRRKWbWVXaghXffS4'      
    # secret_key = 'tw44voz40kHgx3ABHG6j9NOHyTr5B6oK'      
    # region = 'ap-chengdu'     
    # token = None                
    # scheme = 'https'            
    # config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    # client = CosS3Client(config)
    

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            html = response.text
            pattern = re.compile('<img.*?data-src="(.*?)".*?>', re.S)
            pattern2 = re.compile('<h2 class="rich_media_title" id="activity-name">(.*?)</h2>', re.S)
            title = re.findall(pattern2,html)[0].strip()
            items = re.findall(pattern, html)   
            
            if '头像'.decode('utf-8') in title or '情头'.decode('utf-8') in title:
                for item in items:
                    print item
                    if 'mmbiz_jpg' in item:
                        name = 'xhxz_blog/avatar/jpg_' + item.split('/')[4] + '.jpg'
                        input = requests.get(item)
                        # 上传oss
                        bucket.put_object( name, input)
                        # # 上传cos
                        # response = client.put_object(
                        #     Bucket='xhxz-1252795282',
                        #     Body=input.content,
                        #     Key=name,
                        # )
                        # 存数据库
                        avatarImages.objects.create(url='https://xhxz-img.oss-cn-shanghai.aliyuncs.com/'+name)

            elif '壁纸'.decode('utf-8') in title:
                for item in items:
                    print item
                    if 'mmbiz_jpg' in item:
                        name = 'xhxz_blog/wallpaper/jpg_' + item.split('/')[4] + '.jpg'
                        input = requests.get(item)
                        # 上传oss
                        bucket.put_object( name, input)
                        # # 上传cos
                        # response = client.put_object(
                        #     Bucket='xhxz-1252795282',
                        #     Body=input.content,
                        #     Key=name,
                        # )
                        # 存数据库
                        wallpaperImages.objects.create(url='https://xhxz-img.oss-cn-shanghai.aliyuncs.com/'+name)
            
            else:
                print '其它'
                    
        return None
    except RequestException:
        return None


def getimgs(request):
    if request.method == 'POST':
        src = request.POST['src']
        get_one_page(src)
        return render(request, 'blog/qk.html', context={'src': src,'err' : '获取完成!'})
    else:
        return render(request, 'blog/qk.html')

def getavatar(request,pk):
    tempList = []
    pk = int(pk)
    start = (pk-1)*20
    end = pk*20
    for i in avatarImages.objects.all().order_by("-id")[start:end]:
        temp = {}
        temp['id'] = i.id
        temp['url'] = i.url
        tempList.append(temp)
    return JsonResponse({'avatars':tempList})


def getwallpaper(request,pk):
    tempList = []
    pk = int(pk)
    start = (pk-1)*20
    end = pk*20
    for i in wallpaperImages.objects.all().order_by("-id")[start:end]:
        temp = {}
        temp['id'] = i.id
        temp['url'] = i.url
        tempList.append(temp)
    return JsonResponse({'wallpapers':tempList})

def delavatar(request,pk):
    avatarImages.objects.get(id=pk).delete()
    return JsonResponse({'err':'success'})


def delwallpaper(request,pk):
    wallpaperImages.objects.get(id=pk).delete()
    return JsonResponse({'err':'success'})
