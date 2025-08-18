
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate

class StaffLoginAPIView(APIView):
	def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')
		if not email or not password:
			return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

		user = authenticate(request, username=email, password=password)
		if user is not None and user.is_staff:
			return Response({'success': 'Login successful.'}, status=status.HTTP_200_OK)
class StaffLoginAPIView(APIView):
    def post(self, request):
		email = request.data.get('email')
		password = request.data.get('password')
		if not email or not password:
			return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

		user = authenticate(request, username=email, password=password)
		if user is not None and user.is_staff:
			return Response({'success': 'Login successful.'}, status=status.HTTP_200_OK)
		return Response({'error': 'Invalid credentials or not a staff member.'}, status=status.HTTP_401_UNAUTHORIZED)
