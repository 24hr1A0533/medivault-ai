import React from "react";
import { tokens } from "../tokens";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  accentColor?: string;
  hasEmergencyBorder?: boolean;
}

export const Card: React.FC<CardProps> = ({
  accentColor,
  hasEmergencyBorder = false,
  children,
  style,
  ...props
}) => {
  return (
    <div
      style={{
        backgroundColor: tokens.colors.surfacePanel,
        borderRadius: tokens.radii.lg,
        border: hasEmergencyBorder
          ? `2px solid ${tokens.colors.clinicalEmergency}`
          : `1px solid ${tokens.colors.surfaceBorder}`,
        borderLeft: accentColor ? `5px solid ${accentColor}` : undefined,
        padding: "20px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
