"""
Test suite for Contact Form API endpoint.

This module contains comprehensive tests for the ContactSubmissionCreateAPIView
including validation, error handling, email functionality, and edge cases.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.core import mail
from django.conf import settings

from home.models import ContactSubmission
from home.serializers import ContactSubmissionSerializer


class ContactSubmissionAPITestCase(APITestCase):
    """
    Test case for Contact Form API endpoint.
    Tests POST requests to /api/contact/ endpoint.
    """
    
    def setUp(self):
        """Set up test data for each test method."""
        self.contact_url = reverse('contact-api')  # /PerpexBistro/api/contact/
        self.valid_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'message': 'This is a test message for the contact form API endpoint.'
        }
    
    def test_create_contact_submission_success(self):
        """Test successful contact form submission via API."""
        response = self.client.post(self.contact_url, self.valid_data, format='json')
        
        # Check response status and structure
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('success'))
        self.assertIn('message', response.data)
        self.assertIn('Thank you for your message', response.data['message'])
        
        # Check database record was created
        self.assertEqual(ContactSubmission.objects.count(), 1)
        
        submission = ContactSubmission.objects.first()
        self.assertEqual(submission.name, 'John Doe')
        self.assertEqual(submission.email, 'john.doe@example.com')
        self.assertIn('test message', submission.message)
    
    def test_email_sent_on_submission(self):
        """Test that email is sent when contact form is submitted."""
        with patch('home.views.send_mail') as mock_send_mail:
            mock_send_mail.return_value = True
            
            response = self.client.post(self.contact_url, self.valid_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify email was attempted to be sent
            mock_send_mail.assert_called_once()
            args, kwargs = mock_send_mail.call_args
            
            # Check email arguments
            self.assertIn('New Contact Submission from John Doe', args[0])  # subject
            self.assertIn('john.doe@example.com', args[1])  # message body
    
    def test_validation_missing_name(self):
        """Test validation error when name is missing."""
        invalid_data = self.valid_data.copy()
        del invalid_data['name']
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(ContactSubmission.objects.count(), 0)
    
    def test_validation_empty_name(self):
        """Test validation error when name is empty."""
        invalid_data = self.valid_data.copy()
        invalid_data['name'] = ''
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
    
    def test_validation_name_too_short(self):
        """Test validation error when name is too short."""
        invalid_data = self.valid_data.copy()
        invalid_data['name'] = 'J'
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('at least 2 characters', str(response.data['name']))
    
    def test_validation_name_too_long(self):
        """Test validation error when name is too long."""
        invalid_data = self.valid_data.copy()
        invalid_data['name'] = 'J' * 101  # 101 characters
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('no more than 100 characters', str(response.data['name']))
    
    def test_validation_missing_email(self):
        """Test validation error when email is missing."""
        invalid_data = self.valid_data.copy()
        del invalid_data['email']
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_validation_invalid_email_format(self):
        """Test validation error when email format is invalid."""
        invalid_emails = [
            'invalid-email',
            'invalid.email.com',
            '@example.com',
            'user@',
            'user name@example.com',
            ''
        ]
        
        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                invalid_data = self.valid_data.copy()
                invalid_data['email'] = invalid_email
                
                response = self.client.post(self.contact_url, invalid_data, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('email', response.data)
    
    def test_validation_missing_message(self):
        """Test validation error when message is missing."""
        invalid_data = self.valid_data.copy()
        del invalid_data['message']
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
    
    def test_validation_empty_message(self):
        """Test validation error when message is empty."""
        invalid_data = self.valid_data.copy()
        invalid_data['message'] = ''
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
    
    def test_validation_message_too_short(self):
        """Test validation error when message is too short."""
        invalid_data = self.valid_data.copy()
        invalid_data['message'] = 'Short'  # Less than 10 characters
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertIn('at least 10 characters', str(response.data['message']))
    
    def test_validation_message_too_long(self):
        """Test validation error when message is too long."""
        invalid_data = self.valid_data.copy()
        invalid_data['message'] = 'A' * 2001  # 2001 characters
        
        response = self.client.post(self.contact_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
        self.assertIn('cannot exceed 2000 characters', str(response.data['message']))
    
    def test_email_normalization(self):
        """Test that email addresses are normalized (lowercased)."""
        data = self.valid_data.copy()
        data['email'] = 'John.DOE@EXAMPLE.COM'
        
        response = self.client.post(self.contact_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission = ContactSubmission.objects.first()
        self.assertEqual(submission.email, 'john.doe@example.com')
    
    def test_text_field_trimming(self):
        """Test that text fields are trimmed of whitespace."""
        data = {
            'name': '  John Doe  ',
            'email': '  john.doe@example.com  ',
            'message': '  This is a test message with spaces.  '
        }
        
        response = self.client.post(self.contact_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission = ContactSubmission.objects.first()
        self.assertEqual(submission.name, 'John Doe')
        self.assertEqual(submission.email, 'john.doe@example.com')
        self.assertEqual(submission.message, 'This is a test message with spaces.')
    
    def test_multiple_submissions(self):
        """Test multiple contact submissions can be created."""
        # First submission
        response1 = self.client.post(self.contact_url, self.valid_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second submission with different data
        data2 = {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'message': 'This is another test message from a different user.'
        }
        response2 = self.client.post(self.contact_url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Check both records exist
        self.assertEqual(ContactSubmission.objects.count(), 2)
    
    def test_email_failure_does_not_break_api(self):
        """Test that email sending failure doesn't break the API response."""
        with patch('home.views.send_mail') as mock_send_mail:
            mock_send_mail.side_effect = Exception('Email server error')
            
            response = self.client.post(self.contact_url, self.valid_data, format='json')
            
            # API should still succeed even if email fails
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data.get('success'))
            
            # Record should still be created
            self.assertEqual(ContactSubmission.objects.count(), 1)
    
    def test_response_data_structure(self):
        """Test the structure of successful API response."""
        response = self.client.post(self.contact_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check required response fields
        required_fields = ['id', 'name', 'email', 'message', 'submitted_at', 'success']
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check data types
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['success'], bool)
        self.assertTrue(response.data['success'])


class ContactSubmissionSerializerTestCase(TestCase):
    """
    Test case for ContactSubmissionSerializer.
    Tests serializer validation logic independently.
    """
    
    def setUp(self):
        """Set up test data for serializer tests."""
        self.valid_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'message': 'This is a test message for serializer validation.'
        }
    
    def test_serializer_valid_data(self):
        """Test serializer with valid data."""
        serializer = ContactSubmissionSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        submission = serializer.save()
        self.assertEqual(submission.name, 'John Doe')
        self.assertEqual(submission.email, 'john.doe@example.com')
    
    def test_serializer_validation_errors(self):
        """Test serializer validation error messages."""
        # Test with invalid data
        invalid_data = {
            'name': '',
            'email': 'invalid-email',
            'message': 'Short'
        }
        
        serializer = ContactSubmissionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        # Check error messages exist for all fields
        self.assertIn('name', serializer.errors)
        self.assertIn('email', serializer.errors)
        self.assertIn('message', serializer.errors)