'use client';

import React from 'react';
import Image, { ImageProps } from 'next/image';
import { useState } from 'react';
import { Spinner } from './Spinner';

interface OptimizedImageProps extends Omit<ImageProps, 'onLoad' | 'onError'> {
  fallback?: string;
  showSpinner?: boolean;
  className?: string;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  fallback = '/placeholder-image.png',
  showSpinner = true,
  className = '',
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(src);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
    if (fallback && imageSrc !== fallback) {
      setImageSrc(fallback);
      setHasError(false);
    }
  };

  return (
    <div className={`relative ${className}`}>
      {isLoading && showSpinner && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
          <Spinner size="sm" />
        </div>
      )}
      
      <Image
        {...props}
        src={imageSrc}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        className={`transition-opacity duration-300 ${
          isLoading ? 'opacity-0' : 'opacity-100'
        }`}
        quality={85}
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyLli+Kzh3r39vXPi+KXLJ9/wBHGWTh+8jKy2sMbzWWvZhW4WaQWNMaGPDbaBOhUEOhOJgYGZMCJRG0Qm1JmZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/VeVYzq0DQW7VnSgvd4r5mZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/VeVYzq0DQW7VnSgvd4r5mZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/VeVYzq0DQW7VnSgvd4r5mZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/VeVYzq0DQW7VnSgvd4r5mZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/VeVYzq0DQW7VnSgvd4r5mZfFJNZ5jjQOr+fqAytVd2+HnVUoeDnXGjzBcEGNHZ5CaiBECQQU1fjAJGQKAqSAHDlhGaRDKqzCqWLW+I7QKtRidEJGZiBYt1oqEj5gIEzHY9SBhM5zcOXuY6EHzqR9/Vedp//9k="
      />
      
      {hasError && !fallback && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded">
          <div className="text-center text-gray-500">
            <div className="text-2xl mb-2">🖼️</div>
            <p className="text-sm">Image not available</p>
          </div>
        </div>
      )}
    </div>
  );
};