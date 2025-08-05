from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # default
    page_size_query_param = 'page_size'  # enable ?page_size=XX
    max_page_size = 100  # maximum to avoid abuses
