'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className = '',
}) => {
  return (
    <Card className={`${className}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>
            <div className="flex items-baseline space-x-2">
              <p className="text-2xl font-semibold text-foreground">
                {value}
              </p>
              {trend && (
                <span
                  className={`text-xs font-medium ${
                    trend.isPositive
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">
                {description}
              </p>
            )}
          </div>
          {Icon && (
            <div className="w-8 h-8 bg-saffron-100 rounded-full flex items-center justify-center">
              <Icon className="w-4 h-4 text-saffron-600" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};