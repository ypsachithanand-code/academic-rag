import React from 'react';

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  iconBgColor?: string;
  iconColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  iconBgColor = 'var(--primary-light)',
  iconColor = 'var(--primary)',
}) => {
  return (
    <div className="metric-card">
      <div className="metric-icon-box" style={{ background: iconBgColor, color: iconColor }}>
        {icon}
      </div>
      <div>
        <div className="metric-val">{value}</div>
        <div className="metric-label">{label}</div>
      </div>
    </div>
  );
};
