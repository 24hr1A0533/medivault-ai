import React from "react";
import { tokens } from "../tokens";

export interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  description: string;
  category: "LAB" | "MEDICATION" | "ENCOUNTER" | "PROCEDURE";
  isAbnormal?: boolean;
}

export interface TimelineProps {
  events: TimelineEvent[];
  onSelectEvent?: (event: TimelineEvent) => void;
}

export const Timeline: React.FC<TimelineProps> = ({ events, onSelectEvent }) => {
  const getCategoryColor = (cat: string, isAbnormal?: boolean) => {
    if (isAbnormal) return tokens.colors.clinicalEmergency;
    switch (cat) {
      case "LAB":
        return tokens.colors.clinicalInfo;
      case "MEDICATION":
        return tokens.colors.brandPrimary;
      case "ENCOUNTER":
        return tokens.colors.brandSecondary;
      default:
        return tokens.colors.textSecondary;
    }
  };

  return (
    <div style={{ position: "relative", paddingLeft: "24px", borderLeft: `2px solid ${tokens.colors.surfaceBorder}` }}>
      {events.map((event) => (
        <div
          key={event.id}
          onClick={() => onSelectEvent?.(event)}
          style={{
            position: "relative",
            marginBottom: "20px",
            cursor: onSelectEvent ? "pointer" : "default",
          }}
        >
          {/* Milestone bullet */}
          <div
            style={{
              position: "absolute",
              left: "-31px",
              top: "2px",
              width: "14px",
              height: "14px",
              borderRadius: tokens.radii.full,
              backgroundColor: getCategoryColor(event.category, event.isAbnormal),
              border: "2px solid #FFFFFF",
            }}
          />
          <div style={{ fontSize: "0.75rem", color: tokens.colors.textSecondary, fontWeight: 500 }}>
            {event.date}
          </div>
          <div style={{ fontSize: "0.9375rem", fontWeight: 600, color: tokens.colors.textPrimary }}>
            {event.title}
          </div>
          <div style={{ fontSize: "0.8125rem", color: tokens.colors.textSecondary, marginTop: "4px" }}>
            {event.description}
          </div>
        </div>
      ))}
    </div>
  );
};
