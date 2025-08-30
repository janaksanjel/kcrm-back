from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('shop_owner', 'Shop Owner'),
        ('super_admin', 'Super Admin'),
        ('kitchen_user', 'Kitchen User'),
        ('staff', 'Staff'),
    ]
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='shop_owner')
    shop_name = models.CharField(max_length=100, blank=True, null=True)
    restaurant_id = models.IntegerField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    unhashed_password = models.CharField(max_length=128, blank=True, null=True)  # Store unhashed password for kitchen users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ShopOwnerFeatures(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='features')
    dashboard = models.BooleanField(default=True)
    inventory = models.BooleanField(default=True)
    billing = models.BooleanField(default=True)
    udhaar = models.BooleanField(default=True)
    expenses = models.BooleanField(default=True)
    reports = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

class EconomicYear(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='economic_years')
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'name']

class NotificationSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    low_stock_alerts = models.BooleanField(default=True)
    payment_reminders = models.BooleanField(default=True)
    daily_reports = models.BooleanField(default=False)
    system_updates = models.BooleanField(default=True)
    login_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SecuritySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_settings')
    two_factor_enabled = models.BooleanField(default=False)
    login_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SecurityActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('profile_update', 'Profile Update'),
        ('settings_change', 'Settings Change'),
        ('session_terminate', 'Session Terminate'),
        ('failed_login', 'Failed Login'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField()
    device_info = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class StoreConfig(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store_config')
    store_url = models.CharField(max_length=255, blank=True, null=True)
    store_shortcode = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Convert empty strings to None to avoid unique constraint issues
        if not self.store_url or not self.store_url.strip():
            self.store_url = None
        if not self.store_shortcode or not self.store_shortcode.strip():
            self.store_shortcode = None
        
        # Check uniqueness for non-null URLs
        if self.store_url:
            existing = StoreConfig.objects.filter(
                store_url=self.store_url
            ).exclude(user=self.user).first()
            if existing:
                raise ValueError('This URL is already taken')
        
        # Check uniqueness for non-null shortcodes
        if self.store_shortcode:
            existing = StoreConfig.objects.filter(
                store_shortcode=self.store_shortcode
            ).exclude(user=self.user).first()
            if existing:
                raise ValueError('This shortcode is already taken')
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'store_config'
        verbose_name = 'Store Configuration'
        verbose_name_plural = 'Store Configurations'