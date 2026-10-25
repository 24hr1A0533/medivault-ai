import React from "react";
import { tokens } from "../tokens";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "emergency" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  isLoading = false,
  children,
  style,
  disabled,
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    fontFamily: tokens.typography.fontSans,
    fontWeight: 600,
    borderRadius: tokens.radii.md,
    cursor: disabled || isLoading ? "not-allowed" : "pointer",
    opacity: disabled || isLoading ? 0.6 : 1,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    border: "none",
    transition: "all 0.15s ease-in-out",
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: "6px 12px", fontSize: "0.8125rem" },
    md: { padding: "10px 18px", fontSize: "0.9375rem" },
    lg: { padding: "14px 24px", fontSize: "1.0625rem" },
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: tokens.colors.brandPrimary,
      color: "#FFFFFF",
    },
    secondary: {
      backgroundColor: tokens.colors.surfaceLight,
      color: tokens.colors.textPrimary,
      border: `1px solid ${tokens.colors.surfaceBorder}`,
    },
    emergency: {
      backgroundColor: tokens.colors.clinicalEmergency,
      color: "#FFFFFF",
      boxShadow: `0 0 12px ${tokens.colors.clinicalEmergencyGlow}`,
    },
    ghost: {
      backgroundColor: "transparent",
      color: tokens.colors.brandPrimary,
    },
  };

  return (
    <button
      style={{
        ...baseStyle,
        ...sizeStyles[size],
        ...variantStyles[variant],
        ...style,
      }}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? "Processing..." : children}
    </button>
  );
};
