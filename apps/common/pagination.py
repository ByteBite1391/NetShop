"""
Standard pagination.

Page-number pagination with a consistent envelope that wraps the result list in
the same `success/data` shape used everywhere. Page size and a max page size
guard against abusive `?page_size=` values.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                "success": True,
                "message": None,
                "data": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "total_pages": self.page.paginator.num_pages,
                    "results": data,
                },
            }
        )
