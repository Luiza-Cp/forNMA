import React from "react";

// Variants: primary (default), secondary, ghost, and plain (no button chrome; the caller styles it).
function inferVariant(className = "", variant) {
  if (variant) return variant;
  if (className.includes("secondary")) return "secondary";
  if (className.includes("ghost")) return "ghost";
  return "primary";
}

function inferSize(className = "", size) {
  if (size) return size;
  if (className.includes("btn-small")) return "sm";
  return "md";
}

export function Button({ className = "", variant, size, children, ...props }) {
  const finalVariant = inferVariant(className, variant);
  const finalSize = inferSize(className, size);

  return (
    <button
      {...props}
      className={`ds-button ds-button--${finalVariant} ds-button--${finalSize}${className ? ` ${className}` : ""}`}
    >
      {children}
    </button>
  );
}
