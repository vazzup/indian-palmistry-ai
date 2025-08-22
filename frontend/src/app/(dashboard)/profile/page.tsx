'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { 
  User, 
  Mail, 
  Calendar,
  Shield,
  Download,
  Trash2,
  Eye,
  EyeOff,
  Save,
  Camera 
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/lib/auth';

const profileSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .min(2, 'Name must be at least 2 characters')
    .max(50, 'Name cannot exceed 50 characters'),
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = React.useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
    },
  });

  React.useEffect(() => {
    if (user) {
      reset({
        name: user.name,
        email: user.email,
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: ProfileFormData) => {
    try {
      setIsSaving(true);
      
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Profile update:', data);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    reset();
    setIsEditing(false);
  };

  const handleDeleteAccount = async () => {
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await logout();
      router.push('/');
    } catch (error) {
      console.error('Failed to delete account:', error);
    }
  };

  const handleExportData = async () => {
    try {
      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Create and download a JSON file with user data
      const data = {
        user: user,
        exportDate: new Date().toISOString(),
        analyses: [], // Would contain actual user analyses
        conversations: [], // Would contain actual conversations
      };
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `palmistry-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <DashboardLayout
      title="Profile Settings"
      description="Manage your account and privacy settings"
    >
      <div className="max-w-4xl space-y-6">
        {/* Profile Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="w-5 h-5 mr-2" />
              Profile Information
            </CardTitle>
            <CardDescription>
              Update your personal information and account details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Profile Picture */}
              <div className="flex items-center space-x-6">
                <div className="w-20 h-20 bg-saffron-100 rounded-full flex items-center justify-center">
                  {user?.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-20 h-20 rounded-full object-cover"
                    />
                  ) : (
                    <User className="w-8 h-8 text-saffron-600" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{user?.name}</h3>
                  <p className="text-sm text-gray-600">
                    Member since {user?.created_at ? formatDate(user.created_at) : 'Unknown'}
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    disabled
                  >
                    <Camera className="w-4 h-4 mr-2" />
                    Change Photo (Coming Soon)
                  </Button>
                </div>
              </div>

              {/* Form Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  {...register('name')}
                  label="Full Name"
                  placeholder="Enter your full name"
                  error={errors.name?.message}
                  disabled={!isEditing || isSaving}
                />
                
                <Input
                  {...register('email')}
                  type="email"
                  label="Email Address"
                  placeholder="Enter your email"
                  error={errors.email?.message}
                  disabled={!isEditing || isSaving}
                  helpText="Email changes require verification"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div>
                  {isEditing && (
                    <p className="text-sm text-gray-600">
                      {isDirty ? 'You have unsaved changes' : 'Make changes to your profile above'}
                    </p>
                  )}
                </div>
                <div className="flex space-x-3">
                  {isEditing ? (
                    <>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleCancel}
                        disabled={isSaving}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        loading={isSaving}
                        disabled={!isDirty || isSaving}
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {isSaving ? 'Saving...' : 'Save Changes'}
                      </Button>
                    </>
                  ) : (
                    <Button
                      type="button"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit Profile
                    </Button>
                  )}
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Privacy & Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="w-5 h-5 mr-2" />
              Privacy & Security
            </CardTitle>
            <CardDescription>
              Manage your privacy settings and account security
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Password Change */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Password</h4>
                <p className="text-sm text-gray-600">
                  Change your password to keep your account secure
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => router.push('/reset')}
              >
                Change Password
              </Button>
            </div>

            {/* Two-Factor Authentication */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Two-Factor Authentication</h4>
                <p className="text-sm text-gray-600">
                  Add an extra layer of security to your account
                </p>
              </div>
              <Button
                variant="outline"
                disabled
              >
                Coming Soon
              </Button>
            </div>

            {/* Active Sessions */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Active Sessions</h4>
                <p className="text-sm text-gray-600">
                  Manage your active login sessions across devices
                </p>
              </div>
              <Button
                variant="outline"
                disabled
              >
                Manage Sessions
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="w-5 h-5 mr-2" />
              Data Management
            </CardTitle>
            <CardDescription>
              Export or delete your personal data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Export Data */}
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Export Your Data</h4>
                <p className="text-sm text-gray-600">
                  Download a copy of all your palmistry readings and conversations
                </p>
              </div>
              <Button
                variant="outline"
                onClick={handleExportData}
              >
                <Download className="w-4 h-4 mr-2" />
                Export Data
              </Button>
            </div>

            {/* Delete Account */}
            <div className="flex items-center justify-between p-4 border border-red-200 rounded-lg bg-red-50">
              <div>
                <h4 className="font-medium text-red-900">Delete Account</h4>
                <p className="text-sm text-red-600">
                  Permanently delete your account and all associated data
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(true)}
                className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="text-red-900">Delete Account</CardTitle>
                <CardDescription>
                  This action cannot be undone. All your data will be permanently deleted.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">
                      <strong>This will permanently delete:</strong>
                    </p>
                    <ul className="text-sm text-red-700 mt-2 space-y-1">
                      <li>• Your profile and account information</li>
                      <li>• All palm reading analyses</li>
                      <li>• All conversation history</li>
                      <li>• Uploaded images</li>
                    </ul>
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button
                      variant="outline"
                      onClick={() => setShowDeleteConfirm(false)}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleDeleteAccount}
                      className="flex-1 bg-red-600 hover:bg-red-700"
                    >
                      Delete Account
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}