from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from restaurant_management.utils import is_valid_email, normalize_email

@api_view(['POST'])
def staff_login(request):
	try:
		email = request.data.get('email')
		password = request.data.get('password')
		
		if not email or not password:
			return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

		# Validate email format
		if not is_valid_email(email):
			return Response({'error': 'Please provide a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

		# Normalize email for consistent comparison
		email = normalize_email(email)

		user = authenticate(request, username=email, password=password)
		if user is not None and user.is_staff:
			return Response({'success': 'Login successful.'}, status=status.HTTP_200_OK)
		return Response({'error': 'Invalid credentials or not a staff member.'}, status=status.HTTP_401_UNAUTHORIZED)
	except Exception as e:
		return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
