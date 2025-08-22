'use client';

import React from 'react';
import { Camera, Upload, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import type { UploadProgress } from '@/types';

/**
 * Props for the MobileImageUpload component
 */
interface MobileImageUploadProps {
  /** Callback function called when files are successfully validated and ready for upload */
  onUpload: (files: File[]) => void;
  /** Maximum number of files allowed (default: 2) */
  maxFiles?: number;
  /** Maximum file size in MB (default: 15) */
  maxSize?: number;
  /** Whether upload is in progress (disables interactions) */
  isUploading?: boolean;
}

/**
 * A mobile-first image upload component designed for palm reading images.
 * 
 * Features:
 * - Mobile-optimized drag & drop interface
 * - File validation (JPEG/PNG, size limits, magic byte verification)
 * - Support for up to 2 images (left/right palm)
 * - Camera capture support with environment camera preference
 * - Real-time preview with thumbnail generation
 * - Individual file removal capabilities
 * - Cultural design with saffron color scheme
 * - Comprehensive error handling and user feedback
 * 
 * Validation includes:
 * - File type checking (JPEG/PNG only)
 * - File size limits (configurable, default 15MB)
 * - Magic byte verification for security
 * - Maximum file count enforcement
 * 
 * @example
 * ```tsx
 * <MobileImageUpload
 *   onUpload={handleFileUpload}
 *   maxFiles={2}
 *   maxSize={10}
 *   isUploading={uploadInProgress}
 * />
 * ```
 */
export const MobileImageUpload: React.FC<MobileImageUploadProps> = ({
  onUpload,
  maxFiles = 2,
  maxSize = 15,
  isUploading = false,
}) => {
  const [isDragging, setIsDragging] = React.useState(false);
  const [previews, setPreviews] = React.useState<{ 
    left?: { file: File; url: string }; 
    right?: { file: File; url: string }; 
  }>({});
  const [errors, setErrors] = React.useState<string[]>([]);
  const [isValidating, setIsValidating] = React.useState(false);
  
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const cameraInputRef = React.useRef<HTMLInputElement>(null);
  
  // Validate file format and size
  const validateFile = async (file: File): Promise<{ isValid: boolean; error?: string }> => {
    // Check file type
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      return { isValid: false, error: 'Only JPEG and PNG files are allowed' };
    }
    
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return { isValid: false, error: `File size must be less than ${maxSize}MB` };
    }
    
    // Check magic bytes (basic validation)
    try {
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      
      const isValidJPEG = bytes[0] === 0xFF && bytes[1] === 0xD8;
      const isValidPNG = bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47;
      
      if (!isValidJPEG && !isValidPNG) {
        return { isValid: false, error: 'Invalid image format detected' };
      }
    } catch (error) {
      return { isValid: false, error: 'Unable to validate file format' };
    }
    
    return { isValid: true };
  };
  
  const handleFiles = async (files: FileList) => {
    const fileArray = Array.from(files);
    
    if (fileArray.length > maxFiles) {
      setErrors([`Maximum ${maxFiles} images allowed`]);
      return;
    }
    
    setIsValidating(true);
    setErrors([]);
    
    const validationResults = await Promise.all(
      fileArray.map(async (file) => ({
        file,
        validation: await validateFile(file),
      }))
    );
    
    const validFiles = validationResults.filter(({ validation }) => validation.isValid);
    const invalidFiles = validationResults.filter(({ validation }) => !validation.isValid);
    
    // Set errors for invalid files
    if (invalidFiles.length > 0) {
      setErrors(invalidFiles.map(({ validation }) => validation.error!));
    }
    
    // Create previews for valid files
    if (validFiles.length > 0) {
      const newPreviews: typeof previews = {};
      
      validFiles.forEach(({ file }, index) => {
        const url = URL.createObjectURL(file);
        if (index === 0) {
          newPreviews.left = { file, url };
        } else if (index === 1) {
          newPreviews.right = { file, url };
        }
      });
      
      // Clean up old previews
      Object.values(previews).forEach(preview => {
        if (preview) URL.revokeObjectURL(preview.url);
      });
      
      setPreviews(newPreviews);
      
      // Call upload handler
      onUpload(validFiles.map(({ file }) => file));
    }
    
    setIsValidating(false);
  };
  
  const handleDrop = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (isUploading) return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  }, [isUploading]);
  
  const handleDragOver = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!isUploading) {
      setIsDragging(true);
    }
  }, [isUploading]);
  
  const handleDragLeave = React.useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  };
  
  const removePreview = (position: 'left' | 'right') => {
    const preview = previews[position];
    if (preview) {
      URL.revokeObjectURL(preview.url);
      setPreviews(prev => ({ ...prev, [position]: undefined }));
    }
  };
  
  const clearAll = () => {
    Object.values(previews).forEach(preview => {
      if (preview) URL.revokeObjectURL(preview.url);
    });
    setPreviews({});
    setErrors([]);
  };
  
  // Cleanup URLs on unmount
  React.useEffect(() => {
    return () => {
      Object.values(previews).forEach(preview => {
        if (preview) URL.revokeObjectURL(preview.url);
      });
    };
  }, []);
  
  const hasFiles = Object.values(previews).some(Boolean);
  
  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      {/* Upload area */}
      <Card className={`
        border-2 border-dashed transition-all duration-200 cursor-pointer
        ${isDragging 
          ? 'border-saffron-500 bg-saffron-50 scale-[1.02]' 
          : 'border-gray-300 hover:border-saffron-400'
        }
        ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}>
        <CardContent 
          className="p-6"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          style={{ touchAction: 'none' }} // Prevent scroll on mobile drag
        >
          <div className="text-center space-y-4">
            {/* Cultural palm icon placeholder */}
            <div className="mx-auto w-16 h-16 flex items-center justify-center bg-saffron-100 rounded-full">
              <Upload className="w-8 h-8 text-saffron-600" />
            </div>
            
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-gray-900">
                Upload Your Palm Images
              </h3>
              <p className="text-sm text-gray-600">
                Up to {maxFiles} images • JPEG or PNG • Max {maxSize}MB each
              </p>
              <p className="text-xs text-muted-foreground">
                Left palm, Right palm (optional)
              </p>
            </div>
            
            {isValidating && (
              <div className="flex items-center justify-center gap-2">
                <div className="cultural-spinner w-4 h-4" />
                <span className="text-sm text-saffron-600">Validating images...</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Action buttons */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          size="lg"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          icon={<Upload className="w-4 h-4" />}
        >
          Choose Files
        </Button>
        
        <Button
          variant="outline"
          size="lg"
          onClick={() => cameraInputRef.current?.click()}
          disabled={isUploading}
          icon={<Camera className="w-4 h-4" />}
        >
          Take Photo
        </Button>
      </div>
      
      {/* File previews */}
      {hasFiles && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Selected Images</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              disabled={isUploading}
            >
              Clear All
            </Button>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {previews.left && (
              <div className="relative">
                <img
                  src={previews.left.url}
                  alt="Left palm preview"
                  className="w-full h-24 object-cover rounded-md border border-gray-200"
                />
                <button
                  onClick={() => removePreview('left')}
                  disabled={isUploading}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
                <span className="absolute bottom-1 left-1 bg-black/50 text-white text-xs px-1 rounded">
                  Left
                </span>
              </div>
            )}
            
            {previews.right && (
              <div className="relative">
                <img
                  src={previews.right.url}
                  alt="Right palm preview"
                  className="w-full h-24 object-cover rounded-md border border-gray-200"
                />
                <button
                  onClick={() => removePreview('right')}
                  disabled={isUploading}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
                <span className="absolute bottom-1 left-1 bg-black/50 text-white text-xs px-1 rounded">
                  Right
                </span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Error messages */}
      {errors.length > 0 && (
        <div className="space-y-2">
          {errors.map((error, index) => (
            <div key={index} className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          ))}
        </div>
      )}
      
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png"
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />
      
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/jpeg,image/png"
        capture="environment" // Use back camera
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};