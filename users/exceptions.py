"""
Custom exception handler so all API errors return JSON (no HTML).
"""
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            if 'message' not in response.data and 'detail' in response.data:
                detail = response.data['detail']
                response.data = {'status': 'error', 'message': detail[0] if isinstance(detail, list) else str(detail)}
            elif 'status' not in response.data:
                response.data = {'status': 'error', 'message': response.data.get('message', str(response.data))}
        else:
            response.data = {'status': 'error', 'message': str(response.data)}
        response['Content-Type'] = 'application/json'
        return response
    return Response(
        {'status': 'error', 'message': 'An unexpected error occurred. Please try again.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content_type='application/json',
    )
