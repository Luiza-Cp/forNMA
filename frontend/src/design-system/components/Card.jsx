import React from "react";

export function Card({ as: Component = "div", className = "", variant = "panel", children, ...props }) {
  return (
    <Component
      {...props}
      className={`ds-card ds-card--${variant}${className ? ` ${className}` : ""}`}
    >
      {children}
    </Component>
  );
}
